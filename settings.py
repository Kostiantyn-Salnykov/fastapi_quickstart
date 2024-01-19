import enum
import functools
import logging
import os
import pathlib
import typing
from typing import TYPE_CHECKING, Any

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from pydantic import Field, PostgresDsn, model_validator
from pydantic.fields import FieldInfo
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict
from sqlalchemy.engine.url import URL

PROJECT_BASE_DIR = pathlib.Path(__file__).resolve().parent
load_dotenv(dotenv_path=PROJECT_BASE_DIR / ".env")

if TYPE_CHECKING:
    from boto3_type_annotations.ssm.paginator import GetParametersByPath


def _build_db_dsn(*, username: str, password: str, host: str, port: int, database: str, async_dsn: bool = False) -> URL:
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


class Environment(enum.Enum):
    """Enum for environments types.

    Notes:
        It uses as prefixes for BaseSettings builder, e.g.:

        - **DEV** = "dev" - `dev` prefix
        - **TEST** = "test" - `test` prefix
        - **PROD** = "prod" - `prod` prefix
    """

    DEV = "dev"
    TEST = "test"
    PROD = "prod"


class MainSettings(BaseSettings):
    model_config = SettingsConfigDict(
        extra="allow",
        env_file=".env",
        env_file_encoding="UTF-8",
        env_nested_delimiter="__",
        env_prefix="",
    )

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
    # Google settings
    GOOGLE_CLIENT_ID: str = Field()
    GOOGLE_CLIENT_SECRET: str = Field()
    # AWS settings
    AWS_LOG_LEVEL: int = Field(default=logging.WARNING)
    AWS_REGION: str = Field(default="eu-central-1")
    AWS_ACCESS_KEY: str = Field()
    AWS_SECRET_ACCESS_KEY: str = Field()
    # Cognito
    AWS_USER_POOL_ID: str = Field()
    # SES
    AWS_SMTP_SERVICE_USERNAME: str = Field()
    AWS_SMTP_SERVICE_PASSWORD: str = Field()

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

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            SSMSettingsSource(settings_cls=settings_cls),
            env_settings,
            init_settings,
            dotenv_settings,
            file_secret_settings,
        )  # first - more priority.


class SSMSettingsSource(PydanticBaseSettingsSource):
    def __call__(self) -> dict[str, str]:
        env = os.environ.get("ENVIRONMENT", Environment.DEV.value)
        path = pathlib.Path(f"/{env}/")
        session = boto3.Session(
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
            region_name=os.environ.get("AWS_REGION"),
        )
        return self.get_parameters_by_path(session=session, path=path)

    def get_field_value(self, field: FieldInfo, field_name: str) -> tuple[Any, str, bool]:
        ...

    @staticmethod
    def get_parameters_by_path(session: boto3.Session, path: pathlib.Path | str) -> dict[str, str]:
        result = {}
        try:
            client = session.client(service_name="ssm")
            paginator: GetParametersByPath = client.get_paginator("get_parameters_by_path")
            response_iterator = paginator.paginate(Path=str(path), WithDecryption=True)
            result = {
                str(pathlib.Path(parameter["Name"]).relative_to(path)): parameter["Value"]
                for page in response_iterator
                for parameter in page["Parameters"]
            }
        except ClientError:
            ...

        return result


@functools.lru_cache
def get_settings() -> MainSettings:
    return MainSettings()


Settings: MainSettings = get_settings()

if Settings.DEBUG and Settings.SHOW_SETTINGS:
    import pprint

    pprint.pprint(Settings.model_dump())  # noqa: T203
