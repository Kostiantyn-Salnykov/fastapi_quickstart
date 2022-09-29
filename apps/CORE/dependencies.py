import typing
import urllib.parse

from fastapi import Query, Request
from sqlalchemy import Column
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.elements import UnaryExpression

from apps.CORE.db import Base, async_session_factory, session_factory
from apps.CORE.handlers import integrity_error_handler
from apps.CORE.schemas import ObjectsVar, PaginationOutSchema, SchemaVar

DBModelVar = typing.TypeVar(name="DBModelVar", bound=Base)
DBModelColumnVar = typing.TypeVar(name="DBModelColumnVar", bound=Column)


class BasePagination:
    def __init__(self):
        self.offset = 0
        self.limit = 100

    def __call__(
        self,
        offset: int = Query(default=0, ge=0, description="Number of records to skip."),
        limit: int = Query(default=100, ge=1, lt=1000, description="Number of records to return per request."),
    ):
        self.offset = offset
        self.limit = limit
        return self

    def next(self) -> dict[str, int]:
        return {"offset": self.offset + self.limit, "limit": self.limit}

    def previous(self) -> dict[str, int]:
        return {"offset": self.offset - self.limit or 0, "limit": self.limit}

    @staticmethod
    def get_paginated_response(
        pagination: "BasePagination",
        request: Request,
        objects: list[ObjectsVar],
        schema: SchemaVar,
        total: int,
    ) -> PaginationOutSchema:
        offset, limit = pagination.offset, pagination.limit
        previous_uri = (
            request.url_for(name="list_to_do") + urllib.parse.urlencode(query=pagination.previous())
            if offset > 0
            else None
        )
        next_uri = (
            request.url_for(name="list_to_do") + urllib.parse.urlencode(query=pagination.next())
            if total > limit and len(objects)
            else None
        )
        return PaginationOutSchema[schema](
            objects=(schema.from_orm(obj=obj) for obj in objects),
            offset=offset,
            limit=limit,
            previous_uri=previous_uri,
            next_uri=next_uri,
        )


class BaseSorting:
    def __init__(self, model: typing.Type[DBModelVar], available_columns: list[DBModelColumnVar] = None):
        self.model = model
        self.available_columns = available_columns or []
        self.available_columns_names = [col.key for col in self.available_columns]

    def __call__(self, sorting: list[str] = Query(default=None)):
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


async def get_async_session():
    """Creates FastAPI dependency for generation of SQLAlchemy AsyncSession.

    Yields:
        AsyncSession: SQLAlchemy AsyncSession.
    """
    async with async_session_factory() as session:
        try:
            yield session
        except IntegrityError as error:
            await session.rollback()
            integrity_error_handler(error=error)
        finally:
            await session.close()


def get_session():
    """Creates FastAPI dependency for generation of SQLAlchemy Session.

    Yields:
        Session: SQLAlchemy Session.
    """
    with session_factory() as session:
        try:
            yield session
        except IntegrityError as error:
            session.rollback()
            integrity_error_handler(error=error)
        finally:
            session.close()
