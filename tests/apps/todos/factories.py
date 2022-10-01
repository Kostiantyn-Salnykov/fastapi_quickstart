from pydantic_factories import ModelFactory

from apps.todos.models import ToDo
from apps.todos.schemas import ToDoCreateSchema
from tests.bases import AsyncPersistenceHandler


class ToDoFactory(ModelFactory):
    """ToDoFactory based on Faker and Pydantic."""

    __model__ = ToDoCreateSchema
    __async_persistence__ = AsyncPersistenceHandler(model=ToDo)
