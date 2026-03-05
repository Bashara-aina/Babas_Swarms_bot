# /home/newadmin/swarm-bot/tests/test_feedback_learner.py
"""Tests for optimization/feedback_learner.py"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from optimization.feedback_learner import FeedbackLearner, POSITIVE, NEGATIVE


def _learner() -> FeedbackLearner:
    """Return a fresh in-memory learner (no Redis)."""
    l = FeedbackLearner.__new__(FeedbackLearner)
    l._redis = None
    from collections import defaultdict
    l._scores = defaultdict(lambda: {"pos": 0, "neg": 0})
    l._recent = []
    l._pending = {}
    return l


def test_register_and_record_positive():
    l = _learner()
    fid = l.register_response("coding", "write a sort function")
    assert fid in l._pending
    result = l.record(fid, POSITIVE)
    assert "positive" in result
    assert fid not in l._pending


def test_register_and_record_negative():
    l = _learner()
    fid = l.register_response("debug", "fix my pytorch error")
    result = l.record(fid, NEGATIVE, comment="bad answer")
    assert "negative" in result


def test_unknown_fid():
    l = _learner()
    result = l.record("badid", POSITIVE)
    assert "Unknown" in result


def test_score_accumulation():
    l = _learner()
    for _ in range(3):
        fid = l.register_response("vision", "analyze screen")
        l.record(fid, POSITIVE)
    fid = l.register_response("vision", "analyze screen 2")
    l.record(fid, NEGATIVE)

    score = l.get_agent_score("vision")
    assert score["pos"] == 3
    assert score["neg"] == 1
    assert score["total"] == 4
    assert score["rate"] == 75.0


def test_agent_weights_neutral_with_little_data():
    l = _learner()
    weights = l.agent_weights()
    # With no data, all should be 1.0
    for w in weights.values():
        assert w == 1.0


def test_agent_weights_adjust_with_data():
    l = _learner()
    # 10 positives → rate=100% → weight=1.5
    for _ in range(10):
        l.record_by_agent("coding", "task", POSITIVE)
    weights = l.agent_weights()
    assert weights.get("coding", 0) > 1.0


def test_recent_negatives():
    l = _learner()
    for i in range(3):
        l.record_by_agent("math", f"task {i}", NEGATIVE)
    l.record_by_agent("math", "good task", POSITIVE)

    negs = l.recent_negatives(limit=5)
    assert len(negs) == 3
    assert all(e.rating == NEGATIVE for e in negs)


def test_summary_report_no_data():
    l = _learner()
    report = l.summary_report()
    assert "No feedback" in report


def test_summary_report_with_data():
    l = _learner()
    l.record_by_agent("analyst", "task", POSITIVE)
    report = l.summary_report()
    assert "analyst" in report
