from fastapi import APIRouter, FastAPI, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from sqlalchemy import text
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from apps.CORE.db import async_engine, async_session_factory, engine, session_factory
from apps.CORE.enums import JSENDStatus
from apps.CORE.exceptions import BackendException
from apps.CORE.handlers import backend_exception_handler, validation_exception_handler
from apps.CORE.responses import Responses
from apps.CORE.schemas import JSENDOutSchema
from apps.todos.routers import to_do_router
from loggers import get_logger, setup_logging
from settings import Settings

logger = get_logger(name=__name__)

app = FastAPI(
    debug=True,
    title="FastAPI Quickstart",
    description="",
    version="0.0.1",
    openapi_url="/openapi.json" if Settings.ENABLE_OPENAPI else None,
    redoc_url=None,
    docs_url="/docs/" if Settings.ENABLE_OPENAPI else None,
    default_response_class=ORJSONResponse,
    responses=Responses.BASE,
)

# Add exception handlers
app.add_exception_handler(BackendException, backend_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# Add middlewares stack (FIRST IN => LATER EXECUTION)
app.add_middleware(
    middleware_class=CORSMiddleware,
    allow_origins=Settings.CORS_ALLOW_ORIGINS,
    allow_credentials=Settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=Settings.CORS_ALLOW_METHODS,
    allow_headers=Settings.CORS_ALLOW_HEADERS,
)  # №2
app.add_middleware(middleware_class=ProxyHeadersMiddleware, trusted_hosts=Settings.TRUSTED_HOSTS)  # №1


@app.on_event(event_type="startup")
def enable_logging():
    setup_logging()
    logger.debug(msg="Logging configuration completed.")


@app.on_event(event_type="startup")
async def _check_sync_engine() -> None:
    logger.debug(msg="Checking connection with sync engine...")
    with session_factory() as session:
        result = session.execute(statement=text("SELECT current_timestamp;")).scalar()
    logger.debug(msg=f"Result of sync 'SELECT current_timestamp;' is: {result.isoformat() if result else result}")


@app.on_event(event_type="startup")
async def _check_async_engine() -> None:
    logger.debug(msg="Checking connection with async engine...")
    async with async_session_factory() as async_session:
        result = await async_session.execute(statement=text("SELECT current_timestamp;"))
        result = result.scalar()
    logger.debug(msg=f"Result of async 'SELECT current_timestamp;' is: {result.isoformat() if result else result}")


@app.on_event(event_type="shutdown")
async def _dispose_all_connections() -> None:
    logger.debug(msg="Closing all DB connections...")
    await async_engine.dispose()
    engine.dispose()
    logger.debug(msg="All DB connections closed.")


api_router = APIRouter()


@api_router.get(
    path="/",
    response_model=JSENDOutSchema,
    status_code=status.HTTP_200_OK,
    summary="Health check.",
    description="Health check endpoint.",
)
async def healthcheck() -> ORJSONResponse:
    """Check that API endpoints works properly.

    Returns:
        ORJSONResponse: json object with JSENDResponseSchema body.
    """
    return ORJSONResponse(
        content={
            "status": JSENDStatus.SUCCESS,
            "data": None,
            "message": "Health check.",
            "code": status.HTTP_200_OK,
        },
        status_code=status.HTTP_200_OK,
    )


API_PREFIX = "/api/v1"
# Include routers:
app.include_router(router=api_router, prefix=API_PREFIX)
app.include_router(router=to_do_router, prefix=API_PREFIX)


if __name__ == "__main__":
    # Use this for debugging purposes only
    import uvicorn

    uvicorn.run(
        app="apps.main:app",
        host=Settings.HOST,
        port=Settings.PORT,
        loop="uvloop",
        reload=True,
        reload_delay=3,
        log_level=Settings.LOG_LEVEL,
        use_colors=Settings.LOG_USE_COLORS,
    )
