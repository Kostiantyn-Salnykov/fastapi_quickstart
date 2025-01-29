__all__ = ("AsyncSessionDependency", "RedisDependency", "get_async_session", "get_redis")

import typing

from core.custom_logging import get_logger
from core.db.bases import async_session_factory, redis_engine
from fastapi import Depends
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

import redis.asyncio as aioredis
from src.api.exception_handlers import integrity_error_handler, no_result_found_error_handler

logger = get_logger(name=__name__)


async def get_async_session() -> typing.AsyncGenerator[AsyncSession, None]:  # pragma: no cover
    """Creates FastAPI dependency for generation of SQLAlchemy AsyncSession.

    Yields:
        AsyncSession: SQLAlchemy AsyncSession.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except IntegrityError as error:
            await session.rollback()
            integrity_error_handler(error=error)
        except NoResultFound as error:
            await session.rollback()
            no_result_found_error_handler(error=error)
        finally:
            await session.close()


async def get_redis() -> typing.AsyncGenerator[aioredis.Redis, None]:
    async with redis_engine.client() as conn:
        try:
            yield conn
        except aioredis.RedisError as error:
            logger.warning(msg=error)
        finally:
            await conn.aclose()


AsyncSessionDependency = typing.Annotated[AsyncSession, Depends(get_async_session)]
RedisDependency = typing.Annotated[aioredis.Redis, Depends(get_redis)]
