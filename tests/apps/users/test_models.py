from apps.CORE.tables import User
from tests.apps.users.factories import UserFactory
from tests.bases import BaseModelFactory


class TestUser:
    async def test_factory(self) -> None:
        BaseModelFactory.check_factory(factory_class=UserFactory, model=User)

    async def test__repr__(self) -> None:
        user: User = UserFactory()
        expected_result: str = (
            f'{user.__class__.__name__}(email="{user.email}", password_hash="...", status="{user.status}")'
        )

        assert expected_result == repr(user)

    async def test_is_authenticated(self) -> None:
        user: User = UserFactory()

        assert user.is_authenticated is True

    async def test_display_name(self) -> None:
        user: User = UserFactory()
        expected_result = f"{user.first_name} {user.last_name}"

        assert expected_result == user.display_name

    async def test_identity(self) -> None:
        user: User = UserFactory()

        assert str(user.id) == user.identity
