import uuid

from core.schemas.responses import BaseResponseSchema, JSENDPaginationResponseSchema, PaginationResponseSchema
from pydantic import Field

from src.api.authorization.enums import PermissionActions


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
