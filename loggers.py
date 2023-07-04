"""Module for logger settings."""
import copy
import datetime
import functools
import logging
import logging.config
import logging.handlers
import typing

import click

from settings import Settings

LOG_FORMAT = "{name} | {filename}:{lineno} | {funcName} | {levelname} | {message} | ({asctime}/{created})"
LOG_FORMAT_AWS = (
    "%(name)s | %(filename)s:%(lineno)s | %(funcName)s | %(levelname)s | %(message)s | (%(asctime)s/" "%(created)s)"
)
LOG_FORMAT_RAW = "{levelname} | {name} | {filename}:{lineno} | {funcName} | {message} | ({asctime}/{created})"
DATE_TIME_FORMAT_ISO_8601 = "%Y-%m-%dT%H:%M:%S.%fZ"  # ISO 8601
DATE_TIME_FORMAT_WITHOUT_MICROSECONDS = "%Y-%m-%dT%H:%M:%SZ"  # ISO 8601 without microseconds
FILE_FORMAT = click.style(text='╰───📑File "', fg="bright_white", bold=True)
LINE_FORMAT = click.style(text='", line ', fg="bright_white", bold=True)


def _get_root_handler() -> list[str]:
    """Make handlers for `root` logger by runtime.

    Returns:
        result (list[str]): List of strings (names of handlers).

    Notes:
        Adds `slack_handler` for any Environment except LOCAL.
        Change to custom `colorful_handler` & `ColorfulFormatter` when LOG_USE_COLORS and DEBUG enabled.
        In other cases return `default_handler`.
    """
    result = ["default_handler"]
    if Settings.LOG_USE_COLORS and Settings.DEBUG:
        return ["colorful_handler"]
    return result


LOGGING_CONFIG: dict[str, typing.Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "debug_link_formatter": {
            "()": "loggers.ColorfulFormatter",
            "fmt": "{levelname} {message} | {asctime}",
            "style": "{",
            "datefmt": DATE_TIME_FORMAT_ISO_8601,
            "validate": True,
        },
        "default_formatter": {
            "format": LOG_FORMAT,
            "style": "{",
            "datefmt": DATE_TIME_FORMAT_WITHOUT_MICROSECONDS,
            "validate": True,
            "use_colors": Settings.LOG_USE_COLORS,
        },
        "colorful_formatter": {
            "()": "loggers.ColorfulFormatter",
            "fmt": "{levelname} {message} | {asctime}",
            "style": "{",
            "datefmt": DATE_TIME_FORMAT_ISO_8601,
            "link_format": False,
        },
    },
    "handlers": {
        "default_handler": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "default_formatter",
        },
        "debug_handler": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "debug_link_formatter",
        },
        "colorful_handler": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "colorful_formatter",
        },
    },
    "root": {"level": Settings.LOG_LEVEL, "handlers": _get_root_handler()},
    "loggers": {
        "asyncio": {"level": "WARNING", "handlers": ["default_handler"], "propagate": False},
        "gunicorn": {"level": "WARNING", "handlers": ["default_handler"], "propagate": False},
        "uvicorn": {"level": "WARNING", "handlers": ["default_handler"], "propagate": False},
        "local": {"level": "DEBUG", "handlers": ["debug_handler"], "propagate": False},
    },
}


def setup_logging() -> None:
    """Setup logging from dict configuration object. Setup AWS boto3 logging."""
    logging.config.dictConfig(config=LOGGING_CONFIG)


def get_logger(name: str | None = "local") -> logging.Logger:
    """Get logger instance by name.

    Args:
        name (str): Name of logger

    Returns:
        logging.Logger: Instance of logging.Logger

    Examples:
        from loggers import get_logger

        logger = get_logger(name=__name__)
        logger.debug(msg="Debug message")
    """
    _logger = logging.getLogger(name=name)
    return _logger


logger = get_logger(name="root")


class Styler:
    """Style for logs."""

    _default_kwargs: list[dict[str, int | str | float | tuple | list | bool]] = [
        {"level": logging.DEBUG, "fg": (121, 85, 72)},
        {"level": logging.INFO, "fg": "bright_blue"},
        {"level": logging.WARNING, "fg": "bright_yellow"},
        {"level": logging.ERROR, "fg": "bright_red"},
        {
            "level": logging.CRITICAL,
            "fg": (126, 87, 194),
            "bold": True,
            "underline": True,
        },
    ]

    def __init__(self) -> None:
        self.colors_map: dict[int, functools.partial] = {}

        for kwargs in self.__class__._default_kwargs:
            self.set_style(**kwargs)  # type: ignore

    def get_style(self, level: int) -> functools.partial | typing.Callable:
        """Get Style for logs.

        Args:
            level (int): Log level.

        Returns:
            Style for logs.
        """
        return self.colors_map.get(level, lambda text: text)

    def set_style(
        self,
        level: int,
        fg: tuple[int, int, int] | str | None = None,
        bg: tuple[int, int, int] | str | None = None,
        bold: bool | None = None,
        dim: bool | None = None,
        underline: bool | None = None,
        overline: bool | None = None,
        italic: bool | None = None,
        blink: bool | None = None,
        reverse: bool | None = None,
        strikethrough: bool | None = None,
        reset: bool = True,
    ) -> None:
        """Set style for Logs.

        Args:
            level (int): Log level.
            fg (): set foreground color.
            bg (): set background color.
            bold (): Bold on text.
            dim (): Enable/Disable dim mode.  (This is badly supported).
            underline (): Enable/Disable underline.
            overline (): Enable/Disable overline
            italic (): Enable/Disable italic.
            blink (): Enable/Disable blinking on text.
            reverse (): Enable/Disable inverse rendering (foreground becomes background and the other way round).
            strikethrough (): Enable/Disable striking through text
            reset (): by default a reset-all code is added at the end of the string which means that styles do not
                carry over.  This can be disabled to compose styles.
        """
        self.colors_map[level] = functools.partial(
            click.style,
            fg=fg,
            bg=bg,
            bold=bold,
            dim=dim,
            underline=underline,
            overline=overline,
            italic=italic,
            blink=blink,
            reverse=reverse,
            strikethrough=strikethrough,
            reset=reset,
        )


def _format_time(record: logging.LogRecord, datefmt: str = DATE_TIME_FORMAT_ISO_8601) -> str:
    """Format datetime to UTC datetime."""
    date_time_utc = datetime.datetime.utcfromtimestamp(record.created)
    return datetime.datetime.strftime(date_time_utc, datefmt or DATE_TIME_FORMAT_ISO_8601)


class ColorfulFormatter(logging.Formatter):
    """Styler for colorful format."""

    def __init__(
        self,
        fmt: str = LOG_FORMAT_RAW,
        datefmt: str = DATE_TIME_FORMAT_ISO_8601,
        style: typing.Literal["%", "$", "{"] = "{",
        validate: bool = True,
        # Custom setup
        accent_color: str = "bright_cyan",
        styler: Styler = None,
        link_format: bool = True,
    ) -> None:
        self.accent_color = accent_color
        self._styler = styler or Styler()
        if link_format:
            fmt += f"\n{FILE_FORMAT}{{pathname}}{LINE_FORMAT}{{lineno}}"
        super().__init__(fmt=fmt, datefmt=datefmt, style=style, validate=validate)

    def formatTime(self, record: logging.LogRecord, datefmt: str | None = DATE_TIME_FORMAT_ISO_8601) -> str:
        """Custom format datetime to UTC datetime."""
        return _format_time(record=record, datefmt=datefmt or DATE_TIME_FORMAT_ISO_8601)

    def formatMessage(self, record: logging.LogRecord) -> str:
        """Custom format message to new format.

        Args:
            record (str): Log record.

        Returns:
            formatted message.
        """
        record_copy = copy.copy(record)
        for key in record_copy.__dict__:
            if key == "message":
                record_copy.__dict__["message"] = self._styler.get_style(level=record_copy.levelno)(
                    text=record_copy.message
                )
            elif key == "levelname":
                separator = " " * (8 - len(record_copy.levelname))
                record_copy.__dict__["levelname"] = (
                    self._styler.get_style(level=record_copy.levelno)(text=record_copy.levelname)
                    + click.style(text=":", fg=self.accent_color)
                    + separator
                )
            elif key == "levelno":
                continue  # set it after iterations (because using in other cases)
            else:
                record_copy.__dict__[key] = click.style(text=str(record.__dict__[key]), fg=self.accent_color)

        record_copy.__dict__["levelno"] = click.style(text=str(record.__dict__["levelno"]), fg=self.accent_color)

        return super().formatMessage(record=record_copy)
