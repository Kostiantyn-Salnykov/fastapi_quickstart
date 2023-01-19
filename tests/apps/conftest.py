import typing
import uuid

from fastapi import status
from httpx import Response

from apps.CORE.enums import JSENDStatus


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
    except ValueError:
        assert False, "Not uuid"
