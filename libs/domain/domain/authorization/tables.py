import uuid
from typing import TYPE_CHECKING

from core.db.bases import CASCADES, Base
from core.db.mixins import CreatedAtMixin, CreatedUpdatedMixin, UUIDMixin
from sqlalchemy import BIGINT, VARCHAR, Column, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from domain.users.tables import User


class CasbinRule(Base):
    id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    ptype: Mapped[str] = mapped_column(VARCHAR(255))
    v0: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    v1: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    v2: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    v3: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    v4: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    v5: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)

    def __str__(self) -> str:
        arr = [self.ptype]
        for v in (self.v0, self.v1, self.v2, self.v3, self.v4, self.v5):
            if v is None:
                break
            arr.append(v)
        return ", ".join(arr)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.__str__()})"


class Group(Base, CreatedUpdatedMixin, UUIDMixin):
    """Group class and `group` table declaration."""

    title: Mapped[str] = mapped_column(VARCHAR(length=255), nullable=False, unique=True, index=True)

    roles: Mapped[list["Role"]] = relationship(
        "Role",
        secondary="group_role",
        back_populates="groups",
        lazy="joined",
        order_by="Role.title",
    )
    users: Mapped[list["User"]] = relationship("User", secondary="group_user", backref="groups")

    def __repr__(self) -> str:
        """Representation of Group."""
        return f'{self.__class__.__name__}(name="{self.title}")'


class Role(Base, CreatedUpdatedMixin, UUIDMixin):
    """Role class and `role` table declaration."""

    title: Mapped[str] = mapped_column(VARCHAR(length=128), nullable=False, unique=True, index=True)

    groups: Mapped[list["Group"]] = relationship(
        "Group",
        secondary="group_role",
        back_populates="roles",
        order_by="Group.title",
    )
    permissions: Mapped[list["Permission"]] = relationship(
        "Permission",
        secondary="role_permission",
        back_populates="roles",
        lazy="joined",
        order_by="Permission.object_name, Permission.action",
    )
    users: Mapped[list["User"]] = relationship(
        "User",
        secondary="role_user",
        backref="roles",
        order_by="User.email",
    )

    def __repr__(self) -> str:
        """Representation of Role."""
        return f'{self.__class__.__name__}(name="{self.title}")'


class Permission(Base, CreatedUpdatedMixin, UUIDMixin):
    """Permission class and `permission` table declaration."""

    __table_args__ = (UniqueConstraint("object_name", "action"),)

    object_name: Mapped[str] = mapped_column(VARCHAR(length=128), nullable=False)
    action: Mapped[str] = Column(VARCHAR(length=32), nullable=False)

    roles: Mapped[list["Role"]] = relationship(
        "Role",
        secondary="role_permission",
        back_populates="permissions",
        order_by="Role.title",
    )
    users: Mapped[list["User"]] = relationship(
        "User",
        secondary="permission_user",
        backref="permissions",
        order_by="User.email",
    )

    def __repr__(self) -> str:
        """Representation of Permission."""
        return f'{self.__class__.__name__}(object_name="{self.object_name}", action="{self.action}")'

    def to_tuple(self) -> tuple[str, str]:
        """Represent Permission as a tuple: (object_name, action)."""
        return self.object_name, self.action


class GroupRole(Base, CreatedAtMixin):
    """GroupRole class and `group_role` association table declaration."""

    group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(column="group.id", **CASCADES),
        nullable=False,
        primary_key=True,
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(column="role.id", **CASCADES),
        nullable=False,
        primary_key=True,
    )

    def __repr__(self) -> str:
        """Representation of GroupRole."""
        return f'{self.__class__.__name__}(group_id="{self.group_id}", role_id="{self.role_id}")'


class RolePermission(Base, CreatedAtMixin):
    """RolePermission class and `role_permission` association table declaration."""

    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(column="role.id", **CASCADES),
        nullable=False,
        primary_key=True,
    )
    permission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(column="permission.id", **CASCADES),
        nullable=False,
        primary_key=True,
    )

    def __repr__(self) -> str:
        """Representation of RolePermission."""
        return f'{self.__class__.__name__}(role_id="{self.role_id}", permission_id="{self.permission_id}")'


class GroupUser(Base, CreatedAtMixin):
    """GroupUser class and `group_user` association table declaration."""

    group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(column="group.id", **CASCADES),
        nullable=False,
        primary_key=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(column="user.id", **CASCADES),
        nullable=False,
        primary_key=True,
    )

    def __repr__(self) -> str:
        """Representation of GroupUser."""
        return f'{self.__class__.__name__}(group_id="{self.group_id}", user_id="{self.user_id}")'


class RoleUser(Base, CreatedAtMixin):
    """RoleUser class and `role_user` association table declaration."""

    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(column="role.id", **CASCADES),
        nullable=False,
        primary_key=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(column="user.id", **CASCADES),
        nullable=False,
        primary_key=True,
    )

    def __repr__(self) -> str:
        """Representation of RoleUser."""
        return f'{self.__class__.__name__}(role_id="{self.role_id}", user_id="{self.user_id}")'


class PermissionUser(Base, CreatedAtMixin):
    """PermissionUser class and `permission_user` association table declaration."""

    permission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(column="permission.id", **CASCADES),
        nullable=False,
        primary_key=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(column="user.id", **CASCADES),
        nullable=False,
        primary_key=True,
    )

    def __repr__(self) -> str:
        """Representation of PermissionUser."""
        return f'{self.__class__.__name__}(permission_id="{self.permission_id}", user_id="{self.user_id}")'
