from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import ORJSONResponse
from sqlalchemy.exc import IntegrityError

from apps.CORE.enums import JSENDStatus
from apps.CORE.exceptions import BackendException
from settings import Settings


def backend_exception_handler(request: Request, exc: BackendException) -> ORJSONResponse:
    """
    Handler for BackendException.

    Args:
        request (Request): FastAPI Request instance.
        exc (BackendException): Error that Back-end raises.

    Returns:
        result (ORJSONResponse): Transformed JSON response from Back-end exception.
    """
    return ORJSONResponse(content=exc.dict(), status_code=exc.code)


def validation_exception_handler(request: Request, exc: RequestValidationError) -> ORJSONResponse:
    """
    Handler for RequestValidationError. Get the original 'detail' list of errors wrapped with JSEND structure.

    Args:
        request (Request): FastAPI Request instance.
        exc (RequestValidationError): Error that Pydantic raises (in case of validation error).

    Returns:
        result (ORJSONResponse): Transformed JSON response from Back-end exception.
    """
    details = exc.errors()
    modified_details = []
    for error in details:
        modified_details.append(
            {
                "location": error["loc"],
                "message": error["msg"].capitalize() + ".",
                "type": error["type"],
                "context": error.get("ctx", None),
            }
        )
    return ORJSONResponse(
        content={
            "status": JSENDStatus.FAIL,
            "data": modified_details,
            "message": "Validation error.",
            "code": status.HTTP_422_UNPROCESSABLE_ENTITY,
        },
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )


def integrity_error_handler(error: IntegrityError) -> None:
    """
    Handler for IntegrityError (SQLAlchemy error).

    Args:
        error (IntegrityError): Error that Pydantic raises (in case of validation error).

    Raises:
        BackendException: Actually proxies these errors to `backend_exception_handler`.
    """
    if "duplicate" in error.args[0]:
        # Parse duplication error and show it in debug mode, otherwise "update error".
        raise BackendException(message=str(error.orig.args[0].split("\n")[-1]) if Settings.DEBUG else "Update error.")
    else:
        raise BackendException(
            message=str(error) if Settings.DEBUG else "Internal server error.",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            status=JSENDStatus.ERROR,
        )
