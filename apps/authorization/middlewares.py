from fastapi import status
from starlette.authentication import AuthCredentials, AuthenticationBackend, AuthenticationError, BaseUser
from starlette.requests import HTTPConnection

from apps.CORE.db import async_session_factory
from apps.CORE.exceptions import BackendError
from apps.users.schemas import UserTokenPayloadSchema
from apps.users.services import users_service


class JWTTokenBackend(AuthenticationBackend):
    """Authorization Back-end that parse and retrieve user from authorization headers token."""

    def __init__(self, scheme_prefix: str = "Bearer"):
        self.scheme_prefix_lower = scheme_prefix.lower()

    def get_token_from_header(self, *, authorization: str) -> str:
        """Parse token and check schema from `Authorization` header value.

        Keyword Args:
            authorization(str): value of `Authorization` header.

        Returns:
            jwt_token(str): Parsed string value of JWT token.

        Raises:
            BackendException: In case of header parse error.
            BackendException: In case of invalid schema.
        """
        try:
            # parse schema and token
            scheme, jwt_token = authorization.split()
        except Exception as error:
            raise BackendError(
                message="Could not parse Authorization scheme and token.", code=status.HTTP_401_UNAUTHORIZED
            ) from error
        else:
            # check schema
            if scheme.lower() != self.scheme_prefix_lower:
                raise BackendError(
                    message=f"Authorization scheme {scheme} is not suppoerted.", code=status.HTTP_401_UNAUTHORIZED
                )
            return jwt_token

    async def authenticate(self, conn: HTTPConnection) -> tuple[AuthCredentials | None, BaseUser | None] | None:
        """Method for JWT authentication.

        1) Reads `Authorization` header.
        2) Parse check schema and parse JWT code.
        3) Validate JWT code and retrieve user's `id` from it.
        4) Try to get user from DB (should be active).
        5) Provide `request.auth` and `request.user` to HTTPConnection (Request).

        Args:
            conn (HTTPConnection): ASGI Request instance (Starlette or FastAPI).

        Returns:
            - (None): In case `Authorization` header is missing.
            - (tuple[AuthCredentials, None]): In case of user not found or user not active.
            - (tuple[AuthCredentials, User]): In case of user found and active.

        Raises:
            AuthenticationError: In case invalid JWT token value.
        """
        if "Authorization" not in conn.headers:
            return None

        auth_header = conn.headers["Authorization"]
        token = self.get_token_from_header(authorization=auth_header)

        try:
            payload_schema: UserTokenPayloadSchema = conn.app.state.tokens_manager.read_code(
                code=token, convert_to=UserTokenPayloadSchema
            )
            async with async_session_factory() as session:
                user = await users_service.get_with_authorization(session=session, id=payload_schema.id)

            if user is None:
                return AuthCredentials(), None
        except BackendError as error:
            raise AuthenticationError(error.message) from error

        # request.auth, request.user
        return AuthCredentials(scopes=["authenticated"]), user
