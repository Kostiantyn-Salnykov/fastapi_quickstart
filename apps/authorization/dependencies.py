import casbin
from casbin_redis_adapter.adapter import Adapter
from fastapi import Depends, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.security.utils import get_authorization_scheme_param

from apps.authorization.enums import PermissionActions
from apps.authorization.exceptions import PermissionError
from apps.CORE.custom_types import ModelType
from apps.CORE.exceptions import BackendError
from loggers import get_logger
from settings import Settings

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
                    message="Could not parse Authorization scheme and token.", code=status.HTTP_401_UNAUTHORIZED
                )
            else:
                return None
        if scheme.lower() != "bearer":
            if self.auto_error:
                raise BackendError(
                    message=f"Authorization scheme {scheme} is not suppoerted.", code=status.HTTP_401_UNAUTHORIZED
                )
            else:
                return None
        return HTTPAuthorizationCredentials(scheme=scheme, credentials=credentials)


bearer_auth = NewHTTPBearer(bearerFormat="Bearer", auto_error=False)


class IsAuthenticated:
    def __init__(self) -> None:
        ...

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
    def __init__(self, permissions: list[tuple[ModelType, PermissionActions]]):
        """Initializer for required Permissions and Actions that must be in user's Permissions set."""
        self._permissions: set[tuple[str, str]] = self.construct_permissions_set(permissions=permissions)

    async def __call__(self, request: Request = IsAuthenticated()) -> Request:
        if not request.state.authorization_manager:
            raise NotImplementedError(
                "You should set up and AuthorizationManager to use this dependency,"
                "app.state.authorization_manager = AuthorizationManager(engine=<SQLAlchemy Engine>)"
            )
        user_permissions_set = request.state.authorization_manager.get_permissions_set_from_user(user=request.user)
        # if no permissions set in user's permissions set
        if not self._permissions.issubset(user_permissions_set):
            # check by superuser actions.
            transformed_superuser_actions = self.actions_check_on_superuser(
                actions=self.get_all_actions_from_permissions(permissions=self._permissions)
            )
            if not transformed_superuser_actions <= user_permissions_set:
                # user has not such PermissionAction in his superuser permissions.
                raise PermissionError()

        return request

    @classmethod
    def construct_permissions_set(cls, permissions: list[tuple[ModelType, PermissionActions]]) -> set[tuple[str, str]]:
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
            raise PermissionError()
        return request


class HasGroup:
    def __init__(self, name: str) -> None:
        """Initializer for required Group that must be in user's Groups."""
        self._group = name.lower()

    async def __call__(self, request: Request = Depends(IsAuthenticated())) -> Request:
        if self._group not in (group.name.lower() for group in request.user.groups):
            raise PermissionError()
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

    async def __call__(self, request: Request = IsAuthenticated()) -> Request:
        logger.debug(msg=f"{self.__class__.__name__} | __call__ called.")

        who, obj, action = self.parse_request(request=request)
        logger.warning(msg=f"{who=}, {obj=}, {action=}")

        adapter = Adapter(
            host=Settings.REDIS_HOST,
            port=Settings.REDIS_PORT,
            db=Settings.REDIS_DB,
            username=Settings.REDIS_USER,
            password=Settings.REDIS_PASSWORD,
            key="AUTHORIZATION",
        )

        model = casbin.Model()
        model.add_def("r", "r", "who, object, action")  # Request `r` structure
        model.add_def("r", "r2", "who, object, action, expr")  # Request `r2` structure
        model.add_def("p", "p", "who, object, action")  # Policy `p` structure
        model.add_def("p", "p2", "who, object, action, expr")  # Policy `p2` structure
        model.add_def("g", "g", "_, _")  # Role to Role / Action mapping
        model.add_def("g", "g2", "_, _")  # Subscription Resource to group mapping
        # model.add_def("e", "e", "some(where (p.eft == allow))")  # Simplified version
        model.add_def("e", "e", "some(where (p.eft == allow)) && !some(where (p.eft == deny))")
        model.add_def("e", "e2", "some(where (p2.eft == allow)) && !some(where (p2.eft == deny))")
        func_name = "keyMatch5"  # - function to handle `{}` and `*` in `object.`
        # `||` -> OR, `&&` -> AND
        # `g` - function to handle roles / groups logic on `who`
        or_superusers_check = '|| "Superuser" in r2.expr.roles || "Superusers" in r2.expr.groups'
        model.add_def(
            "m", "m", f"g(r.who, p.who) && {func_name}(r.object, p.object) && r.action == p.action"
        )  # Matcher `m` structure
        model.add_def(
            "m",
            "m2",
            f"(eval(p2.expr) && g(r2.who, p2.who) && {func_name}(r2.object, p2.object) && r2.action == p2.action) "
            f"{or_superusers_check}",
        )  # Matcher `m2` structure

        # cur_dir = pathlib.Path(__file__).resolve().parent
        # adapter = casbin.FileAdapter(file_path=f'{cur_dir / "policy.csv"}')
        # model_path = f'{cur_dir / "model.conf"}'
        # enforcer = casbin.Enforcer(model=model_path, adapter=adapter)
        enforcer = casbin.Enforcer(model=model, adapter=adapter)

        owner_id = "064f9fdf-1ab1-7bed-8000-69b5810d275f"
        superuser = "<USER_ID>"
        data_1 = "/data/{id}/*"
        super_data = "/superusers/{id}/*"

        enforcer.add_named_policy("p", owner_id, "abac_data", "read")
        enforcer.add_named_policy("p", owner_id, data_1, "read")
        enforcer.add_named_policy("p2", owner_id, data_1, "read", f"r2.expr.owner_id == '{owner_id}'")

        enforcer.add_named_grouping_policy("g", owner_id, "Admins")  # User assigned to `Admins` role
        enforcer.add_named_grouping_policy("g", "Superusers", "Admins")  # `Superusers` role contains `Admins` in it.

        enforcer.add_named_policy("p", "Admins", data_1, "write")  # `Admins` can write /data/{id}/<ANY>
        enforcer.add_named_policy(
            "p", "Superusers", super_data, "write"
        )  # `Superusers` can write /superusers/{id}/<ANY>

        # Superuser check
        enforcer.add_named_grouping_policy("g", superuser, "Superusers")

        # Get implicit roles for users (need to load hierarchy)
        # logger.info(enforcer.get_implicit_roles_for_user(name=owner_id))
        # logger.info(enforcer.get_implicit_roles_for_user(name=superuser))
        # logger.info(enforcer.get_implicit_permissions_for_user(user=owner_id))
        # logger.info(enforcer.get_implicit_permissions_for_user(user=superuser))

        # enforcer.save_policy()  # Needs for FileAdapter

        requests = [
            [owner_id, "abac_data", "read"],  # By object
            [owner_id, "/data/1/", "read", {"groups": ["Superusers"], "roles": [], "owner_id": None}],  # By groups
            [owner_id, "/data/1/", "read", {"groups": [], "roles": ["Superuser"], "owner_id": None}],  # By roles
            [owner_id, "/data/1/", "read", {"groups": [], "roles": [], "owner_id": owner_id}],  # By owner_id
            [owner_id, "/data/1/", "read"],  # By simple
            [owner_id, "/data/1/", "write"],  # By role hierarchy
            [superuser, "/superusers/1/", "write"],  # By role hierarchy (Should be accessed!!!)
            [superuser, "/data/1/", "write"],  # By role hierarchy (Should be accessed!!!)
            [owner_id, "/superusers/1/", "write"],  # By role hierarchy (Should be declined!!!)
        ]

        for req in requests:
            if len(req) == 4:
                ctx = enforcer.new_enforce_context(suffix="2")
                if enforcer.enforce(ctx, *req):
                    logger.info(msg=f"{req}, ENFORCED r2!")
                else:
                    logger.warning(msg=f"{req}, NOT ENFORCE r2!")
            else:
                if enforcer.enforce(*req):
                    logger.info(msg=f"{req}, ENFORCED r!")
                else:
                    logger.warning(msg=f"{req}, NOT ENFORCE r!")

        return request
