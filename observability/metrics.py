# /home/newadmin/swarm-bot/observability/metrics.py
"""Prometheus metrics + structured JSON logging for LegionSwarm.

Exports metrics on http://localhost:8001/metrics (Prometheus scrape endpoint).
Structured logs emitted as JSON to swarm-bot.log for log aggregation.

Metrics:
- swarm_requests_total{agent, status}
- swarm_latency_seconds{agent}
- swarm_cache_hits_total{agent}
- swarm_cache_misses_total{agent}
- swarm_errors_total{agent, error_type}
- swarm_active_threads (gauge)
"""

from __future__ import annotations

import json
import logging
import time
from contextlib import asynccontextmanager
from typing import AsyncIterator

logger = logging.getLogger(__name__)

# ── Prometheus Setup ───────────────────────────────────────────────────────────

_prometheus_available = False
_counters: dict = {}
_histograms: dict = {}
_gauges: dict = {}


def _init_prometheus() -> None:
    """Initialise Prometheus metrics (lazy, fails gracefully)."""
    global _prometheus_available, _counters, _histograms, _gauges

    try:
        from prometheus_client import Counter, Histogram, Gauge, start_http_server

        _counters["requests"] = Counter(
            "swarm_requests_total",
            "Total requests per agent",
            ["agent", "status"],
        )
        _counters["cache_hits"] = Counter(
            "swarm_cache_hits_total",
            "Semantic cache hits per agent",
            ["agent"],
        )
        _counters["cache_misses"] = Counter(
            "swarm_cache_misses_total",
            "Semantic cache misses per agent",
            ["agent"],
        )
        _counters["errors"] = Counter(
            "swarm_errors_total",
            "Errors per agent and type",
            ["agent", "error_type"],
        )
        _histograms["latency"] = Histogram(
            "swarm_latency_seconds",
            "Request latency per agent",
            ["agent"],
            buckets=[0.5, 1, 2, 5, 10, 20, 30, 60, 120],
        )
        _gauges["active_threads"] = Gauge(
            "swarm_active_threads",
            "Number of active conversation threads",
        )
        _gauges["cache_hit_rate"] = Gauge(
            "swarm_cache_hit_rate",
            "Semantic cache hit rate (rolling)",
            ["agent"],
        )

        start_http_server(8001)
        _prometheus_available = True
        logger.info("Prometheus metrics server started on :8001")
    except ImportError:
        logger.info("prometheus-client not installed — metrics disabled")
    except OSError as exc:
        logger.warning("Could not start Prometheus server: %s", exc)


# Initialise on module load
_init_prometheus()


# ── Structured Logger ──────────────────────────────────────────────────────────

class StructuredLogger:
    """JSON-formatted structured logger for machine-parseable logs."""

    def __init__(self, name: str) -> None:
        self._log = logging.getLogger(name)

    def _emit(self, level: str, event: str, **kwargs) -> None:
        entry = {
            "ts": time.time(),
            "level": level,
            "event": event,
            **{k: v for k, v in kwargs.items() if v is not None},
        }
        msg = json.dumps(entry, default=str)
        getattr(self._log, level.lower(), self._log.info)(msg)

    def info(self, event: str, **kwargs) -> None:
        self._emit("INFO", event, **kwargs)

    def warning(self, event: str, **kwargs) -> None:
        self._emit("WARNING", event, **kwargs)

    def error(self, event: str, **kwargs) -> None:
        self._emit("ERROR", event, **kwargs)


slog = StructuredLogger("swarm.structured")


# ── Metric Recording Functions ─────────────────────────────────────────────────

def record_request(agent: str, status: str, latency: float) -> None:
    """Record a completed request with status and latency.

    Args:
        agent: Agent key that handled the request.
        status: 'success' or 'error'.
        latency: Wall-clock time in seconds.
    """
    if _prometheus_available:
        _counters["requests"].labels(agent=agent, status=status).inc()
        _histograms["latency"].labels(agent=agent).observe(latency)

    slog.info("request_complete", agent=agent, status=status, latency_s=round(latency, 2))


def record_cache_event(agent: str, hit: bool) -> None:
    """Record a semantic cache hit or miss.

    Args:
        agent: Agent key.
        hit: True if cache returned a result.
    """
    if _prometheus_available:
        if hit:
            _counters["cache_hits"].labels(agent=agent).inc()
        else:
            _counters["cache_misses"].labels(agent=agent).inc()

    slog.info("cache_event", agent=agent, hit=hit)


def record_error(agent: str, error_type: str) -> None:
    """Record an agent execution error.

    Args:
        agent: Agent key.
        error_type: Exception class name.
    """
    if _prometheus_available:
        _counters["errors"].labels(agent=agent, error_type=error_type).inc()

    slog.error("agent_error", agent=agent, error_type=error_type)


def set_active_threads(count: int) -> None:
    """Update the active threads gauge.

    Args:
        count: Current number of active threads.
    """
    if _prometheus_available:
        _gauges["active_threads"].set(count)


# ── Async Context Manager for Tracing ─────────────────────────────────────────

@asynccontextmanager
async def trace_agent(agent: str) -> AsyncIterator[None]:
    """Async context manager that times agent execution and records metrics.

    Usage:
        async with trace_agent("coding"):
            result = await run_task(...)

    Args:
        agent: Agent key being executed.

    Yields:
        Nothing — used for timing side effects.
    """
    start = time.monotonic()
    status = "success"
    try:
        yield
    except Exception as exc:
        status = "error"
        record_error(agent, type(exc).__name__)
        raise
    finally:
        latency = time.monotonic() - start
        record_request(agent, status, latency)


# ── Human-Readable Stats ───────────────────────────────────────────────────────

def format_stats(cache_stats: dict, failure_summary: str, thread_count: int) -> str:
    """Format a human-readable stats report for Telegram.

    Args:
        cache_stats: Dict from SemanticCache.stats().
        failure_summary: String from ErrorRecoveryManager.failure_summary().
        thread_count: Number of active threads.

    Returns:
        HTML-formatted stats string.
    """
    hit_rate_pct = round(cache_stats.get("hit_rate", 0) * 100, 1)
    cache_size = cache_stats.get("size", 0)
    total_queries = cache_stats.get("total_queries", 0)
    total_hits = cache_stats.get("total_hits", 0)

    lines = [
        "<b>LegionSwarm System Stats</b>\n",
        f"<b>Cache:</b> {total_hits}/{total_queries} hits ({hit_rate_pct}%) | {cache_size} entries",
        f"<b>Threads:</b> {thread_count} active",
        f"<b>Metrics:</b> {'enabled :8001' if _prometheus_available else 'disabled'}",
        "",
        failure_summary,
    ]
    return "\n".join(lines)
