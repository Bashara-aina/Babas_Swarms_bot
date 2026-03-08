# /home/newadmin/swarm-bot/reliability/error_recovery.py
"""Multi-level error recovery with circuit breaker and self-healing.

Recovery hierarchy:
1. Retry with exponential backoff (transient errors)
2. Fallback model (rate limits / model overloaded)
3. Alternative agent (if primary agent family fails)
4. Simplified prompt (reduce complexity, retry)
5. Human escalation (notify user, return partial result)
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)

# Retry config
MAX_RETRIES = 3
BASE_BACKOFF = 2.0      # seconds
MAX_BACKOFF = 16.0      # seconds

# Circuit breaker config
FAILURE_THRESHOLD = 5   # Failures before opening circuit
RESET_TIMEOUT = 60      # Seconds before attempting to close circuit


class CircuitState(Enum):
    CLOSED = "closed"       # Normal operation
    OPEN = "open"           # Failing — reject calls immediately
    HALF_OPEN = "half_open" # Testing — allow one call through


@dataclass
class CircuitBreaker:
    """Circuit breaker per agent/model.

    Attributes:
        name: Identifier (e.g. agent key or model string).
        failure_count: Consecutive failures.
        last_failure: Timestamp of last failure.
        state: Current circuit state.
    """

    name: str
    failure_count: int = 0
    last_failure: float = 0.0
    state: CircuitState = CircuitState.CLOSED

    def record_success(self) -> None:
        """Reset circuit on success."""
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def record_failure(self) -> None:
        """Record failure, open circuit if threshold reached."""
        self.failure_count += 1
        self.last_failure = time.monotonic()
        if self.failure_count >= FAILURE_THRESHOLD:
            self.state = CircuitState.OPEN
            logger.warning(
                "Circuit OPENED for %s after %d failures",
                self.name, self.failure_count,
            )

    def is_available(self) -> bool:
        """Check if calls should be allowed through.

        Returns:
            True if circuit is CLOSED or HALF_OPEN (testing).
        """
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN:
            if time.monotonic() - self.last_failure > RESET_TIMEOUT:
                self.state = CircuitState.HALF_OPEN
                logger.info("Circuit HALF_OPEN for %s — testing", self.name)
                return True
            return False
        return True   # HALF_OPEN


@dataclass
class FailureRecord:
    """A single failure event for pattern analysis.

    Attributes:
        timestamp: When failure occurred.
        strategy: Recovery strategy attempted.
        agent: Agent key involved.
        task_hash: Hash of task for deduplication.
        error_type: Exception class name.
        error_msg: Error message (truncated).
    """

    timestamp: float
    strategy: str
    agent: str
    task_hash: str
    error_type: str
    error_msg: str


class ErrorRecoveryManager:
    """Comprehensive error handling with circuit breakers and fallback chains."""

    def __init__(self) -> None:
        self._circuits: dict[str, CircuitBreaker] = {}
        self._failures: list[FailureRecord] = []

    def _get_circuit(self, name: str) -> CircuitBreaker:
        if name not in self._circuits:
            self._circuits[name] = CircuitBreaker(name=name)
        return self._circuits[name]

    def _log_failure(
        self, strategy: str, agent: str, task: str, exc: Exception
    ) -> None:
        self._failures.append(
            FailureRecord(
                timestamp=time.time(),
                strategy=strategy,
                agent=agent,
                task_hash=hashlib.sha256(task.encode()).hexdigest()[:8],
                error_type=type(exc).__name__,
                error_msg=str(exc)[:200],
            )
        )

        if len(self._failures) % 50 == 0:
            self._analyze_patterns()

    def _analyze_patterns(self) -> None:
        """Detect recurring failure patterns and log alerts."""
        recent = self._failures[-100:]
        counts: dict[tuple, int] = defaultdict(int)
        for f in recent:
            counts[(f.agent, f.error_type)] += 1

        for (agent, error_type), count in counts.items():
            if count >= 5:
                logger.error(
                    "PATTERN: %s failing with %s (%d times in last 100 failures). "
                    "Consider adjusting model or prompt.",
                    agent, error_type, count,
                )

    async def _retry_with_backoff(self, fn, agent: str, *args, **kwargs):
        """Retry fn up to MAX_RETRIES with exponential backoff.

        Args:
            fn: Async callable to retry.
            agent: Agent key for circuit breaker.
            *args, **kwargs: Passed to fn.

        Returns:
            Result of fn on success.

        Raises:
            Last exception if all retries exhausted.
        """
        circuit = self._get_circuit(agent)
        last_exc: Optional[Exception] = None

        for attempt in range(MAX_RETRIES):
            if not circuit.is_available():
                raise RuntimeError(f"Circuit open for {agent} — too many failures")

            try:
                result = await fn(*args, **kwargs)
                circuit.record_success()
                return result
            except Exception as exc:
                last_exc = exc
                circuit.record_failure()
                self._log_failure("retry", agent, str(args[0] if args else ""), exc)

                if attempt < MAX_RETRIES - 1:
                    wait = min(BASE_BACKOFF * (2 ** attempt), MAX_BACKOFF)
                    logger.warning(
                        "Retry %d/%d for %s in %.1fs: %s",
                        attempt + 1, MAX_RETRIES, agent, wait, exc,
                    )
                    await asyncio.sleep(wait)

        raise last_exc

    async def execute(
        self,
        task: str,
        agent_key: str,
        run_fn,
        simplify_on_fail: bool = True,
    ) -> str:
        """Execute task with full recovery chain.

        Strategy order:
        1. Primary model with retry + backoff
        2. Fallback model (same agent)
        3. Alternative agent
        4. Simplified prompt
        5. Return partial error message

        Args:
            task: Task to execute.
            agent_key: Preferred agent.
            run_fn: Async function(model, task, agent_key) → str.
            simplify_on_fail: Whether to attempt prompt simplification.

        Returns:
            Result string (never raises — always returns something).
        """
        from core.agent_registry import get_model as _get_model

        primary_model = _get_model(agent_key)
        if not primary_model:
            return f"Unknown agent: {agent_key}"

        # 1. Primary with retry
        try:
            result = await self._retry_with_backoff(
                run_fn, agent_key, primary_model, task, agent_key
            )
            logger.info("Strategy 1 (primary) succeeded for %s", agent_key)
            return result
        except Exception as exc:
            self._log_failure("primary", agent_key, task, exc)
            logger.warning("Primary failed for %s: %s", agent_key, exc)

        # 2. Fallback model
        fallback_model = _get_model(agent_key, use_fallback=True)
        if fallback_model and fallback_model != primary_model:
            try:
                result = await run_fn(fallback_model, task, agent_key)
                logger.info("Strategy 2 (fallback model) succeeded for %s", agent_key)
                return result
            except Exception as exc:
                self._log_failure("fallback_model", agent_key, task, exc)
                logger.warning("Fallback model failed: %s", exc)

        # 3. Alternative agent
        alt_map = {
            "coding": "debug",
            "debug": "coding",
            "math": "coding",
            "architect": "mentor",
            "mentor": "architect",
            "analyst": "coding",
            "vision": "coding",
        }
        alt_key = alt_map.get(agent_key)
        if alt_key:
            alt_model = _get_model(alt_key)
            if alt_model:
                try:
                    result = await run_fn(alt_model, task, alt_key)
                    logger.info("Strategy 3 (alt agent %s) succeeded", alt_key)
                    return result
                except Exception as exc:
                    self._log_failure("alternative_agent", agent_key, task, exc)
                    logger.warning("Alternative agent %s failed: %s", alt_key, exc)

        # 4. Simplified prompt
        if simplify_on_fail and len(task) > 200:
            simplified = task[:200] + "\n\n[Simplified for recovery — answer concisely]"
            for model in [primary_model, fallback_model]:
                if model:
                    try:
                        result = await run_fn(model, simplified, agent_key)
                        logger.info("Strategy 4 (simplified) succeeded")
                        return result
                    except Exception as exc:
                        self._log_failure("simplified", agent_key, task, exc)

        # 5. Human escalation — return useful partial info
        logger.error("All recovery strategies exhausted for %s", agent_key)
        return (
            f"All recovery strategies failed for agent [{agent_key}].\n"
            f"Please check Ollama is running (`ollama list`) and API keys are set in .env.\n"
            f"Task: {task[:200]}"
        )

    def circuit_status(self) -> str:
        """Return formatted circuit breaker status for all agents.

        Returns:
            HTML-formatted status string for Telegram.
        """
        if not self._circuits:
            return "No circuit breakers active."
        lines = ["<b>Circuit Breakers</b>\n"]
        for name, cb in self._circuits.items():
            icon = {"closed": "✅", "open": "🔴", "half_open": "🟡"}[cb.state.value]
            lines.append(f"  {icon} <b>{name}</b>: {cb.state.value} (failures: {cb.failure_count})")
        return "\n".join(lines)

    def failure_summary(self, last_n: int = 20) -> str:
        """Return a summary of recent failures.

        Args:
            last_n: Number of recent failures to summarize.

        Returns:
            Formatted summary string.
        """
        recent = self._failures[-last_n:]
        if not recent:
            return "No failures recorded."
        by_agent: dict[str, int] = defaultdict(int)
        by_type: dict[str, int] = defaultdict(int)
        for f in recent:
            by_agent[f.agent] += 1
            by_type[f.error_type] += 1

        lines = [f"<b>Last {len(recent)} failures:</b>"]
        lines.append("By agent: " + ", ".join(f"{k}={v}" for k, v in by_agent.items()))
        lines.append("By type: " + ", ".join(f"{k}={v}" for k, v in by_type.items()))
        return "\n".join(lines)


# Singleton
_recovery: ErrorRecoveryManager | None = None


def get_recovery() -> ErrorRecoveryManager:
    """Return global ErrorRecoveryManager singleton."""
    global _recovery
    if _recovery is None:
        _recovery = ErrorRecoveryManager()
    return _recovery
