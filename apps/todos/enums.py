from enum import Enum

__all__ = ("ToDoStatuses",)


class ToDoStatuses(str, Enum):
    CREATED = "CREATED"
    IN_WORK = "IN WORK"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"
