from sqlalchemy import VARCHAR, Column
from sqlalchemy.orm import relationship
from starlette.authentication import BaseUser

from apps.authorization.models import Group, Permission, Role
from apps.CORE.db import Base, CreatedUpdatedMixin, UUIDMixin
from apps.users.enums import UsersStatuses


class User(Base, UUIDMixin, CreatedUpdatedMixin, BaseUser):
    """
    User class and `user` table declaration.

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

    first_name = Column(VARCHAR(length=128), nullable=False)
    last_name = Column(VARCHAR(length=128), nullable=False)
    email = Column(VARCHAR(length=256), nullable=False, index=True, unique=True)
    password_hash = Column(VARCHAR(length=1024), nullable=False)
    status = Column(VARCHAR(length=64), default=UsersStatuses.UNCONFIRMED.value, nullable=False)

    groups = relationship(Group, secondary="group_user", back_populates="users")
    roles = relationship(Role, secondary="role_user", back_populates="users")
    permissions = relationship(Permission, secondary="permission_user", back_populates="users")

    def __repr__(self) -> str:
        """Representation of User."""
        return f'{self.__class__.__name__}(email="{self.email}", password_hash="...", status="{self.status}")'

    @property
    def is_authenticated(self) -> bool:
        """User is authenticated automatically."""
        return True

    @property
    def display_name(self) -> str:
        """
        Concatenate full name of user.

        Returns:
            - (str): Full name of user.
        """
        return f"{self.first_name} {self.last_name}"

    @property
    def identity(self) -> str:
        """
        Get user UUID and convert it to string.

        Returns:
            - (str): User's id converted to string.
        """
        return str(self.id)
