import uuid

from pydantic import Field

from apps.authorization.enums import PermissionActions
from apps.CORE.schemas.responses import BaseResponseSchema, JSENDPaginationResponseSchema, PaginationResponseSchema


class PermissionResponse(BaseResponseSchema):
    id: uuid.UUID
    object_name: str = Field(default=..., max_length=128, alias="objectName")
    action: PermissionActions = Field(default=...)


class RoleResponse(BaseResponseSchema):
    id: uuid.UUID
    title: str = Field(default=..., max_length=128)
    permissions: list[PermissionResponse] | None = Field(default_factory=list)


class GroupResponse(BaseResponseSchema):
    id: uuid.UUID
    title: str = Field(default=..., max_length=255)
    roles: list[RoleResponse] | None = Field(default_factory=list)


class GroupListResponse(JSENDPaginationResponseSchema):
    data: PaginationResponseSchema[GroupResponse]


class RoleListResponse(JSENDPaginationResponseSchema):
    data: PaginationResponseSchema[RoleResponse]


class PermissionListResponse(JSENDPaginationResponseSchema):
    data: PaginationResponseSchema[PermissionResponse]
