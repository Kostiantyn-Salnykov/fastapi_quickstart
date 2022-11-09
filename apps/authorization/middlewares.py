from fastapi import status
from starlette.authentication import AuthCredentials, AuthenticationBackend, AuthenticationError, BaseUser
from starlette.requests import HTTPConnection

from apps.CORE.db import async_session_factory
from apps.CORE.exceptions import BackendException
from apps.users.schemas import UserTokenPayloadSchema
from apps.users.services import users_service


class JWTTokenBackend(AuthenticationBackend):
    def __init__(self, scheme_prefix: str = "Bearer"):
        self.scheme_prefix_lower = scheme_prefix.lower()

    def get_token_from_header(self, authorization: str) -> str:
        try:
            scheme, jwt_token = authorization.split()
        except Exception:
            raise BackendException(
                message="Could not parse Authorization scheme and token.", code=status.HTTP_401_UNAUTHORIZED
            )
        else:
            if scheme.lower() != self.scheme_prefix_lower:
                raise BackendException(
                    message=f"Authorization scheme {scheme} is not suppoerted.", code=status.HTTP_401_UNAUTHORIZED
                )
            return jwt_token

    async def authenticate(self, conn: HTTPConnection) -> tuple[AuthCredentials | None, BaseUser | None] | None:
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
        except BackendException as error:
            raise AuthenticationError(error.message)

        # request.auth, request.user
        return AuthCredentials(scopes=["authenticated"]), user
