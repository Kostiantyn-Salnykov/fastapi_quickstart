__all__ = ("Responses",)

import typing

from fastapi import status

from apps.CORE.custom_types import DictIntOfAny
from apps.CORE.schemas.responses import JSENDErrorResponse, JSENDFailResponse, UnprocessableEntityResponse


class Responses:
    """Default responses for FastAPI routers."""

    BASE: typing.ClassVar[DictIntOfAny] = {
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": JSENDFailResponse[list[UnprocessableEntityResponse]]},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": JSENDErrorResponse},
    }
    AUTH: typing.ClassVar[DictIntOfAny] = BASE | {
        status.HTTP_401_UNAUTHORIZED: {"model": JSENDFailResponse[str]},
        status.HTTP_403_FORBIDDEN: {"model": JSENDFailResponse[str]},
    }
    BAD_REQUEST: typing.ClassVar[DictIntOfAny] = {status.HTTP_400_BAD_REQUEST: {"model": JSENDFailResponse}}
    NOT_FOUND: typing.ClassVar[DictIntOfAny] = {status.HTTP_404_NOT_FOUND: {"model": JSENDFailResponse}}
    NOT_IMPLEMENTED: typing.ClassVar[DictIntOfAny] = {status.HTTP_501_NOT_IMPLEMENTED: {"model": JSENDErrorResponse}}
