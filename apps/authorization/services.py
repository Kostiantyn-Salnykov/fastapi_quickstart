from apps.CORE.models import Group, GroupRole, Permission, Role, RolePermission
from apps.CORE.repositories import BaseCoreRepository
from loggers import get_logger

logger = get_logger(name=__name__)


class GroupsService(BaseCoreRepository):
    ...


class GroupRoleService(BaseCoreRepository):
    ...


class RolesService(BaseCoreRepository):
    ...


class RolePermissionService(BaseCoreRepository):
    ...


class PermissionsService(BaseCoreRepository):
    ...


groups_service = GroupsService(model=Group)
group_role_service = GroupRoleService(model=GroupRole)
roles_service = RolesService(model=Role)
role_permission_service = RolePermissionService(model=RolePermission)
permissions_service = PermissionsService(model=Permission)
