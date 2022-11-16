import typing
import uuid

from pydantic_factories import PostGenerated, Use

from apps.CORE.managers import PasswordsManager
from apps.users.models import User
from apps.users.schemas import UserCreateToDBSchema
from tests.bases import AsyncPersistenceHandler, BaseFactory

passwords_manager = PasswordsManager()
DEFAULT_PASSWORD = "12345678"


def make_password(name: str, values: dict[str, typing.Any], **kwargs: str) -> str:
    return passwords_manager.make_password(password=kwargs.get("password", DEFAULT_PASSWORD))


class UserFactory(BaseFactory):
    """UserFactory based on Faker and Pydantic."""

    id = Use(fn=uuid.uuid4)
    password_hash: str = PostGenerated(fn=make_password, password=DEFAULT_PASSWORD)

    __model__ = UserCreateToDBSchema
    __allow_none_optionals__ = False  # Factory will generate all fields (even for Optional fields)
    __async_persistence__ = AsyncPersistenceHandler(model=User)
