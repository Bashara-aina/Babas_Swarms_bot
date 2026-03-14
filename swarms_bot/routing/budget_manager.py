"""Budget manager — per-user cost tracking and enforcement.

Tracks LLM API spend per user and enforces configurable daily limits.
Uses in-memory storage (suitable for single-user Telegram bot).
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Default budget limits
DEFAULT_DAILY_LIMIT_USD = 50.0
DEFAULT_MONTHLY_LIMIT_USD = 500.0


@dataclass
class CostEntry:
    """A single cost record."""

    timestamp: float
    agent: str
    model: str
    cost_usd: float
    tokens_in: int = 0
    tokens_out: int = 0
    task_type: str = ""


class BudgetManager:
    """Track and enforce LLM API spending limits.

    Designed for single-user Telegram bot — stores everything in memory.
    For multi-user, swap storage to Redis/SQLite.
    """

    def __init__(
        self,
        daily_limit: float = DEFAULT_DAILY_LIMIT_USD,
        monthly_limit: float = DEFAULT_MONTHLY_LIMIT_USD,
    ) -> None:
        self.daily_limit = daily_limit
        self.monthly_limit = monthly_limit
        self._entries: List[CostEntry] = []

    def record_cost(
        self,
        agent: str,
        model: str,
        cost_usd: float,
        tokens_in: int = 0,
        tokens_out: int = 0,
        task_type: str = "",
    ) -> None:
        """Record a cost event.

        Args:
            agent: Agent key that incurred the cost.
            model: litellm model string.
            cost_usd: Cost in USD.
            tokens_in: Input tokens used.
            tokens_out: Output tokens used.
            task_type: Type of task (for analytics).
        """
        self._entries.append(CostEntry(
            timestamp=time.time(),
            agent=agent,
            model=model,
            cost_usd=cost_usd,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            task_type=task_type,
        ))

        # Keep max 10000 entries
        if len(self._entries) > 10000:
            self._entries = self._entries[-10000:]

    def check_budget(self) -> Dict[str, Any]:
        """Check if spending is within limits.

        Returns:
            Dict with 'allowed', 'daily_spent', 'monthly_spent',
            'daily_remaining', 'monthly_remaining'.
        """
        now = time.time()
        today_start = datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        ).timestamp()
        month_start = datetime.now().replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        ).timestamp()

        daily_spent = sum(
            e.cost_usd for e in self._entries
            if e.timestamp >= today_start
        )
        monthly_spent = sum(
            e.cost_usd for e in self._entries
            if e.timestamp >= month_start
        )

        daily_ok = daily_spent < self.daily_limit
        monthly_ok = monthly_spent < self.monthly_limit

        return {
            "allowed": daily_ok and monthly_ok,
            "daily_spent": round(daily_spent, 4),
            "monthly_spent": round(monthly_spent, 4),
            "daily_remaining": round(max(0, self.daily_limit - daily_spent), 4),
            "monthly_remaining": round(max(0, self.monthly_limit - monthly_spent), 4),
            "daily_limit": self.daily_limit,
            "monthly_limit": self.monthly_limit,
        }

    def get_cost_breakdown(self, period: str = "day") -> Dict[str, Any]:
        """Get cost breakdown by agent and model.

        Args:
            period: 'day', 'week', or 'month'.

        Returns:
            Dict with breakdowns by agent, model, and task type.
        """
        now = time.time()
        if period == "day":
            cutoff = datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            ).timestamp()
        elif period == "week":
            cutoff = now - 7 * 86400
        else:
            cutoff = datetime.now().replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            ).timestamp()

        entries = [e for e in self._entries if e.timestamp >= cutoff]

        by_agent: Dict[str, float] = {}
        by_model: Dict[str, float] = {}
        by_task_type: Dict[str, float] = {}
        total_tokens = 0

        for e in entries:
            by_agent[e.agent] = by_agent.get(e.agent, 0) + e.cost_usd
            by_model[e.model] = by_model.get(e.model, 0) + e.cost_usd
            by_task_type[e.task_type] = (
                by_task_type.get(e.task_type, 0) + e.cost_usd
            )
            total_tokens += e.tokens_in + e.tokens_out

        total_cost = sum(e.cost_usd for e in entries)

        return {
            "period": period,
            "total_cost": round(total_cost, 4),
            "total_requests": len(entries),
            "total_tokens": total_tokens,
            "by_agent": {k: round(v, 4) for k, v in sorted(
                by_agent.items(), key=lambda x: x[1], reverse=True
            )},
            "by_model": {k: round(v, 4) for k, v in sorted(
                by_model.items(), key=lambda x: x[1], reverse=True
            )},
            "by_task_type": {k: round(v, 4) for k, v in sorted(
                by_task_type.items(), key=lambda x: x[1], reverse=True
            )},
        }

    def format_budget_html(self) -> str:
        """Format budget status as HTML for Telegram."""
        budget = self.check_budget()
        breakdown = self.get_cost_breakdown("day")

        icon = "✅" if budget["allowed"] else "🚨"

        lines = [
            f"{icon} <b>Budget Status</b>\n",
            f"Today: ${budget['daily_spent']:.4f} / ${budget['daily_limit']:.2f}"
            f" (${budget['daily_remaining']:.4f} left)",
            f"Month: ${budget['monthly_spent']:.4f} / ${budget['monthly_limit']:.2f}"
            f" (${budget['monthly_remaining']:.4f} left)",
            f"Requests today: {breakdown['total_requests']}",
            f"Tokens today: {breakdown['total_tokens']:,}",
        ]

        if breakdown["by_agent"]:
            lines.append("\n<b>By agent:</b>")
            for agent, cost in list(breakdown["by_agent"].items())[:5]:
                lines.append(f"  <code>{agent}</code>: ${cost:.4f}")

        return "\n".join(lines)
