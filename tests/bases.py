import datetime
import random
import typing
from typing import Any

import factory
from pydantic_factories import AsyncPersistenceProtocol, ModelFactory, PostGenerated

from apps.CORE.db import Base, async_session_factory
from apps.CORE.helpers import utc_now
from apps.CORE.repositories import BaseCoreRepository
from apps.CORE.types import ModelType, SchemaType


class AsyncPersistenceHandler(AsyncPersistenceProtocol):
    def __init__(self, model: type[Base]):
        self._model = model
        self._service = BaseCoreRepository(model=self._model)

    async def save(self, data: SchemaType) -> ModelType:
        async with async_session_factory() as db_session, db_session.begin():
            return await self._service.create(session=db_session, obj=data)

    async def save_many(self, data: list[SchemaType]) -> list[ModelType]:
        async with async_session_factory() as db_session, db_session.begin():
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


class BaseSchemaFactory(BaseRawFactory):
    created_at: datetime.datetime = PostGenerated(fn=generate_dt)
    updated_at: datetime.datetime = PostGenerated(fn=generate_dt)


class BaseModelFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        abstract = True
        sqlalchemy_session_persistence = "commit"

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Change RuntimeError to help with factory set up."""
        if cls._meta.sqlalchemy_session is None:
            raise RuntimeError(
                f"Register {cls.__name__} factory inside conftest.py in set_session_for_factories fixture declaration."
            )
        return super()._create(model_class=model_class, *args, **kwargs)

    @staticmethod
    def check_factory(factory_class: type["BaseModelFactory"], model: type[Base]) -> None:
        """Test that factory creates successfully."""
        obj = factory_class()
        size = random.randint(2, 3)
        objs = factory_class.create_batch(size=size)

        assert isinstance(obj, model)
        assert size == len(objs)
        for i in objs:
            assert isinstance(i, model)
