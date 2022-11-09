from sqlalchemy import VARCHAR, Column, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from apps.CORE.db import Base, CreatedAtMixin, CreatedUpdatedMixin, UUIDMixin
from apps.users.models import User

CASCADES = {"ondelete": "CASCADE", "onupdate": "CASCADE"}


class Group(Base, CreatedUpdatedMixin, UUIDMixin):
    name = Column(VARCHAR(length=256), nullable=False, unique=True, index=True)

    roles = relationship("Role", secondary="group_role", back_populates="groups", lazy="joined")
    users = relationship(User, secondary="group_user", backref="groups")

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(name="{self.name}")'


class Role(Base, CreatedUpdatedMixin, UUIDMixin):
    name = Column(VARCHAR(length=128), nullable=False, unique=True, index=True)

    groups = relationship(Group, secondary="group_role", back_populates="roles")
    permissions = relationship("Permission", secondary="role_permission", back_populates="roles", lazy="joined")
    users = relationship(User, secondary="role_user", backref="roles")

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(name="{self.name}")'


class Permission(Base, CreatedUpdatedMixin, UUIDMixin):
    __table_args__ = (UniqueConstraint("object_name", "action"),)

    object_name = Column(VARCHAR(length=128), nullable=False)
    action = Column(VARCHAR(length=32), nullable=False)

    roles = relationship(Role, secondary="role_permission", back_populates="permissions")
    users = relationship(User, secondary="permission_user", backref="permissions")

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(object_name="{self.object_name}", action="{self.action}")'

    def to_tuple(self) -> tuple[str, str]:
        return self.object_name, self.action


class GroupRole(Base, CreatedAtMixin):
    group_id = Column(UUID(as_uuid=True), ForeignKey(column=Group.id, **CASCADES), nullable=False, primary_key=True)
    role_id = Column(UUID(as_uuid=True), ForeignKey(column=Role.id, **CASCADES), nullable=False, primary_key=True)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(group_id="{self.group_id}", role_id="{self.role_id}")'


class RolePermission(Base, CreatedAtMixin):
    role_id = Column(UUID(as_uuid=True), ForeignKey(column=Role.id, **CASCADES), nullable=False, primary_key=True)
    permission_id = Column(
        UUID(as_uuid=True), ForeignKey(column=Permission.id, **CASCADES), nullable=False, primary_key=True
    )

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(role_id="{self.role_id}", permission_id="{self.permission_id}")'


class GroupUser(Base, CreatedAtMixin):
    group_id = Column(UUID(as_uuid=True), ForeignKey(column=Group.id, **CASCADES), nullable=False, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey(column=User.id, **CASCADES), nullable=False, primary_key=True)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(group_id="{self.group_id}", user_id="{self.user_id}")'


class RoleUser(Base, CreatedAtMixin):
    role_id = Column(UUID(as_uuid=True), ForeignKey(column=Role.id, **CASCADES), nullable=False, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey(column=User.id, **CASCADES), nullable=False, primary_key=True)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(role_id="{self.role_id}", user_id="{self.user_id}")'


class PermissionUser(Base, CreatedAtMixin):
    permission_id = Column(
        UUID(as_uuid=True), ForeignKey(column=Permission.id, **CASCADES), nullable=False, primary_key=True
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey(column=User.id, **CASCADES), nullable=False, primary_key=True)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(permission_id="{self.permission_id}", user_id="{self.user_id}")'
