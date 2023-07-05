import typing

import uuid_extensions
from fastapi import Request, status
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import BinaryExpression, UnaryExpression

from apps.authorization.schemas import GroupCreateToDBSchema, RoleCreateToDBSchema
from apps.authorization.schemas.requests import GroupCreateRequest, GroupUpdateRequest, RoleCreateRequest
from apps.authorization.schemas.responses import GroupResponse, PermissionResponse, RoleResponse
from apps.authorization.services import (
    group_role_service,
    groups_service,
    permissions_service,
    role_permission_service,
    roles_service,
)
from apps.CORE.deps.pagination import NextTokenPagination
from apps.CORE.exceptions import BackendError
from apps.CORE.helpers import to_db_encoder
from apps.CORE.models import Group, Permission, Role
from apps.CORE.types import StrOrUUID
from loggers import get_logger

logger = get_logger(name=__name__)


class GroupsHandler:
    async def create_group(self, *, request: Request, session: AsyncSession, data: GroupCreateRequest) -> GroupResponse:
        group_schema: GroupCreateToDBSchema = GroupCreateToDBSchema(id=uuid_extensions.uuid7str(), title=data.title)
        if data.roles_ids:
            await roles_service.list_or_not_found(session=session, ids=data.roles_ids, message="Role(s) not found.")
        async with session.begin_nested():
            group: Group = await groups_service.create(session=session, values=to_db_encoder(obj=group_schema))
            if data.roles_ids:
                await group_role_service.create_many(
                    session=session,
                    values_list=[{"group_id": group.id, "role_id": role_id} for role_id in data.roles_ids],
                )
        await session.refresh(group)
        return GroupResponse.from_orm(obj=group)

    async def read_group(self, *, request: Request, session: AsyncSession, id: StrOrUUID) -> GroupResponse:
        group: Group = await groups_service.read_or_not_found(session=session, id=id, message="Group not found.")
        return GroupResponse.from_orm(obj=group)

    async def list_groups(
        self,
        *,
        request: Request,
        session: AsyncSession,
        pagination: NextTokenPagination,
        sorting: list[UnaryExpression],
        filters: list[BinaryExpression] | None = None
    ) -> tuple[int, list[Group]]:
        return await groups_service.list(
            session=session,
            next_token=pagination.next_token,
            limit=pagination.limit,
            sorting=sorting,
            filters=filters,
        )

    async def update_group(
        self, *, request: Request, session: AsyncSession, id: StrOrUUID, data: GroupUpdateRequest
    ) -> GroupResponse:
        values: dict[str, typing.Any] = to_db_encoder(obj=data, exclude={"roles_ids"})
        if not values:
            raise BackendError(message="Nothing to update.")
        group: Group = await groups_service.read_or_not_found(session=session, id=id, message="Group no found.")
        if data.roles_ids:
            roles = await roles_service.list_or_not_found(
                session=session, ids=data.roles_ids, message="Role(s) not found."
            )
            group.roles = roles
        else:
            group.roles = []
        for k, v in values.items():
            setattr(group, k, v)
        await session.flush()
        return group

    async def delete_group(self, *, request: Request, session: AsyncSession, id: StrOrUUID, safe: bool = False) -> None:
        result: CursorResult = await groups_service.delete(session=session, id=id)
        if not result.rowcount and not safe:
            raise BackendError(message="Group not found.", code=status.HTTP_404_NOT_FOUND)
        return None


class RolesHandler:
    async def create_role(self, *, request: Request, session: AsyncSession, data: RoleCreateRequest) -> RoleResponse:
        role_schema: RoleCreateToDBSchema = RoleCreateToDBSchema(id=uuid_extensions.uuid7str(), title=data.title)
        if data.permissions_ids:
            await permissions_service.list_or_not_found(
                session=session, ids=data.permissions_ids, message="Permission(s) not found."
            )
        async with session.begin_nested():
            role: Role = await roles_service.create(session=session, values=to_db_encoder(role_schema), unique=True)
            if data.permissions_ids:
                await role_permission_service.create_many(
                    session=session,
                    values_list=[
                        {"role_id": role_schema.id, "permission_id": permission_id}
                        for permission_id in data.permissions_ids
                    ],
                )
        await session.refresh(role)
        return role

    async def read_role(self, *, request: Request, session: AsyncSession, id: StrOrUUID) -> RoleResponse:
        role: Role = await roles_service.read(session=session, id=id)
        if not role:
            raise BackendError(message="Role not found.", code=status.HTTP_404_NOT_FOUND)
        return RoleResponse.from_orm(obj=role)

    async def list_roles(
        self,
        *,
        request: Request,
        session: AsyncSession,
        pagination: NextTokenPagination,
        sorting: list[UnaryExpression],
        filters: list[BinaryExpression] | None = None
    ) -> tuple[int, list[Role]]:
        return await roles_service.list(
            session=session,
            next_token=pagination.next_token,
            limit=pagination.limit,
            sorting=sorting,
            filters=filters,
            unique=True,
        )

    async def delete_role(self, *, request: Request, session: AsyncSession, id: StrOrUUID, safe: bool = False) -> None:
        result: CursorResult = await roles_service.delete(session=session, id=id)
        if not result.rowcount and not safe:
            raise BackendError(message="Role not found.", code=status.HTTP_404_NOT_FOUND)
        return None


class PermissionsHandler:
    async def read_permission(self, *, request: Request, session: AsyncSession, id: StrOrUUID) -> PermissionResponse:
        permission: Permission = await permissions_service.read(session=session, id=id)
        if not permission:
            raise BackendError(message="Permission not found.", code=status.HTTP_404_NOT_FOUND)
        return PermissionResponse.from_orm(obj=permission)

    async def list_permissions(
        self,
        *,
        request: Request,
        session: AsyncSession,
        pagination: NextTokenPagination,
        sorting: list[UnaryExpression],
        filters: list[BinaryExpression] | None = None
    ) -> tuple[int, list[Permission]]:
        objects: list[Permission]
        total, objects = await permissions_service.list(
            session=session, limit=pagination.limit, next_token=pagination.next_token, sorting=sorting, filters=filters
        )
        return total, objects


groups_handler = GroupsHandler()
roles_handler = RolesHandler()
permissions_handler = PermissionsHandler()
