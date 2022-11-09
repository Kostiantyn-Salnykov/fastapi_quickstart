from apps.CORE.services import AsyncCRUDBase
from apps.todos.models import ToDo


class ToDoCRUDBase(AsyncCRUDBase):
    ...


to_do_service = ToDoCRUDBase(model=ToDo)
