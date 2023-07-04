import uuid

from sqlalchemy import VARCHAR, Column, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from starlette.authentication import BaseUser

from apps.CORE.db import Base, CreatedAtMixin, CreatedUpdatedMixin, UUIDMixin
from apps.users.enums import UsersStatuses

CASCADES = {"ondelete": "CASCADE", "onupdate": "CASCADE"}


class User(Base, UUIDMixin, CreatedUpdatedMixin, BaseUser):
    """User class and `user` table declaration.

    Keyword Args:
        first_name (str): First name of user.
        last_name (str): Last name of user.
        email (str): User's email.
        password_hash (str): Hashed value of password.
        status (str): Current status of user.

        groups (list[Group]): Groups that assigned to user.
        roles (list[Role]): Roles that assigned to user.
        permissions (list[Role]): Permissions that assigned to user.
    """

    first_name: Mapped[str] = mapped_column(VARCHAR(length=128), nullable=False)
    last_name: Mapped[str] = mapped_column(VARCHAR(length=128), nullable=False)
    email: Mapped[str] = mapped_column(VARCHAR(length=255), nullable=False, index=True, unique=True)
    password_hash: Mapped[str] = mapped_column(VARCHAR(length=1024), nullable=False)
    status: Mapped[str] = mapped_column(VARCHAR(length=64), default=UsersStatuses.UNCONFIRMED.value, nullable=False)

    groups: Mapped[list["Group"]] = relationship(
        "Group", secondary="group_user", back_populates="users", order_by="Group.title"
    )
    roles: Mapped[list["Role"]] = relationship(
        "Role", secondary="role_user", back_populates="users", order_by="Role.title"
    )
    permissions: Mapped[list["Permission"]] = relationship(
        "Permission",
        secondary="permission_user",
        back_populates="users",
        order_by="Permission.object_name, Permission.action",
    )

    def __repr__(self) -> str:
        """Representation of User."""
        return f'{self.__class__.__name__}(email="{self.email}", password_hash="...", status="{self.status}")'

    @property
    def is_authenticated(self) -> bool:
        """User is authenticated automatically."""
        return True

    @property
    def display_name(self) -> str:
        """Concatenate full name of user.

        Returns:
            - (str): Full name of user.
        """
        return f"{self.first_name} {self.last_name}"

    @property
    def identity(self) -> str:
        """Get user UUID and convert it to string.

        Returns:
            - (str): User's id converted to string.
        """
        return str(self.id)


class Group(Base, CreatedUpdatedMixin, UUIDMixin):
    title: Mapped[str] = mapped_column(VARCHAR(length=255), nullable=False, unique=True, index=True)

    roles: Mapped[list["Role"]] = relationship(
        "Role", secondary="group_role", back_populates="groups", lazy="joined", order_by="Role.title"
    )
    users: Mapped[list["User"]] = relationship("User", secondary="group_user", back_populates="groups")

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(name="{self.title}")'


class Role(Base, CreatedUpdatedMixin, UUIDMixin):
    title: Mapped[str] = mapped_column(VARCHAR(length=128), nullable=False, unique=True, index=True)

    groups: Mapped[list["Group"]] = relationship(
        "Group", secondary="group_role", back_populates="roles", order_by="Group.title"
    )
    permissions: Mapped[list["Permission"]] = relationship(
        "Permission",
        secondary="role_permission",
        back_populates="roles",
        lazy="joined",
        order_by="Permission.object_name, Permission.action",
    )
    users: Mapped[list["User"]] = relationship(
        "User", secondary="role_user", back_populates="roles", order_by="User.email"
    )

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(name="{self.title}")'


class Permission(Base, CreatedUpdatedMixin, UUIDMixin):
    __table_args__ = (UniqueConstraint("object_name", "action"),)

    object_name: Mapped[str] = mapped_column(VARCHAR(length=128), nullable=False)
    action: Mapped[str] = Column(VARCHAR(length=32), nullable=False)

    roles: Mapped[list["Role"]] = relationship(
        "Role", secondary="role_permission", back_populates="permissions", order_by="Role.title"
    )
    users: Mapped[list["User"]] = relationship(
        "User", secondary="permission_user", back_populates="permissions", order_by="User.email"
    )

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(object_name="{self.object_name}", action="{self.action}")'

    def to_tuple(self) -> tuple[str, str]:
        return self.object_name, self.action


class GroupRole(Base, CreatedAtMixin):
    group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(column="group.id", **CASCADES), nullable=False, primary_key=True
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(column="role.id", **CASCADES), nullable=False, primary_key=True
    )

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(group_id="{self.group_id}", role_id="{self.role_id}")'


class RolePermission(Base, CreatedAtMixin):
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(column="role.id", **CASCADES), nullable=False, primary_key=True
    )
    permission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(column="permission.id", **CASCADES), nullable=False, primary_key=True
    )

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(role_id="{self.role_id}", permission_id="{self.permission_id}")'


class GroupUser(Base, CreatedAtMixin):
    group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(column="group.id", **CASCADES), nullable=False, primary_key=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(column="user.id", **CASCADES), nullable=False, primary_key=True
    )

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(group_id="{self.group_id}", user_id="{self.user_id}")'


class RoleUser(Base, CreatedAtMixin):
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(column="role.id", **CASCADES), nullable=False, primary_key=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(column="user.id", **CASCADES), nullable=False, primary_key=True
    )

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(role_id="{self.role_id}", user_id="{self.user_id}")'


class PermissionUser(Base, CreatedAtMixin):
    permission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(column="permission.id", **CASCADES), nullable=False, primary_key=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(column="user.id", **CASCADES), nullable=False, primary_key=True
    )

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(permission_id="{self.permission_id}", user_id="{self.user_id}")'
