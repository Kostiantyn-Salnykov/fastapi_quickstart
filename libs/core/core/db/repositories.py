"""Basic CRUD for services."""

__all__ = (
    "BaseRepository",
    "ExtendedRepository",
)

import typing
from collections.abc import Iterable

from fastapi import status
from sqlalchemy import BinaryExpression, delete, func, insert, select, update
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.engine import ChunkedIteratorResult, CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from core.annotations import (
    CountModelListResult,
    ModelInstance,
    ModelListOrNone,
    ModelOrNone,
    ModelType,
    StrOrUUID,
)
from core.dependencies.body.filtration import Filtration
from core.dependencies.body.pagination import Pagination
from core.dependencies.body.projection import Projection
from core.dependencies.body.searching import Searching
from core.dependencies.body.sorting import Sorting
from core.enums import JSENDStatus
from core.exceptions import BackendError


class BaseRepository:
    def __init__(
        self,
        *,
        model: ModelType,
        use_unique: bool = True,
        use_flush: bool = True,
        use_safe: bool = True,
    ) -> None:
        self._model = model
        self._use_unique = use_unique  # Deduplicate result of rows or joined objects (for O2M, M2M joins).
        self._use_flush = use_flush  # Automatically send to object to db, but not committing (PK, FK checked).
        self._use_safe = use_safe  # return `None` instead of raise on scalar convertion.

    @property
    def model(self) -> ModelType:
        return self._model

    @property
    def use_unique(self) -> bool:
        return self._use_unique

    @property
    def use_flush(self) -> bool:
        return self._use_flush

    @property
    def use_safe(self) -> bool:
        return self._use_safe

    async def create_one(self, *, session: AsyncSession, data: dict[str, typing.Any]) -> None:
        insert_statement = insert(self.model).values(**data)
        result = await session.execute(statement=insert_statement)
        await session.flush() if self.use_flush else ...
        return result

    async def create_many(self, *, session: AsyncSession, data: Iterable[dict[str, typing.Any]]) -> ModelListOrNone:
        insert_statement = postgresql_insert(self.model).values(list(data)).returning(self.model)
        statement = select(self.model).from_statement(insert_statement).execution_options(populate_existing=True)
        result: ChunkedIteratorResult = await session.execute(statement=statement)
        await session.flush()
        result.unique() if self.use_unique else ...
        objects: ModelListOrNone = result.scalars().all()
        return objects

    async def get_by_attr(self, *, session: AsyncSession, attr_name: str, attr_value: StrOrUUID) -> ModelOrNone:
        statement = select(self.model).where(getattr(self.model, attr_name) == attr_value)
        result: ChunkedIteratorResult = await session.execute(statement=statement)
        result.unique() if self.use_unique else ...
        data: ModelOrNone = result.scalar_one_or_none() if self.use_safe else result.scalar_one()
        return data

    async def get_one(self, *, session: AsyncSession, id: StrOrUUID) -> ModelOrNone:
        return await self.get_by_attr(session=session, attr_name="id", attr_value=id)

    async def get_where(
        self, *, session: AsyncSession, filtration: Filtration | list[BinaryExpression]
    ) -> ModelListOrNone:
        statement = select(self.model).where(*filtration)
        result: ChunkedIteratorResult = await session.execute(statement=statement)
        result.unique() if self.use_unique else ...
        objects: list[ModelInstance] = result.scalars().all()
        return objects

    async def get_many(self, *, session: AsyncSession, ids: list[StrOrUUID]) -> ModelListOrNone:
        return await self.get_where(session=session, filtration=[self.model.id.in_(ids)])

    async def count_and_get_many(
        self,
        *,
        session: AsyncSession,
        sorting: Sorting,
        pagination: Pagination,
        filtration: Filtration,
        projection: Projection,
        searching: Searching,
    ) -> CountModelListResult:
        select_statement = (
            select(self.model)
            .options(projection.query)
            .order_by(*sorting.query)
            .limit(pagination.limit)
            .execution_options(populate_existing=True)
        )
        count_statement = select(func.count(self.model.id)).select_from(self.model).where(*filtration).where(*searching)
        select_statement = select_statement.where(*filtration).where(*searching)

        next_token = pagination.next_token
        if pagination.next_token:
            select_statement = select_statement.where(pagination.get_query(next_token=next_token))

        async with session.begin_nested():
            count_result: ChunkedIteratorResult = await session.execute(statement=count_statement)
            select_result: ChunkedIteratorResult = await session.execute(statement=select_statement)

        total: int = count_result.scalar()  # number of counted results.
        select_result.unique() if self.use_unique else ...
        objects: list[ModelInstance] = select_result.scalars().all()
        return total, objects

    async def update_one(self, *, session: AsyncSession, id: StrOrUUID, data: dict[str, typing.Any]) -> bool:
        statement = update(self.model).where(self.model.id == id).values(**data)
        result = await session.execute(statement=statement)
        return result.rowcount() > 0

    async def update_many(self): ...  # noqa: ANN201

    async def delete_one(self, *, session: AsyncSession, id: StrOrUUID) -> CursorResult:
        return await self.delete_where(session=session, filtration=[self.model.id == id])

    async def delete_where(
        self, *, session: AsyncSession, filtration: Filtration | list[BinaryExpression]
    ) -> CursorResult:
        delete_statement = delete(self.model).where(*filtration)
        result: CursorResult = await session.execute(statement=delete_statement)
        await session.flush()
        return result

    async def delete_many(self, *, session: AsyncSession, ids: list[StrOrUUID]):  # noqa: ANN201
        return await self.delete_where(session=session, filtration=[self.model.id.in_(ids)])


class ExtendedRepository(BaseRepository):
    async def create_or_update(self): ...  # noqa: ANN201

    async def create_or_get(self): ...  # noqa: ANN201

    async def create_one_and_return(self, *, session: AsyncSession, values: dict[str, typing.Any]) -> ModelInstance:
        insert_statement = postgresql_insert(self.model).values(**values).returning(self.model)
        statement = select(self.model).from_statement(insert_statement).execution_options(populate_existing=True)
        result: ChunkedIteratorResult = await session.execute(statement=statement)
        await session.flush()
        result.unique() if self.use_unique else ...
        obj: ModelInstance = result.scalar_one()
        return obj

    async def update_one_and_return(
        self, *, session: AsyncSession, id: StrOrUUID, values: dict[str, typing.Any]
    ) -> ModelOrNone:
        update_statement = (
            update(self.model)
            .where(self.model.id == id)
            .values(**values)
            .returning(self.model)
            .execution_options(synchronize_session="fetch")
        )
        statement = (
            select(self.model).from_statement(statement=update_statement).execution_options(populate_existing=True)
        )
        result: ChunkedIteratorResult = await session.execute(statement=statement)
        await session.flush()
        result.unique() if self.use_unique else ...
        obj: ModelOrNone = result.scalar_one_or_none()
        return obj

    async def create_or_update_many(self): ...  # noqa: ANN201

    async def get_by_id_or_not_found(
        self, *, session: AsyncSession, id: StrOrUUID, message: str = "Not found."
    ) -> ModelInstance:
        obj: ModelOrNone = await self.get_one(session=session, id=id)
        if not obj:
            raise BackendError(message=message, code=status.HTTP_404_NOT_FOUND, status=JSENDStatus.FAIL)
        return obj

    async def list_or_not_found(
        self, *, session: AsyncSession, ids: list[StrOrUUID], message: str = "Not found."
    ) -> list[ModelInstance]:
        statement = select(self.model).where(self.model.id.in_(ids))
        result = await session.execute(statement=statement)
        result.unique()
        objs = result.scalars().all()
        if diff := set(ids) - {obj.id for obj in objs}:
            raise BackendError(message=message, data=list(diff), code=status.HTTP_404_NOT_FOUND)
        return objs
