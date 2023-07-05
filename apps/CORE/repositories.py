"""Basic CRUD for services."""
import typing
from typing import TypeAlias

from fastapi import status
from sqlalchemy import delete, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import ChunkedIteratorResult, CursorResult
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import BinaryExpression, UnaryExpression

from apps.CORE.enums import JSENDStatus
from apps.CORE.exceptions import BackendError
from apps.CORE.types import ModelType, StrOrUUID

__all__ = (
    "NoneModelType",
    "NoneModelTypeList",
    "BaseORMRepository",
    "BaseCoreRepository",
)

NoneModelType: TypeAlias = ModelType | None
NoneModelTypeList: TypeAlias = list[ModelType] | None


class _BaseCommonRepository:
    def __init__(self, *, model: type[ModelType]):
        self._model = model

    @property
    def model(self) -> type[ModelType]:
        return self._model

    async def read(
        self, *, session: AsyncSession, id: StrOrUUID, unique: bool = True, safe: bool = True
    ) -> NoneModelType:
        statement = select(self.model).where(self.model.id == id)
        result: ChunkedIteratorResult = await session.execute(statement=statement)
        result.unique() if unique else ...
        data: NoneModelType = result.scalar_one_or_none() if safe else result.scalar_one()
        return data

    async def read_or_not_found(
        self, *, session: AsyncSession, id: StrOrUUID, unique: bool = True, message: str = "Not found."
    ) -> ModelType:
        obj: NoneModelType = await self.read(session=session, id=id, unique=unique, safe=True)
        if not obj:
            raise BackendError(
                message=message,
                code=status.HTTP_404_NOT_FOUND,
                status=JSENDStatus.FAIL,
            )
        return obj

    async def list_or_not_found(self, *, session: AsyncSession, ids: list[StrOrUUID], message: str = "Not found."):
        statement = select(self.model).where(self.model.id.in_(ids))
        result = await session.execute(statement=statement)
        result.unique()
        objs = result.scalars().all()
        if diff := set(ids) - {obj.id for obj in objs}:
            raise BackendError(message=message, data=[i for i in diff], code=status.HTTP_404_NOT_FOUND)
        return objs

    async def list(
        self,
        *,
        session: AsyncSession,
        sorting: list[UnaryExpression],
        limit: int = 100,
        next_token: str = None,
        filters: list[BinaryExpression] | None = None,
        unique: bool = True,
    ) -> tuple[int, list[ModelType]]:
        select_statement = select(self.model)
        if filters:
            select_statement = select_statement.where(*filters)
        if next_token:
            select_statement = select_statement.where(self.model.id > next_token)
        select_statement = select_statement.order_by(*sorting).limit(limit).execution_options(populate_existing=True)

        count_statement = select(func.count(self.model.id)).select_from(self.model).where(*filters or {})

        async with session.begin_nested():
            count_result: ChunkedIteratorResult = await session.execute(statement=count_statement)
            select_result: ChunkedIteratorResult = await session.execute(statement=select_statement)

        total: int = count_result.scalar()  # number of counted results.
        select_result.unique() if unique else ...  # Logic for M2M joins
        objects: list[ModelType] = select_result.scalars().all()
        return total, objects

    async def update(
        self, *, session: AsyncSession, id: StrOrUUID, values: dict[str, typing.Any], unique: bool = True
    ) -> NoneModelType:
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
        obj: NoneModelType = result.scalar_one_or_none()
        return obj


class BaseORMRepository(_BaseCommonRepository):
    @staticmethod
    async def create(*, session: AsyncSession, obj: ModelType) -> ModelType:
        session.add(instance=obj)
        await session.flush()
        # await session.refresh(instance=obj)
        return obj

    @staticmethod
    async def create_many(*, session: AsyncSession, objs: typing.Iterable[ModelType]) -> list[ModelType]:
        objects = list(objs)
        session.add_all(instances=objects)
        await session.flush()
        return objects

    @staticmethod
    async def update(*, session: AsyncSession, obj: ModelType) -> ModelType:
        await session.flush()
        return obj

    @staticmethod
    async def delete(*, session: AsyncSession, obj: ModelType) -> ModelType:
        await session.delete(instance=obj)
        await session.flush()
        return obj


class BaseCoreRepository(_BaseCommonRepository):
    async def create(self, *, session: AsyncSession, values: dict[str, typing.Any], unique: bool = True) -> ModelType:
        insert_statement = insert(self.model).values(**values).returning(self.model)
        statement = select(self.model).from_statement(insert_statement).execution_options(populate_existing=True)
        result: ChunkedIteratorResult = await session.execute(statement=statement)
        await session.flush()
        result.unique() if unique else ...
        obj: ModelType = result.scalar_one()
        return obj

    async def create_many(
        self, *, session: AsyncSession, values_list: list[dict[str, typing.Any]], unique: bool = True
    ) -> NoneModelTypeList:
        insert_statement = insert(self.model).values(list(values_list)).returning(self.model)
        statement = select(self.model).from_statement(insert_statement).execution_options(populate_existing=True)
        result: ChunkedIteratorResult = await session.execute(statement=statement)
        await session.flush()
        result.unique() if unique else ...
        objects: NoneModelTypeList = result.scalars().all()
        return objects

    async def delete(self, *, session: AsyncSession, id: StrOrUUID) -> CursorResult:
        delete_statement = delete(self.model).where(self.model.id == id)
        result: CursorResult = await session.execute(statement=delete_statement)
        await session.flush()
        return result
