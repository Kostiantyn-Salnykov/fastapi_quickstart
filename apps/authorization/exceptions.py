import typing

from fastapi import status as http_status

from apps.CORE.enums import JSENDStatus
from apps.CORE.exceptions import BackendException


class PermissionException(BackendException):
    def __init__(
        self,
        *,
        status: JSENDStatus = JSENDStatus.FAIL,
        data: typing.Union[None, int, str, list[typing.Any], dict[str, typing.Any]] = None,
        message: str = "User has no access to perform this action.",
        code: int = http_status.HTTP_403_FORBIDDEN,
    ):
        super().__init__(status=status, data=data, message=message, code=code)
