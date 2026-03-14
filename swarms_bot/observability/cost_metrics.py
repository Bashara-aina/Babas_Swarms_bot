"""Cost metrics collector — tracks LLM spend with per-agent breakdowns.

Integrates with both BudgetManager (enforcement) and Prometheus
(visualization). Provides real-time cost tracking without external
dependencies beyond what's already in the project.
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class CostSnapshot:
    """Point-in-time cost snapshot for trend analysis."""

    timestamp: float
    daily_cost: float
    hourly_rate: float
    top_agent: str
    top_model: str
    request_count: int


class CostMetricsCollector:
    """Collect and aggregate cost metrics across all agent executions.

    Provides:
    - Real-time cost burn rate ($/hour)
    - Per-agent cost breakdown
    - Per-model cost breakdown
    - Trend snapshots for dashboard display
    - Alert thresholds for cost spikes
    """

    def __init__(
        self,
        alert_hourly_rate: float = 5.0,
        snapshot_interval_minutes: int = 15,
    ) -> None:
        self._alert_hourly_rate = alert_hourly_rate
        self._snapshot_interval = snapshot_interval_minutes * 60

        # Running totals
        self._total_cost: float = 0.0
        self._total_tokens: int = 0
        self._total_requests: int = 0

        # Per-agent tracking
        self._agent_costs: Dict[str, float] = defaultdict(float)
        self._agent_requests: Dict[str, int] = defaultdict(int)
        self._agent_tokens: Dict[str, int] = defaultdict(int)
        self._agent_latency_sum: Dict[str, float] = defaultdict(float)

        # Per-model tracking
        self._model_costs: Dict[str, float] = defaultdict(float)
        self._model_requests: Dict[str, int] = defaultdict(int)

        # Time series for rate calculation
        self._recent_costs: List[tuple[float, float]] = []  # (timestamp, cost)
        self._snapshots: List[CostSnapshot] = []
        self._last_snapshot: float = 0.0

    def record(
        self,
        agent_name: str,
        model: str,
        cost_usd: float,
        tokens_used: int = 0,
        latency_ms: int = 0,
    ) -> Optional[str]:
        """Record a cost event. Returns alert message if threshold exceeded.

        Args:
            agent_name: Agent that incurred the cost.
            model: LLM model string.
            cost_usd: Cost in USD.
            tokens_used: Total tokens consumed.
            latency_ms: Execution latency.

        Returns:
            Alert message string if hourly rate exceeds threshold, else None.
        """
        now = time.time()

        self._total_cost += cost_usd
        self._total_tokens += tokens_used
        self._total_requests += 1

        self._agent_costs[agent_name] += cost_usd
        self._agent_requests[agent_name] += 1
        self._agent_tokens[agent_name] += tokens_used
        self._agent_latency_sum[agent_name] += latency_ms

        self._model_costs[model] += cost_usd
        self._model_requests[model] += 1

        self._recent_costs.append((now, cost_usd))

        # Prune entries older than 1 hour
        cutoff = now - 3600
        self._recent_costs = [
            (t, c) for t, c in self._recent_costs if t >= cutoff
        ]

        # Take snapshot if interval elapsed
        if now - self._last_snapshot >= self._snapshot_interval:
            self._take_snapshot(now)

        # Check for cost spike
        hourly_rate = self.get_hourly_rate()
        if hourly_rate > self._alert_hourly_rate:
            return (
                f"Cost alert: ${hourly_rate:.2f}/hr exceeds "
                f"${self._alert_hourly_rate:.2f}/hr threshold"
            )

        return None

    def get_hourly_rate(self) -> float:
        """Calculate current hourly cost burn rate."""
        if not self._recent_costs:
            return 0.0

        now = time.time()
        one_hour_ago = now - 3600
        recent = [c for t, c in self._recent_costs if t >= one_hour_ago]
        return sum(recent)

    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive cost summary."""
        hourly_rate = self.get_hourly_rate()

        # Top agent by cost
        top_agent = max(self._agent_costs, key=self._agent_costs.get) if self._agent_costs else "none"
        top_model = max(self._model_costs, key=self._model_costs.get) if self._model_costs else "none"

        return {
            "total_cost_usd": round(self._total_cost, 4),
            "total_tokens": self._total_tokens,
            "total_requests": self._total_requests,
            "hourly_rate_usd": round(hourly_rate, 4),
            "projected_daily_usd": round(hourly_rate * 24, 2),
            "top_agent": top_agent,
            "top_model": top_model,
            "by_agent": {
                agent: {
                    "cost_usd": round(cost, 4),
                    "requests": self._agent_requests[agent],
                    "tokens": self._agent_tokens[agent],
                    "avg_latency_ms": round(
                        self._agent_latency_sum[agent] / self._agent_requests[agent], 0
                    ) if self._agent_requests[agent] else 0,
                }
                for agent, cost in sorted(
                    self._agent_costs.items(), key=lambda x: x[1], reverse=True
                )
            },
            "by_model": {
                model: {
                    "cost_usd": round(cost, 4),
                    "requests": self._model_requests[model],
                }
                for model, cost in sorted(
                    self._model_costs.items(), key=lambda x: x[1], reverse=True
                )
            },
        }

    def format_dashboard_html(self) -> str:
        """Format cost metrics as HTML for Telegram display."""
        summary = self.get_summary()
        hourly = summary["hourly_rate_usd"]
        daily_proj = summary["projected_daily_usd"]

        # Rate warning indicator
        rate_icon = "🟢" if hourly < 1.0 else "🟡" if hourly < 3.0 else "🔴"

        lines = [
            "<b>Cost Metrics Dashboard</b>\n",
            f"Total: ${summary['total_cost_usd']:.4f} | "
            f"Requests: {summary['total_requests']} | "
            f"Tokens: {summary['total_tokens']:,}",
            f"{rate_icon} Rate: ${hourly:.4f}/hr → ~${daily_proj:.2f}/day",
        ]

        if summary["by_agent"]:
            lines.append("\n<b>By Agent:</b>")
            for agent, data in list(summary["by_agent"].items())[:8]:
                lines.append(
                    f"  <code>{agent:12s}</code> "
                    f"${data['cost_usd']:.4f} "
                    f"({data['requests']} reqs, "
                    f"avg {data['avg_latency_ms']:.0f}ms)"
                )

        if summary["by_model"]:
            lines.append("\n<b>By Model:</b>")
            for model, data in list(summary["by_model"].items())[:5]:
                short = model.split("/")[-1][:25]
                lines.append(
                    f"  <code>{short:25s}</code> "
                    f"${data['cost_usd']:.4f} ({data['requests']} reqs)"
                )

        return "\n".join(lines)

    def _take_snapshot(self, now: float) -> None:
        """Take a point-in-time snapshot for trend analysis."""
        top_agent = max(self._agent_costs, key=self._agent_costs.get) if self._agent_costs else "none"
        top_model = max(self._model_costs, key=self._model_costs.get) if self._model_costs else "none"

        self._snapshots.append(CostSnapshot(
            timestamp=now,
            daily_cost=self._total_cost,
            hourly_rate=self.get_hourly_rate(),
            top_agent=top_agent,
            top_model=top_model,
            request_count=self._total_requests,
        ))

        # Keep last 96 snapshots (24 hours at 15min intervals)
        if len(self._snapshots) > 96:
            self._snapshots = self._snapshots[-96:]

        self._last_snapshot = now
