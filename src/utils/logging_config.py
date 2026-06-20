"""Central structured logging configuration for the project."""

from __future__ import annotations

from contextvars import ContextVar
from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
import sys
from typing import Any


_LOG_LEVEL_MAP: dict[str, int] = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
_LOG_CONTEXT: ContextVar[dict[str, Any]] = ContextVar(
    "gold_prediction_log_context",
    default={},
)
_STANDARD_RECORD_FIELDS = set(logging.makeLogRecord({}).__dict__) | {
    "message",
    "asctime",
}


class _ContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        context = _LOG_CONTEXT.get()
        record.run_id = context.get("run_id", "-")
        record.command = context.get("command", "-")
        for key, value in context.items():
            if not hasattr(record, key):
                setattr(record, key, value)
        return True


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created,
                tz=timezone.utc,
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "run_id": getattr(record, "run_id", "-"),
            "command": getattr(record, "command", "-"),
        }
        for key, value in record.__dict__.items():
            if (
                key not in _STANDARD_RECORD_FIELDS
                and key not in payload
                and not key.startswith("_")
            ):
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


def set_log_context(**fields: Any) -> None:
    """Attach stable correlation fields to every subsequent log record."""

    context = dict(_LOG_CONTEXT.get())
    context.update(fields)
    _LOG_CONTEXT.set(context)


def clear_log_context() -> None:
    """Clear correlation fields after a workflow finishes."""

    _LOG_CONTEXT.set({})


def _handler_exists(
    root_logger: logging.Logger,
    handler_type: type[logging.Handler],
    path: Path | None = None,
) -> bool:
    resolved = path.resolve() if path is not None else None
    for handler in root_logger.handlers:
        if not isinstance(handler, handler_type):
            continue
        if resolved is None:
            return True
        handler_path = getattr(handler, "baseFilename", None)
        if handler_path and Path(handler_path).resolve() == resolved:
            return True
    return False


def setup_logging(
    level: str | None = None,
    log_file: Path | None = None,
    json_log_file: Path | None = None,
    run_id: str | None = None,
    command: str | None = None,
) -> None:
    """Configure console, human-readable file and JSONL file handlers.

    The function is intentionally additive and idempotent. This allows modules
    to obtain loggers during import while a CLI later adds run-specific files.
    """

    if run_id is not None or command is not None:
        set_log_context(run_id=run_id or "-", command=command or "-")

    raw_level = level or os.environ.get("LOG_LEVEL", "INFO")
    numeric_level = _LOG_LEVEL_MAP.get(raw_level.upper(), logging.INFO)
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    context_filter = _ContextFilter()
    human_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | "
        "run_id=%(run_id)s | command=%(command)s | %(message)s",
        datefmt=_DATE_FORMAT,
    )

    if not _handler_exists(root_logger, logging.StreamHandler):
        console = logging.StreamHandler(sys.stdout)
        console.setFormatter(human_formatter)
        console.addFilter(context_filter)
        root_logger.addHandler(console)

    if log_file is not None:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        if not _handler_exists(root_logger, logging.FileHandler, log_file):
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setFormatter(human_formatter)
            file_handler.addFilter(context_filter)
            root_logger.addHandler(file_handler)

    if json_log_file is not None:
        json_log_file = Path(json_log_file)
        json_log_file.parent.mkdir(parents=True, exist_ok=True)
        if not _handler_exists(root_logger, logging.FileHandler, json_log_file):
            json_handler = logging.FileHandler(json_log_file, encoding="utf-8")
            json_handler.setFormatter(_JsonFormatter())
            json_handler.addFilter(context_filter)
            root_logger.addHandler(json_handler)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger using the centralized configuration."""

    setup_logging()
    return logging.getLogger(name)


__all__ = [
    "clear_log_context",
    "get_logger",
    "set_log_context",
    "setup_logging",
]
