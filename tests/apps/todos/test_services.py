from faker import Faker
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from apps.todos.models import ToDo
from apps.todos.services import ToDoCRUDBase
from tests.apps.todos.factories import ToDoFactory


class TestToDoCRUDBase:
    @classmethod
    def setup_class(cls):
        cls.service = ToDoCRUDBase(model=ToDo)

    async def clear_todos(self, session: AsyncSession):
        await session.execute(statement=delete(ToDo))
        await session.commit()

    async def test_list(self, faker: Faker, db_session: AsyncSession):
        await self.clear_todos(session=db_session)
        todos = await ToDoFactory.create_batch_async(size=faker.pyint(min_value=3, max_value=5))

        total, todos_list = await self.service.list(session=db_session, sorting=[])

        assert total == len(todos)
        assert [todo.__repr__() for todo in todos_list] == [todo.__repr__() for todo in todos]
