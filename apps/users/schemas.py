import typing
import uuid

from pydantic import Field, root_validator

from apps.authorization.schemas.responses import GroupResponse, PermissionResponse, RoleResponse
from apps.CORE.schemas import TokenPayloadSchema
from apps.CORE.schemas.requests import BaseRequestSchema
from apps.CORE.schemas.responses import BaseResponseSchema
from apps.CORE.types import DatetimeOrNone, Email, StrOrNone, Timestamp
from apps.users.enums import UsersStatuses


class UserCreateSchema(BaseRequestSchema):
    first_name: str = Field(default=..., title="First name", max_length=128, alias="firstName", example="John")
    last_name: str = Field(default=..., title="Last name", max_length=128, alias="lastName", example="Doe")
    email: Email = Field(default=..., title="Email", example="kostiantyn.salnykov@gmail.com")
    password: str = Field(default=..., title="Password", min_length=8, max_length=255, example="!QAZxsw2")


class UserUpdateSchema(BaseRequestSchema):
    first_name: StrOrNone = Field(default=None, title="First name", max_length=128, alias="firstName", example="")
    last_name: StrOrNone = Field(default=None, title="Last name", max_length=128, alias="lastName", example="")
    old_password: StrOrNone = Field(default=None, min_length=8, max_length=255, example="!QAZxsw2", alias="oldPassword")
    new_password: StrOrNone = Field(default=None, min_length=8, max_length=255, example="!QAZxsw2", alias="newPassword")

    @root_validator()
    def validate_new_password(cls, values: dict[str, typing.Any]) -> dict[str, typing.Any]:
        """Validate `new_password` field.

        Raises:
            ValueError: In case when user didn't provide `old_password` but provide `new_password`
        """
        if values.get("new_password") is not None and values.get("old_password") is None:
            raise ValueError("You should provide old password to set up new one.")
        return values

    @root_validator()
    def validate_old_password(cls, values: dict[str, typing.Any]) -> dict[str, typing.Any]:
        """Validate `old_password` field.

        Raises:
            ValueError: In case when user didn't provide `new_password` but provide `old_password`
        """
        if values.get("old_password") is not None and values.get("new_password") is None:
            raise ValueError("It makes no sense to send the old password without sending the new one.")
        return values


class UserToDBBaseSchema(BaseRequestSchema):
    id: uuid.UUID | None
    first_name: StrOrNone = Field(default=None, title="First name", max_length=128, alias="firstName", example="John")
    last_name: StrOrNone = Field(default=None, title="Last name", max_length=128, alias="lastName", example="Doe")
    email: Email | None = Field(default=None, title="Email", example="kostiantyn.salnykov@gmail.com")
    status: UsersStatuses = Field(default=UsersStatuses.UNCONFIRMED, title="User status", alias="status")
    created_at: DatetimeOrNone = Field(default=None, title="Created at", alias="createdAt")
    updated_at: DatetimeOrNone = Field(default=None, title="Updated at", alias="updatedAt")
    password_hash: StrOrNone = Field(default=None, max_length=1024)


class UserCreateToDBSchema(UserToDBBaseSchema):
    password_hash: str = Field(max_length=1024)


class UserResponseSchema(BaseResponseSchema):
    id: uuid.UUID
    first_name: str = Field(title="First name", max_length=128, alias="firstName", example="John")
    last_name: str = Field(title="Last name", max_length=128, alias="lastName", example="Doe")
    email: Email = Field(title="Email", example="kostiantyn.salnykov@gmail.com")
    status: UsersStatuses = Field(default=UsersStatuses.UNCONFIRMED, title="User status", alias="status")
    created_at: Timestamp = Field(title="Created at", alias="createdAt")
    updated_at: Timestamp = Field(title="Updated at", alias="updatedAt")
    groups: list[GroupResponse] | None = Field(default_factory=list)
    roles: list[RoleResponse] | None = Field(default_factory=list)
    permissions: list[PermissionResponse] | None = Field(default_factory=list)


class TokenRefreshSchema(BaseRequestSchema):
    refresh_token: str = Field(title="Refresh token", alias="refreshToken")


class LoginOutSchema(TokenRefreshSchema):
    access_token: str = Field(title="Access token", alias="accessToken")


class UserTokenPayloadSchema(TokenPayloadSchema):
    id: uuid.UUID
    token_id: StrOrNone


class LoginSchema(BaseRequestSchema):
    email: Email = Field(default=..., title="Email", example="kostiantyn.salnykov@gmail.com")
    password: str = Field(default=..., min_length=8, max_length=255, example="!QAZxsw2")
