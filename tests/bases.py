from typing import Type, TypeVar

from pydantic import BaseModel
from pydantic_factories import AsyncPersistenceProtocol

from apps.CORE.db import Base, async_session_factory
from apps.CORE.services import AsyncCRUDBase

SchemaType = TypeVar("SchemaType", bound=BaseModel)
DBModelType = TypeVar("DBModelType", bound=Base)


class AsyncPersistenceHandler(AsyncPersistenceProtocol):
    def __init__(self, model: Type[Base]):
        self._model = model
        self._service = AsyncCRUDBase(model=self._model)

    async def save(self, data: SchemaType) -> DBModelType:
        async with async_session_factory() as db_session:
            async with db_session.begin():
                return await self._service.create(session=db_session, obj=data)

    async def save_many(self, data: list[SchemaType]) -> list[DBModelType]:
        async with async_session_factory() as db_session:
            async with db_session.begin():
                return await self._service.create_many(session=db_session, objs=data)
