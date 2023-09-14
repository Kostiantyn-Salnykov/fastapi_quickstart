import functools
import logging
import pathlib
import typing

from pydantic import Extra, Field, PostgresDsn, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine.url import URL

PROJECT_BASE_DIR = pathlib.Path(__file__).resolve().parent


def _build_db_dsn(username: str, password: str, host: str, port: int, database: str, async_dsn: bool = False) -> URL:
    """Factory for PostgreSQL DSN."""
    driver_name = "postgresql"
    if async_dsn:
        driver_name += "+asyncpg"
    return URL.create(
        drivername=driver_name,
        username=username,
        password=password,
        host=host,
        port=port,
        database=database,
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
    TOKENS_ACCESS_LIFETIME_SECONDS: int = Field(default=3600 * 10)  # 1 HOUR
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
    POSTGRES_URL: PostgresDsn | None = Field(default=None)
    POSTGRES_URL_ASYNC: PostgresDsn | None = Field(default=None)
    # Redis settings
    REDIS_SECURE: bool = Field(default=True)
    REDIS_HOST: str = Field(default="0.0.0.0")
    REDIS_PORT: int = Field(default=6379)
    REDIS_USER: str | None = Field(default=None)
    REDIS_PASSWORD: str = Field(default="redis")
    REDIS_DB: int = Field(default=0)
    REDIS_DECODE_RESPONSES: bool = Field(default=True)
    REDIS_ENCODING: str = Field(default="utf-8")
    REDIS_POOL_MAX_CONNECTIONS: int = Field(default=100)

    class Config(SettingsConfigDict):
        extra = Extra.ignore
        env_file = ".env"
        env_file_encoding = "UTF-8"
        env_nested_delimiter = "__"

    @model_validator(mode="after")
    def validate_database_url(self) -> typing.Self:
        """Construct PostgreSQL DSN."""
        self.POSTGRES_URL = _build_db_dsn(
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            database=self.POSTGRES_DB,
        )
        return self

    @model_validator(mode="after")
    def validate_database_url_async(self) -> typing.Self:
        """Construct async (with asyncpg driver) PostgreSQL DSN."""
        self.POSTGRES_URL_ASYNC = _build_db_dsn(
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            database=self.POSTGRES_DB,
            async_dsn=True,
        )
        return self


@functools.lru_cache
def get_settings() -> MainSettings:
    return MainSettings()


Settings: MainSettings = get_settings()

if Settings.DEBUG and Settings.SHOW_SETTINGS:
    import pprint  # noqa

    pprint.pprint(Settings.model_dump())
