"""Config file for tests."""
import asyncio
import random
import typing

import fastapi
import httpx
import psycopg2
import pytest
from _pytest.monkeypatch import MonkeyPatch
from fastapi import Depends, Request, Response
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from pytest_alembic import Config, runner
from sqlalchemy import create_engine
from sqlalchemy.engine import URL, Engine
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import Session, close_all_sessions, scoped_session, sessionmaker

import redis.asyncio as aioredis
from apps.CORE.db import async_session_factory as AsyncSessionFactory  # noqa
from apps.CORE.db import session_factory as SessionFactory  # noqa
from apps.CORE.deps import get_async_session, get_redis, get_session
from apps.CORE.deps.limiters import SlidingWindowRateLimiter
from settings import Settings
from tests.apps.CORE.factories import (
    GroupFactory,
    GroupRoleFactory,
    GroupUserFactory,
    PermissionFactory,
    PermissionUserFactory,
    RoleFactory,
    RolePermissionFactory,
    RoleUserFactory,
    UserFactory,
)
from tests.apps.wishmaster.factories import CategoryFactory, TagFactory, WishFactory, WishListFactory, WishTagFactory
from tests.bases import BaseModelFactory


@pytest.fixture(scope="session", autouse=True)
def _mock_db_url(monkeypatch_session: MonkeyPatch) -> None:
    """Change all PostgreSQL URLs and environments to use `test` database."""
    db_url: URL = Settings.POSTGRES_URL
    async_db_url: URL = Settings.POSTGRES_URL_ASYNC
    monkeypatch_session.setattr(target=Settings, name="POSTGRES_URL", value=db_url.set(database="test"))
    monkeypatch_session.setattr(target=Settings, name="POSTGRES_URL_ASYNC", value=async_db_url.set(database="test"))
    monkeypatch_session.setenv(name="POSTGRES_DB", value="test")
    monkeypatch_session.setattr(target=Settings, name="POSTGRES_DB", value="test")


@pytest.fixture(scope="session", autouse=True)
def _create_database(_mock_db_url: None) -> typing.Generator[None, None, None]:
    """Recreates `test` database for tests."""
    con = psycopg2.connect(
        f"postgresql://{Settings.POSTGRES_USER}:{Settings.POSTGRES_PASSWORD}@"
        f"{Settings.POSTGRES_HOST}:{Settings.POSTGRES_PORT}"
    )

    con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    cursor = con.cursor()
    cursor.execute(f"""DROP DATABASE IF EXISTS {Settings.POSTGRES_DB};""")
    cursor.execute(f"""CREATE DATABASE {Settings.POSTGRES_DB};""")
    yield
    cursor.execute(f"""DROP DATABASE IF EXISTS {Settings.POSTGRES_DB};""")
    close_all_sessions()


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

    def raise_mock(*args, **kwargs):  # type: ignore
        """Thrown and exception when tests try to use HTTP connection.

        Raises:
            RuntimeError: indicates that HTTPS request found.
        """
        raise RuntimeError(f"Found request: {args}, {kwargs}")

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
async def _mock_sessions_factories(async_db_engine: AsyncEngine, sync_db_engine: Engine) -> None:
    """Mocks session_factory and async_session_factory from `apps.CORE.sessions`.

    Notes:
        This should prevent errors with middlewares, that are using these methods.
    """
    AsyncSessionFactory.configure(bind=async_db_engine)
    SessionFactory.configure(bind=sync_db_engine)


@pytest.fixture()
async def app_fixture(
    db_session: AsyncSession, sync_db_session: Session, event_loop: asyncio.AbstractEventLoop, monkeypatch
) -> fastapi.FastAPI:
    """Overrides dependencies for FastAPI and returns FastAPI instance (app).

    Yields:
        app (fastapi.FastAPI): Instance of FastAPI ASGI application.
    """

    async def override_get_async_session() -> AsyncSession:
        """Replace `get_async_session` dependency with AsyncSession from `db_session` fixture."""
        return db_session

    def override_get_session() -> Session:
        """Replace `get_session` dependency with Session from `sync_db_session` fixture."""
        return sync_db_session

    from apps.main import app

    app.dependency_overrides[get_async_session] = override_get_async_session
    app.dependency_overrides[get_session] = override_get_session
    return app


@pytest.fixture(scope="session", autouse=True)
async def _mock_limiters(monkeypatch_session: MonkeyPatch) -> None:
    async def limiter_mock(
        self, *, request: Request, response: Response, redis_client: aioredis.Redis = Depends(get_redis)
    ):
        return True

    monkeypatch_session.setattr(target=SlidingWindowRateLimiter, name="__call__", value=limiter_mock, raising=False)


@pytest.fixture()
async def async_client(app_fixture: fastapi.FastAPI, event_loop: asyncio.AbstractEventLoop) -> httpx.AsyncClient:
    """Prepare async HTTP client with FastAPI app context.

    Yields:
        httpx_client (httpx.AsyncClient): Instance of AsyncClient to perform a requests to API.
    """
    async with httpx.AsyncClient(
        app=app_fixture, base_url=f"http://{Settings.HOST}:{Settings.PORT}"  # noqa
    ) as httpx_client:
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
def alembic_engine(sync_db_engine: Engine) -> Engine:
    """Proxy sync_db_engine to pytest_alembic (make it as a default engine)."""
    return sync_db_engine


@pytest.fixture(scope="session")
def alembic_runner(alembic_config: Config, alembic_engine: Engine) -> typing.Generator[runner, None, None]:
    """Setup runner for pytest_alembic (combine Config and engine)."""
    config = Config.from_raw_config(alembic_config)
    with runner(config=config, engine=alembic_engine) as alembic_runner:
        yield alembic_runner


@pytest.fixture(scope="session", autouse=True)
def _apply_migrations(
    _create_database: None, alembic_runner: runner, alembic_engine: Engine
) -> typing.Generator[None, None, None]:
    """Applies all migrations from base to head (via pytest_alembic)."""
    alembic_runner.migrate_up_to(revision="head")
    yield
    alembic_runner.migrate_down_to(revision="base")


@pytest.fixture(scope="session")
def sync_db_engine() -> Engine:
    """Create sync database engine and dispose it after all tests.

    Yields:
        engine (Engine): SQLAlchemy Engine instance.
    """
    engine = create_engine(url=Settings.POSTGRES_URL, echo=Settings.POSTGRES_ECHO)
    try:
        yield engine
    finally:
        engine.dispose()
        close_all_sessions()


@pytest.fixture(scope="session")
async def async_db_engine(event_loop: asyncio.AbstractEventLoop) -> AsyncEngine:
    """Create async database engine and dispose it after all tests.

    Yields:
        async_engine (AsyncEngine): SQLAlchemy AsyncEngine instance.
    """
    async_engine = create_async_engine(url=Settings.POSTGRES_URL_ASYNC, echo=Settings.POSTGRES_ECHO)
    try:
        yield async_engine
    finally:
        await async_engine.dispose()
        close_all_sessions()


@pytest.fixture()
def sync_session_factory(sync_db_engine: Engine) -> sessionmaker:
    """Create async session factory."""
    return sessionmaker(bind=sync_db_engine, expire_on_commit=False, class_=Session)


@pytest.fixture()
def sync_db_session(sync_session_factory: sessionmaker) -> typing.Generator[Session, None, None]:
    """Create sync session for database and rollback it after test."""
    with sync_session_factory() as session:
        try:
            yield session
        finally:
            session.rollback()
            session.close()


@pytest.fixture()
async def session_factory(async_db_engine: AsyncEngine) -> sessionmaker:
    """Create async session factory."""
    return sessionmaker(bind=async_db_engine, expire_on_commit=False, class_=AsyncSession)


@pytest.fixture()
async def db_session(session_factory: sessionmaker) -> typing.AsyncGenerator[AsyncSession, None]:
    """Create async session for database and rollback it after test."""
    async with session_factory() as async_session:
        try:
            yield async_session
        finally:
            await async_session.rollback()
            await async_session.close()


@pytest.fixture(scope="session")
def scoped_db_session() -> scoped_session:
    """Create scoped session for tests runner and model factories."""
    session = scoped_session(session_factory=SessionFactory)
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(autouse=True, scope="session")
def _set_session_for_factories(scoped_db_session: scoped_session) -> None:
    """Registration of model factories to set up a scoped session during the test run."""
    known_factories: list[type[BaseModelFactory]] = [
        UserFactory,
        WishListFactory,
        WishFactory,
        CategoryFactory,
        TagFactory,
        WishTagFactory,
        PermissionFactory,
        RolePermissionFactory,
        RoleFactory,
        GroupRoleFactory,
        GroupFactory,
        PermissionUserFactory,
        RoleUserFactory,
        GroupUserFactory,
        # === Add new factory classes here!!! ===
    ]

    for factory_class in known_factories:
        # Set up session to factory
        factory_class._meta.sqlalchemy_session = scoped_db_session
