"""Basic CRUD for services."""
import uuid
from typing import Type, TypeVar

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import ChunkedIteratorResult, CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from apps.CORE.db import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class AsyncCRUDBase:
    def __init__(self, *, model: Type[ModelType]):
        self.model = model

    async def create(self, *, session: AsyncSession, obj: CreateSchemaType) -> ModelType:
        obj_in_data = jsonable_encoder(obj=obj, exclude_unset=True, by_alias=False)
        insert_statement = insert(self.model).values(**obj_in_data).returning(self.model)
        statement = select(self.model).from_statement(insert_statement).execution_options(populate_existing=True)
        result: ChunkedIteratorResult = await session.execute(statement=statement)
        await session.commit()
        data: ModelType = result.scalar_one()
        return data

    async def create_many(self, *, session: AsyncSession, objs: list[CreateSchemaType]) -> list[ModelType] | None:
        insert_statement = (
            insert(self.model)
            .values([jsonable_encoder(obj=obj, exclude_unset=True, by_alias=False) for obj in objs])
            .returning(self.model)
        )
        statement = select(self.model).from_statement(insert_statement).execution_options(populate_existing=True)
        result: ChunkedIteratorResult = await session.execute(statement=statement)
        await session.commit()
        data: list[ModelType] | None = result.scalars().all()
        return data

    async def read(self, *, session: AsyncSession, id: str | uuid.UUID) -> ModelType | None:
        statement = select(self.model).where(self.model.id == id)
        result: ChunkedIteratorResult = await session.execute(statement=statement)
        data: ModelType | None = result.scalar_one_or_none()
        return data

    async def update(self, *, session: AsyncSession, id: str | uuid.UUID, obj: UpdateSchemaType) -> ModelType | None:
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
        await session.commit()
        data: ModelType | None = result.scalar_one_or_none()
        return data

    async def delete(self, *, session: AsyncSession, id: str | uuid.UUID) -> CursorResult:
        delete_statement = delete(self.model).where(self.model.id == id)
        result: CursorResult = await session.execute(statement=delete_statement)
        await session.commit()
        return result
