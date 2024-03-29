from fastapi import status as http_status

from apps.CORE.custom_types import DictStrOfAny, ListOfAny
from apps.CORE.enums import JSENDStatus
from apps.CORE.exceptions import BackendError


class BackendPermissionError(BackendError):
    """Class to raise on permission error for API."""

    def __init__(
        self,
        *,
        status: JSENDStatus = JSENDStatus.FAIL,
        data: None | int | str | ListOfAny | DictStrOfAny = None,
        message: str = "User has no access to perform this action.",
        code: int = http_status.HTTP_403_FORBIDDEN,
    ) -> None:
        super().__init__(status=status, data=data, message=message, code=code)
