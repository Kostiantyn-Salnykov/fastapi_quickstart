import typing
import urllib.parse

import aioredis
from fastapi import Query, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import UnaryExpression

from apps.CORE.db import async_session_factory, redis, session_factory
from apps.CORE.handlers import integrity_error_handler
from apps.CORE.schemas import ObjectsVar, PaginationOutSchema
from apps.CORE.types import ModelColumnVar, ModelType, SchemaType
from loggers import get_logger

logger = get_logger(name=__name__)


class BasePagination:
    def __init__(self) -> None:
        self.offset = 0
        self.limit = 100

    def __call__(
        self,
        offset: int = Query(default=0, ge=0, description="Number of records to skip."),
        limit: int = Query(default=100, ge=1, lt=1000, description="Number of records to return per request."),
    ) -> "BasePagination":
        self.offset = offset
        self.limit = limit
        return self

    def next(self) -> dict[str, int]:
        return {"offset": self.offset + self.limit, "limit": self.limit}

    def previous(self) -> dict[str, int]:
        return {"offset": val if (val := self.offset - self.limit) >= 0 else 0, "limit": self.limit}

    @staticmethod
    def get_paginated_response(
        pagination: "BasePagination",
        request: Request,
        objects: list[ObjectsVar],
        schema: SchemaType,
        total: int,
        endpoint_name: str,
    ) -> PaginationOutSchema:
        offset, limit = pagination.offset, pagination.limit
        previous_uri = (
            request.url_for(name=endpoint_name) + "?" + urllib.parse.urlencode(query=pagination.previous())
            if offset > 0
            else None
        )
        next_uri = (
            request.url_for(name=endpoint_name) + "?" + urllib.parse.urlencode(query=pagination.next())
            if total > limit and len(objects)
            else None
        )
        return PaginationOutSchema[schema](
            objects=(schema.from_orm(obj=obj) for obj in objects),
            offset=offset,
            limit=limit,
            count=total,
            previous_uri=previous_uri,
            next_uri=next_uri,
        )


class BaseSorting:
    def __init__(self, model: typing.Type[ModelType], available_columns: list[ModelColumnVar] | None = None):
        self.model = model
        self.available_columns = available_columns or []
        self.available_columns_names = [col.key for col in self.available_columns]

    def __call__(self, sorting: list[str] = Query(default=None)) -> list[UnaryExpression]:
        return self.build_sorting(sorting=sorting)

    def build_sorting(self, sorting: list[str]) -> list[UnaryExpression]:
        result = []
        for column in sorting or ["-created_at"]:
            raw_column = column.strip().removeprefix("-").removeprefix("+")
            if hasattr(self.model, raw_column) and raw_column in self.available_columns_names:
                ordering_method = "desc" if column.startswith("-") else "asc"  # Choose method to use: .acs() OR .desc()
                col_attr = getattr(self.model, raw_column)  # e.g. Get model attribute dynamically: Model.<raw_column>
                result.append(getattr(col_attr, ordering_method)())  # e.g. Model.<raw_column>.desc()
        return result


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
        finally:
            session.close()


async def get_redis() -> typing.AsyncGenerator[aioredis.Redis, None]:
    async with redis.client() as conn:
        try:
            yield conn
        except Exception as error:
            logger.warning(msg=error)
        finally:
            await conn.close()
