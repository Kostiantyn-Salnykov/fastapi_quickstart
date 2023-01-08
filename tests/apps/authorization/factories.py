import random
import typing

import factory

from apps.authorization.enums import PermissionActions
from apps.authorization.managers import AuthorizationManager
from apps.authorization.models import (
    Group,
    GroupRole,
    GroupUser,
    Permission,
    PermissionUser,
    Role,
    RolePermission,
    RoleUser,
)
from tests.bases import BaseModelFactory


class PermissionFactory(BaseModelFactory):
    object_name = factory.Faker("pystr", max_chars=128)
    action = factory.Faker("word", ext_word_list=list(PermissionActions))

    class Meta:
        model = Permission
        sqlalchemy_get_or_create = ("object_name", "action")

    @classmethod
    def _create(
        cls, model_class: typing.Type[Permission], *args: tuple[typing.Any], **kwargs: dict[str, typing.Any]
    ) -> Permission:
        session = cls._meta.sqlalchemy_session
        am = AuthorizationManager(engine=session.bind)
        permissions: list[str] = [table for table in am._get_table_names()]
        kwargs["object_name"] = random.choice(permissions)
        return super(BaseModelFactory, cls)._create(model_class=model_class, *args, **kwargs)


class RolePermissionFactory(BaseModelFactory):
    role_id = factory.SelfAttribute(attribute_name="role.id")
    permission_id = factory.SelfAttribute(attribute_name="permission.id")

    role = factory.SubFactory(factory="tests.apps.authorization.factories.RoleFactory")
    permission = factory.SubFactory(factory=PermissionFactory)

    class Meta:
        model = RolePermission
        exclude = ("role", "permission")
        sqlalchemy_get_or_create = ("role_id", "permission_id")


class RoleFactory(BaseModelFactory):
    name = factory.Faker("pystr", max_chars=128)
    permissions = factory.RelatedFactoryList(factory=RolePermissionFactory, factory_related_name="role", size=2)

    class Meta:
        model = Role
        sqlalchemy_get_or_create = ("name",)


class GroupRoleFactory(BaseModelFactory):
    group_id = factory.SelfAttribute(attribute_name="group.id")
    role_id = factory.SelfAttribute(attribute_name="role.id")

    group = factory.SubFactory(factory="tests.apps.authorization.factories.GroupFactory")
    role = factory.SubFactory(factory=RoleFactory)

    class Meta:
        model = GroupRole
        exclude = ("group", "role")
        sqlalchemy_get_or_create = ("group_id", "role_id")


class GroupFactory(BaseModelFactory):
    name = factory.Faker("pystr", max_chars=256)
    roles = factory.RelatedFactoryList(factory=GroupRoleFactory, factory_related_name="group", size=1)

    class Meta:
        model = Group
        sqlalchemy_get_or_create = ("name",)


class PermissionUserFactory(BaseModelFactory):
    permission_id = factory.SelfAttribute(attribute_name="permission.id")
    user_id = factory.SelfAttribute(attribute_name="user.id")

    permission = factory.SubFactory(factory=PermissionFactory)
    user = factory.SubFactory(factory="tests.apps.users.factories.UserFactory")

    class Meta:
        model = PermissionUser
        exclude = ("permission", "user")
        sqlalchemy_get_or_create = ("permission_id", "user_id")


class RoleUserFactory(BaseModelFactory):
    role_id = factory.SelfAttribute(attribute_name="role.id")
    user_id = factory.SelfAttribute(attribute_name="user.id")

    role = factory.SubFactory(factory=RoleFactory)
    user = factory.SubFactory(factory="tests.apps.users.factories.UserFactory")

    class Meta:
        model = RoleUser
        exclude = ("role", "user")
        sqlalchemy_get_or_create = ("role_id", "user_id")


class GroupUserFactory(BaseModelFactory):
    group_id = factory.SelfAttribute(attribute_name="group.id")
    user_id = factory.SelfAttribute(attribute_name="user.id")

    group = factory.SubFactory(factory=GroupFactory)
    user = factory.SubFactory(factory="tests.apps.users.factories.UserFactory")

    class Meta:
        model = GroupUser
        exclude = ("group", "user")
        sqlalchemy_get_or_create = ("group_id", "user_id")
