import datetime
import typing
import uuid

from pydantic import Field, root_validator

from apps.authorization.schemas import GroupOutSchema, PermissionOutSchema, RoleOutSchema
from apps.CORE.schemas import BaseInSchema, BaseOutSchema, TokenPayloadSchema
from apps.CORE.types import Email, Timestamp
from apps.users.enums import UsersStatuses


class UserCreateSchema(BaseInSchema):
    first_name: str = Field(default=..., title="First name", max_length=128, alias="firstName", example="John")
    last_name: str = Field(default=..., title="Last name", max_length=128, alias="lastName", example="Doe")
    email: Email = Field(default=..., title="Email", example="kostiantyn.salnykov@gmail.com")
    password: str = Field(default=..., title="Password", min_length=8, max_length=256, example="!QAZxsw2")


class UserUpdateSchema(BaseInSchema):
    first_name: str | None = Field(default=None, title="First name", max_length=128, alias="firstName", example="")
    last_name: str | None = Field(default=None, title="Last name", max_length=128, alias="lastName", example="")
    old_password: str | None = Field(
        default=None, min_length=8, max_length=256, example="!QAZxsw2", alias="oldPassword"
    )
    new_password: str | None = Field(
        default=None, min_length=8, max_length=256, example="!QAZxsw2", alias="newPassword"
    )

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


class UserToDBBaseSchema(BaseInSchema):
    id: uuid.UUID | None
    first_name: str | None = Field(default=None, title="First name", max_length=128, alias="firstName", example="John")
    last_name: str | None = Field(default=None, title="Last name", max_length=128, alias="lastName", example="Doe")
    email: Email | None = Field(default=None, title="Email", example="kostiantyn.salnykov@vilmate.com")
    status: UsersStatuses = Field(default=UsersStatuses.UNCONFIRMED, title="User status", alias="status")
    created_at: datetime.datetime | None = Field(default=None, title="Created at", alias="createdAt")
    updated_at: datetime.datetime | None = Field(default=None, title="Updated at", alias="updatedAt")
    password_hash: str | None = Field(default=None, max_length=1024)


class UserCreateToDBSchema(UserToDBBaseSchema):
    password_hash: str = Field(max_length=1024)


class UserOutSchema(BaseOutSchema):
    id: uuid.UUID
    first_name: str = Field(title="First name", max_length=128, alias="firstName", example="John")
    last_name: str = Field(title="Last name", max_length=128, alias="lastName", example="Doe")
    email: Email = Field(title="Email", example="kostiantyn.salnykov@gmail.com")
    status: UsersStatuses = Field(default=UsersStatuses.UNCONFIRMED, title="User status", alias="status")
    created_at: Timestamp = Field(title="Created at", alias="createdAt")
    updated_at: Timestamp = Field(title="Updated at", alias="updatedAt")
    groups: list[GroupOutSchema] | None = Field(default=[])
    roles: list[RoleOutSchema] | None = Field(default=[])
    permissions: list[PermissionOutSchema] | None = Field(default=[])


class TokenRefreshSchema(BaseInSchema):
    refresh_token: str = Field(title="Refresh token", alias="refreshToken")


class LoginOutSchema(TokenRefreshSchema):
    access_token: str = Field(title="Access token", alias="accessToken")


class UserTokenPayloadSchema(TokenPayloadSchema):
    id: uuid.UUID
    token_id: str


class LoginSchema(BaseInSchema):
    email: Email = Field(default=..., title="Email", example="kostiantyn.salnykov@gmail.com")
    password: str = Field(default=..., min_length=8, max_length=256, example="!QAZxsw2")
