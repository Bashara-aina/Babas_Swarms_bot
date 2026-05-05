"""Circuit breaker pattern for external service resilience.

States:
  CLOSED  — normal operation, failures counted
  OPEN    — circuit tripped, fast-fail without calling service
  HALF_OPEN — test if service recovered

Usage:
  cb = CircuitBreaker("duckduckgo", failure_threshold=5, recovery_timeout=60)
  async with cb:
      results = await search_web(query)
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Awaitable
from enum import Enum
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Async circuit breaker with configurable thresholds and recovery timeout."""

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        half_open_max_calls: int = 1,
    ) -> None:
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: float | None = None
        self._half_open_calls = 0
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        return self._state

    def _should_attempt_recovery(self) -> bool:
        if self._last_failure_time is None:
            return True
        return (time.monotonic() - self._last_failure_time) >= self.recovery_timeout

    def _record_success(self) -> None:
        self._failure_count = 0
        self._state = CircuitState.CLOSED
        self._half_open_calls = 0
        logger.debug("[CircuitBreaker][%s] success — reset to CLOSED", self.name)

    def _record_failure(self) -> None:
        self._failure_count += 1
        self._last_failure_time = time.monotonic()
        if self._failure_count >= self.failure_threshold:
            self._state = CircuitState.OPEN
            logger.warning(
                "[CircuitBreaker][%s] opened after %d failures (recovery in %.0fs)",
                self.name,
                self._failure_count,
                self.recovery_timeout,
            )
        elif self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.OPEN
            logger.warning("[CircuitBreaker][%s] half-open call failed — re-open", self.name)

    async def __aenter__(self) -> CircuitBreaker:
        async with self._lock:
            if self._state == CircuitState.OPEN:
                if self._should_attempt_recovery():
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
                    logger.info("[CircuitBreaker][%s] OPEN → HALF_OPEN (testing recovery)", self.name)
                else:
                    raise CircuitOpenError(
                        f"CircuitBreaker[{self.name}] is OPEN — service unavailable "
                        f"(retry in {self.recovery_timeout:.0f}s)"
                    )

            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_calls >= self.half_open_max_calls:
                    raise CircuitOpenError(f"CircuitBreaker[{self.name}] is HALF_OPEN — max probe calls reached")
                self._half_open_calls += 1

        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type is not None and issubclass(exc_type, Exception):
            self._record_failure()
        else:
            self._record_success()
        return None


class CircuitOpenError(Exception):
    """Raised when circuit breaker is OPEN and fast-fails."""

    pass


# ── Pre-built circuit breakers for common external services ────────────────────


def get_circuit_breakers() -> dict[str, CircuitBreaker]:
    """Return the shared circuit breaker registry."""
    global _circuit_breakers
    return _circuit_breakers


def circuit(name: str) -> CircuitBreaker:
    """Get a named circuit breaker, creating if needed."""
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(name=name)
    return _circuit_breakers[name]


async def with_circuit(  # noqa: UP047
    name: str,
    coro: Awaitable[T],
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
) -> T:
    """Execute a coroutine within a named circuit breaker."""
    cb = circuit(name)
    async with cb:
        return await coro


_circuit_breakers: dict[str, CircuitBreaker] = {}
