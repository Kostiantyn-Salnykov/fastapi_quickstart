"""Basic CRUD for services."""
import typing
import uuid
from typing import Generic, Type, TypeVar

from pydantic import BaseModel
from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import ChunkedIteratorResult, CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from apps.CORE.db import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class AsyncCRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, *, model: Type[ModelType]):
        self.model = model

    async def create(self, *, session: AsyncSession, obj: CreateSchemaType) -> ModelType:
        obj_in_data = obj.dict(exclude_unset=True, by_alias=False)
        insert_statement = insert(self.model).values(**obj_in_data).returning(self.model)
        statement = select(self.model).from_statement(insert_statement).execution_options(populate_existing=True)
        result: ChunkedIteratorResult = await session.execute(statement=statement)
        await session.commit()
        result: ModelType = result.scalar_one()
        return result

    async def read(self, *, session: AsyncSession, id: typing.Union[str, uuid.UUID]) -> typing.Optional[ModelType]:
        statement = select(self.model).where(self.model.id == id)
        result: ChunkedIteratorResult = await session.execute(statement=statement)
        return result.scalar_one_or_none()

    async def update(self, *, session: AsyncSession, id: typing.Union[str, uuid.UUID], values: dict):
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
        data = result.scalar_one_or_none()
        return data

    async def delete(self, *, session: AsyncSession, id: typing.Union[str, uuid.UUID]) -> CursorResult:
        delete_statement = delete(self.model).where(self.model.id == id)
        result: CursorResult = await session.execute(statement=delete_statement)
        await session.commit()
        return result
