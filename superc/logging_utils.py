"""Helpers for consistent logging configuration and Supabase mirroring."""

from __future__ import annotations

import logging
from typing import Optional

from superc import config


class SupabaseLogHandler(logging.Handler):
    """Custom handler that mirrors log output into Supabase."""

    def __init__(self) -> None:
        super().__init__()
        self._write_log = None

    def emit(self, record: logging.LogRecord) -> None:  # pragma: no cover - thin wrapper
        if self._write_log is False:
            return

        if self._write_log is None:
            try:
                from db.utils import write_log  # local import to avoid hard dependency if disabled
            except Exception:
                self._write_log = False
                self.handleError(record)
                return
            self._write_log = write_log

        try:
            formatted = self.format(record)
            if not formatted:
                return
            self._write_log(formatted)
        except Exception:
            self.handleError(record)


def _resolve_log_level(level: Optional[int]) -> int:
    if level is not None:
        return level

    configured = config.LOG_LEVEL
    if isinstance(configured, int):
        return configured

    if isinstance(configured, str):
        mapped = getattr(logging, configured.upper(), None)
        if isinstance(mapped, int):
            return mapped

    return logging.INFO


def setup_logging(level: Optional[int] = None, *, force: bool = False) -> None:
    """Configure root logging once and, if enabled, attach the Supabase mirror."""

    resolved_level = _resolve_log_level(level)

    logging.basicConfig(level=resolved_level, format=config.LOG_FORMAT, force=force)

    logging.getLogger("httpx").setLevel(logging.WARNING)

    if not config.ENABLE_SUPABASE_LOGS:
        return

    root_logger = logging.getLogger()
    if any(isinstance(handler, SupabaseLogHandler) for handler in root_logger.handlers):
        return

    supabase_handler = SupabaseLogHandler()
    supabase_handler.setLevel(logging.INFO)
    supabase_handler.setFormatter(logging.Formatter(config.LOG_FORMAT))
    root_logger.addHandler(supabase_handler)
