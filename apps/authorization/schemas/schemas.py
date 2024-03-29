__all__ = (
    "GroupCreateToDBSchema",
    "RoleCreateToDBSchema",
)

import uuid

from pydantic import Field

from apps.CORE.schemas.requests import BaseRequestSchema


class GroupCreateToDBSchema(BaseRequestSchema):
    id: uuid.UUID | None = None
    title: str = Field(default=..., max_length=255)


class RoleCreateToDBSchema(BaseRequestSchema):
    id: uuid.UUID | None = None
    title: str = Field(default=..., max_length=128)
