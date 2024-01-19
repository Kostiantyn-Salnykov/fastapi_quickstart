from pydantic import AwareDatetime, Field

from apps.authorization.schemas.responses import GroupResponse, PermissionResponse, RoleResponse
from apps.CORE.custom_types import Email, StrUUID
from apps.CORE.schemas.responses import BaseResponseSchema
from apps.users.enums import UsersStatuses
from apps.users.schemas.requests import TokenRefreshSchema


class UserResponseSchema(BaseResponseSchema):
    id: StrUUID
    first_name: str = Field(title="First name", max_length=128, alias="firstName")
    last_name: str = Field(title="Last name", max_length=128, alias="lastName")
    email: Email = Field(title="Email")
    status: UsersStatuses = Field(default=UsersStatuses.UNCONFIRMED, title="User status", alias="status")
    created_at: AwareDatetime = Field(title="Created at", alias="createdAt")
    updated_at: AwareDatetime = Field(title="Updated at", alias="updatedAt")
    groups: list[GroupResponse] = Field(default_factory=list)
    roles: list[RoleResponse] = Field(default_factory=list)
    permissions: list[PermissionResponse] = Field(default_factory=list)


class LoginOutSchema(TokenRefreshSchema):
    access_token: str = Field(title="Access token", alias="accessToken")
