from sqlalchemy import VARCHAR, Column
from starlette.authentication import BaseUser

from apps.CORE.db import Base, CreatedUpdatedMixin, UUIDMixin
from apps.users.enums import UsersStatuses


class User(Base, UUIDMixin, CreatedUpdatedMixin, BaseUser):
    first_name = Column(VARCHAR(length=128), nullable=False)
    last_name = Column(VARCHAR(length=128), nullable=False)
    email = Column(VARCHAR(length=256), nullable=False, index=True, unique=True)
    password_hash = Column(VARCHAR(length=1024), nullable=False)
    status = Column(VARCHAR(length=64), default=UsersStatuses.UNCONFIRMED.value, nullable=False)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(email="{self.email}", password_hash="...", status="{self.status}")'

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def display_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def identity(self) -> str:
        return str(self.id)
