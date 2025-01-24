import casbin
from core.annotations import ModelInstance
from core.custom_logging import get_logger
from core.exceptions import BackendError
from fastapi import Depends, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.security.utils import get_authorization_scheme_param

from src.api.authorization.enums import PermissionActions
from src.api.authorization.exceptions import BackendPermissionError

logger = get_logger(name=__name__)


class NewHTTPBearer(HTTPBearer):
    """HTTPBearer with updated errors."""

    async def __call__(self, request: Request) -> HTTPAuthorizationCredentials | None:
        """Parse authorization credentials. Used by FastAPI router's dependencies.

        Args:
            request (Request): FastAPI request instance.

        Returns:
            HTTPAuthorizationCredentials: In case of successfully parsed schema and token

        Raises:
            BackendException: In case of header parse error.
            BackendException: In case of invalid schema.
        """
        authorization: str = request.headers.get("Authorization")
        scheme, credentials = get_authorization_scheme_param(authorization)
        if not (authorization and scheme and credentials):
            if self.auto_error:
                raise BackendError(
                    message="Could not parse Authorization scheme and token.",
                    code=status.HTTP_401_UNAUTHORIZED,
                )
            return None
        if scheme.lower() != "bearer":
            if self.auto_error:
                raise BackendError(
                    message=f"Authorization scheme {scheme} is not suppoerted.",
                    code=status.HTTP_401_UNAUTHORIZED,
                )
            return None
        return HTTPAuthorizationCredentials(scheme=scheme, credentials=credentials)


bearer_auth = NewHTTPBearer(bearerFormat="Bearer", auto_error=False)


class IsAuthenticated:
    def __init__(self) -> None: ...

    def __call__(self, request: Request) -> Request:
        """Make this `Depends` class callable.

        Checks that user is authenticated.

        Raises:
            BackendException: In case of not authenticated

        Returns:
            request(Request): Proxies FastAPI Request.
        """
        logger.debug(msg=f"{self.__class__.__name__} | __call__ called.")
        if not request.user or not request.user.is_authenticated:
            raise BackendError(message="Not authenticated.", code=status.HTTP_401_UNAUTHORIZED)
        return request


class HasPermissions:
    def __init__(self, permissions: list[tuple[ModelInstance, PermissionActions]]) -> None:
        """Initializer for required Permissions and Actions that must be in user's Permissions set."""
        self._permissions: set[tuple[str, str]] = self.construct_permissions_set(permissions=permissions)

    async def __call__(self, request: Request = IsAuthenticated()) -> Request:
        if not request.state.authorization_manager:
            msg = (
                "You should set up and AuthorizationManager to use this dependency,app.state.authorization_manager "
                "= AuthorizationManager(engine=<SQLAlchemy Engine>)"
            )
            raise NotImplementedError(msg)
        user_permissions_set = request.state.authorization_manager.get_permissions_set_from_user(user=request.user)
        # if no permissions set in user's permissions set
        if not self._permissions.issubset(user_permissions_set):
            # check by superuser actions.
            transformed_superuser_actions = self.actions_check_on_superuser(
                actions=self.get_all_actions_from_permissions(permissions=self._permissions),
            )
            if not transformed_superuser_actions <= user_permissions_set:
                # user has not such PermissionAction in his superuser permissions.
                raise BackendPermissionError()

        return request

    @classmethod
    def construct_permissions_set(
        cls,
        permissions: list[tuple[ModelInstance, PermissionActions]],
    ) -> set[tuple[str, str]]:
        result = set()
        for model, action in permissions:
            result.add((model.__tablename__, action.value))
        return result

    @classmethod
    def get_all_actions_from_permissions(cls, permissions: set[tuple[str, str | PermissionActions]]) -> set[str]:
        result = set()
        for _, action in permissions:
            result.add(action.value if isinstance(action, PermissionActions) else action)
        return result

    @classmethod
    def actions_check_on_superuser(cls, actions: set[str]) -> set[tuple[str, str]]:
        return {("__all__", action) for action in actions}


class HasRole:
    def __init__(self, name: str) -> None:
        """Initializer for required Role that must be in user's Roles."""
        self._role = name.lower()

    async def __call__(self, request: Request = IsAuthenticated()) -> Request:
        if self._role not in (role.name.lower() for role in request.user.roles):
            raise BackendPermissionError()
        return request


class HasGroup:
    def __init__(self, name: str) -> None:
        """Initializer for required Group that must be in user's Groups."""
        self._group = name.lower()

    async def __call__(self, request: Request = Depends(IsAuthenticated())) -> Request:
        if self._group not in (group.name.lower() for group in request.user.groups):
            raise BackendPermissionError()
        return request


class IsAuthorized:
    def __init__(self) -> None:
        # TODO: Make actual logic
        ...

    def parse_request(self, request: Request) -> tuple[str, str, str]:
        # TODO: Make actual logic
        who: str = request.user.identity
        obj: str = request.url.path
        action = request.method

        return who, obj, action

    async def __call__(self, request: Request = IsAuthenticated()) -> Request:  # noqa: PLR0915
        logger.debug(msg=f"{self.__class__.__name__} | __call__ called.")

        who, obj, action = self.parse_request(request=request)
        logger.warning(msg=f"{who=}, {obj=}, {action=}")

        import casbin_async_sqlalchemy_adapter
        from core.db.bases import async_engine

        adapter = casbin_async_sqlalchemy_adapter.Adapter(engine=async_engine, warning=False)

        import pathlib

        cur_dir = pathlib.Path(__file__).resolve().parent
        # adapter = casbin.FileAdapter(file_path=f'{cur_dir / "policy.csv"}')
        model_path = f"{cur_dir / 'model.conf'}"
        enforcer = casbin.AsyncEnforcer(model=model_path, adapter=adapter)

        user_id = "<USER>"
        admin_id = "<ADMIN>"
        superuser_id = "<SUPERUSER>"
        data_1 = "/data/{id}/*"
        super_data = "/superusers/{id}/*"
        users_group = "Users"
        admins_group = "Admins"
        superusers_group = "Superusers"

        await enforcer.add_named_policy("p", user_id, "abac_data", "read")
        await enforcer.add_named_policy("p", user_id, data_1, "read")
        await enforcer.add_named_policy("p2", user_id, data_1, "read", f'r2.expr.owner_id == "{user_id}"')
        await enforcer.add_named_policy("p", admins_group, data_1, "*")  # `Admins` can write /data/{id}/<ANY>
        await enforcer.add_named_policy(
            "p",
            superusers_group,
            super_data,
            "*",
        )  # `Superusers` can do anything /superusers/{id}/<ANY>

        await enforcer.add_named_grouping_policy("g", user_id, users_group)  # User assigned to `Users` role
        await enforcer.add_named_grouping_policy("g", admin_id, admins_group)  # Admin assigned to `Admins` role
        await enforcer.add_named_grouping_policy(
            "g",
            superuser_id,
            superusers_group,
        )  # Superuser assigned to `Superusers` role.

        await enforcer.add_named_grouping_policy("g", admins_group, users_group)  # `Admins` > `Users`.
        await enforcer.add_named_grouping_policy("g", superusers_group, admins_group)  # `Superusers` > `Admins`.

        # Get implicit roles for users (need to load hierarchy)
        logger.info(await enforcer.get_roles_for_user(name=user_id))
        logger.info(await enforcer.get_roles_for_user(name=admin_id))
        logger.info(await enforcer.get_roles_for_user(name=superuser_id))
        logger.info(await enforcer.get_implicit_roles_for_user(name=user_id))
        logger.info(await enforcer.get_implicit_roles_for_user(name=admin_id))
        logger.info(await enforcer.get_implicit_roles_for_user(name=superuser_id))
        logger.info(await enforcer.get_permissions_for_user(user=user_id))
        logger.info(await enforcer.get_permissions_for_user(user=admin_id))
        logger.info(await enforcer.get_permissions_for_user(user=superuser_id))
        logger.info(await enforcer.get_implicit_permissions_for_user(user=user_id))
        logger.info(await enforcer.get_implicit_permissions_for_user(user=admin_id))
        logger.info(await enforcer.get_implicit_permissions_for_user(user=superuser_id))

        # enforcer.save_policy()  # Needs for FileAdapter

        requests = [
            [user_id, "abac_data", "read"],  # By object
            [user_id, "/data/1/", "read", {"groups": [superusers_group], "roles": [], "owner_id": None}],  # By groups
            [user_id, "/data/1/", "read", {"groups": [], "roles": ["Superuser"], "owner_id": None}],  # By roles
            [user_id, "/data/1/", "read", {"groups": [], "roles": [], "owner_id": user_id}],  # By owner_id
            [user_id, "/data/1/", "read"],  # By simple
            [admin_id, "/data/1/", "write"],  # By admin policy
            [superuser_id, "/data/1/", "write"],  # By role hierarchy (Should be accessed!!!)
            [user_id, "/superusers/1/", "write"],  # By role hierarchy (Should be declined!!!)
            [admin_id, "/superusers/1/", "write"],  # By role hierarchy (Should be declined!!!)
            [superuser_id, "/superusers/1/", "write"],  # By role hierarchy (Should be accessed!!!)
        ]
        policy_params = 4

        for req in requests:
            if len(req) == policy_params:
                ctx = enforcer.new_enforce_context(suffix="2")
                if enforcer.enforce(ctx, *req):
                    logger.success(msg=f"{req} => ENFORCED r2!")
                else:
                    logger.warning(msg=f"{req} => NOT ENFORCE r2!")
            else:  # noqa: PLR5501
                if enforcer.enforce(*req):
                    logger.success(msg=f"{req} => ENFORCED r!")
                else:
                    logger.warning(msg=f"{req} => NOT ENFORCE r!")

        return request
