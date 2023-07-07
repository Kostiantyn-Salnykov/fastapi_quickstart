__all__ = (
    "get_async_session",
    "get_session",
    "get_redis",
)

import typing

from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

import redis.asyncio as aioredis
from apps.CORE.db import async_session_factory, redis_engine, session_factory
from apps.CORE.handlers import integrity_error_handler, no_result_found_error_handler
from loggers import get_logger

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


def get_session() -> typing.Generator[Session, None, None]:
    """Creates FastAPI dependency for generation of SQLAlchemy Session.

    Yields:
        Session: SQLAlchemy Session.
    """
    with session_factory() as session:
        try:
            yield session
            session.commit()
        except IntegrityError as error:
            session.rollback()
            integrity_error_handler(error=error)
        except NoResultFound as error:
            session.rollback()
            no_result_found_error_handler(error=error)
        finally:
            session.close()


async def get_redis() -> typing.AsyncGenerator[aioredis.Redis, None]:
    async with redis_engine.client() as conn:
        try:
            yield conn
        except aioredis.RedisError as error:
            logger.warning(msg=error)
        finally:
            await conn.close()
