from core.domain.authorization.exceptions import BackendPermissionError
from core.enums import JSENDStatus
from fastapi import status


class TestPermissionException:
    def test__init__(self) -> None:
        exception = BackendPermissionError()

        assert exception.status == JSENDStatus.FAIL
        assert exception.data is None
        assert exception.message == "User has no access to perform this action."
        assert exception.code == status.HTTP_403_FORBIDDEN
