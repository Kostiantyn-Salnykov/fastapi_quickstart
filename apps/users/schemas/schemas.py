from pydantic import Field

from apps.CORE.custom_types import DatetimeOrNone, Email, StrOrNone, StrUUID
from apps.CORE.schemas import TokenPayloadSchema
from apps.CORE.schemas.requests import BaseRequestSchema
from apps.users.enums import UsersStatuses


class UserToDBBaseSchema(BaseRequestSchema):
    id: StrUUID | None = None
    first_name: StrOrNone = Field(default=None, title="First name", max_length=128, alias="firstName")
    last_name: StrOrNone = Field(default=None, title="Last name", max_length=128, alias="lastName")
    email: Email | None = Field(default=None, title="Email")
    status: UsersStatuses = Field(default=UsersStatuses.UNCONFIRMED, title="User status", alias="status")
    created_at: DatetimeOrNone = Field(default=None, title="Created at", alias="createdAt")
    updated_at: DatetimeOrNone = Field(default=None, title="Updated at", alias="updatedAt")
    password_hash: StrOrNone = Field(default=None, max_length=1024)


class UserCreateToDBSchema(UserToDBBaseSchema):
    password_hash: str = Field(max_length=1024)


class UserTokenPayloadSchema(TokenPayloadSchema):
    id: StrUUID = Field(default=...)
    token_id: StrOrNone = Field(default=None)
