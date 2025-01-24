import functools

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ManagersSettings(BaseSettings):
    model_config = SettingsConfigDict(
        extra="ignore",
        env_file_encoding="utf-8",
        env_prefix="",
        env_nested_delimiter="__",
    )

    TOKENS_ACCESS_LIFETIME_SECONDS: int = Field(default=3600 * 10)  # 1 HOUR
    TOKENS_ISSUER: str = Field(default="FastAPI Quickstart")
    TOKENS_REFRESH_LIFETIME_SECONDS: int = Field(default=86400)  # 1 DAY
    TOKENS_SECRET_KEY: str = Field(default="TEST")


@functools.lru_cache
def get_managers_settings() -> ManagersSettings:
    """Default getter with cache for ManagersSettings."""
    return ManagersSettings()


managers_settings: ManagersSettings = get_managers_settings()
