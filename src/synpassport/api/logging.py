"""Structured JSON logging utilities for SynPassport backend.

Ensures all log events are serialized as structured JSON records containing run_id.
Dataset rows or raw personal data are strictly excluded from log outputs.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

__all__ = ["JsonFormatter", "get_logger", "log_run_event"]


class JsonFormatter(logging.Formatter):
    """Formats log records as structured, single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include run_id if attached to record
        if hasattr(record, "run_id") and record.run_id:
            log_obj["run_id"] = str(record.run_id)

        # Include extra structured fields if present (excluding data rows)
        if hasattr(record, "extra_fields") and isinstance(record.extra_fields, dict):
            for k, v in record.extra_fields.items():
                if k not in ("raw_data", "rows", "dataframe", "dataset_content"):
                    log_obj[k] = v

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj)


def get_logger(name: str = "synpassport.api") -> logging.Logger:
    """Return configured logger instance with JSON formatting."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


def log_run_event(
    logger: logging.Logger,
    level: int,
    message: str,
    run_id: str | None = None,
    **extra: Any,
) -> None:
    """Log structured message bound to run_id, omitting sensitive raw data."""
    # Strip any potential dataset row payloads
    safe_extra = {
        k: v
        for k, v in extra.items()
        if k not in ("raw_data", "rows", "dataframe", "dataset_content")
    }
    record = logger.makeRecord(
        name=logger.name,
        level=level,
        fn="",
        lno=0,
        msg=message,
        args=(),
        exc_info=None,
    )
    record.run_id = run_id
    record.extra_fields = safe_extra
    logger.handle(record)
