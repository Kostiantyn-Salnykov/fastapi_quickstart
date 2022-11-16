import uuid

from fastapi import Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import UnaryExpression

from apps.authorization.models import Group, Permission, Role
from apps.authorization.schemas import (
    CreateGroupRoleSchema,
    CreateRolePermissionSchema,
    GroupCreateSchema,
    GroupCreateToDBSchema,
    GroupOutSchema,
    PermissionOutSchema,
    RoleCreateSchema,
    RoleCreateToDBSchema,
    RoleOutSchema,
)
from apps.authorization.services import (
    group_role_service,
    groups_service,
    permissions_service,
    role_permission_service,
    roles_service,
)
from apps.CORE.dependencies import BasePagination
from apps.CORE.exceptions import BackendException


class GroupsHandler:
    async def create_group(self, *, request: Request, session: AsyncSession, data: GroupCreateSchema) -> GroupOutSchema:
        group_schema: GroupCreateToDBSchema = GroupCreateToDBSchema(id=uuid.uuid4(), name=data.name)
        async with session.begin_nested():
            group: Group = await groups_service.create(session=session, obj=group_schema, unique=True)
            if data.roles_ids:
                await group_role_service.create_many(
                    session=session,
                    objs=[CreateGroupRoleSchema(group_id=group.id, role_id=role_id) for role_id in data.roles_ids],
                )
        await session.refresh(group)
        return group

    async def read_group(self, *, request: Request, session: AsyncSession, id: uuid.UUID | str) -> GroupOutSchema:
        group: Group = await groups_service.read(session=session, id=id)
        if not group:
            raise BackendException(message="Group not found.", code=status.HTTP_404_NOT_FOUND)
        return GroupOutSchema.from_orm(obj=group)

    async def list_groups(
        self,
        *,
        request: Request,
        session: AsyncSession,
        pagination: BasePagination,
        sorting: list[UnaryExpression],
        filters: dict | None = None
    ) -> tuple[int, list[Group]]:
        objects: list[Group]
        return await groups_service.list(
            session=session,
            offset=pagination.offset,
            limit=pagination.limit,
            sorting=sorting,
            filters=filters,
            unique=True,
        )


class RolesHandler:
    async def create_role(self, *, request: Request, session: AsyncSession, data: RoleCreateSchema) -> RoleOutSchema:
        role_schema: RoleCreateToDBSchema = RoleCreateToDBSchema(id=uuid.uuid4(), name=data.name)
        async with session.begin_nested():
            role: Role = await roles_service.create(session=session, obj=role_schema, unique=True)
            if data.permissions_ids:
                await role_permission_service.create_many(
                    session=session,
                    objs=[
                        CreateRolePermissionSchema(role_id=role_schema.id, permission_id=permission_id)
                        for permission_id in data.permissions_ids
                    ],
                )
        await session.refresh(role)
        return role

    async def read_role(self, *, request: Request, session: AsyncSession, id: uuid.UUID | str) -> RoleOutSchema:
        role: Role = await roles_service.read(session=session, id=id)
        if not role:
            raise BackendException(message="Role not found.", code=status.HTTP_404_NOT_FOUND)
        return RoleOutSchema.from_orm(obj=role)

    async def list_roles(
        self,
        *,
        request: Request,
        session: AsyncSession,
        pagination: BasePagination,
        sorting,
        filters: dict | None = None
    ) -> tuple[int, list[Role]]:
        objects: list[Role]
        return await roles_service.list(
            session=session,
            offset=pagination.offset,
            limit=pagination.limit,
            sorting=sorting,
            filters=filters,
            unique=True,
        )


class PermissionsHandler:
    async def read_permission(
        self, *, request: Request, session: AsyncSession, id: uuid.UUID | str
    ) -> PermissionOutSchema:
        permission: Permission = await permissions_service.read(session=session, id=id)
        if not permission:
            raise BackendException(message="Permission not found.", code=status.HTTP_404_NOT_FOUND)
        return PermissionOutSchema.from_orm(obj=permission)

    async def list_permissions(
        self,
        *,
        request: Request,
        session: AsyncSession,
        pagination: BasePagination,
        sorting,
        filters: dict | None = None
    ) -> tuple[int, list[Permission]]:
        objects: list[Permission]
        total, objects = await permissions_service.list(
            session=session, offset=pagination.offset, limit=pagination.limit, sorting=sorting, filters=filters
        )
        return total, objects


groups_handler = GroupsHandler()
roles_handler = RolesHandler()
permissions_handler = PermissionsHandler()
