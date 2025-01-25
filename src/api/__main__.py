import datetime
from typing import Annotated

from core.custom_logging import LOGGING_CONFIG, get_logger
from core.db.bases import async_engine
from core.dependencies import get_async_session, get_redis
from core.enums import JSENDStatus
from core.exceptions import BackendError, RateLimitError
from core.managers.tokens import TokensManager
from core.schemas.responses import JSENDResponseSchema
from domain.authorization.managers import AuthorizationManager
from domain.authorization.middlewares import JWTTokenBackend
from fastapi import APIRouter, Depends, FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import ORJSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.authentication import AuthenticationMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

import redis.exceptions
from src.api.exception_handlers import (
    backend_exception_handler,
    rate_limit_exception_handler,
    validation_exception_handler,
)
from src.api.lifespan import lifespan
from src.api.responses import Responses
from src.api.users.routers import register_router, tokens_router, users_router
from src.settings import PROJECT_SRC_DIR, Settings

logger = get_logger(name=__name__)


app = FastAPI(
    debug=Settings.APP_DEBUG,
    title="FastAPI Quickstart",
    description="",
    version="0.0.1",
    openapi_url="/openapi.json" if Settings.APP_ENABLE_OPENAPI else None,
    swagger_ui_parameters={
        "syntaxHighlight.theme": "monokai",
        "persistAuthorization": True,
    },
    redoc_url=None,  # Redoc disabled
    docs_url="/docs/" if Settings.APP_ENABLE_OPENAPI else None,
    default_response_class=ORJSONResponse,
    responses=Responses.BASE,
    lifespan=lifespan,
)

# State objects
app.state.tokens_manager = TokensManager(
    secret_key=Settings.TOKENS_SECRET_KEY,
    default_token_lifetime=datetime.timedelta(seconds=Settings.TOKENS_ACCESS_LIFETIME_SECONDS),
)
app.state.authorization_manager = AuthorizationManager(engine=async_engine)

# Add exception handlers (<Error type>, <Error handler>)
app.add_exception_handler(BackendError, backend_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(RateLimitError, rate_limit_exception_handler)

# Add middlewares stack (FIRST IN => LATER EXECUTION)
app.add_middleware(middleware_class=GZipMiddleware, minimum_size=512)  # №5
# app.add_middleware(middleware_class=CasbinMiddleware, enforcer=enforcer)  # №4
app.add_middleware(
    middleware_class=AuthenticationMiddleware,
    backend=JWTTokenBackend(scheme_prefix="Bearer"),
    on_error=lambda conn, exc: ORJSONResponse(
        content={"status": JSENDStatus.FAIL, "data": None, "message": str(exc), "code": status.HTTP_401_UNAUTHORIZED},
        status_code=status.HTTP_401_UNAUTHORIZED,
    ),
)  # №3
app.add_middleware(
    middleware_class=CORSMiddleware,
    allow_origins=Settings.CORS_ALLOW_ORIGINS,
    allow_credentials=Settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=Settings.CORS_ALLOW_METHODS,
    allow_headers=Settings.CORS_ALLOW_HEADERS,
)  # №2
app.add_middleware(middleware_class=ProxyHeadersMiddleware, trusted_hosts=Settings.APP_TRUSTED_HOSTS)  # №1


api_router = APIRouter()


@api_router.get(
    path="/",
    response_model=JSENDResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Health check.",
    description="Health check endpoint.",
)
async def healthcheck(
    request: Request,
    redis: Annotated[redis.Redis, Depends(get_redis)],
    async_session: Annotated[AsyncSession, Depends(get_async_session)],
) -> ORJSONResponse:
    """Check that API endpoints work properly.

    Returns:
        ORJSONResponse: json object with JSENDResponseSchema body.
    """
    if Settings.APP_DEBUG:
        async_result = await async_session.execute(statement=text("SELECT true;"))
        data = {
            "redis": await redis.ping(),
            "postgresql_async": async_result.scalar_one(),
        }
    else:
        data = None
    return ORJSONResponse(
        content={
            "status": JSENDStatus.SUCCESS,
            "data": data,
            "message": "Health check.",
            "code": status.HTTP_200_OK,
        },
        status_code=status.HTTP_200_OK,
    )


API_PREFIX = "/api/v1"
# Include routers:
app.include_router(router=api_router, prefix=API_PREFIX)
app.include_router(router=register_router, prefix=API_PREFIX)
app.include_router(router=users_router, prefix=API_PREFIX)
app.include_router(router=tokens_router, prefix=API_PREFIX)


if __name__ == "__main__":  # pragma: no cover
    # Use this for debugging purposes only
    import uvicorn

    uvicorn.run(
        app="src.api.__main__:app",
        host=Settings.SERVER_HOST,
        port=Settings.SERVER_PORT,
        workers=Settings.SERVER_WORKERS_COUNT,
        # loop="uvloop",
        reload=True,
        reload_delay=3,
        reload_dirs=[PROJECT_SRC_DIR],
        reload_includes=[".env"],
        log_level=Settings.LOG_LEVEL,
        log_config=LOGGING_CONFIG,
        use_colors=Settings.LOG_USE_COLORS,
        date_header=False,
        server_header=False,
    )
