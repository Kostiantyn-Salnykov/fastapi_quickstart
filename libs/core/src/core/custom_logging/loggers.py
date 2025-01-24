import logging

from core.custom_logging.settings import log_settings


class ExtendedLogger(logging.Logger):
    """Custom logger class, with new log methods."""

    def trace(self, msg: str, *args, **kwargs) -> None:
        """Add extra `trace` log method."""
        if self.isEnabledFor(log_settings.LOG_TRACE_LEVEL):
            self._log(log_settings.LOG_TRACE_LEVEL, msg, args, **kwargs, stacklevel=2)

    def success(self, msg: str, *args, **kwargs) -> None:
        """Add extra `success` log method."""
        if self.isEnabledFor(log_settings.LOG_SUCCESS_LEVEL):
            self._log(log_settings.LOG_SUCCESS_LEVEL, msg, args, **kwargs, stacklevel=2)
