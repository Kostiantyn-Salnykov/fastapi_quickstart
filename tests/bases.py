import random

import factory

from apps.CORE.custom_types import ModelType
from apps.CORE.db import Base


class BaseModelFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        abstract = True
        sqlalchemy_session_persistence = "commit"

    @classmethod
    def _create(cls, model_class, *args, **kwargs) -> ModelType:
        """Change RuntimeError to help with factory set up."""
        if cls._meta.sqlalchemy_session is None:
            msg = (
                f"Register {cls.__name__} factory inside conftest.py in set_session_for_factories fixture "
                f"declaration."
            )
            raise RuntimeError(msg)
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
