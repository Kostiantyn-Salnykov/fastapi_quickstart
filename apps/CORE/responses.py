__all__ = ("Responses",)

from fastapi import status

from apps.CORE.schemas.responses import (
    JSENDErrorResponse,
    JSENDFailResponse,
    JSENDResponse,
    UnprocessableEntityResponse,
)


class Responses:
    """Default responses for FastAPI routers."""

    BASE = {
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": JSENDResponse[list[UnprocessableEntityResponse]]},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": JSENDErrorResponse},
    }
    AUTH = BASE | {
        status.HTTP_401_UNAUTHORIZED: {"model": JSENDResponse[str]},
        status.HTTP_403_FORBIDDEN: {"model": JSENDResponse[str]},
    }
    BAD_REQUEST = {status.HTTP_400_BAD_REQUEST: {"model": JSENDFailResponse}}
    NOT_FOUND = {status.HTTP_404_NOT_FOUND: {"model": JSENDFailResponse}}
    NOT_IMPLEMENTED = {status.HTTP_501_NOT_IMPLEMENTED: {"model": JSENDErrorResponse}}
