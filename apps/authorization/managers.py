import uuid
from typing import Generator, Iterable

from sqlalchemy import inspect, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import ChunkedIteratorResult, Engine
from sqlalchemy.ext.asyncio import AsyncSession

from apps.authorization.enums import PermissionActions
from apps.authorization.models import Group, Permission, Role
from apps.CORE.db import Base
from apps.users.models import User
from loggers import get_logger

logger = get_logger(name=__name__)


# TODO: Split for commands / handlers
class AuthorizationManager:
    def __init__(self, engine: Engine = None) -> None:
        self._superuser_object_name = "__all__"
        self.excluded_table_names = ["alembic_version"]
        self._engine = engine

    def _get_table_names(self, engine: Engine = None) -> Generator[str, None, None]:
        inspector = inspect(subject=engine or self._engine)
        current_schema = str(Base.metadata.schema or "public")
        for schema in inspector.get_schema_names():
            if str(schema) == current_schema:
                for table in inspector.get_table_names(schema=schema):
                    if table in self.excluded_table_names:
                        continue
                    yield table

    def _generate_permissions_variants(self) -> Generator[tuple[str, PermissionActions], None, None]:
        for table_name in self._get_table_names():
            for action in PermissionActions:
                yield table_name, action

    async def create_permissions(self, session: AsyncSession) -> None:
        logger.debug(msg="Creating permissions for all models...")
        upsert_statement = (
            insert(Permission)
            .values(
                [{"object_name": table, "action": action} for table, action in self._generate_permissions_variants()]
            )
            .on_conflict_do_nothing()
        )
        await session.execute(statement=upsert_statement)
        await session.commit()
        logger.debug(msg="Permissions created successfully.")

    async def create_superuser_permissions(self, session: AsyncSession) -> list[Permission]:
        logger.debug(msg="Creating permissions...")
        async with session.begin_nested():
            permissions = [
                Permission(id=uuid.uuid4(), object_name=self._superuser_object_name, action=action)
                for action in PermissionActions
            ]
            upsert_permission = (
                insert(Permission)
                .values([{"id": p.id, "object_name": p.object_name, "action": p.action} for p in permissions])
                .on_conflict_do_nothing()
            )
            await session.execute(statement=upsert_permission)
        select_statement = select(Permission).where(Permission.object_name == self._superuser_object_name)
        query_result: ChunkedIteratorResult = await session.execute(statement=select_statement)
        result: list[Permission] = query_result.scalars().all()
        return result

    async def setup_superusers(self, session: AsyncSession) -> None:
        logger.debug(msg="Creating superuser Group, Role, Permissions...")
        permissions = await self.create_superuser_permissions(session=session)

        role: Role = Role(id=uuid.uuid4(), name="Superuser", permissions=permissions)
        try:
            logger.debug(msg=f"Creating {role}")
            async with session.begin_nested():
                session.add(instance=role)
                await session.commit()
            logger.debug(msg=f"{role} created.")
        except Exception:
            logger.debug(msg=f"{role} already created.")
            query_result: ChunkedIteratorResult = await session.execute(
                statement=select(Role).where(Role.name == "Superuser")
            )
            role = query_result.unique().scalar_one()

        group = Group(name="Superusers", roles=[role])
        try:
            logger.debug(msg=f"Creating {group}")
            async with session.begin_nested():
                session.add(instance=group)
                await session.commit()
            logger.debug(msg=f"{group} created.")
        except Exception:
            logger.debug(msg=f"{group} already created.")

    def get_permissions_set(
        self, groups: Iterable[Group], roles: Iterable[Role], permissions: Iterable[Permission]
    ) -> set[tuple[str, str]]:
        result_set: set[tuple[str, str]] = set()
        result_set.update(
            self.yield_permissions_from_groups(groups=groups),
            self.yield_permissions_from_roles(roles=roles),
            self.yield_permissions(permissions=permissions),
        )
        return result_set

    def get_permissions_set_from_user(self, user: User) -> set[tuple[str, str]]:
        return self.get_permissions_set(groups=user.groups, roles=user.roles, permissions=user.permissions)

    @staticmethod
    def yield_permissions(permissions: Iterable[Permission]) -> Generator[tuple[str, str], None, None]:
        for permission in permissions:
            yield permission.to_tuple()

    def yield_permissions_from_roles(self, roles: Iterable[Role]) -> Generator[tuple[str, str], None, None]:
        for role in roles:
            yield from self.yield_permissions(permissions=role.permissions)

    def yield_permissions_from_groups(self, groups: Iterable[Group]) -> Generator[tuple[str, str], None, None]:
        for group in groups:
            yield from self.yield_permissions_from_roles(roles=group.roles)
