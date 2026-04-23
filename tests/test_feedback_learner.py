# /home/newadmin/swarm-bot/tests/test_feedback_learner.py
"""Tests for optimization/feedback_learner.py"""

import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.optimization.feedback_learner import NEGATIVE, POSITIVE, FeedbackLearner


def _learner() -> FeedbackLearner:
    """Return a fresh in-memory learner (no Redis)."""
    learner = FeedbackLearner.__new__(FeedbackLearner)
    learner._redis = None
    learner._scores = defaultdict(lambda: {"pos": 0, "neg": 0})
    learner._recent = []
    learner._pending = {}
    return learner


def test_register_and_record_positive():
    learner = _learner()
    fid = learner.register_response("coding", "write a sort function")
    assert fid in learner._pending
    result = learner.record(fid, POSITIVE)
    assert "positive" in result
    assert fid not in learner._pending


def test_register_and_record_negative():
    learner = _learner()
    fid = learner.register_response("debug", "fix my pytorch error")
    result = learner.record(fid, NEGATIVE, comment="bad answer")
    assert "negative" in result


def test_unknown_fid():
    learner = _learner()
    result = learner.record("badid", POSITIVE)
    assert "Unknown" in result


def test_score_accumulation():
    learner = _learner()
    for _ in range(3):
        fid = learner.register_response("vision", "analyze screen")
        learner.record(fid, POSITIVE)
    fid = learner.register_response("vision", "analyze screen 2")
    learner.record(fid, NEGATIVE)

    score = learner.get_agent_score("vision")
    assert score["pos"] == 3
    assert score["neg"] == 1
    assert score["total"] == 4
    assert score["rate"] == 75.0


def test_agent_weights_neutral_with_little_data():
    learner = _learner()
    weights = learner.agent_weights()
    # With no data, all should be 1.0
    for w in weights.values():
        assert w == 1.0


def test_agent_weights_adjust_with_data():
    learner = _learner()
    # 10 positives → rate=100% → weight=1.5
    for _ in range(10):
        learner.record_by_agent("coding", "task", POSITIVE)
    weights = learner.agent_weights()
    assert weights.get("coding", 0) > 1.0


def test_recent_negatives():
    learner = _learner()
    for i in range(3):
        learner.record_by_agent("math", f"task {i}", NEGATIVE)
    learner.record_by_agent("math", "good task", POSITIVE)

    negs = learner.recent_negatives(limit=5)
    assert len(negs) == 3
    assert all(e.rating == NEGATIVE for e in negs)


def test_summary_report_no_data():
    learner = _learner()
    report = learner.summary_report()
    assert "No feedback" in report


def test_summary_report_with_data():
    learner = _learner()
    learner.record_by_agent("analyst", "task", POSITIVE)
    report = learner.summary_report()
    assert "analyst" in report
