"""SlopMonitor — Sliding window slop detection and alerting.

Tracks rejection rate, guard hits, and patterns over a sliding time window.
Designed to integrate with existing swarms_bot/observability/ patterns.

Usage:
    monitor = SlopMonitor(window_seconds=300)  # 5-minute window
    monitor.log_event("reject", guard="format", reason="filler_phrase")
    stats = monitor.get_stats()
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

from legion.anti_slop.core import _ANTI_SLOP_DIR

logger = logging.getLogger(__name__)

# ── Event types ────────────────────────────────────────────────────────────────

EventType = Literal[
    "reject", "pass", "needs_improvement", "guard_format", "guard_package", "guard_critique", "guard_confidence"
]


@dataclass
class SlopEvent:
    """A single anti-slop event."""

    event_type: EventType
    guard: str | None
    reason: str | None
    latency_ms: float
    timestamp: float = field(default_factory=time.time)


@dataclass
class SlopWindowStats:
    """Statistics for a sliding time window."""

    window_seconds: int
    total_events: int = 0
    rejects: int = 0
    passes: int = 0
    needs_improvement: int = 0
    guard_format_hits: int = 0
    guard_package_hits: int = 0
    guard_critique_hits: int = 0
    guard_confidence_hits: int = 0
    avg_latency_ms: float = 0.0
    rejection_rate: float = 0.0
    events: list[SlopEvent] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "window_seconds": self.window_seconds,
            "total_events": self.total_events,
            "rejects": self.rejects,
            "passes": self.passes,
            "needs_improvement": self.needs_improvement,
            "rejection_rate": f"{self.rejection_rate:.1%}",
            "guard_format_hits": self.guard_format_hits,
            "guard_package_hits": self.guard_package_hits,
            "guard_critique_hits": self.guard_critique_hits,
            "guard_confidence_hits": self.guard_confidence_hits,
            "avg_latency_ms": f"{self.avg_latency_ms:.1f}",
        }


# ── SlopMonitor ────────────────────────────────────────────────────────────────


class SlopMonitor:
    """Sliding window slop detection monitor.

    Tracks anti-slop events over a configurable time window.
    Integrates with existing observability patterns.

    Attributes:
        window_seconds: Size of the sliding window in seconds.
        max_events: Maximum events to store in memory.

    Example:
        monitor = SlopMonitor(window_seconds=300)
        monitor.log_event("reject", guard="format", reason="filler")
        stats = monitor.get_stats()
    """

    def __init__(
        self,
        window_seconds: int = 300,
        max_events: int = 10000,
    ) -> None:
        self.window_seconds = window_seconds
        self.max_events = max_events
        self._events: deque[SlopEvent] = deque(maxlen=max_events)
        self._guard_counts: dict[str, int] = defaultdict(int)
        self._reason_counts: dict[str, int] = defaultdict(int)
        self._lock = asyncio.Lock()

    def log_event(
        self,
        event_type: EventType,
        guard: str | None = None,
        reason: str | None = None,
        latency_ms: float = 0.0,
    ) -> None:
        """Log an anti-slop event.

        Args:
            event_type: Type of event (reject, pass, needs_improvement).
            guard: Which guard triggered (format, package, critique, confidence).
            reason: Specific reason for the event.
            latency_ms: Latency of the quality gate.
        """
        event = SlopEvent(
            event_type=event_type,
            guard=guard,
            reason=reason,
            latency_ms=latency_ms,
        )
        self._events.append(event)
        if guard:
            self._guard_counts[guard] += 1
        if reason:
            self._reason_counts[reason] += 1

        # Also log to file asynchronously
        asyncio.create_task(self._append_to_log(event))

    async def _append_to_log(self, event: SlopEvent) -> None:
        """Append event to the persistent log file."""
        _ANTI_SLOP_DIR.mkdir(parents=True, exist_ok=True)
        log_path = _ANTI_SLOP_DIR / "events.jsonl"

        event_dict = {
            "event_type": event.event_type,
            "guard": event.guard,
            "reason": event.reason,
            "latency_ms": event.latency_ms,
            "timestamp": event.timestamp,
            "datetime": datetime.fromtimestamp(event.timestamp).isoformat(),
        }

        try:
            async with asyncio.Lock():
                with open(log_path, "a") as f:
                    f.write(json.dumps(event_dict) + "\n")
        except OSError as e:
            logger.warning("Failed to write slop event to log: %s", e)

    def get_stats(self) -> SlopWindowStats:
        """Get statistics for the current sliding window.

        Returns:
            SlopWindowStats with counts and rates for the window.
        """
        now = time.time()
        window_start = now - self.window_seconds

        # Filter events to window
        window_events = [e for e in self._events if e.timestamp >= window_start]

        if not window_events:
            return SlopWindowStats(window_seconds=self.window_seconds)

        # Calculate stats
        rejects = sum(1 for e in window_events if e.event_type == "reject")
        passes = sum(1 for e in window_events if e.event_type == "pass")
        needs_improvement = sum(1 for e in window_events if e.event_type == "needs_improvement")

        guard_format = sum(1 for e in window_events if e.guard == "format")
        guard_package = sum(1 for e in window_events if e.guard == "package")
        guard_critique = sum(1 for e in window_events if e.guard == "critique")
        guard_confidence = sum(1 for e in window_events if e.guard == "confidence")

        total_latency = sum(e.latency_ms for e in window_events)
        avg_latency = total_latency / len(window_events)

        total = len(window_events)
        rejection_rate = rejects / total if total > 0 else 0.0

        return SlopWindowStats(
            window_seconds=self.window_seconds,
            total_events=total,
            rejects=rejects,
            passes=passes,
            needs_improvement=needs_improvement,
            guard_format_hits=guard_format,
            guard_package_hits=guard_package,
            guard_critique_hits=guard_critique,
            guard_confidence_hits=guard_confidence,
            avg_latency_ms=avg_latency,
            rejection_rate=rejection_rate,
            events=list(window_events),
        )

    def get_guard_breakdown(self) -> dict[str, int]:
        """Get breakdown of events by guard."""
        return dict(self._guard_counts)

    def get_top_reasons(self, n: int = 5) -> list[tuple[str, int]]:
        """Get top N rejection reasons."""
        sorted_reasons = sorted(self._reason_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_reasons[:n]

    def reset(self) -> None:
        """Clear all events and counters."""
        self._events.clear()
        self._guard_counts.clear()
        self._reason_counts.clear()

    async def load_historical(self, hours: int = 24) -> int:
        """Load historical events from the log file.

        Args:
            hours: Number of hours to look back.

        Returns:
            Number of events loaded.
        """
        log_path = _ANTI_SLOP_DIR / "events.jsonl"
        if not log_path.exists():
            return 0

        cutoff = time.time() - (hours * 3600)
        count = 0

        try:
            with open(log_path) as f:
                for line in f:
                    try:
                        event_dict = json.loads(line)
                        if event_dict.get("timestamp", 0) >= cutoff:
                            event = SlopEvent(
                                event_type=event_dict["event_type"],
                                guard=event_dict.get("guard"),
                                reason=event_dict.get("reason"),
                                latency_ms=event_dict.get("latency_ms", 0.0),
                                timestamp=event_dict.get("timestamp", 0.0),
                            )
                            self._events.append(event)
                            if event.guard:
                                self._guard_counts[event.guard] += 1
                            if event.reason:
                                self._reason_counts[event.reason] += 1
                            count += 1
                    except (json.JSONDecodeError, KeyError):
                        continue
        except OSError as e:
            logger.warning("Failed to load historical slop events: %s", e)

        return count


# ── Global monitor instance ────────────────────────────────────────────────────

_slop_monitor: SlopMonitor | None = None


def get_slop_monitor() -> SlopMonitor:
    """Get the global SlopMonitor instance."""
    global _slop_monitor
    if _slop_monitor is None:
        _slop_monitor = SlopMonitor()
    return _slop_monitor


def reset_monitor() -> None:
    """Reset the global monitor."""
    global _slop_monitor
    if _slop_monitor is not None:
        _slop_monitor.reset()
    _slop_monitor = None
