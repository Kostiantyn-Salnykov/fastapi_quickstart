import typing

from pydantic import Field, model_validator

from apps.CORE.custom_types import Email, StrOrNone
from apps.CORE.schemas.requests import BaseRequestSchema


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

    @model_validator(mode="after")
    def validate_new_password(self) -> typing.Self:
        """Validate `new_password` field.

        Raises:
            ValueError: In case when user didn't provide `old_password` but provide `new_password`
        """
        if self.new_password is not None and self.old_password is None:
            raise ValueError("You should provide old password to set up new one.")
        return self

    @model_validator(mode="after")
    def validate_old_password(self) -> typing.Self:
        """Validate `old_password` field.

        Raises:
            ValueError: In case when user didn't provide `new_password` but provide `old_password`
        """
        if self.old_password is not None and self.new_password is None:
            raise ValueError("It makes no sense to send the old password without sending the new one.")
        return self


class TokenRefreshSchema(BaseRequestSchema):
    refresh_token: str = Field(title="Refresh token", alias="refreshToken")


class LoginSchema(BaseRequestSchema):
    email: Email = Field(default=..., title="Email", example="kostiantyn.salnykov@gmail.com")
    password: str = Field(default=..., min_length=8, max_length=255, example="!QAZxsw2")
