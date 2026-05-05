"""Centralised logging configuration with rotation and API key redaction.

Usage:
    from core.log_config import setup_logging
    setup_logging()  # call once at startup before anything else
"""

import json
import logging
import logging.handlers
import os
import re
import sys
from contextvars import ContextVar
from datetime import UTC, datetime, timezone
from typing import Any

# ── Request ID context var (propagated across async tasks) ────────────────────
_request_id_var: ContextVar[str] = ContextVar("request_id", default="")


def get_request_id() -> str:
    return _request_id_var.get()


def set_request_id(rid: str) -> None:
    _request_id_var.set(rid)


# ── Patterns that look like API keys / secrets ────────────────────────────────
_SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{20,}"),  # OpenAI / Groq style
    re.compile(r"AIza[A-Za-z0-9_\-]{20,}"),  # Google API key variants
    re.compile(r"[A-Za-z0-9]{32,}(?=.*secret)", re.I),  # generic secret
    re.compile(r"Bearer [A-Za-z0-9\-._~+/]+=*"),  # Bearer tokens
    re.compile(r"bot[0-9]{8,}:[A-Za-z0-9_\-]{20,}"),  # Telegram bot token variants
]


class RedactingFormatter(logging.Formatter):
    """Formatter that strips API keys and secrets from log lines."""

    def format(self, record: logging.LogRecord) -> str:
        original = super().format(record)
        result = original
        for pattern in _SECRET_PATTERNS:
            result = pattern.sub("[REDACTED]", result)
        return result


class _JsonFormatter(logging.Formatter):
    """Structured JSON formatter for production logs.

    Format: {"ts": "ISO8601", "level": "INFO/WARNING/ERROR", "component": "...",
             "user": "...", "msg": "...", "duration_ms": ..., "request_id": "..."}
    """

    def format(self, record: logging.LogRecord) -> str:
        ts = datetime.now(UTC).isoformat(timespec="milliseconds")
        request_id = _request_id_var.get() or ""
        duration_ms = getattr(record, "duration_ms", None)

        payload: dict[str, Any] = {
            "ts": ts,
            "level": record.levelname,
            "component": record.name,
            "msg": record.getMessage(),
        }
        if request_id:
            payload["request_id"] = request_id
        if duration_ms is not None:
            payload["duration_ms"] = duration_ms
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


def setup_logging(
    log_file: str = "bot.log",
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
    level: int = logging.INFO,
) -> None:
    """Configure root logger with rotating file handler + redaction.

    Set LOG_FORMAT=json env var for production JSON logs.
    """
    json_mode = os.getenv("LOG_FORMAT", "").strip().lower() == "json"

    if json_mode:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(_JsonFormatter())
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(_JsonFormatter())
    else:
        formatter = RedactingFormatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    root.addHandler(file_handler)
    root.addHandler(console_handler)

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("litellm").setLevel(logging.WARNING)
