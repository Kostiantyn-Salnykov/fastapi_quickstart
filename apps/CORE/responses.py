from fastapi import status

from apps.CORE.schemas import JSENDErrorOutSchema, JSENDFailOutSchema, JSENDOutSchema, UnprocessableEntityOutSchema

__all__ = ("Responses",)


class Responses:
    """Default responses for FastAPI routers."""

    BASE = {
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": JSENDOutSchema[list[UnprocessableEntityOutSchema]]},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": JSENDErrorOutSchema},
    }
    AUTH = BASE | {
        status.HTTP_401_UNAUTHORIZED: {"model": JSENDOutSchema[str]},
        status.HTTP_403_FORBIDDEN: {"model": JSENDOutSchema[str]},
    }
    BAD_REQUEST = {status.HTTP_400_BAD_REQUEST: {"model": JSENDFailOutSchema}}
    NOT_FOUND = {status.HTTP_404_NOT_FOUND: {"model": JSENDFailOutSchema}}
    NOT_IMPLEMENTED = {status.HTTP_501_NOT_IMPLEMENTED: {"model": JSENDErrorOutSchema}}
