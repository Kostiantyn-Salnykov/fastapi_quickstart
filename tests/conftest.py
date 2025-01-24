"""Config file for tests."""

import asyncio
import random
import typing

import fastapi
import httpx
import psycopg2
import pytest
import redis.asyncio as aioredis
from _pytest.monkeypatch import MonkeyPatch
from fastapi import Depends, Request, Response
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from pytest_alembic import Config, runner
from sqlalchemy.engine import URL, Engine
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import close_all_sessions

from core.db.bases import async_session_factory as AsyncSessionFactory  # noqa
from core.deps import get_async_session, get_redis
from core.deps.limiters import SlidingWindowRateLimiter
from src.settings import Settings


@pytest.fixture(scope="session", autouse=True)
def _mock_db_url(monkeypatch_session: MonkeyPatch) -> None:
    """Change all PostgreSQL URLs and environments to use `test` database."""
    async_db_url: URL = Settings.APP_RDMS_URL
    monkeypatch_session.setattr(target=Settings, name="APP_RDMS_URL", value=async_db_url.set(database="test"))
    monkeypatch_session.setenv(name="APP_RDMS_DB", value="test")
    monkeypatch_session.setattr(target=Settings, name="APP_RDMS_DB", value="test")


@pytest.fixture(scope="session", autouse=True)
def _create_database(_mock_db_url: None) -> typing.Generator[None, None, None]:
    """Recreates `test` database for tests."""
    con = psycopg2.connect(
        f"postgresql://{Settings.APP_RDMS_USER}:{Settings.APP_RDMS_PASSWORD}@"
        f"{Settings.APP_RDMS_HOST}:{Settings.APP_RDMS_PORT}",
    )

    con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    cursor = con.cursor()
    cursor.execute(f"""DROP DATABASE IF EXISTS {Settings.APP_RDMS_DB};""")
    cursor.execute(f"""CREATE DATABASE {Settings.APP_RDMS_DB};""")
    yield
    close_all_sessions()
    cursor.execute(f"""DROP DATABASE IF EXISTS {Settings.APP_RDMS_DB};""")


@pytest.fixture(scope="session")
def monkeypatch_session() -> MonkeyPatch:
    """Create monkeypatch for session scope.

    Yields:
        monkeypatch (MonkeyPatch): MonkeyPatch instance with `session` (one time per tests run) scope.
    """
    monkeypatch = MonkeyPatch()
    try:
        yield monkeypatch
    finally:
        monkeypatch.undo()


@pytest.fixture(scope="session", autouse=True)
def _no_http_requests(monkeypatch_session: MonkeyPatch) -> None:
    """Disable HTTP requests for 3-rd party libraries.

    Notes:
        This isn't working with `httpx`, because it uses in tests to call Back-end API endpoints.
    """

    def raise_mock(*args, **kwargs) -> None:  # type: ignore
        """Thrown and exception when tests try to use HTTP connection.

        Raises:
            RuntimeError: indicates that HTTPS request found.
        """
        msg = f"Found request: {args}, {kwargs}"
        raise RuntimeError(msg)

    # Disable library `urllib3`
    monkeypatch_session.setattr(target="urllib3.connectionpool.HTTPConnectionPool.urlopen", name=raise_mock)
    # Disable library `urllib`
    monkeypatch_session.setattr(target="urllib.request.urlopen", name=raise_mock)
    # Disable BackgroundTasks
    monkeypatch_session.setattr(target="fastapi.BackgroundTasks.add_task", name=raise_mock)
    # Disable library `requests`
    monkeypatch_session.setattr(target="requests.sessions.Session.request", name=raise_mock)


@pytest.fixture(scope="session", autouse=True)
def event_loop() -> typing.Generator[asyncio.AbstractEventLoop, None, None]:
    """Create asyncio (uvloop) for tests runtime.

    Yields:
        loop (asyncio.AbstractEventLoop): Shared with FastAPI, asyncio instance loop, that created for test runs.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    try:
        yield loop
    finally:
        loop.close()


@pytest.fixture(scope="session", autouse=True)
async def _mock_sessions_factories(async_db_engine: AsyncEngine) -> None:
    """Mocks session_factory and async_session_factory from `core.sessions`.

    Notes:
        This should prevent errors with middlewares, that are using these methods.
    """
    AsyncSessionFactory.configure(bind=async_db_engine)


@pytest.fixture
async def app_fixture(
    db_session: AsyncSession,
    event_loop: asyncio.AbstractEventLoop,
    monkeypatch: MonkeyPatch,
) -> fastapi.FastAPI:
    """Overrides dependencies for FastAPI and returns FastAPI instance (app).

    Yields:
        app (fastapi.FastAPI): Instance of FastAPI ASGI application.
    """

    async def override_get_async_session() -> AsyncSession:
        """Replace `get_async_session` dependency with AsyncSession from `db_session` fixture."""
        return db_session

    from src.api.__main__ import app

    app.dependency_overrides[get_async_session] = override_get_async_session
    return app


@pytest.fixture(scope="session", autouse=True)
async def _mock_limiters(monkeypatch_session: MonkeyPatch) -> None:
    async def limiter_mock(
        self,
        *,
        request: Request,
        response: Response,
        redis_client: aioredis.Redis = Depends(get_redis),
    ) -> bool:
        return True

    monkeypatch_session.setattr(target=SlidingWindowRateLimiter, name="__call__", value=limiter_mock, raising=False)


@pytest.fixture
async def async_client(app_fixture: fastapi.FastAPI, event_loop: asyncio.AbstractEventLoop) -> httpx.AsyncClient:
    """Prepare async HTTP client with FastAPI app context.

    Yields:
        httpx_client (httpx.AsyncClient): Instance of AsyncClient to perform a requests to API.
    """
    async with httpx.AsyncClient(app=app_fixture, base_url=f"http://{Settings.SERVER_HOST}:{Settings.SERVER_PORT}") as httpx_client:
        yield httpx_client


@pytest.fixture(autouse=True)
def faker_seed() -> None:
    """Generate random seed for Faker instance."""
    return random.seed(version=3)


@pytest.fixture(scope="session")
def alembic_config() -> Config:
    """Initialize pytest_alembic Config."""
    return Config()


@pytest.fixture(scope="session")
def alembic_engine(async_db_engine: AsyncEngine) -> AsyncEngine:
    """Proxy async_db_engine to pytest_alembic (make it as a default engine)."""
    return async_db_engine


@pytest.fixture(scope="session")
def alembic_runner(alembic_config: Config, alembic_engine: Engine) -> typing.Generator[runner, None, None]:
    """Setup runner for pytest_alembic (combine Config and engine)."""
    config = Config.from_raw_config(alembic_config)
    with runner(config=config, engine=alembic_engine) as alembic_runner:
        yield alembic_runner


@pytest.fixture(scope="session", autouse=True)
def _apply_migrations(
    _create_database: None,
    alembic_runner: runner,
    alembic_engine: Engine,
) -> typing.Generator[None, None, None]:
    """Applies all migrations from base to head (via pytest_alembic)."""
    alembic_runner.migrate_up_to(revision="head")
    yield
    alembic_runner.migrate_down_to(revision="base")


@pytest.fixture(scope="session")
async def async_db_engine(event_loop: asyncio.AbstractEventLoop) -> AsyncEngine:
    """Create async database engine and dispose it after all tests.

    Yields:
        async_engine (AsyncEngine): SQLAlchemy AsyncEngine instance.
    """
    async_engine = create_async_engine(url=Settings.APP_RDMS_URL, echo=Settings.APP_RDMS_ECHO)
    try:
        yield async_engine
    finally:
        close_all_sessions()
        await async_engine.dispose()


@pytest.fixture
async def session_factory(async_db_engine: AsyncEngine) -> async_sessionmaker:
    """Create async session factory."""
    return async_sessionmaker(bind=async_db_engine, expire_on_commit=False, class_=AsyncSession)


@pytest.fixture
async def db_session(session_factory: async_sessionmaker) -> typing.AsyncGenerator[AsyncSession, None]:
    """Create async session for database and rollback it after test."""
    async with session_factory() as async_session:
        try:
            yield async_session
        except Exception as error:
            await async_session.rollback()
            raise error
        finally:
            await async_session.rollback()
            await async_session.close()
