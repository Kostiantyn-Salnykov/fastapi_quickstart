from core.annotations import DatetimeOrNone, StrOrNone
from core.custom_types import Email, StrUUID
from core.managers.schemas import TokenPayloadSchema
from core.schemas.requests import BaseRequestSchema
from pydantic import Field

from domain.users.enums import UserStatuses


class UserToDBBaseSchema(BaseRequestSchema):
    id: StrUUID | None = None
    first_name: StrOrNone = Field(default=None, title="First name", max_length=128, alias="firstName")
    last_name: StrOrNone = Field(default=None, title="Last name", max_length=128, alias="lastName")
    email: Email | None = Field(default=None, title="Email")
    status: UserStatuses = Field(default=UserStatuses.UNCONFIRMED, title="User status", alias="status")
    created_at: DatetimeOrNone = Field(default=None, title="Created at", alias="createdAt")
    updated_at: DatetimeOrNone = Field(default=None, title="Updated at", alias="updatedAt")
    password_hash: StrOrNone = Field(default=None, max_length=1024)


class UserCreateToDBSchema(UserToDBBaseSchema):
    password_hash: str = Field(max_length=1024)


class UserTokenPayloadSchema(TokenPayloadSchema):
    id: StrUUID = Field(default=...)
    token_id: StrOrNone = Field(default=None)
