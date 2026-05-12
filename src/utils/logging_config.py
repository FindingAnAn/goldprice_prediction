"""
src/utils/logging_config.py
Central logging configuration for the project.

All modules must obtain a logger via `get_logger(__name__)` from this module.
Do not call `logging.basicConfig()` or configure handlers in individual modules.

Functions:
    get_logger: Return a named logger using the project-wide configuration.
    setup_logging: Initialize logging handlers and formatter once at startup.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path


_LOG_LEVEL_MAP: dict[str, int] = {
    "DEBUG":    logging.DEBUG,
    "INFO":     logging.INFO,
    "WARNING":  logging.WARNING,
    "ERROR":    logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_initialized = False


def setup_logging(
    level: str | None = None,
    log_file: Path | None = None,
) -> None:
    """Initialize the project-wide logging configuration.

    Must be called once at application startup. Subsequent calls are no-ops.
    Log level is controlled by the LOG_LEVEL environment variable (default: INFO).

    Args:
        level: Override log level string ('DEBUG', 'INFO', etc.).
            If None, reads from LOG_LEVEL environment variable.
        log_file: Optional path to write logs to a file in addition to stdout.
    """
    global _initialized
    if _initialized:
        return

    raw_level = level or os.environ.get("LOG_LEVEL", "INFO")
    numeric_level = _LOG_LEVEL_MAP.get(raw_level.upper(), logging.INFO)

    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))

    for handler in handlers:
        handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    for handler in handlers:
        root_logger.addHandler(handler)

    _initialized = True


def get_logger(name: str) -> logging.Logger:
    """Return a named logger using the project-wide configuration.

    Args:
        name: Logger name, typically passed as ``__name__`` from the calling module.

    Returns:
        Configured Logger instance.

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Pipeline started", extra={"source": "kaggle"})
    """
    setup_logging()
    return logging.getLogger(name)
