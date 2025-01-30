from core.custom_types import Email, StrUUID
from core.schemas.fields import Fields
from core.schemas.responses import BaseResponseSchema
from pydantic import Field

from domain.users.enums import UserStatuses
from domain.users.schemas.requests import TokenRefreshSchema


class UserResponseSchema(BaseResponseSchema):
    id: StrUUID
    first_name: Fields.first_name
    last_name: Fields.last_name
    email: Email
    status: UserStatuses = Field(default=UserStatuses.UNCONFIRMED, title="User status", alias="status")
    created_at: Fields.created_at
    updated_at: Fields.updated_at
    # groups: list[GroupResponse] = Field(default_factory=list)
    # roles: list[RoleResponse] = Field(default_factory=list)
    # permissions: list[PermissionResponse] = Field(default_factory=list)


class LoginOutSchema(TokenRefreshSchema):
    access_token: str = Field(title="Access token", alias="accessToken")
