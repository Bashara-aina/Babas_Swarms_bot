"""tests/test_circuit_breaker.py — Circuit breaker resilience tests."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.asyncio


async def test_circuit_breaker_initial_state():
    """Circuit breaker should start in CLOSED state."""
    from core.circuit_breaker import CircuitBreaker, CircuitState

    cb = CircuitBreaker(name="test", failure_threshold=5)
    assert cb.state == CircuitState.CLOSED


async def test_circuit_breaker_all_states_exist():
    """CircuitState enum should have all expected states."""
    from core.circuit_breaker import CircuitState

    states = [CircuitState.CLOSED, CircuitState.OPEN, CircuitState.HALF_OPEN]
    assert len(states) == 3


async def test_circuit_breaker_has_failure_count():
    """Circuit breaker should track failure count internally."""
    from core.circuit_breaker import CircuitBreaker

    cb = CircuitBreaker(name="test", failure_threshold=3)
    assert hasattr(cb, "_failure_count")
    assert cb._failure_count == 0


async def test_circuit_breaker_failure_threshold_configurable():
    """Circuit breaker failure_threshold should be configurable."""
    from core.circuit_breaker import CircuitBreaker

    cb = CircuitBreaker(name="test", failure_threshold=2)
    assert cb.failure_threshold == 2


async def test_circuit_breaker_name_attribute():
    """Circuit breaker stores its name."""
    from core.circuit_breaker import CircuitBreaker

    cb = CircuitBreaker(name="my_breaker")
    assert cb.name == "my_breaker"
