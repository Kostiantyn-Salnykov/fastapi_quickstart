__all__ = (
    "GroupCreateToDBSchema",
    "RoleCreateToDBSchema",
)

import uuid

from core.schemas.requests import BaseRequestSchema
from pydantic import Field


class GroupCreateToDBSchema(BaseRequestSchema):
    id: uuid.UUID | None = None
    title: str = Field(default=..., max_length=255)


class RoleCreateToDBSchema(BaseRequestSchema):
    id: uuid.UUID | None = None
    title: str = Field(default=..., max_length=128)
