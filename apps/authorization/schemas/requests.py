import uuid

from pydantic import Field

from apps.CORE.custom_types import StrOrNone
from apps.CORE.schemas.requests import BaseRequestSchema


class GroupCreateRequest(BaseRequestSchema):
    title: str = Field(default=..., max_length=255)
    roles_ids: list[uuid.UUID] | None = Field(default_factory=list)


class GroupUpdateRequest(GroupCreateRequest):
    title: StrOrNone = Field(default=None, max_length=255)


class CreateGroupRoleRequest(BaseRequestSchema):
    group_id: uuid.UUID
    role_id: uuid.UUID


class RoleCreateRequest(BaseRequestSchema):
    title: str = Field(default=..., max_length=128)
    permissions_ids: list[uuid.UUID] | None = Field(default_factory=list)


class CreateRolePermissionRequest(BaseRequestSchema):
    role_id: uuid.UUID
    permission_id: uuid.UUID
