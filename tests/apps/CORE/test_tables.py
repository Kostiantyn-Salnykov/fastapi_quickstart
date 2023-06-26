from apps.CORE.models import (
    Group,
    GroupRole,
    GroupUser,
    Permission,
    PermissionUser,
    Role,
    RolePermission,
    RoleUser,
    User,
)
from tests.apps.CORE.factories import (
    GroupFactory,
    GroupRoleFactory,
    GroupUserFactory,
    PermissionFactory,
    PermissionUserFactory,
    RoleFactory,
    RolePermissionFactory,
    RoleUserFactory,
    UserFactory,
)
from tests.bases import BaseModelFactory


class TestPermission:
    def test_factory(self) -> None:
        BaseModelFactory.check_factory(factory_class=PermissionFactory, model=Permission)

    def test__repr__(self) -> None:
        obj: Permission = PermissionFactory()
        expected_result = f'{obj.__class__.__name__}(object_name="{obj.object_name}", action="{obj.action}")'

        result = obj.__repr__()

        assert expected_result == result

    def test_to_tuple(self) -> None:
        obj: Permission = PermissionFactory()

        result = obj.to_tuple()

        assert (obj.object_name, obj.action) == result


class TestRole:
    def test_factory(self) -> None:
        BaseModelFactory.check_factory(factory_class=RoleFactory, model=Role)

    def test__repr__(self) -> None:
        obj: Role = RoleFactory()
        expected_result = f'{obj.__class__.__name__}(name="{obj.title}")'

        result = obj.__repr__()

        assert expected_result == result


class TestGroup:
    def test_factory(self) -> None:
        BaseModelFactory.check_factory(factory_class=GroupFactory, model=Group)

    def test__repr__(self) -> None:
        obj: Group = GroupFactory()
        expected_result = f'{obj.__class__.__name__}(name="{obj.title}")'

        result = obj.__repr__()

        assert expected_result == result


class TestRolePermission:
    def test_factory(self) -> None:
        BaseModelFactory.check_factory(factory_class=RolePermissionFactory, model=RolePermission)

    def test__repr__(self) -> None:
        obj: RolePermission = RolePermissionFactory()
        expected_result = f'{obj.__class__.__name__}(role_id="{obj.role_id}", permission_id="{obj.permission_id}")'

        result = obj.__repr__()

        assert expected_result == result


class TestGroupRole:
    def test_factory(self) -> None:
        BaseModelFactory.check_factory(factory_class=GroupRoleFactory, model=GroupRole)

    def test__repr__(self) -> None:
        obj: GroupRole = GroupRoleFactory()
        expected_result = f'{obj.__class__.__name__}(group_id="{obj.group_id}", role_id="{obj.role_id}")'

        result = obj.__repr__()

        assert expected_result == result


class TestPermissionUser:
    def test_factory(self) -> None:
        BaseModelFactory.check_factory(factory_class=PermissionUserFactory, model=PermissionUser)

    def test__repr__(self) -> None:
        obj: PermissionUser = PermissionUserFactory()
        expected_result = f'{obj.__class__.__name__}(permission_id="{obj.permission_id}", user_id="{obj.user_id}")'

        result = obj.__repr__()

        assert expected_result == result


class TestRoleUser:
    def test_factory(self) -> None:
        BaseModelFactory.check_factory(factory_class=RoleUserFactory, model=RoleUser)

    def test__repr__(self) -> None:
        obj: RoleUser = RoleUserFactory()
        expected_result = f'{obj.__class__.__name__}(role_id="{obj.role_id}", user_id="{obj.user_id}")'

        result = obj.__repr__()

        assert expected_result == result


class TestGroupUser:
    def test_factory(self) -> None:
        BaseModelFactory.check_factory(factory_class=GroupUserFactory, model=GroupUser)

    def test__repr__(self) -> None:
        obj: GroupUser = GroupUserFactory()
        expected_result = f'{obj.__class__.__name__}(group_id="{obj.group_id}", user_id="{obj.user_id}")'

        result = obj.__repr__()

        assert expected_result == result


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
