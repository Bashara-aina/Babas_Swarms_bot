"""Structured logging configuration for production observability.

Provides JSON-formatted structured logs with standard fields
for machine parsing and log aggregation.

Standard fields on every log entry:
  timestamp, level, component, event, session_id, task_id,
  agent_name, cost_usd, tokens_used, latency_ms, success
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any, Dict, Optional


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured log output."""

    def format(self, record: logging.LogRecord) -> str:
        entry: Dict[str, Any] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add structured fields from extra
        for key in (
            "component", "event", "session_id", "task_id",
            "agent_name", "cost_usd", "tokens_used", "latency_ms",
            "success", "model", "error_type",
        ):
            val = getattr(record, key, None)
            if val is not None:
                entry[key] = val

        if record.exc_info and record.exc_info[1]:
            entry["exception"] = str(record.exc_info[1])
            entry["exception_type"] = type(record.exc_info[1]).__name__

        return json.dumps(entry, default=str)


class SwarmLogger:
    """Structured logger with bound context fields.

    Usage:
        log = SwarmLogger("orchestrator")
        log.info("task_routed", agent_name="coding", latency_ms=150)
        log.error("task_failed", error_type="timeout", exc_info=True)
    """

    def __init__(self, component: str) -> None:
        self._logger = logging.getLogger(f"swarm.{component}")
        self._component = component
        self._bound: Dict[str, Any] = {}

    def bind(self, **kwargs: Any) -> "SwarmLogger":
        """Return a new logger with additional bound context."""
        new = SwarmLogger(self._component)
        new._bound = {**self._bound, **kwargs}
        new._logger = self._logger
        return new

    def _log(self, level: int, event: str, **kwargs: Any) -> None:
        extra = {"component": self._component, "event": event}
        extra.update(self._bound)
        extra.update(kwargs)

        exc_info = extra.pop("exc_info", False)
        self._logger.log(level, event, extra=extra, exc_info=exc_info)

    def info(self, event: str, **kwargs: Any) -> None:
        self._log(logging.INFO, event, **kwargs)

    def warning(self, event: str, **kwargs: Any) -> None:
        self._log(logging.WARNING, event, **kwargs)

    def error(self, event: str, **kwargs: Any) -> None:
        self._log(logging.ERROR, event, **kwargs)

    def debug(self, event: str, **kwargs: Any) -> None:
        self._log(logging.DEBUG, event, **kwargs)


def configure_structured_logging(
    log_file: str = "swarm-structured.log",
    level: int = logging.INFO,
) -> None:
    """Configure structured JSON logging for production.

    Adds a JSON file handler to the swarm.* logger hierarchy.
    Does not affect existing logging configuration.
    """
    swarm_logger = logging.getLogger("swarm")
    swarm_logger.setLevel(level)

    # JSON file handler
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(StructuredFormatter())
    swarm_logger.addHandler(file_handler)

    # Also log to stdout in structured format if not already
    if not any(
        isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
        for h in swarm_logger.handlers
    ):
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(StructuredFormatter())
        swarm_logger.addHandler(stream_handler)

    swarm_logger.info("Structured logging configured", extra={
        "component": "logging",
        "event": "logging_configured",
    })
