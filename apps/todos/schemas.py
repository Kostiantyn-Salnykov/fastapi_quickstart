import uuid

from pydantic import Field

from apps.CORE.schemas import (
    BaseInSchema,
    BaseOutSchema,
    CreatedUpdatedOutSchema,
    JSENDPaginationOutSchema,
    PaginationOutSchema,
)
from apps.todos.enums import ToDoStatuses


class ToDoCreateSchema(BaseInSchema):
    title: str = Field(max_length=128)
    description: str = Field(max_length=256)


class ToDoUpdateSchema(ToDoCreateSchema):
    title: str | None = Field(max_length=128)
    description: str | None = Field(max_length=256)
    status: ToDoStatuses | None = Field(default=ToDoStatuses.CREATED)


class ToDoOutSchema(BaseOutSchema, CreatedUpdatedOutSchema):
    id: uuid.UUID
    title: str = Field(max_length=128)
    description: str = Field(max_length=256)
    status: ToDoStatuses = Field(default=ToDoStatuses.CREATED)


class ToDoListOutSchema(JSENDPaginationOutSchema):
    data: PaginationOutSchema[ToDoOutSchema]
