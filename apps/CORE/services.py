"""Basic CRUD for services."""
from typing import Type, TypeAlias

from fastapi.encoders import jsonable_encoder
from sqlalchemy import delete, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import ChunkedIteratorResult, CursorResult
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import UnaryExpression

from apps.CORE.types import ModelType, SchemaType, StrOrUUID
from apps.CORE.utils import to_db_encoder

NoneModelType: TypeAlias = ModelType | None
NoneModelTypeList: TypeAlias = list[ModelType] | None


class AsyncCRUDBase:
    def __init__(self, *, model: Type[ModelType]):
        self.model = model

    async def create(self, *, session: AsyncSession, obj: SchemaType, unique: bool = False) -> ModelType:
        obj_in_data = to_db_encoder(obj=obj)
        insert_statement = insert(self.model).values(**obj_in_data).returning(self.model)
        statement = select(self.model).from_statement(insert_statement).execution_options(populate_existing=True)
        result: ChunkedIteratorResult = await session.execute(statement=statement)
        await session.flush()
        result.unique() if unique else ...
        data: ModelType = result.scalar_one()
        return data

    async def create_many(
        self, *, session: AsyncSession, objs: list[SchemaType], unique: bool = False
    ) -> NoneModelTypeList:
        insert_statement = insert(self.model).values([to_db_encoder(obj=obj) for obj in objs]).returning(self.model)
        statement = select(self.model).from_statement(insert_statement).execution_options(populate_existing=True)
        result: ChunkedIteratorResult = await session.execute(statement=statement)
        await session.flush()
        result.unique() if unique else ...
        data: NoneModelTypeList = result.scalars().all()
        return data

    async def read(self, *, session: AsyncSession, id: StrOrUUID, unique: bool = False) -> NoneModelType:
        statement = select(self.model).where(self.model.id == id)
        result: ChunkedIteratorResult = await session.execute(statement=statement)
        result.unique() if unique else ...
        data: NoneModelType = result.scalar_one_or_none()
        return data

    async def list(
        self,
        *,
        session: AsyncSession,
        sorting: list[UnaryExpression],
        offset: int = 0,
        limit: int = 100,
        filters: dict | None = None,  # TODO: Add dynamic filtering system
        unique: bool = False
    ) -> tuple[int, list[ModelType]]:
        select_statement = select(self.model)
        if filters:
            select_statement = select_statement.filter_by(**filters)
        select_statement = (
            select_statement.order_by(*sorting).offset(offset).limit(limit).execution_options(populate_existing=True)
        )

        async with session.begin_nested():
            count_result: ChunkedIteratorResult = await session.execute(statement=select(func.count(self.model.id)))
            select_result: ChunkedIteratorResult = await session.execute(statement=select_statement)

        total: int = count_result.scalar()  # number of counted results.
        select_result.unique() if unique else ...  # Logic for M2M joins
        objects: list[ModelType] = select_result.scalars().all()
        return total, objects

    async def update(self, *, session: AsyncSession, id: StrOrUUID, obj: SchemaType) -> NoneModelType:
        values = jsonable_encoder(obj=obj, exclude_unset=True, by_alias=False)
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
        data: NoneModelType = result.scalar_one_or_none()
        return data

    async def delete(self, *, session: AsyncSession, id: StrOrUUID) -> CursorResult:
        delete_statement = delete(self.model).where(self.model.id == id)
        result: CursorResult = await session.execute(statement=delete_statement)
        await session.flush()
        return result
