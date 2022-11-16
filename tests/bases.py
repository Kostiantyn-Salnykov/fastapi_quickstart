import datetime
import typing
from typing import Any, Type

from pydantic_factories import AsyncPersistenceProtocol, ModelFactory, PostGenerated

from apps.CORE.db import Base, async_session_factory
from apps.CORE.services import AsyncCRUDBase
from apps.CORE.types import ModelType, SchemaType
from apps.CORE.utils import utc_now


class AsyncPersistenceHandler(AsyncPersistenceProtocol):
    def __init__(self, model: Type[Base]):
        self._model = model
        self._service = AsyncCRUDBase(model=self._model)

    async def save(self, data: SchemaType) -> ModelType:
        async with async_session_factory() as db_session:
            async with db_session.begin():
                return await self._service.create(session=db_session, obj=data)

    async def save_many(self, data: list[SchemaType]) -> list[ModelType]:
        async with async_session_factory() as db_session:
            async with db_session.begin():
                return await self._service.create_many(session=db_session, objs=data)


class BaseRawFactory(ModelFactory):
    @classmethod
    def get_mock_value(cls, field_type: Any) -> Any:
        type_name = str(field_type.__name__)
        if type_name == "Email":
            return cls.get_faker().email()

        return super().get_mock_value(field_type)


def generate_dt(name: str, values: dict[str, typing.Any]) -> datetime.datetime:
    result = utc_now()
    if name == "updated_at":
        result = values["created_at"]
    return result


class BaseFactory(BaseRawFactory):
    created_at: datetime.datetime = PostGenerated(fn=generate_dt)
    updated_at: datetime.datetime = PostGenerated(fn=generate_dt)
