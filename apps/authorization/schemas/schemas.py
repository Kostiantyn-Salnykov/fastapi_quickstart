__all__ = (
    "GroupCreateToDBSchema",
    "RoleCreateToDBSchema",
)

import uuid

from pydantic import Field

from apps.CORE.schemas.requests import BaseRequestSchema


class GroupCreateToDBSchema(BaseRequestSchema):
    id: uuid.UUID | None
    title: str = Field(default=..., max_length=255, example="Group title")


class RoleCreateToDBSchema(BaseRequestSchema):
    id: uuid.UUID | None
    title: str = Field(default=..., max_length=128, example="Role title")
