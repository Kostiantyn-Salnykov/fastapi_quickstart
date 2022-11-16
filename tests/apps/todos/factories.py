from apps.todos.models import ToDo
from apps.todos.schemas import ToDoCreateSchema
from tests.bases import AsyncPersistenceHandler, BaseFactory


class ToDoFactory(BaseFactory):
    """ToDoFactory based on Faker and Pydantic."""

    __model__ = ToDoCreateSchema
    __async_persistence__ = AsyncPersistenceHandler(model=ToDo)
