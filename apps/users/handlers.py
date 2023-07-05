import datetime
import hashlib
import uuid

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from apps.CORE.enums import TokenAudience
from apps.CORE.exceptions import BackendError
from apps.CORE.helpers import utc_now
from apps.CORE.managers import PasswordsManager
from apps.CORE.models import User
from apps.CORE.types import StrOrUUID
from apps.users.enums import UsersStatuses
from apps.users.schemas import (
    LoginOutSchema,
    LoginSchema,
    TokenRefreshSchema,
    UserCreateSchema,
    UserCreateToDBSchema,
    UserResponseSchema,
    UserToDBBaseSchema,
    UserTokenPayloadSchema,
    UserUpdateSchema,
)
from apps.users.services import users_service
from settings import Settings

__all__ = ("users_handler",)


class UsersHandler:
    def __init__(self) -> None:
        self.passwords_manager = PasswordsManager()

    async def create_user(
        self, *, request: Request, session: AsyncSession, data: UserCreateSchema
    ) -> UserResponseSchema:
        create_to_db = UserCreateToDBSchema(
            **data.dict(by_alias=True, exclude={"password"}),
            password_hash=self.passwords_manager.make_password(password=data.password),
        )
        user: User = await users_service.create(session=session, obj=create_to_db)
        return UserResponseSchema.from_orm(obj=user)

    async def update_user(
        self, *, request: Request, session: AsyncSession, data: UserUpdateSchema
    ) -> UserResponseSchema:
        values = data.dict(exclude_unset=True)
        if not values:
            raise BackendError(message="Nothing to update.")
        if data.old_password:
            if not self.passwords_manager.check_password(
                password=data.old_password, password_hash=request.user.password_hash
            ):
                raise BackendError(message="Invalid credentials.")
            values = data.dict(exclude_unset=True, exclude={"old_password", "new_password"})
            values |= {
                "password_hash": self.passwords_manager.make_password(password=data.new_password),
                "status": UsersStatuses.CONFIRMED.value,
            }
        user = await users_service.update(session=session, id=request.user.id, obj=UserToDBBaseSchema(**values))
        return UserResponseSchema.from_orm(user)

    @staticmethod
    def generate_tokens(*, request: Request, id: StrOrUUID) -> LoginOutSchema:
        user_id = str(id) if isinstance(id, uuid.UUID) else id
        now = utc_now()
        token_id = hashlib.blake2s(f"{user_id}_{now.isoformat()}".encode(encoding="utf-8")).hexdigest()  # noqa: UP012
        return LoginOutSchema(
            access_token=request.app.state.tokens_manager.create_code(
                data={"id": user_id, "token_id": token_id},
                aud=TokenAudience.ACCESS,
                nbf=now,
                iat=now,
                exp=now + datetime.timedelta(seconds=Settings.TOKENS_ACCESS_LIFETIME_SECONDS),
            ),
            refresh_token=request.app.state.tokens_manager.create_code(
                data={"id": user_id, "token_id": token_id},
                aud=TokenAudience.REFRESH,
                nbf=now,
                iat=now,
                exp=now + datetime.timedelta(seconds=Settings.TOKENS_REFRESH_LIFETIME_SECONDS),
            ),
        )

    async def login(self, *, request: Request, session: AsyncSession, data: LoginSchema) -> LoginOutSchema:
        """Retrieve user's credentials and provide (access & refresh | password change tokens).

        Args:
            request (Request): FastAPI Request instance.
            session (AsyncSession): SQLAlchemy AsyncSession instance.
            data (LoginSchema): user's credentials (email, password).

        Returns:
            LoginOutSchema: a pair of tokens (access & refresh) - success flow.

        Raises:
            BackendException: In case of invalid credentials, invalid user's status, or inactive user.
        """
        user: User | None = await users_service.get_by_email(session=session, email=data.email)
        if (
            user
            and users_handler.passwords_manager.check_password(password=data.password, password_hash=user.password_hash)
            and user.status == UsersStatuses.CONFIRMED.value
        ):
            return users_handler.generate_tokens(request=request, id=user.id)
        raise BackendError(message="Invalid credentials.")

    async def refresh(self, *, request: Request, session: AsyncSession, data: TokenRefreshSchema) -> LoginOutSchema:
        """Generate new tokens pair (access, refresh) from refresh token."""
        payload_schema: UserTokenPayloadSchema = request.app.state.tokens_manager.read_code(
            aud=TokenAudience.REFRESH, code=data.refresh_token, convert_to=UserTokenPayloadSchema
        )
        user: User | None = await users_service.read(session=session, id=payload_schema.id)
        if user and user.status in (UsersStatuses.CONFIRMED.value, UsersStatuses.FORCE_CHANGE_PASSWORD.value):
            return self.generate_tokens(request=request, id=user.id)
        raise BackendError(message="Inactive user.")


users_handler = UsersHandler()
