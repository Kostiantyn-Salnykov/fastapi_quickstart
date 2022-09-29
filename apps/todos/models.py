from sqlalchemy import VARCHAR, Column

from apps.CORE.db import Base, CreatedUpdatedMixin, UUIDMixin
from apps.todos.enums import ToDoStatuses


class ToDo(Base, UUIDMixin, CreatedUpdatedMixin):
    title = Column(VARCHAR(length=128), nullable=False, index=True, unique=True)
    description = Column(VARCHAR(length=256))
    status = Column(VARCHAR(length=32), default=ToDoStatuses.CREATED.value, nullable=False)
