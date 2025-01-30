import typing

from core.annotations import StrOrNone
from core.custom_types import Email
from core.schemas.requests import BaseRequestSchema
from pydantic import Field, model_validator


class UserCreateSchema(BaseRequestSchema):
    first_name: str = Field(default=..., title="First name", max_length=128, alias="firstName")
    last_name: str = Field(default=..., title="Last name", max_length=128, alias="lastName")
    email: Email = Field(default=..., title="Email")
    password: str = Field(default=..., title="Password", min_length=8, max_length=255)


class UserUpdateSchema(BaseRequestSchema):
    first_name: StrOrNone = Field(default=None, title="First name", max_length=128, alias="firstName")
    last_name: StrOrNone = Field(default=None, title="Last name", max_length=128, alias="lastName")
    old_password: StrOrNone = Field(default=None, min_length=8, max_length=255, alias="oldPassword")
    new_password: StrOrNone = Field(default=None, min_length=8, max_length=255, alias="newPassword")

    @model_validator(mode="after")
    def validate_new_password(self) -> typing.Self:
        """Validate `new_password` field.

        Raises:
            ValueError: In case when user didn't provide `old_password` but provide `new_password`
        """
        if self.new_password is not None and self.old_password is None:
            msg = "You should provide old password to set up new one."
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def validate_old_password(self) -> typing.Self:
        """Validate `old_password` field.

        Raises:
            ValueError: In case when user didn't provide `new_password` but provide `old_password`
        """
        if self.old_password is not None and self.new_password is None:
            msg = "It makes no sense to send the old password without sending the new one."
            raise ValueError(msg)
        return self


class TokenRefreshSchema(BaseRequestSchema):
    refresh_token: str = Field(title="Refresh token", alias="refreshToken")


class LoginSchema(BaseRequestSchema):
    email: Email = Field(default=..., title="Email")
    password: str = Field(default=..., min_length=8, max_length=255)
