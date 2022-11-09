import uuid

from pydantic import Field

from apps.authorization.enums import PermissionActions
from apps.CORE.schemas import BaseInSchema, BaseOutSchema, JSENDPaginationOutSchema, PaginationOutSchema


class GroupCreateSchema(BaseInSchema):
    name: str = Field(default=..., max_length=256, example="Group name")
    roles_ids: list[uuid.UUID] | None = Field(default=[])


class GroupCreateToDBSchema(BaseInSchema):
    id: uuid.UUID | None
    name: str = Field(default=..., max_length=256, example="Group name")


class CreateGroupRoleSchema(BaseInSchema):
    group_id: uuid.UUID
    role_id: uuid.UUID


class PermissionOutSchema(BaseOutSchema):
    id: uuid.UUID
    object_name: str = Field(default=..., max_length=128, alias="objectName")
    action: PermissionActions = Field(default=...)


class RoleCreateSchema(BaseInSchema):
    name: str = Field(default=..., max_length=128, example="Role name")
    permissions_ids: list[uuid.UUID] | None = Field(default=[])


class RoleCreateToDBSchema(BaseInSchema):
    id: uuid.UUID | None
    name: str = Field(default=..., max_length=128, example="Role name")


class CreateRolePermissionSchema(BaseInSchema):
    role_id: uuid.UUID
    permission_id: uuid.UUID


class RoleOutSchema(BaseOutSchema):
    id: uuid.UUID
    name: str = Field(default=..., max_length=128)
    permissions: list[PermissionOutSchema] | None = Field(default=[])


class GroupOutSchema(BaseOutSchema):
    id: uuid.UUID
    name: str = Field(default=..., max_length=256)
    roles: list[RoleOutSchema] | None = Field(default=[])


class GroupListOutSchema(JSENDPaginationOutSchema):
    data: PaginationOutSchema[GroupOutSchema]


class RoleListOutSchema(JSENDPaginationOutSchema):
    data: PaginationOutSchema[RoleOutSchema]


class PermissionListOutSchema(JSENDPaginationOutSchema):
    data: PaginationOutSchema[PermissionOutSchema]
