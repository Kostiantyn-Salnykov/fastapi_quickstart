"""Basic CRUD for services."""

import typing

from fastapi import status
from sqlalchemy import BinaryExpression, delete, func, select, update
from sqlalchemy.dialects.postgresql import insert
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

__all__ = (
    "BaseCoreRepository",
    "BaseORMRepository",
)


class _BaseCommonRepository:
    def __init__(self, *, model: ModelType) -> None:
        self._model = model

    @property
    def model(self) -> ModelType:
        return self._model

    async def retrieve(
        self, *, session: AsyncSession, attr_name: str, attr_value: StrOrUUID, unique: bool = True, safe: bool = True
    ) -> ModelOrNone:
        statement = select(self.model).where(getattr(self.model, attr_name) == attr_value)
        result: ChunkedIteratorResult = await session.execute(statement=statement)
        result.unique() if unique else ...
        data: ModelOrNone = result.scalar_one_or_none() if safe else result.scalar_one()
        return data

    async def retrieve_by_id(
        self, *, session: AsyncSession, id: StrOrUUID, unique: bool = True, safe: bool = True
    ) -> ModelOrNone:
        return await self.retrieve(session=session, attr_name="id", attr_value=id, unique=unique, safe=safe)

    async def retrieve_by_id_or_not_found(
        self, *, session: AsyncSession, id: StrOrUUID, unique: bool = True, message: str = "Not found."
    ) -> ModelInstance:
        obj: ModelOrNone = await self.retrieve_by_id(session=session, id=id, unique=unique, safe=True)
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

    async def list(
        self,
        *,
        session: AsyncSession,
        sorting: Sorting,
        pagination: Pagination,
        filtration: Filtration,
        projection: Projection,
        searching: Searching,
        unique: bool = True,
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
        select_result.unique() if unique else ...  # Logic for M2M joins
        objects: list[ModelInstance] = select_result.scalars().all()
        return total, objects

    async def update(
        self, *, session: AsyncSession, id: StrOrUUID, values: dict[str, typing.Any], unique: bool = True
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
        result.unique() if unique else ...  # Logic for M2M joins
        obj: ModelOrNone = result.scalar_one_or_none()
        return obj


class BaseORMRepository(_BaseCommonRepository):
    @staticmethod
    async def create(*, session: AsyncSession, obj: ModelInstance) -> ModelInstance:
        session.add(instance=obj)
        await session.flush()
        # await session.refresh(instance=obj)
        return obj

    @staticmethod
    async def create_many(*, session: AsyncSession, objs: typing.Iterable[ModelInstance]) -> list[ModelInstance]:
        objects = list(objs)
        session.add_all(instances=objects)
        await session.flush()
        return objects

    @staticmethod
    async def update(*, session: AsyncSession, obj: ModelInstance) -> ModelInstance:
        await session.flush()
        return obj

    @staticmethod
    async def delete(*, session: AsyncSession, obj: ModelInstance) -> ModelInstance:
        await session.delete(instance=obj)
        await session.flush()
        return obj


class BaseCoreRepository(_BaseCommonRepository):
    async def create(
        self, *, session: AsyncSession, values: dict[str, typing.Any], unique: bool = True
    ) -> ModelInstance:
        insert_statement = insert(self.model).values(**values).returning(self.model)
        statement = select(self.model).from_statement(insert_statement).execution_options(populate_existing=True)
        result: ChunkedIteratorResult = await session.execute(statement=statement)
        await session.flush()
        result.unique() if unique else ...
        obj: ModelInstance = result.scalar_one()
        return obj

    async def create_many(
        self, *, session: AsyncSession, values_list: list[dict[str, typing.Any]], unique: bool = True
    ) -> ModelListOrNone:
        insert_statement = insert(self.model).values(list(values_list)).returning(self.model)
        statement = select(self.model).from_statement(insert_statement).execution_options(populate_existing=True)
        result: ChunkedIteratorResult = await session.execute(statement=statement)
        await session.flush()
        result.unique() if unique else ...
        objects: ModelListOrNone = result.scalars().all()
        return objects

    async def delete_by_id(self, *, session: AsyncSession, id: StrOrUUID) -> CursorResult:
        return await self.delete(session=session, filtration=[self.model.id == id])

    async def delete(self, *, session: AsyncSession, filtration: Filtration | list[BinaryExpression]) -> CursorResult:
        delete_statement = delete(self.model).where(*filtration)
        result: CursorResult = await session.execute(statement=delete_statement)
        await session.flush()
        return result
