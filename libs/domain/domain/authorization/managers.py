import itertools
from collections.abc import Generator, Iterable

import uuid_extensions
from core.custom_logging import get_logger
from core.db.bases import Base
from sqlalchemy import inspect, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import ChunkedIteratorResult, Engine
from sqlalchemy.ext.asyncio import AsyncSession

from domain.authorization.enums import PermissionActions
from domain.authorization.tables import Group, Permission, Role
from domain.users.tables import User

logger = get_logger(name=__name__)


# TODO: Split for commands / handlers
class AuthorizationManager:
    def __init__(self, engine: Engine = None) -> None:
        self._superuser_object_name = "__all__"
        self._superuser_role_name = "Superuser"
        self._superuser_group_name = f"{self._superuser_role_name}s"
        self.excluded_table_names = ["alembic_version"]
        self._engine = engine

    def get_db_table_names(self, *, engine: Engine = None) -> Generator[str, None, None]:
        """Iterates through the db schema and return table names.

        Keyword Args:
            engine (Engine): SQLAlchemy Engine instance.

        Yields:
            str: Table name.
        """
        inspector = inspect(subject=engine or self._engine)
        current_schema = str(Base.metadata.schema or "public")
        for schema in inspector.get_schema_names():
            if str(schema) == current_schema:
                for table in inspector.get_table_names(schema=schema):
                    if table not in self.excluded_table_names:
                        yield table

    def _generate_permissions_variants(self) -> Generator[tuple[str, PermissionActions], None, None]:
        """Iterates through all tables in "public" schema, iterate through PermissionActions.

        Yields:
            tuple[str, PermissionActions]: Tuple with variant where (table_name, action).
        """
        return itertools.product(self.get_db_table_names(), PermissionActions)

    async def create_object_permissions(self, *, session: AsyncSession) -> None:
        """Creates permissions for all tables and actions ("<TABLE_NAME>", "create|read|update|delete").

        Keyword Args:
            session (AsyncSession): SQLAlchemy AsyncSession instance.
        """
        logger.debug("Creating permissions for all models...")
        upsert_statement = (
            insert(Permission)
            .values(
                [{"object_name": table, "action": action} for table, action in self._generate_permissions_variants()],
            )
            .on_conflict_do_nothing()
        )
        await session.execute(statement=upsert_statement)
        await session.commit()
        logger.debug("Permissions created successfully.")

    async def create_superuser_permissions(self, *, session: AsyncSession) -> list[Permission]:
        """Creates 4 superuser permissions ("__all__", "create|read|update|delete").

        Keyword Args:
            session (AsyncSession): SQLAlchemy AsyncSession instance.

        Returns:
            list[Permission]: list of Permission instances.
        """
        logger.debug("Creating permissions for superusers...")
        async with session.begin_nested():
            # Generate Permission instances with superuser object_name.
            permissions = (
                Permission(id=uuid_extensions.uuid7str(), object_name=self._superuser_object_name, action=action)
                for action in PermissionActions
            )
            # Create or Update permissions
            upsert_permission = (
                insert(Permission)
                .values([{"id": p.id, "object_name": p.object_name, "action": p.action} for p in permissions])
                .on_conflict_do_nothing()
            )
            await session.execute(statement=upsert_permission)
        # Retrieve permissions with superuser privileges.
        select_statement = select(Permission).where(Permission.object_name == self._superuser_object_name)
        query_result: ChunkedIteratorResult = await session.execute(statement=select_statement)
        result: list[Permission] = query_result.scalars().all()
        return result

    async def setup_superusers(self, *, session: AsyncSession) -> None:
        """Method to prepare Superuser Group (with Role and Permissions).

        1) Creates 4 superuser permissions ("__all__", "create|read|update|delete").
        2) Create "Superuser" Role with these permissions.
        3) Create "Superusers" Group and assign "Superuser" Role to it.

        Keyword Args:
            session (AsyncSession): SQLAlchemy AsyncSession instance.
        """
        logger.debug("Creating Permissions, Role, Group for superusers...")
        permissions = await self.create_superuser_permissions(session=session)

        role: Role = Role(id=uuid_extensions.uuid7str(), title=self._superuser_role_name, permissions=permissions)
        try:
            logger.debug(f"Creating {role}")
            async with session.begin_nested():
                session.add(instance=role)
                await session.commit()
            logger.debug(f"{role} created.")
        except Exception:
            logger.debug(f"{role} already created.")
            query_result: ChunkedIteratorResult = await session.execute(
                statement=select(Role).where(Role.title == self._superuser_role_name),
            )
            role = query_result.unique().scalar_one()

        group = Group(title=self._superuser_group_name, roles=[role])
        try:
            logger.debug(f"Creating {group}")
            async with session.begin_nested():
                session.add(instance=group)
                await session.commit()
            logger.debug(f"{group} created.")
        except Exception:
            logger.debug(f"{group} already created.")

    def get_permissions_set(
        self,
        *,
        groups: Iterable[Group],
        roles: Iterable[Role],
        permissions: Iterable[Permission],
    ) -> set[tuple[str, str]]:
        """Collect all permissions from groups, roles, and permissions to result set of permissions.

        Keyword Args:
            groups (Iterable[Group]): collection of Group instances.
            roles (Iterable[Role]): collection of Role instances.
            permissions (Iterable[Permission]): collection of Role instances.

        Returns:
            set[tuple[str, str]]: set of permissions (e.g. {("user", "read"), ("user", "update")}
        """
        result_set: set[tuple[str, str]] = set()
        result_set.update(
            self.yield_permissions_from_groups(groups=groups),
            self.yield_permissions_from_roles(roles=roles),
            self.yield_permissions(permissions=permissions),
        )
        return result_set

    def get_permissions_set_from_user(self, *, user: User) -> set[tuple[str, str]]:
        """Grab all users groups, roles and permissions then produce result set of permissions.

        Keyword Args:
            user (User): User instance

        Returns:
            set[tuple[str, str]]: set of permissions (e.g. {("user", "read"), ("user", "update")}
        """
        return self.get_permissions_set(groups=user.groups, roles=user.roles, permissions=user.permissions)

    @staticmethod
    def yield_permissions(*, permissions: Iterable[Permission]) -> Generator[tuple[str, str], None, None]:
        """Iterate through the collection of permissions and convert them to tuple.

        Keyword Args:
            permissions (Iterable[Permission]): collection of Permission instances.

        Yields:
            tuple[str, str]: Permission.to_tuple(), where index 0 - object name & 1 - action.
        """
        for permission in permissions:
            yield permission.to_tuple()

    def yield_permissions_from_roles(self, *, roles: Iterable[Role]) -> Generator[tuple[str, str], None, None]:
        """Iterate through the collection of roles, get permissions from them and convert them to tuple.

        Keyword Args:
            roles (Iterable[Role]): collection of Role instances.

        Yields:
            tuple[str, str]: Permission.to_tuple(), where index 0 - object name & 1 - action.
        """
        for role in roles:
            yield from self.yield_permissions(permissions=role.permissions)

    def yield_permissions_from_groups(self, *, groups: Iterable[Group]) -> Generator[tuple[str, str], None, None]:
        """Iterate through the collection of roles, get permissions from them and convert them to tuple.

        Keyword Args:
            groups (Iterable[Group]): collection of Group instances.

        Yields:
            tuple[str, str]: Permission.to_tuple(), where index 0 - object name & 1 - action.
        """
        for group in groups:
            yield from self.yield_permissions_from_roles(roles=group.roles)
