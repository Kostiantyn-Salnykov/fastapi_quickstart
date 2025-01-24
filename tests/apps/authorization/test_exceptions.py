from core.enums import JSENDStatus
from fastapi import status

from src.api.authorization.exceptions import BackendPermissionError


class TestPermissionException:
    def test__init__(self) -> None:
        exception = BackendPermissionError()

        assert exception.status == JSENDStatus.FAIL
        assert exception.data is None
        assert exception.message == "User has no access to perform this action."
        assert exception.code == status.HTTP_403_FORBIDDEN
