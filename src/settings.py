import functools
import pathlib

from core.custom_logging.settings import LogSettings
from core.db.settings import DBSettings
from core.dependencies.settings import DependenciesSettings
from core.managers.settings import ManagersSettings
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import SettingsConfigDict

PROJECT_SRC_DIR = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT_DIR = PROJECT_SRC_DIR.parent
load_dotenv(dotenv_path=PROJECT_ROOT_DIR / ".env", override=True)


class MainSettings(LogSettings, DBSettings, ManagersSettings, DependenciesSettings):
    """Main settings class definition."""

    model_config = SettingsConfigDict(
        extra="allow",
        env_file=".env",
        env_file_encoding="UTF-8",
        env_nested_delimiter="__",
        env_prefix="",
    )

    APP_DEBUG: bool = Field(default=False)
    APP_SHOW_SETTINGS: bool = Field(default=False)
    APP_ENABLE_OPENAPI: bool = Field(default=False)
    APP_TRUSTED_HOSTS: list[str] = Field(default=["*"])

    SERVER_HOST: str = Field(default="0.0.0.0")
    SERVER_PORT: int = Field(default=8000)
    SERVER_WORKERS_COUNT: int = Field(default=1)

    CORS_ALLOW_CREDENTIALS: bool = Field(default=True)
    CORS_ALLOW_HEADERS: list[str] = Field(default=["*"])
    CORS_ALLOW_METHODS: list[str] = Field(default=["*"])
    CORS_ALLOW_ORIGINS: list[str] = Field(default=["*"])


@functools.lru_cache
def get_settings() -> MainSettings:
    """Default getter with cache for MainSettings."""
    return MainSettings()


Settings: MainSettings = get_settings()

if Settings.APP_DEBUG and Settings.APP_SHOW_SETTINGS:
    import pprint

    pprint.pprint(Settings.model_dump())  # noqa: T203
