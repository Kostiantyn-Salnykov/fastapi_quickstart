import datetime
import uuid

import pytest
from faker import Faker
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from apps.todos.enums import ToDoStatuses
from apps.todos.models import ToDo
from apps.todos.schemas import ToDoCreateSchema, ToDoOutSchema, ToDoUpdateSchema
from apps.todos.services import ToDoCRUDBase
from tests.apps.todos.factories import ToDoFactory


class TestToDoCRUDBase:
    @classmethod
    def setup_class(cls):
        cls.service = ToDoCRUDBase(model=ToDo)

    async def clear_todos(self, session: AsyncSession):
        await session.execute(statement=delete(ToDo))
        await session.commit()

    @staticmethod
    def check_uuid(field, expected_type: type = uuid.UUID) -> None:
        assert isinstance(field, expected_type)

    @staticmethod
    def check_datetime(field, expected_type: type = datetime.datetime) -> None:
        assert isinstance(field, expected_type)

    def check_defaults(self, obj):
        self.check_uuid(field=getattr(obj, "id"))
        self.check_datetime(field=getattr(obj, "created_at"))
        self.check_datetime(field=getattr(obj, "updated_at"))

    async def test_list(self, faker: Faker, db_session: AsyncSession):
        await self.clear_todos(session=db_session)
        todos = await ToDoFactory.create_batch_async(size=faker.pyint(min_value=3, max_value=5))

        total, todos_list = await self.service.list(session=db_session, sorting=[])

        assert total == len(todos)
        assert [todo.__repr__() for todo in todos_list] == [todo.__repr__() for todo in todos]

    async def test_create(self, db_session: AsyncSession) -> None:
        equal_fields = {"text", "description"}
        todo: ToDoCreateSchema = ToDoFactory.build()

        result = await self.service.create(session=db_session, obj=todo)

        assert isinstance(result, ToDo)
        result_schema = ToDoOutSchema.from_orm(obj=result)
        assert result_schema.dict(include=equal_fields) == todo.dict(include=equal_fields)
        self.check_defaults(obj=result)

    async def test_read(self, db_session: AsyncSession) -> None:
        todo: ToDo = await ToDoFactory.create_async()

        result: ToDo = await self.service.read(session=db_session, id=todo.id)

        assert isinstance(result, ToDo)
        assert result.id == todo.id
        assert str(result) == str(todo)

    async def test_read_none(self, faker: Faker, db_session: AsyncSession) -> None:
        fake_uuid = faker.uuid4(cast_to=None)

        result = await self.service.read(session=db_session, id=fake_uuid)

        assert result is None

    @pytest.mark.parametrize(
        argnames="status", argvalues=[ToDoStatuses.IN_WORK, ToDoStatuses.ARCHIVED, ToDoStatuses.COMPLETED]
    )
    async def test_update(self, faker: Faker, db_session: AsyncSession, status: ToDoStatuses) -> None:
        todo: ToDo = await ToDoFactory.create_async()
        new_title, new_description = faker.pystr(), faker.pystr()
        assert todo.title != new_title
        assert todo.description != new_description
        assert todo.status != status

        result: ToDo = await self.service.update(
            session=db_session,
            id=todo.id,
            obj=ToDoUpdateSchema(title=new_title, description=new_description, status=status),
        )

        assert result.title == new_title
        assert result.description == new_description
        assert result.status == status

    async def test_delete(self, db_session: AsyncSession) -> None:
        todo: ToDo = await ToDoFactory.create_async()

        result = await self.service.delete(session=db_session, id=todo.id)
        assert result.rowcount == 1  # deleted one object from db

        result2 = await self.service.delete(session=db_session, id=todo.id)
        assert result2.rowcount == 0  # already deleted
