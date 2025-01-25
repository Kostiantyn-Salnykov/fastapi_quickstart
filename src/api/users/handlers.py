__all__ = ("users_handler",)
import datetime
import hashlib
import uuid
from typing import TYPE_CHECKING

from core.annotations import StrOrUUID
from core.enums import TokenAudience
from core.exceptions import BackendError
from core.helpers import utc_now
from core.managers.passwords import PasswordsManager
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.users.enums import UserStatuses
from src.api.users.schemas import UserCreateToDBSchema, UserToDBBaseSchema, UserTokenPayloadSchema
from src.api.users.schemas.requests import LoginSchema, TokenRefreshSchema, UserCreateSchema, UserUpdateSchema
from src.api.users.schemas.responses import LoginOutSchema, UserResponseSchema
from src.api.users.services import users_service
from src.settings import Settings

if TYPE_CHECKING:
    from core.db.tables import User


class UsersHandler:
    def __init__(self) -> None:
        self.passwords_manager = PasswordsManager()

    async def create_user(
        self,
        *,
        request: Request,
        session: AsyncSession,
        data: UserCreateSchema,
    ) -> UserResponseSchema:
        create_to_db = UserCreateToDBSchema(
            **data.model_dump(by_alias=True, exclude={"password"}),
            password_hash=self.passwords_manager.make_password(password=data.password),
        )
        user: User = await users_service.create(session=session, obj=create_to_db)
        return UserResponseSchema.from_model(obj=user)

    async def update_user(
        self,
        *,
        request: Request,
        session: AsyncSession,
        data: UserUpdateSchema,
    ) -> UserResponseSchema:
        values = data.model_dump(exclude_unset=True)
        if not values:
            raise BackendError(message="Nothing to update.")
        if data.old_password:
            if not self.passwords_manager.check_password(
                password=data.old_password,
                password_hash=request.user.password_hash,
            ):
                raise BackendError(message="Invalid credentials.")
            values = data.model_dump(exclude_unset=True, exclude={"old_password", "new_password"})
            values |= {
                "password_hash": self.passwords_manager.make_password(password=data.new_password),
                "status": UserStatuses.CONFIRMED.value,
            }
        user = await users_service.update(session=session, id=request.user.id, obj=UserToDBBaseSchema(**values))
        return UserResponseSchema.from_model(obj=user)

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
            and user.status == UserStatuses.CONFIRMED.value
        ):
            return users_handler.generate_tokens(request=request, id=user.id)
        raise BackendError(message="Invalid credentials.")

    async def refresh(self, *, request: Request, session: AsyncSession, data: TokenRefreshSchema) -> LoginOutSchema:
        """Generate the new tokens pair (access, refresh) from provided refresh token."""
        payload_schema: UserTokenPayloadSchema = request.app.state.tokens_manager.read_code(
            aud=TokenAudience.REFRESH,
            code=data.refresh_token,
            convert_to=UserTokenPayloadSchema,
        )
        user: User | None = await users_service.retrieve_by_id(session=session, id=payload_schema.id)
        if user and user.status in (UserStatuses.CONFIRMED.value, UserStatuses.FORCE_CHANGE_PASSWORD.value):
            return self.generate_tokens(request=request, id=user.id)
        raise BackendError(message="Inactive user.")


users_handler = UsersHandler()
