import typing

from fastapi import status as http_status

from apps.CORE.enums import JSENDStatus


class BackendException(Exception):
    """Exception for Back-end with JSEND adaptation.

    Examples:
        >>> raise BackendException(status=JSENDStatus.SUCCESS, data=["Something", "Interesting"],
        ... message="Fascinating exception.", code=http_status.HTTP_200_OK)
    """

    def __init__(
        self,
        *,
        status: JSENDStatus = JSENDStatus.FAIL,
        data: typing.Union[None, int, str, list[typing.Any], dict[str, typing.Any]] = None,
        message: str,
        code: int = http_status.HTTP_400_BAD_REQUEST,
    ):
        """
        Initializer for BackException.

        Keyword Args:
            status (JSENDStatus): status for JSEND
            data: any detail or data for this exception.
            message (str): any text detail for this exception.
            code (int): HTTP status code or custom code from Back-end.
        """
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
        """Converts BackendException to python dict. Actually used to wrap JSEND response."""
        return {
            "status": self.status.value if isinstance(self.status, JSENDStatus) else self.status,
            "data": self.data,
            "message": self.message,
            "code": self.code,
        }


class RateLimitException(BackendException):
    def __init__(
        self,
        *,
        status: JSENDStatus = JSENDStatus.FAIL,
        data: typing.Union[None, int, str, list[typing.Any], dict[str, typing.Any]] = None,
        message: str,
        code: int = http_status.HTTP_429_TOO_MANY_REQUESTS,
        headers: dict[str, str] = None,
    ) -> None:
        super().__init__(status=status, data=data, message=message, code=code)
        self.headers = headers
