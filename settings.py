import functools
import logging
import pathlib

from pydantic import BaseSettings, Extra, Field, PostgresDsn, validator
from sqlalchemy.engine.url import URL

PROJECT_BASE_DIR = pathlib.Path(__file__).resolve().parent


def _build_db_dsn(values: dict[str, str | int | bool], async_dsn: bool = False) -> URL:
    """Factory for PostgreSQL DSN."""
    driver_name = "postgresql"
    if async_dsn:
        driver_name += "+asyncpg"
    return URL.create(
        drivername=driver_name,
        username=values.get("POSTGRES_USER"),
        password=values.get("POSTGRES_PASSWORD"),
        host=values.get("POSTGRES_HOST"),
        port=values.get("POSTGRES_PORT"),
        database=values.get("POSTGRES_DB"),
    )


class MainSettings(BaseSettings):
    # Back-end settings
    DEBUG: bool = Field(default=False)
    SHOW_SETTINGS: bool = Field(default=False)
    ENABLE_OPENAPI: bool = Field(default=False)
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)
    WORKERS_COUNT: int = Field(default=1)
    DATETIME_FORMAT: str = Field(default="%Y-%m-%d %H:%M:%S")
    TRUSTED_HOSTS: list[str] = Field(default=["*"])
    # CORS settings
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True)
    CORS_ALLOW_HEADERS: list[str] = Field(default=["*"])
    CORS_ALLOW_METHODS: list[str] = Field(default=["*"])
    CORS_ALLOW_ORIGINS: list[str] = Field(default=["*"])
    # JWT tokens managements settings
    TOKENS_ACCESS_LIFETIME_SECONDS: int = Field(default=3600)  # 1 HOUR
    TOKENS_ISSUER: str = Field(default="FastAPI Quickstart")
    TOKENS_REFRESH_LIFETIME_SECONDS: int = Field(default=86400)  # 1 DAY
    TOKENS_SECRET_KEY: str = Field(default="TEST")
    # Logging settings
    LOG_LEVEL: int = Field(default=logging.WARNING)
    LOG_USE_COLORS: bool = Field(default=False)
    # Database settings
    POSTGRES_ECHO: bool = Field(default=False)
    POSTGRES_DB: str = Field(default="postgres")
    POSTGRES_HOST: str = Field(default="0.0.0.0")
    POSTGRES_PASSWORD: str = Field(default="postgres")
    POSTGRES_USER: str = Field(default="postgres")
    POSTGRES_PORT: int = Field(default=5432)
    POSTGRES_URL: PostgresDsn = Field(default=None)
    POSTGRES_URL_ASYNC: PostgresDsn = Field(default=None)
    # Redis settings
    REDIS_SECURE: bool = Field(default=True)
    REDIS_HOST: str = Field(default="0.0.0.0")
    REDIS_PORT: int = Field(default=6379)
    REDIS_USER: str = Field(default=None)
    REDIS_PASSWORD: str = Field(default="redis")
    REDIS_DB: int = Field(default=0)
    REDIS_DECODE_RESPONSES: bool = Field(default=True)
    REDIS_ENCODING: str = Field(default="utf-8")
    REDIS_POOL_MAX_CONNECTIONS: int = Field(default=100)

    class Config(BaseSettings.Config):
        extra = Extra.ignore
        env_file = ".env"
        env_file_encoding = "UTF-8"
        env_nested_delimiter = "__"

    @validator("POSTGRES_URL", always=True)
    def validate_database_url(cls, value: str | None, values: dict[str, str | int | bool]) -> URL | str:
        """Construct PostgreSQL DSN."""
        if value is None:
            return _build_db_dsn(values=values)
        return value

    @validator("POSTGRES_URL_ASYNC", always=True)
    def validate_database_url_async(cls, value: str | None, values: dict[str, str | int | bool]) -> URL | str:
        """Construct async (with asyncpg driver) PostgreSQL DSN."""
        if value is None:
            return _build_db_dsn(values=values, async_dsn=True)
        return value


@functools.lru_cache
def get_settings() -> MainSettings:
    return MainSettings()


Settings: MainSettings = get_settings()

if Settings.DEBUG and Settings.SHOW_SETTINGS:
    import pprint  # noqa

    pprint.pprint(Settings.dict())
