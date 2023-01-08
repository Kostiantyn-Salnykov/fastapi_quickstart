import factory

from apps.CORE.managers import PasswordsManager
from apps.users.models import User
from tests.bases import BaseModelFactory

__all__ = ("UserFactory",)


passwords_manager = PasswordsManager()
DEFAULT_PASSWORD = "12345678"


class UserFactory(BaseModelFactory):
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email = factory.Faker("email")
    password = factory.Faker("pystr", min_chars=8)
    password_hash = factory.LazyAttribute(function=lambda obj: passwords_manager.make_password(password=obj.password))

    class Meta:
        model = User
        exclude = ("password",)
        sqlalchemy_get_or_create = ("email",)
