import datetime

from core.custom_logging import LOGGING_CONFIG, get_logger
from core.db.bases import async_engine
from core.enums import JSENDStatus
from core.exceptions import BackendError, RateLimitError
from core.managers.tokens import TokensManager
from domain.authorization.managers import AuthorizationManager
from domain.authorization.middlewares import JWTTokenBackend
from fastapi import FastAPI, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import ORJSONResponse
from sqlalchemy.exc import IntegrityError, NoResultFound
from starlette.middleware.authentication import AuthenticationMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from src.api.exception_handlers import (
    backend_exception_handler,
    integrity_error_handler,
    no_result_found_error_handler,
    rate_limit_exception_handler,
    validation_exception_handler,
)
from src.api.lifespan import lifespan
from src.api.responses import Responses
from src.api.routers import register_routers
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
app.add_exception_handler(NoResultFound, no_result_found_error_handler)
app.add_exception_handler(IntegrityError, integrity_error_handler)

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

register_routers(app=app)


if __name__ == "__main__":  # pragma: no cover
    # Use this for debugging purposes only
    import uvicorn

    uvicorn.run(
        app="src.api.__main__:app",
        host=Settings.SERVER_HOST,
        port=Settings.SERVER_PORT,
        workers=Settings.SERVER_WORKERS_COUNT,
        # loop="uvloop",
        # reload=True,
        reload_delay=3,
        reload_dirs=[PROJECT_SRC_DIR],
        reload_includes=[".env"],
        log_level=Settings.LOG_LEVEL,
        log_config=LOGGING_CONFIG,
        use_colors=Settings.LOG_USE_COLORS,
        date_header=False,
        server_header=False,
    )
