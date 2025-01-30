import functools
import logging

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LogSettings(BaseSettings):
    model_config = SettingsConfigDict(
        extra="ignore",
        env_file_encoding="utf-8",
        env_prefix="",
        env_nested_delimiter="__",
    )

    LOG_LEVEL: int = Field(default=logging.WARNING)
    LOG_USE_LINKS: bool = Field(default=False)
    LOG_USE_COLORS: bool = Field(default=False)
    LOG_FORMAT_EXTENDED: str = Field(
        default="{levelname} | {name} | {filename}:{lineno} | {funcName} | {message} ({asctime})"
    )
    LOG_FORMAT: str = Field(default="{levelname} | {message} | ({asctime})")
    LOG_DATE_TIME_FORMAT_ISO_8601: str = Field(default="%Y-%m-%dT%H:%M:%S.%fZ", description="ISO 8601.")
    LOG_DATE_TIME_FORMAT_WITHOUT_MICROSECONDS: str = Field(
        default="%Y-%m-%dT%H:%M:%SZ", description="ISO 8601 without microseconds."
    )
    LOG_SUCCESS_LEVEL: int = Field(default=25)
    LOG_TRACE_LEVEL: int = Field(default=15)
    LOG_DEFAULT_HANDLER_CLASS: str = Field(default="logging.StreamHandler")


@functools.lru_cache
def get_log_settings() -> LogSettings:
    """Default getter with cache for LogSettings."""
    return LogSettings()


log_settings: LogSettings = get_log_settings()
