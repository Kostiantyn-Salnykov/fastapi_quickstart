from core.db.bases import Base
from core.db.mixins import CreatedUpdatedMixin, UUIDMixin
from sqlalchemy import VARCHAR
from sqlalchemy.dialects.postgresql import JSONB, TEXT
from sqlalchemy.orm import Mapped, mapped_column
from starlette.authentication import BaseUser

from domain.users.enums import UserStatuses


class User(Base, UUIDMixin, CreatedUpdatedMixin, BaseUser):
    """User class and `user` table declaration.

    Keyword Args:
        first_name (str): First name of user.
        last_name (str): Last name of user.
        email (str): User's email.
        password_hash (str): Hashed value of password.
        status (str): Current status of user.
        settings (dict[str, Any]): Settings for the user.

        groups (list[Group]): Groups that are assigned to user.
        roles (list[Role]): Roles that assigned to user.
        permissions (list[Role]): Permissions that assigned to user.
    """

    first_name: Mapped[str] = mapped_column(VARCHAR(length=128), nullable=False)
    last_name: Mapped[str] = mapped_column(VARCHAR(length=128), nullable=False)
    email: Mapped[str] = mapped_column(VARCHAR(length=320), nullable=False, index=True, unique=True)
    password_hash: Mapped[str] = mapped_column(VARCHAR(length=1024), nullable=False)
    status: Mapped[str] = mapped_column(VARCHAR(length=64), default=UserStatuses.UNCONFIRMED.value, nullable=False)
    settings: Mapped[dict] = mapped_column(
        JSONB(none_as_null=True, astext_type=TEXT()),
        default=dict,
        nullable=False,
        doc="User's settings.",
        comment="TEST COMMENT.",
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
