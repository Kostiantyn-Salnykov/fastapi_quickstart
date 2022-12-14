import uuid

from pydantic import Field

from apps.authorization.enums import PermissionActions
from apps.CORE.schemas import BaseInSchema, BaseOutSchema, JSENDPaginationOutSchema, PaginationOutSchema


class GroupCreateSchema(BaseInSchema):
    title: str = Field(default=..., max_length=256, example="Group title")
    roles_ids: list[uuid.UUID] | None = Field(default=[])


class GroupUpdateSchema(GroupCreateSchema):
    title: str | None = Field(default=None, max_length=256, example="Group title")


class GroupCreateToDBSchema(BaseInSchema):
    id: uuid.UUID | None
    title: str = Field(default=..., max_length=256, example="Group title")


class CreateGroupRoleSchema(BaseInSchema):
    group_id: uuid.UUID
    role_id: uuid.UUID


class PermissionOutSchema(BaseOutSchema):
    id: uuid.UUID
    object_name: str = Field(default=..., max_length=128, alias="objectName")
    action: PermissionActions = Field(default=...)


class RoleCreateSchema(BaseInSchema):
    title: str = Field(default=..., max_length=128, example="Role title")
    permissions_ids: list[uuid.UUID] | None = Field(default=[])


class RoleCreateToDBSchema(BaseInSchema):
    id: uuid.UUID | None
    title: str = Field(default=..., max_length=128, example="Role title")


class CreateRolePermissionSchema(BaseInSchema):
    role_id: uuid.UUID
    permission_id: uuid.UUID


class RoleOutSchema(BaseOutSchema):
    id: uuid.UUID
    title: str = Field(default=..., max_length=128, example="Role title")
    permissions: list[PermissionOutSchema] | None = Field(default=[])


class GroupOutSchema(BaseOutSchema):
    id: uuid.UUID
    title: str = Field(default=..., max_length=256)
    roles: list[RoleOutSchema] | None = Field(default=[])


class GroupListOutSchema(JSENDPaginationOutSchema):
    data: PaginationOutSchema[GroupOutSchema]


class RoleListOutSchema(JSENDPaginationOutSchema):
    data: PaginationOutSchema[RoleOutSchema]


class PermissionListOutSchema(JSENDPaginationOutSchema):
    data: PaginationOutSchema[PermissionOutSchema]
