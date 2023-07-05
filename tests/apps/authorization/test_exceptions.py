from fastapi import status

from apps.authorization.exceptions import PermissionError
from apps.CORE.enums import JSENDStatus


class TestPermissionException:
    def test__init__(self) -> None:
        exception = PermissionError()

        assert exception.status == JSENDStatus.FAIL
        assert exception.data is None
        assert exception.message == "User has no access to perform this action."
        assert exception.code == status.HTTP_403_FORBIDDEN
