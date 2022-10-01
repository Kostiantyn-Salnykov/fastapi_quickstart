from apps.todos.models import ToDo
from apps.todos.schemas import ToDoCreateSchema
from tests.apps.todos.factories import ToDoFactory


class TestToDo:
    async def test_factory(self) -> None:
        to_do_schema: ToDoCreateSchema = ToDoFactory.build()
        todo: ToDo = await ToDoFactory.create_async()
        todos: list[ToDo] = await ToDoFactory.create_batch_async(size=2)

        assert isinstance(todo, ToDo)
        assert isinstance(to_do_schema, ToDoCreateSchema)
        for i in todos:
            assert isinstance(i, ToDo)

    async def test__repr__(self) -> None:
        obj: ToDo = await ToDoFactory.create_async()
        result = obj.__repr__()
        expected_result = (
            f'{obj.__class__.__name__}(title="{obj.title}", description="{obj.description}", status="{obj.status}")'
        )
        assert expected_result == result
