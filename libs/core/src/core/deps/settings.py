import functools

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DependenciesSettings(BaseSettings):
    model_config = SettingsConfigDict(
        extra="ignore",
        env_file_encoding="utf-8",
        env_prefix="",
        env_nested_delimiter="__",
    )

    DEPENDENCIES_DEBUG: bool = Field(default=False)


@functools.lru_cache
def get_dependencies_settings() -> DependenciesSettings:
    """Default getter with cache for DependenciesSettings."""
    return DependenciesSettings()


dependencies_settings: DependenciesSettings = get_dependencies_settings()
