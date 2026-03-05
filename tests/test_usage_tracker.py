# /home/newadmin/swarm-bot/tests/test_usage_tracker.py
"""Tests for optimization/usage_tracker.py"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from collections import defaultdict
from optimization.usage_tracker import UsageTracker, DAILY_LIMITS


def _tracker() -> UsageTracker:
    """Return a fresh in-memory tracker (no Redis)."""
    t = UsageTracker.__new__(UsageTracker)
    t._redis = None
    t._memory = defaultdict(lambda: defaultdict(float))
    return t


def test_record_free_model():
    t = _tracker()
    alert = t.record("ollama_chat/gemma3:12b", input_tokens=1000, output_tokens=500)
    assert alert is None
    stats = t.get_today("ollama_chat/gemma3:12b")
    assert stats["requests"] == 1
    assert stats["cost_usd"] == 0.0


def test_record_paid_model():
    t = _tracker()
    t.record("gemini/gemini-3.1-pro", input_tokens=1_000_000, output_tokens=1_000_000)
    stats = t.get_today("gemini/gemini-3.1-pro")
    # input: $0.035, output: $0.105 → total $0.14
    assert abs(stats["cost_usd"] - 0.14) < 0.0001


def test_daily_limit_alert():
    t = _tracker()
    model = "zai/glm-4"
    limit = DAILY_LIMITS[model]
    # Simulate 85% usage
    t.record(model, requests=int(limit * 0.85))
    stats = t.get_today(model)
    alert = t.record(model, requests=0)   # just trigger check
    # The last record call that crosses 80% should return alert
    # Re-trigger by reaching 80%
    t2 = _tracker()
    alert2 = t2.record(model, requests=int(limit * 0.81))
    assert alert2 is not None
    assert "Rate limit warning" in alert2 or "%" in alert2


def test_daily_report_empty():
    t = _tracker()
    report = t.daily_report()
    assert "No API usage" in report


def test_daily_report_with_usage():
    t = _tracker()
    t.record("zai/glm-4", input_tokens=100, output_tokens=50, requests=5)
    report = t.daily_report()
    assert "glm-4" in report
    assert "5" in report


def test_unknown_model_no_crash():
    t = _tracker()
    alert = t.record("unknown/model-x", input_tokens=500, output_tokens=200)
    assert alert is None   # no limit configured → no alert
    stats = t.get_today("unknown/model-x")
    assert stats["cost_usd"] == 0.0   # no pricing → free
