"""Centralised logging configuration with rotation and API key redaction.

Usage:
    from core.log_config import setup_logging
    setup_logging()  # call once at startup before anything else
"""
import logging
import logging.handlers
import re
import os


# Patterns that look like API keys / secrets
_SECRET_PATTERNS = [
    re.compile(r'sk-[A-Za-z0-9]{20,}'),          # OpenAI / Groq style
    re.compile(r'AIza[A-Za-z0-9_\-]{20,}'),        # Google API key variants
    re.compile(r'[A-Za-z0-9]{32,}(?=.*secret)', re.I),  # generic secret
    re.compile(r'Bearer [A-Za-z0-9\-._~+/]+=*'),  # Bearer tokens
    re.compile(r'bot[0-9]{8,}:[A-Za-z0-9_\-]{20,}'),  # Telegram bot token variants
]


class RedactingFormatter(logging.Formatter):
    """Formatter that strips API keys and secrets from log lines."""

    def format(self, record: logging.LogRecord) -> str:
        original = super().format(record)
        result = original
        for pattern in _SECRET_PATTERNS:
            result = pattern.sub('[REDACTED]', result)
        return result


def setup_logging(
    log_file: str = "bot.log",
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
    level: int = logging.INFO,
) -> None:
    """Configure root logger with rotating file handler + redaction."""
    formatter = RedactingFormatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Rotating file handler — 10 MB max, keep 5 backups
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    # Console handler
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
