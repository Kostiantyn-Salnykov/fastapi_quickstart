import typing

from fastapi import status as http_status

from apps.CORE.enums import JSENDStatus


class BackendException(Exception):
    def __init__(
        self,
        *,
        status: JSENDStatus = JSENDStatus.FAIL,
        data: typing.Union[None, int, str, list, dict] = None,
        message: str,
        code: int = http_status.HTTP_400_BAD_REQUEST,
    ):
        self.status = status
        self.data = data
        self.message = message
        self.code = code

    def __repr__(self) -> str:
        """Representation for BackendException."""
        return (
            f'{self.__class__.__name__}(status={self.status}, data={self.data}, message="{self.message}", '
            f"code={self.code})"
        )

    def __str__(self) -> str:
        """String representation for BackendException."""
        return self.__repr__()

    def dict(self) -> typing.Dict[str, typing.Any]:
        """Converts BackendException to python dict."""
        return {
            "status": self.status.value,
            "data": self.data,
            "message": self.message,
            "code": self.code,
        }
