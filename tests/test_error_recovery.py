"""Tests for ErrorRecoveryManager — retry chain, circuit breaker, and fallback chains."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.reliability.error_recovery import (
    CircuitBreaker,
    CircuitState,
    ErrorRecoveryManager,
    FailureRecord,
)


class TestCircuitBreaker:
    """Unit tests for CircuitBreaker state machine."""

    def test_closed_is_available(self):
        cb = CircuitBreaker(name="test")
        assert cb.is_available() is True
        assert cb.state == CircuitState.CLOSED

    def test_record_success_resets(self):
        cb = CircuitBreaker(name="test", failure_count=3)
        cb.record_success()
        assert cb.failure_count == 0
        assert cb.state == CircuitState.CLOSED

    def test_record_failure_increments_and_opens(self):
        cb = CircuitBreaker(name="test", failure_count=4)
        cb.record_failure()
        assert cb.failure_count == 5
        assert cb.state == CircuitState.OPEN

    def test_open_blocks_calls(self):
        cb = CircuitBreaker(name="test", state=CircuitState.OPEN, failure_count=5)
        with patch("time.monotonic", return_value=cb.last_failure + 30):
            assert cb.is_available() is False

    def test_half_open_after_timeout(self):
        cb = CircuitBreaker(name="test", state=CircuitState.OPEN, failure_count=5, last_failure=100.0)
        with patch("time.monotonic", return_value=100.0 + 65):
            assert cb.is_available() is True
            assert cb.state == CircuitState.HALF_OPEN


class TestErrorRecoveryManagerRetry:
    """Tests for retry with exponential backoff."""

    @pytest.fixture
    def manager(self):
        return ErrorRecoveryManager()

    async def test_retry_succeeds_on_first_attempt(self, manager):
        """Successful call on first try — no retries needed."""
        call_count = 0

        async def fn():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await manager._retry_with_backoff(fn, "test-agent")
        assert result == "success"
        assert call_count == 1

    async def test_retry_retries_on_transient_error(self, manager):
        """Transient error triggers retry chain."""
        call_count = 0

        async def fn():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RuntimeError("transient")
            return "success after retry"

        result = await manager._retry_with_backoff(fn, "test-agent")
        assert result == "success after retry"
        assert call_count == 3

    async def test_retry_exhausts_after_max_retries(self, manager):
        """All retries exhausted raises the last exception."""
        async def fn():
            raise RuntimeError("permanent error")

        with pytest.raises(RuntimeError, match="permanent error"):
            await manager._retry_with_backoff(fn, "test-agent")

    async def test_circuit_open_prevents_call(self, manager):
        """When circuit is OPEN, call is blocked immediately."""
        circuit = manager._get_circuit("test-agent")
        circuit.state = CircuitState.OPEN
        circuit.failure_count = 5
        circuit.last_failure = 0

        with patch("time.monotonic", return_value=0):
            with pytest.raises(RuntimeError, match="Circuit open"):
                await manager._retry_with_backoff(AsyncMock(), "test-agent")


class TestErrorRecoveryManagerExecute:
    """Tests for the full execute() recovery chain."""

    @pytest.fixture
    def manager(self):
        return ErrorRecoveryManager()

    async def test_execute_retries_on_transient_error(self, manager):
        """Mock model error, verify retry chain is triggered."""
        attempt_count = 0

        async def run_fn(model, task, agent_key):
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count == 1:
                raise RuntimeError("rate limit — transient")
            return "recovery success"

        with patch("core.agent_registry.get_model") as mock_get_model:
            mock_model = MagicMock()
            mock_get_model.return_value = mock_model

            result = await manager.execute(
                task="test task",
                agent_key="coding",
                run_fn=run_fn,
            )

            assert result == "recovery success"
            assert attempt_count == 2

    async def test_fallback_chain_triggered(self, manager):
        """First model fails, fallback model is called."""
        primary_attempt = 0
        fallback_attempt = 0

        async def run_fn(model, task, agent_key):
            nonlocal primary_attempt, fallback_attempt
            primary_attempt += 1
            if primary_attempt == 1:
                raise RuntimeError("primary model overloaded")
            return "fallback success"

        with patch("core.agent_registry.get_model") as mock_get_model:
            mock_primary = MagicMock()
            mock_fallback = MagicMock()
            mock_get_model.side_effect = [mock_primary, mock_fallback, mock_primary]

            # First call: primary fails all retries
            with patch.object(manager, "_retry_with_backoff", side_effect=RuntimeError("primary failed")):
                await manager.execute(
                    task="test task",
                    agent_key="coding",
                    run_fn=run_fn,
                )

            # Should have called fallback model
            assert mock_get_model.call_count >= 2


class TestFailureRecord:
    """Unit tests for FailureRecord dataclass."""

    def test_failure_record_fields(self):
        record = FailureRecord(
            timestamp=1234567890.0,
            strategy="retry",
            agent="test-agent",
            task_hash="abc123",
            error_type="RuntimeError",
            error_msg="test error",
        )
        assert record.agent == "test-agent"
        assert record.strategy == "retry"
        assert record.error_type == "RuntimeError"


class TestCircuitStatus:
    """Tests for circuit_status() formatting."""

    async def test_circuit_status_empty(self):
        manager = ErrorRecoveryManager()
        assert "No circuit breakers active" in manager.circuit_status()

    async def test_circuit_status_one_circuit(self):
        manager = ErrorRecoveryManager()
        manager._get_circuit("coding")
        status = manager.circuit_status()
        assert "coding" in status


class TestFailureSummary:
    """Tests for failure_summary() formatting."""

    async def test_failure_summary_empty(self):
        manager = ErrorRecoveryManager()
        assert "No failures recorded" in manager.failure_summary()

    async def test_failure_summary_records(self):
        manager = ErrorRecoveryManager()
        manager._log_failure("retry", "coding", "task text", RuntimeError("test error"))
        summary = manager.failure_summary()
        assert "coding" in summary
        assert "RuntimeError" in summary
