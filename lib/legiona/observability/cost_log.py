"""
lib/legiona/observability/cost_log.py
Simple ¥ cost logger. Appends to memory/cost_log.jsonl.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

COST_LOG = Path("lib/legiona/memory/cost_log.jsonl")


# ¥ per 1K tokens (MiniMax M3)
_IN_JPY_PER_1K = 0.04
_OUT_JPY_PER_1K = 0.12


def log_usage(prompt_tokens: int, completion_tokens: int, cached_tokens: int = 0) -> None:
    """Convert token usage to JPY and append to cost_log.jsonl."""
    input_jpy = (prompt_tokens / 1000) * _IN_JPY_PER_1K
    output_jpy = (completion_tokens / 1000) * _OUT_JPY_PER_1K
    record = {
        "ts": datetime.now(UTC).isoformat(),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "cached_tokens": cached_tokens,
        "input_jpy": round(input_jpy, 4),
        "output_jpy": round(output_jpy, 4),
        "total_jpy": round(input_jpy + output_jpy, 4),
    }
    try:
        with open(COST_LOG, "a") as f:
            f.write(json.dumps(record) + "\n")
    except Exception:
        pass  # never fail a call due to logging


def today_total_jpy() -> float:
    """Return today's total M2.7 cost in ¥ from cost_log.jsonl."""
    if not COST_LOG.exists():
        return 0.0
    today = datetime.now(UTC).date().isoformat()
    total = 0.0
    for line in COST_LOG.read_text().splitlines():
        try:
            r = json.loads(line)
            if r.get("ts", "").startswith(today):
                total += r.get("total_jpy", 0.0)
        except Exception:
            pass
    return round(total, 2)


def current_month_total_jpy() -> float:
    """Return the current calendar month's total M2.7 cost in ¥."""
    if not COST_LOG.exists():
        return 0.0
    month_prefix = datetime.now(UTC).strftime("%Y-%m")
    total = 0.0
    for line in COST_LOG.read_text().splitlines():
        try:
            r = json.loads(line)
            if r.get("ts", "").startswith(month_prefix):
                total += r.get("total_jpy", 0.0)
        except Exception:
            pass
    return round(total, 2)


def monthly_projection_jpy() -> tuple[float, int, float]:
    """
    Project monthly spend from cost_log.jsonl.
    Returns (month_total_jpy, days_elapsed, projected_monthly_jpy).
    """
    import calendar
    now = datetime.now(UTC)
    month_total = current_month_total_jpy()
    day_of_month = now.day
    days_in_month = calendar.monthrange(now.year, now.month)[1]
    days_elapsed = max(day_of_month, 1)
    daily_avg = month_total / days_elapsed
    projected = daily_avg * days_in_month
    return (round(month_total, 2), days_elapsed, round(projected, 2))
