import functools
from typing import Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine.url import URL


class DBSettings(BaseSettings):
    model_config = SettingsConfigDict(
        extra="ignore",
        env_file_encoding="utf-8",
        env_prefix="",
        env_nested_delimiter="__",
    )

    APP_RDMS_ECHO: bool = Field(default=False)
    APP_RDMS_DRIVER_NAME: str = Field(default="postgresql+asyncpg")
    APP_RDMS_HOST: str = Field(default="localhost")
    APP_RDMS_PORT: int = Field(default=5432)
    APP_RDMS_DB: str = Field(default="postgres")
    APP_RDMS_USER: str = Field(default="postgres")
    APP_RDMS_PASSWORD: str = Field(default="postgres")
    APP_RDMS_URL: URL | str | None = Field(
        default=None, description="This url will be constructed from other settings."
    )

    REDIS_SECURE: bool = Field(default=True)
    REDIS_HOST: str = Field(default="0.0.0.0")
    REDIS_PORT: int = Field(default=6379)
    REDIS_USER: str | None = Field(default=None)
    REDIS_PASSWORD: str = Field(default="redis")
    REDIS_DB: int = Field(default=0)
    REDIS_DECODE_RESPONSES: bool = Field(default=True)
    REDIS_ENCODING: str = Field(default="utf-8")
    REDIS_POOL_MAX_CONNECTIONS: int = Field(default=100)

    @model_validator(mode="after")
    def after_constructor(self) -> Self:
        self.APP_RDMS_URL = URL.create(
            drivername=self.APP_RDMS_DRIVER_NAME,
            username=self.APP_RDMS_USER,
            password=self.APP_RDMS_PASSWORD,
            host=self.APP_RDMS_HOST,
            port=self.APP_RDMS_PORT,
            database=self.APP_RDMS_DB,
        )
        return self


@functools.lru_cache
def get_db_settings() -> DBSettings:
    """Default getter with cache for DBSettings."""
    return DBSettings()


db_settings: DBSettings = get_db_settings()
