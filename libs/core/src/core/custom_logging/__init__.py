__all__ = (
    "LOGGING_CONFIG",
    "ExtendedLogger",
    "LogSettings",
    "get_logger",
    "setup_logging",
)

import functools
import logging
import logging.config
import logging.handlers
import typing

from core.custom_logging.formatters import ColorfulFormatter
from core.custom_logging.loggers import ExtendedLogger
from core.custom_logging.settings import LogSettings, log_settings

LOGGING_INITIALIZED = False  # no-qa: F841


def _get_main_handler(*, is_third_party: bool = True) -> list[str]:
    """Returns handler name depends on Settings."""
    result = ["default_handler"]

    if log_settings.LOG_USE_COLORS:
        result = (
            ["colorful_link_handler"] if log_settings.LOG_USE_LINKS and not is_third_party else ["colorful_handler"]
        )

    return result


def _get_default_log_format() -> str:
    """Returns log format depends on Settings."""
    return log_settings.LOG_FORMAT_EXTENDED if log_settings.LOG_FORMAT_EXTENDED else log_settings.LOG_FORMAT


def _get_default_formatter() -> dict[str, typing.Any]:
    """Constructs default formatter settings."""
    return {
        "format": _get_default_log_format(),
        "style": "{",
        "datefmt": log_settings.LOG_DATE_TIME_FORMAT_WITHOUT_MICROSECONDS,
        "validate": True,
        "use_colors": log_settings.LOG_USE_COLORS,
    }


LOGGING_CONFIG: dict[str, typing.Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "colorful_link_formatter": {
            "()": ColorfulFormatter,
            "fmt": _get_default_log_format(),
            "style": "{",
            "datefmt": log_settings.LOG_DATE_TIME_FORMAT_ISO_8601,
            "validate": True,
            "link_format": log_settings.LOG_USE_LINKS,
        },
        "default": _get_default_formatter(),
        "access": _get_default_formatter(),
        "colorful_formatter": {
            "()": ColorfulFormatter,
            "fmt": _get_default_log_format(),
            "style": "{",
            "datefmt": log_settings.LOG_DATE_TIME_FORMAT_ISO_8601,
            "link_format": False,
        },
    },
    "handlers": {
        "default_handler": {
            "class": log_settings.LOG_DEFAULT_HANDLER_CLASS,
            "level": logging.DEBUG,
            "formatter": "default",
        },
        "colorful_handler": {
            "class": log_settings.LOG_DEFAULT_HANDLER_CLASS,
            "level": logging.DEBUG,
            "formatter": "colorful_formatter",
        },
        "colorful_link_handler": {
            "class": log_settings.LOG_DEFAULT_HANDLER_CLASS,
            "level": logging.DEBUG,
            "formatter": "colorful_link_formatter",
        },
    },
    "root": {"level": log_settings.LOG_LEVEL, "handlers": _get_main_handler(is_third_party=False)},
    "loggers": {
        "alembic": {"level": "INFO", "handlers": _get_main_handler(), "propagate": False},
        "sqlalchemy": {"level": "WARNING", "handlers": _get_main_handler(), "propagate": False},
        "asyncio": {"level": "WARNING", "handlers": _get_main_handler(), "propagate": False},
        "gunicorn": {"level": "INFO", "handlers": _get_main_handler(), "propagate": False},
        "gunicorn.error": {"level": "INFO", "handlers": _get_main_handler(), "propagate": False},
        "gunicorn.access": {"level": "INFO", "handlers": _get_main_handler(), "propagate": False},
        "uvicorn": {"level": "INFO", "handlers": _get_main_handler(), "propagate": False},
        "uvicorn.error": {"level": "INFO", "handlers": _get_main_handler(), "propagate": False},
        "uvicorn.access": {"level": "INFO", "handlers": _get_main_handler(), "propagate": False},
        "granian.access": {"level": "INFO", "handlers": _get_main_handler(), "propagate": False},
        "_granian": {"level": "INFO", "handlers": _get_main_handler(), "propagate": False},
        "casbin": {"level": "WARNING", "handlers": _get_main_handler(), "propagate": False},
        "watchfiles": {"level": "WARNING", "handlers": _get_main_handler(), "propagate": False},
        "app.debug": {
            "level": log_settings.LOG_LEVEL,
            "handlers": _get_main_handler(is_third_party=False),
            "propagate": False,
        },
    },
}


def setup_logging() -> None:
    """Setup logging from dict configuration object."""
    global LOGGING_INITIALIZED  # noqa: PLW0603
    if LOGGING_INITIALIZED:
        return
    logging.addLevelName(log_settings.LOG_SUCCESS_LEVEL, "SUCCESS")
    logging.addLevelName(log_settings.LOG_TRACE_LEVEL, "TRACE")
    logging.setLoggerClass(klass=ExtendedLogger)
    logger = logging.getLogger()
    logger.trace = ExtendedLogger.trace
    logger.success = ExtendedLogger.success
    logging.config.dictConfig(config=LOGGING_CONFIG)
    logging.getLogger(name=__name__).warning("setup_logging() initialized.")
    LOGGING_INITIALIZED = True


def get_logger(name: str | None = "apps.") -> ExtendedLogger:
    """Get logger instance by name.

    Args:
        name (str): Name of logger.

    Returns:
        ExtendedLogger: Instance of logging.Logger.

    Examples:
        >>>from core.custom_logging import get_logger

        >>>logger = get_logger(name=__name__)
        >>>logger.debug("Debug message")
    """
    global LOGGING_INITIALIZED  # noqa: PLW0602
    if not LOGGING_INITIALIZED:
        setup_logging()

    logger = logging.getLogger(name=name)
    logger.debug(f"get_logger(name={name}) initialized.")
    return logger


@functools.lru_cache
def get_root_logger() -> ExtendedLogger:
    return get_logger(name="root")
