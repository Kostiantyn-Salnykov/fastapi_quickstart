import copy
import datetime
import functools
import logging
import typing

import click
from core.annotations import StrOrNone
from core.custom_logging.settings import log_settings
from core.helpers import get_utc_timezone


class Styler:
    """Style for logs."""

    _default_kwargs: typing.ClassVar[list[dict[str, int | str | float | tuple | list | bool]]] = [
        {"level": logging.DEBUG, "fg": "white"},
        {"level": log_settings.LOG_TRACE_LEVEL, "fg": (121, 85, 72)},
        {"level": log_settings.LOG_SUCCESS_LEVEL, "fg": "bright_green"},
        {"level": logging.INFO, "fg": "bright_blue"},
        {"level": logging.WARNING, "fg": "bright_yellow"},
        {"level": logging.ERROR, "fg": "bright_red"},
        {"level": logging.CRITICAL, "fg": (126, 87, 194), "bold": True, "underline": True},
    ]

    def __init__(self) -> None:
        """Initialize the colors map with related log level."""
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
        return self.colors_map.get(level, lambda x: True)

    def set_style(
        self,
        *,
        level: int,
        fg: tuple[int, int, int] | StrOrNone = None,
        bg: tuple[int, int, int] | StrOrNone = None,
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
        """This function sets style for Logs.

        Args:
            level (int): Log level.
            fg (): set foreground color.
            bg (): set background color.
            bold (): Bold on the text.
            dim (): Enable/Disable dim mode.  (This is badly supported).
            underline (): Enable/Disable underline.
            overline (): Enable/Disable overline
            italic (): Enable/Disable italic.
            blink (): Enable/Disable blinking on the text.
            reverse (): Enable/Disable inverse rendering (foreground becomes background and the other way round).
            strikethrough (): Enable/Disable striking through text
            reset (): by default, a reset-all code is added at the end of the string, which means that styles do not
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


def _format_time(record: logging.LogRecord, datefmt: str = log_settings.LOG_DATE_TIME_FORMAT_ISO_8601) -> str:
    """Format datetime to UTC datetime."""
    date_time_utc = datetime.datetime.fromtimestamp(record.created, tz=get_utc_timezone())
    return datetime.datetime.strftime(date_time_utc, datefmt or log_settings.LOG_DATE_TIME_FORMAT_ISO_8601)


class ColorfulFormatter(logging.Formatter):
    """Styler for colorful format."""

    LOG_FILE_FORMAT = click.style(text='╰───📑File "', fg="bright_white", bold=True)
    LOG_LINE_FORMAT = click.style(text='", line ', fg="bright_white", bold=True)

    def __init__(
        self,
        *,
        fmt: str = log_settings.LOG_FORMAT,
        datefmt: str = log_settings.LOG_DATE_TIME_FORMAT_ISO_8601,
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
            fmt += f"\n{self.LOG_FILE_FORMAT}{{pathname}}{self.LOG_LINE_FORMAT}{{lineno}}"
        super().__init__(fmt=fmt, datefmt=datefmt, style=style, validate=validate)

    def formatTime(  # noqa: N802
        self,
        record: logging.LogRecord,
        datefmt: str | None = log_settings.LOG_DATE_TIME_FORMAT_ISO_8601,
    ) -> str:
        """Custom format datetime to UTC datetime."""
        return _format_time(record=record, datefmt=datefmt or log_settings.LOG_DATE_TIME_FORMAT_ISO_8601)

    def formatMessage(self, record: logging.LogRecord) -> str:  # noqa: N802
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
                    text=record_copy.message,
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
