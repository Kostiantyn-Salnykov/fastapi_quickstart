__all__ = ("Responses",)

import typing

from fastapi import status

from apps.CORE.custom_types import DictIntOfAny
from apps.CORE.schemas.responses import (
    JSENDErrorResponseSchema,
    JSENDFailResponseSchema,
    UnprocessableEntityResponseSchema,
)


class Responses:
    """Default responses for FastAPI routers."""

    BASE: typing.ClassVar[DictIntOfAny] = {
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "model": JSENDFailResponseSchema[list[UnprocessableEntityResponseSchema]]
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": JSENDErrorResponseSchema},
    }
    AUTH: typing.ClassVar[DictIntOfAny] = BASE | {
        status.HTTP_401_UNAUTHORIZED: {"model": JSENDFailResponseSchema[str]},
        status.HTTP_403_FORBIDDEN: {"model": JSENDFailResponseSchema[str]},
    }
    BAD_REQUEST: typing.ClassVar[DictIntOfAny] = {status.HTTP_400_BAD_REQUEST: {"model": JSENDFailResponseSchema}}
    NOT_FOUND: typing.ClassVar[DictIntOfAny] = {status.HTTP_404_NOT_FOUND: {"model": JSENDFailResponseSchema}}
    NOT_IMPLEMENTED: typing.ClassVar[DictIntOfAny] = {
        status.HTTP_501_NOT_IMPLEMENTED: {"model": JSENDErrorResponseSchema}
    }
