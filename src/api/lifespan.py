import contextlib
import typing

from core.custom_logging import get_logger, setup_logging
from core.db.bases import async_engine, async_session_factory, redis_engine
from fastapi import FastAPI
from sqlalchemy import text

import redis.exceptions

logger = get_logger(name=__name__)


def enable_logging() -> None:
    """Initializing the logging."""
    setup_logging()
    logger.success(msg="Logging configuration completed.")


async def _check_async_engine() -> None:
    """Checks that back-end can query the PostgreSQL from SQLAlchemy with async session."""
    logger.debug("Checking connection with async engine 'SQLAlchemy + asyncpg'...")
    async with async_session_factory() as async_session:
        result = await async_session.execute(statement=text("SELECT current_timestamp;"))
        result = result.scalar()
    logger.success(f"Result of async 'SELECT current_timestamp;' is: {result.isoformat() if result else result}")


async def _setup_redis(app: FastAPI) -> None:
    """Initialize global connection to Redis."""
    logger.debug("Setting up global Redis `app.redis`...")
    # proxy Redis client to request.app.state.redis
    app.redis = redis_engine
    logger.debug("Checking connection with Redis...")
    try:
        async with app.redis.client() as conn:
            result = await conn.ping()
            if result is not True:
                msg = "Connection to Redis failed."
                logger.error(msg)
                raise RuntimeError(msg)
            logger.success(f"Result of Redis 'PING' command: {result}")
    except redis.exceptions.ConnectionError as e:
        logger.error(e)


async def _dispose_all_connections() -> None:
    """Closes connections to PostgreSQL."""
    logger.debug("Closing PostgreSQL connections...")
    await async_engine.dispose()  # Close sessions to async engine
    logger.success("All PostgreSQL connections closed.")


async def _close_redis(app: FastAPI) -> None:
    """Closes connection to a Redis client."""
    logger.debug("Closing Redis connection...")
    await app.redis.close(close_connection_pool=True)
    logger.success("Redis connection closed.")


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> typing.AsyncGenerator[None, None]:
    """FastAPI global initializer/destructor."""
    enable_logging()
    logger.info("Lifespan started.")
    await _setup_redis(app=app)
    await _check_async_engine()
    yield
    await _close_redis(app=app)
    await _dispose_all_connections()
    logger.info("Lifespan ended.")
