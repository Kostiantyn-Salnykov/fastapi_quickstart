import contextlib
import datetime
import typing

import sqlalchemy.ext.asyncio
import sqlalchemy.orm
from fastapi import APIRouter, Depends, FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import ORJSONResponse
from sqlalchemy import text
from starlette.middleware.authentication import AuthenticationMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

import redis.asyncio as redis
import redis.exceptions
from apps.authorization.managers import AuthorizationManager
from apps.authorization.middlewares import JWTTokenBackend
from apps.authorization.routers import groups_router, permissions_router, roles_router
from apps.CORE.db import async_engine, async_session_factory, engine, redis_engine, session_factory
from apps.CORE.deps import get_async_session, get_redis, get_session
from apps.CORE.enums import JSENDStatus
from apps.CORE.exceptions import BackendError, RateLimitError
from apps.CORE.handlers import backend_exception_handler, rate_limit_exception_handler, validation_exception_handler
from apps.CORE.managers import TokensManager
from apps.CORE.responses import Responses
from apps.CORE.schemas.responses import JSENDResponse
from apps.users.routers import register_router, tokens_router, users_router
from apps.wishmaster.routers import wish_router, wishlist_router
from loggers import get_logger, setup_logging
from settings import Settings

logger = get_logger(name=__name__)


def enable_logging() -> None:
    setup_logging()
    logger.debug(msg="Logging configuration completed.")


async def _check_sync_engine() -> None:
    logger.debug(msg="Checking connection with sync engine 'SQLAlchemy + psycopg2'...")
    with session_factory() as session:
        result = session.execute(statement=text("SELECT current_timestamp;")).scalar()
    logger.debug(msg=f"Result of sync 'SELECT current_timestamp;' is: {result.isoformat() if result else result}")


async def _check_async_engine() -> None:
    logger.debug(msg="Checking connection with async engine 'SQLAlchemy + asyncpg'...")
    async with async_session_factory() as async_session:
        result = await async_session.execute(statement=text("SELECT current_timestamp;"))
        result = result.scalar()
    logger.debug(msg=f"Result of async 'SELECT current_timestamp;' is: {result.isoformat() if result else result}")


async def _setup_redis(app: FastAPI) -> None:
    logger.debug(msg="Setting up global Redis `app.redis`...")
    # proxy Redis client to request.app.state.redis
    app.redis = redis_engine
    logger.debug(msg="Checking connection with Redis...")
    try:
        async with app.redis.client() as conn:
            result = await conn.ping()
            if result is not True:
                msg = "Connection to Redis failed."
                logger.error(msg=msg)
                raise RuntimeError(msg)
            logger.debug(msg=f"Result of Redis 'PING' command: {result}")
    except redis.exceptions.ConnectionError as e:
        logger.error(msg=e)


async def _dispose_all_connections() -> None:
    logger.debug(msg="Closing PostgreSQL connections...")
    await async_engine.dispose()  # Close sessions to async engine
    engine.dispose()  # Close sessions to sync engine
    logger.debug(msg="All PostgreSQL connections closed.")


async def _close_redis(app: FastAPI) -> None:
    logger.debug(msg="Closing Redis connection...")
    await app.redis.close(close_connection_pool=True)
    logger.debug(msg="Redis connection closed.")


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> typing.AsyncGenerator[None, None]:
    setup_logging()
    logger.info(msg="Lifespan started.")
    await _setup_redis(app=app)
    await _check_sync_engine()
    await _check_async_engine()
    yield
    await _close_redis(app=app)
    await _dispose_all_connections()
    logger.info(msg="Lifespan ended.")


app = FastAPI(
    debug=Settings.DEBUG,
    title="FastAPI Quickstart",
    description="",
    version="0.0.1",
    openapi_url="/openapi.json" if Settings.ENABLE_OPENAPI else None,
    redoc_url=None,  # Redoc disabled
    docs_url="/docs/" if Settings.ENABLE_OPENAPI else None,
    default_response_class=ORJSONResponse,
    responses=Responses.BASE,
    lifespan=lifespan,
)

# State objects
app.state.tokens_manager = TokensManager(
    secret_key=Settings.TOKENS_SECRET_KEY,
    default_token_lifetime=datetime.timedelta(seconds=Settings.TOKENS_ACCESS_LIFETIME_SECONDS),
)
app.state.authorization_manager = AuthorizationManager(engine=engine)

# Add exception handlers (<Error type>, <Error handler>)
app.add_exception_handler(BackendError, backend_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(RateLimitError, rate_limit_exception_handler)

# Add middlewares stack (FIRST IN => LATER EXECUTION)
app.add_middleware(middleware_class=GZipMiddleware, minimum_size=512)  # №5
# app.add_middleware(middleware_class=CasbinMiddleware, enforcer=enforcer)  # №4
app.add_middleware(
    middleware_class=AuthenticationMiddleware,
    backend=JWTTokenBackend(scheme_prefix="Bearer"),
    on_error=lambda conn, exc: ORJSONResponse(
        content={"status": JSENDStatus.FAIL, "data": None, "message": str(exc), "code": status.HTTP_401_UNAUTHORIZED},
        status_code=status.HTTP_401_UNAUTHORIZED,
    ),
)  # №3
app.add_middleware(
    middleware_class=CORSMiddleware,
    allow_origins=Settings.CORS_ALLOW_ORIGINS,
    allow_credentials=Settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=Settings.CORS_ALLOW_METHODS,
    allow_headers=Settings.CORS_ALLOW_HEADERS,
)  # №2
app.add_middleware(middleware_class=ProxyHeadersMiddleware, trusted_hosts=Settings.TRUSTED_HOSTS)  # №1


api_router = APIRouter()


@api_router.get(
    path="/",
    response_model=JSENDResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check.",
    description="Health check endpoint.",
)
async def healthcheck(
    request: Request,
    redis: redis.Redis = Depends(get_redis),
    async_session: sqlalchemy.ext.asyncio.AsyncSession = Depends(get_async_session),
    session: sqlalchemy.orm.Session = Depends(get_session),
) -> ORJSONResponse:
    """Check that API endpoints works properly.

    Returns:
        ORJSONResponse: json object with JSENDResponseSchema body.
    """
    if Settings.DEBUG:
        async_result = await async_session.execute(statement=text("SELECT true;"))
        data = {
            "redis": await redis.ping(),
            "postgresql_sync": session.execute(statement=text("SELECT true;")).scalar_one(),
            "postgresql_async": async_result.scalar_one(),
        }
    else:
        data = None
    return ORJSONResponse(
        content={
            "status": JSENDStatus.SUCCESS,
            "data": data,
            "message": "Health check.",
            "code": status.HTTP_200_OK,
        },
        status_code=status.HTTP_200_OK,
    )


API_PREFIX = "/api/v1"
# Include routers:
app.include_router(router=api_router, prefix=API_PREFIX)
app.include_router(router=wishlist_router, prefix=API_PREFIX)
app.include_router(router=wish_router, prefix=API_PREFIX)
app.include_router(router=register_router, prefix=API_PREFIX)
app.include_router(router=users_router, prefix=API_PREFIX)
app.include_router(router=tokens_router, prefix=API_PREFIX)
app.include_router(router=groups_router, prefix=API_PREFIX)
app.include_router(router=roles_router, prefix=API_PREFIX)
app.include_router(router=permissions_router, prefix=API_PREFIX)


if __name__ == "__main__":  # pragma: no cover
    # Use this for debugging purposes only
    import uvicorn

    uvicorn.run(
        app="apps.main:app",
        host=Settings.HOST,
        port=Settings.PORT,
        loop="uvloop",
        reload=True,
        reload_delay=5,
        log_level=Settings.LOG_LEVEL,
        use_colors=Settings.LOG_USE_COLORS,
    )
