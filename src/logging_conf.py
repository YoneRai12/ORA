"""Logging configuration helpers."""

from __future__ import annotations

import logging
import os
import time
from logging.config import dictConfig
from typing import Any, Dict

# Default base directory for logs (legacy). Prefer passing `log_dir=` from Config.
DEFAULT_LOG_DIR = r"L:\ORA_Logs"


class ISO8601UTCFormatter(logging.Formatter):
    """Formatter that outputs timestamps in ISO-8601 UTC."""

    converter = time.localtime

    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:  # noqa: N802
        formatted = super().formatTime(record, datefmt=datefmt)
        if record.msecs:
            return f"{formatted}.{int(record.msecs):03d}"
        return f"{formatted}"


from src.utils.privacy import PrivacyFilter


class MaxLevelFilter(logging.Filter):
    """Filter that only allows records BELOW OR EQUAL to a certain level."""

    def __init__(self, level):
        super().__init__()
        self.level = level

    def filter(self, record):
        return record.levelno <= self.level


def setup_logging(level: str, *, log_dir: str | None = None) -> None:
    """Configure application logging."""
    base_dir = (log_dir or "").strip() or os.getenv("ORA_LOG_DIR", "").strip() or DEFAULT_LOG_DIR

    # Ensure log directory exists (fallback to ./logs if the target isn't writable)
    if not os.path.exists(base_dir):
        try:
            os.makedirs(base_dir, exist_ok=True)
            print(f"[Logging] Created Log Directory: {base_dir}")
        except Exception as e:
            print(f"[Logging] FAILED to create {base_dir}. Fallback to local logs. Error: {e}")
            # Fallback path if L: drive is missing/unwritable
            fallback_dir = "logs"
            if not os.path.exists(fallback_dir):
                os.makedirs(fallback_dir, exist_ok=True)
            base_dir = fallback_dir

    config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "structured": {
                "()": ISO8601UTCFormatter,
                "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
            }
        },
        "filters": {
            "exclude_errors": {"()": MaxLevelFilter, "level": logging.INFO},
            "privacy": {"()": PrivacyFilter}
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "structured",
                "level": level,
                "filters": ["privacy"],
            },
            "file_all": {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "structured",
                "level": "DEBUG",  # Capture everything
                "filename": os.path.join(base_dir, "ora_all.log"),
                "maxBytes": 10 * 1024 * 1024,  # 10 MB
                "backupCount": 5,
                "encoding": "utf-8",
                "filters": ["privacy"],
            },
            "file_success": {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "structured",
                "level": "INFO",
                "filename": os.path.join(base_dir, "ora_success.log"),
                "maxBytes": 5 * 1024 * 1024,  # 5 MB
                "backupCount": 5,
                "encoding": "utf-8",
                "filters": ["exclude_errors", "privacy"],  # Exclude WARNING/ERROR/CRITICAL
            },
            "file_error": {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "structured",
                "level": "ERROR",
                "filename": os.path.join(base_dir, "ora_error.log"),
                "maxBytes": 5 * 1024 * 1024,
                "backupCount": 5,
                "encoding": "utf-8",
                "filters": ["privacy"],
            },
            "queue": {
                "class": "src.utils.logger.QueueHandler",
                "queue": "src.utils.logger.GuildLogger.queue",
            },
        },
        "root": {
            "handlers": ["console", "file_all", "file_success", "file_error"],
            "level": level,
            "filters": ["privacy"],
        },
    }

    dictConfig(config)

    # Manually attach QueueHandler (as dictConfig can't pass the queue object reference easily)
    from src.utils.logger import GuildLogger, QueueHandler

    q_handler = QueueHandler(GuildLogger.queue)
    q_handler.setLevel(logging.INFO)  # Filter logic will happen in SystemCog
    logging.getLogger().addHandler(q_handler)
