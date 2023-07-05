import random
import typing

import factory

from apps.authorization.enums import PermissionActions
from apps.authorization.managers import AuthorizationManager
from apps.CORE.managers import PasswordsManager
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
from tests.bases import BaseModelFactory

passwords_manager = PasswordsManager()
DEFAULT_PASSWORD = "12345678"


class UserFactory(BaseModelFactory):
    id = factory.Faker("uuid4", cast_to=None)
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email = factory.Faker("email")
    password = factory.Faker("pystr", min_chars=8)
    password_hash = factory.LazyAttribute(function=lambda obj: passwords_manager.make_password(password=obj.password))

    groups = factory.RelatedFactoryList(
        factory="tests.apps.CORE.factories.GroupUserFactory", factory_related_name="user", size=0
    )
    roles = factory.RelatedFactoryList(
        factory="tests.apps.CORE.factories.RoleUserFactory", factory_related_name="user", size=0
    )
    permissions = factory.RelatedFactoryList(
        factory="tests.apps.CORE.factories.PermissionUserFactory", factory_related_name="user", size=0
    )

    class Meta:
        model = User
        exclude = ("password",)
        sqlalchemy_get_or_create = ("email",)


class PermissionFactory(BaseModelFactory):
    id = factory.Faker("uuid4", cast_to=None)
    object_name = factory.Faker("pystr", max_chars=128)
    action = factory.Faker("word", ext_word_list=list(PermissionActions))

    roles = factory.RelatedFactoryList(
        factory="tests.apps.CORE.factories.RolePermissionFactory", factory_related_name="permission", size=0
    )
    users = factory.RelatedFactoryList(
        factory="tests.apps.CORE.factories.PermissionUserFactory", factory_related_name="permission", size=0
    )

    class Meta:
        model = Permission
        sqlalchemy_get_or_create = ("object_name", "action")

    @classmethod
    def _create(
        cls, model_class: type[Permission], *args: tuple[typing.Any], **kwargs: dict[str, typing.Any]
    ) -> Permission:
        session = cls._meta.sqlalchemy_session
        am = AuthorizationManager(engine=session.bind)
        permissions: list[str] = list(am.get_db_table_names())
        kwargs["object_name"] = random.choice(permissions)
        return super(BaseModelFactory, cls)._create(model_class=model_class, *args, **kwargs)


class RolePermissionFactory(BaseModelFactory):
    role_id = factory.SelfAttribute(attribute_name="role.id")
    permission_id = factory.SelfAttribute(attribute_name="permission.id")

    role = factory.SubFactory(factory="tests.apps.CORE.factories.RoleFactory")
    permission = factory.SubFactory(factory=PermissionFactory)

    class Meta:
        model = RolePermission
        exclude = ("role", "permission")
        sqlalchemy_get_or_create = ("role_id", "permission_id")


class RoleFactory(BaseModelFactory):
    id = factory.Faker("uuid4", cast_to=None)
    title = factory.Faker("pystr", max_chars=128)

    groups = factory.RelatedFactoryList(
        factory="tests.apps.CORE.factories.GroupRoleFactory", factory_related_name="roles", size=0
    )
    permissions = factory.RelatedFactoryList(factory=RolePermissionFactory, factory_related_name="role", size=1)
    users = factory.RelatedFactoryList(
        factory="tests.apps.CORE.factories.RoleUserFactory", factory_related_name="role", size=0
    )

    class Meta:
        model = Role
        sqlalchemy_get_or_create = ("title",)


class GroupRoleFactory(BaseModelFactory):
    group_id = factory.SelfAttribute(attribute_name="group.id")
    role_id = factory.SelfAttribute(attribute_name="role.id")

    group = factory.SubFactory(factory="tests.apps.CORE.factories.GroupFactory")
    role = factory.SubFactory(factory=RoleFactory)

    class Meta:
        model = GroupRole
        exclude = ("group", "role")
        sqlalchemy_get_or_create = ("group_id", "role_id")


class GroupFactory(BaseModelFactory):
    id = factory.Faker("uuid4", cast_to=None)
    title = factory.Faker("pystr", max_chars=255)

    roles = factory.RelatedFactoryList(factory=GroupRoleFactory, factory_related_name="group", size=1)
    users = factory.RelatedFactoryList(
        factory="tests.apps.CORE.factories.GroupUserFactory", factory_related_name="group", size=0
    )

    class Meta:
        model = Group
        sqlalchemy_get_or_create = ("title",)


class PermissionUserFactory(BaseModelFactory):
    permission_id = factory.SelfAttribute(attribute_name="permission.id")
    user_id = factory.SelfAttribute(attribute_name="user.id")

    permission = factory.SubFactory(factory=PermissionFactory)
    user = factory.SubFactory(factory=UserFactory)

    class Meta:
        model = PermissionUser
        exclude = ("permission", "user")
        sqlalchemy_get_or_create = ("permission_id", "user_id")


class RoleUserFactory(BaseModelFactory):
    role_id = factory.SelfAttribute(attribute_name="role.id")
    user_id = factory.SelfAttribute(attribute_name="user.id")

    role = factory.SubFactory(factory=RoleFactory)
    user = factory.SubFactory(factory=UserFactory)

    class Meta:
        model = RoleUser
        exclude = ("role", "user")
        sqlalchemy_get_or_create = ("role_id", "user_id")


class GroupUserFactory(BaseModelFactory):
    group_id = factory.SelfAttribute(attribute_name="group.id")
    user_id = factory.SelfAttribute(attribute_name="user.id")

    group = factory.SubFactory(factory=GroupFactory)
    user = factory.SubFactory(factory=UserFactory)

    class Meta:
        model = GroupUser
        exclude = ("group", "user")
        sqlalchemy_get_or_create = ("group_id", "user_id")
