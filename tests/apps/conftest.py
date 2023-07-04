import typing
import uuid

from fastapi import status
from httpx import Response

from apps.CORE.enums import JSENDStatus
from apps.CORE.managers import TokensManager
from apps.CORE.models import User
from apps.users.enums import UsersStatuses
from settings import Settings
from tests.apps.CORE.factories import UserFactory


def assert_jsend_response(
    response: Response, http_code: status, status: JSENDStatus, message: str, code: int, data: typing.Any = ...
) -> None:
    response_json = response.json()
    assert response.status_code == http_code
    assert response_json["status"] == status
    assert response_json["message"] == message
    assert response_json["code"] == code
    if data is not ...:
        assert response_json["data"] == data


def assert_is_uuid(val: str) -> None:
    try:
        uuid.UUID(val)
        assert True, "Valid UUID"
    except ValueError as error:
        raise AssertionError("Not uuid") from error


class UsersHelper:
    def __init__(
        self, user: User = None, token: str = None, user_kwargs: dict = None, token_kwargs: dict = None
    ) -> None:
        self._user = user
        self._token = token
        self._user_kwargs = user_kwargs or {"status": UsersStatuses.CONFIRMED}
        self._token_kwargs = token_kwargs or {}
        self._tokens_manager = TokensManager(secret_key=Settings.TOKENS_SECRET_KEY)

    @property
    def token(self) -> str:
        if self._token:
            return self._token
        else:
            return self._generate_token()

    @property
    def user(self) -> User:
        if self._user:
            return self._user
        else:
            return self._generate_user()

    def _generate_token(self) -> str:
        self._token = self._tokens_manager.create_code(data={"id": str(self.user.id), "token_id": 1})
        return self._token

    def _generate_user(self) -> User:
        user = UserFactory(**self._user_kwargs)
        self._user = user
        return self._user

    def get_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
