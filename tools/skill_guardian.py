"""tools/skill_guardian.py — Tool-use guardian with retried execution and failure classification.

Inspired by the antigravity-awesome-skills tool-use-guardian SKILL.md.
Wraps any async tool call with exponential backoff, failure classification,
and safety pre-checks.
"""
from __future__ import annotations

import asyncio
import logging
import time
from enum import Enum
from typing import Any, Callable, Coroutine, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class FailureType(str, Enum):
    TRANSIENT = "TRANSIENT"       # network, rate-limit → retry
    INVALID_INPUT = "INVALID_INPUT"  # bad params → fix + retry
    PERMISSION = "PERMISSION"     # 401/403 → escalate
    NOT_FOUND = "NOT_FOUND"       # 404 → stop
    FATAL = "FATAL"               # crash → stop


_TRANSIENT_KEYWORDS = ("timeout", "rate limit", "429", "503", "connection", "reset")
_PERMISSION_KEYWORDS = ("401", "403", "unauthorized", "forbidden", "permission")
_NOT_FOUND_KEYWORDS = ("404", "not found", "does not exist", "no such")


def classify_error(exc: Exception) -> FailureType:
    msg = str(exc).lower()
    if any(k in msg for k in _TRANSIENT_KEYWORDS):
        return FailureType.TRANSIENT
    if any(k in msg for k in _PERMISSION_KEYWORDS):
        return FailureType.PERMISSION
    if any(k in msg for k in _NOT_FOUND_KEYWORDS):
        return FailureType.NOT_FOUND
    if isinstance(exc, (ValueError, TypeError, KeyError)):
        return FailureType.INVALID_INPUT
    return FailureType.FATAL


SAFE_RETRYABLE = {FailureType.TRANSIENT, FailureType.INVALID_INPUT}
_BACKOFF = [0, 1.0, 4.0, 16.0]  # seconds before each attempt


async def guarded_call(
    fn: Callable[..., Coroutine[Any, Any, T]],
    *args: Any,
    tool_name: str = "unknown",
    max_attempts: int = 4,
    **kwargs: Any,
) -> T:
    """Execute an async tool call with retries, backoff, and failure classification.

    Args:
        fn: async callable to execute
        *args: positional args to fn
        tool_name: label for logging
        max_attempts: total attempts before raising (default 4 = 3 retries)
        **kwargs: keyword args to fn

    Returns:
        Result of fn(*args, **kwargs)

    Raises:
        The last exception if all attempts fail or failure is non-retryable.
    """
    last_exc: Exception | None = None
    for attempt in range(max_attempts):
        wait = _BACKOFF[attempt] if attempt < len(_BACKOFF) else 16.0
        if wait > 0:
            await asyncio.sleep(wait)
        t0 = time.monotonic()
        try:
            result = await fn(*args, **kwargs)
            elapsed = (time.monotonic() - t0) * 1000
            logger.debug(
                "[guardian] %s OK attempt=%d elapsed=%.0fms",
                tool_name, attempt + 1, elapsed,
            )
            return result
        except Exception as exc:
            elapsed = (time.monotonic() - t0) * 1000
            failure = classify_error(exc)
            logger.warning(
                "[guardian] %s FAIL attempt=%d/%d type=%s elapsed=%.0fms err=%s",
                tool_name, attempt + 1, max_attempts, failure.value, elapsed, exc,
            )
            last_exc = exc
            if failure not in SAFE_RETRYABLE:
                logger.error(
                    "[guardian] %s non-retryable failure (%s), stopping.",
                    tool_name, failure.value,
                )
                raise

    assert last_exc is not None
    raise last_exc


def safety_check(params: dict[str, Any]) -> list[str]:
    """Pre-call safety check on tool params. Returns list of warnings (empty = safe)."""
    warnings: list[str] = []
    for key, value in params.items():
        if not isinstance(value, str):
            continue
        if "../" in value or "..\\\\" in value:
            warnings.append(f"{key}: path traversal pattern detected")
        if value.strip().lower().startswith(("drop ", "delete ", "truncate ", "rm -rf")):
            warnings.append(f"{key}: destructive operation keyword detected")
        if "localhost" in value or "127.0.0.1" in value or "169.254" in value:
            warnings.append(f"{key}: SSRF risk — localhost/metadata IP detected")
    return warnings
