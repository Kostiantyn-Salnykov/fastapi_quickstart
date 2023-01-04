import uuid

from sqlalchemy import select
from sqlalchemy.engine import ChunkedIteratorResult
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import BinaryExpression, UnaryExpression

from apps.authorization.models import Group, GroupRole, Permission, Role, RolePermission
from apps.authorization.schemas import CreateGroupRoleSchema, CreateRolePermissionSchema
from apps.CORE.services import AsyncCRUDBase


class GroupsService(AsyncCRUDBase):
    async def read(self, *, session: AsyncSession, id: str | uuid.UUID, unique: bool = True) -> Group | None:
        return await super().read(session=session, id=id, unique=True)

    async def list(
        self,
        *,
        session: AsyncSession,
        sorting: list[UnaryExpression],
        offset: int = 0,
        limit: int = 100,
        filters: list[BinaryExpression] | None = None,  # TODO: Add dynamic filtering system
        unique: bool = False
    ) -> tuple[int, list[Group]]:
        return await super().list(
            session=session, sorting=sorting, offset=offset, limit=limit, filters=filters, unique=True
        )


class GroupRoleService(AsyncCRUDBase):
    async def create_many(
        self, *, session: AsyncSession, objs: list[CreateGroupRoleSchema], unique: bool = False
    ) -> list[GroupRole] | None:
        return await super().create_many(session=session, objs=objs, unique=unique)


class RolesService(AsyncCRUDBase):
    async def read(self, *, session: AsyncSession, id: str | uuid.UUID) -> Role | None:
        statement = select(self.model).where(self.model.id == id)
        result: ChunkedIteratorResult = await session.execute(statement=statement)
        data: Role | None = result.unique().scalar_one_or_none()
        return data

    async def list(
        self,
        *,
        session: AsyncSession,
        sorting: list[UnaryExpression],
        offset: int = 0,
        limit: int = 100,
        filters: list[BinaryExpression] | None = None,  # TODO: Add dynamic filtering system
        unique: bool = False
    ) -> tuple[int, list[Role]]:
        return await super().list(
            session=session, sorting=sorting, offset=offset, limit=limit, filters=filters, unique=True
        )


class RolePermissionService(AsyncCRUDBase):
    async def create_many(
        self, *, session: AsyncSession, objs: list[CreateRolePermissionSchema], unique: bool = False
    ) -> list[RolePermission] | None:
        return await super().create_many(session=session, objs=objs, unique=unique)


class PermissionsService(AsyncCRUDBase):
    ...


groups_service = GroupsService(model=Group)
group_role_service = GroupRoleService(model=GroupRole)
roles_service = RolesService(model=Role)
role_permission_service = RolePermissionService(model=RolePermission)
permissions_service = PermissionsService(model=Permission)
