from fastapi import Depends, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.security.utils import get_authorization_scheme_param

from apps.authorization.enums import PermissionActions
from apps.authorization.exceptions import PermissionError
from apps.CORE.exceptions import BackendError
from apps.CORE.types import ModelType


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
        if not request.user or not request.user.is_authenticated:
            raise BackendError(message="Not authenticated.", code=status.HTTP_401_UNAUTHORIZED)
        return request


class HasPermissions:
    def __init__(self, permissions: list[tuple[ModelType, PermissionActions]]):
        """Initializer for required Permissions and Actions that must be in user's Permissions set."""
        self._permissions: set[tuple[str, str]] = self.construct_permissions_set(permissions=permissions)

    async def __call__(self, request: Request = Depends(IsAuthenticated())) -> Request:
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

    async def __call__(self, request: Request = Depends(IsAuthenticated())) -> Request:
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
