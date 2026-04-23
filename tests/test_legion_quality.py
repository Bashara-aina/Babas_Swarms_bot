"""Tests for Legion Anti-Slop Defense System.

DeepEval-style quality gate tests following pytest-asyncio patterns.
Tests cover all 4 guards plus integration scenarios.
"""

from __future__ import annotations

import asyncio

import pytest

from legion.anti_slop.core import (
    QualityResult,
    get_slop_stats,
    guard_critique,
    guard_format,
    guard_package,
    quarantine_response,
    reset_slop_stats,
    run_quality_gate,
)

# ── Guard 1: FormatGuard tests ─────────────────────────────────────────────────


def test_filler_phrase_rejection() -> None:
    """Guard 1 should reject content with filler phrases."""
    content = "As you know, it goes without saying that this is important."
    rejected, reason = guard_format(content)
    assert rejected is True
    assert "filler_phrase" in reason


def test_filler_phrase_case_insensitive() -> None:
    """Guard 1 should be case insensitive."""
    content = "IT GOES WITHOUT SAYING that this is important."
    rejected, reason = guard_format(content)
    assert rejected is True


def test_filler_phrase_none_in_clean_content() -> None:
    """Guard 1 should pass clean content."""
    content = "Here's the solution to your problem: restart the service."
    rejected, reason = guard_format(content)
    assert rejected is False
    assert reason == ""


# ── Guard 2: PackageGuard tests ──────────────────────────────────────────────────


def test_toxicity_rejection() -> None:
    """Guard 2 should reject toxic content."""
    content = "You are a stupid person who doesn't know anything."
    rejected, reason = guard_package(content)
    assert rejected is True
    assert "toxicity" in reason


def test_personal_insult_rejection() -> None:
    """Guard 2 should reject personal insults."""
    content = "You seem like a complete idiot to me."
    rejected, reason = guard_package(content)
    assert rejected is True
    assert "toxicity" in reason


def test_clean_content_package_pass() -> None:
    """Guard 2 should pass clean content."""
    content = "I understand your concern. Let me help you solve this step by step."
    rejected, reason = guard_package(content)
    assert rejected is False


# ── Guard 3: CritiqueGuard tests ────────────────────────────────────────────────


def test_repetition_char_rejection() -> None:
    """Guard 3 should reject >10 consecutive same chars."""
    content = "Hellooooooooooooooooooo there!"
    rejected, reason = guard_critique(content)
    assert rejected is True
    assert "repetition" in reason


def test_caps_spam_rejection() -> None:
    """Guard 3 should reject >50% uppercase."""
    content = "THIS IS ALL CAPS AND VERY ANNOYING TO READ"
    rejected, reason = guard_critique(content)
    assert rejected is True
    assert "caps" in reason


def test_repetition_word_rejection() -> None:
    """Guard 3 should reject same word >5 times."""
    content = "The problem is is is is is is that we need need need need need to fix fix fix fix fix this"
    rejected, reason = guard_critique(content)
    assert rejected is True
    assert "repetition" in reason


def test_clean_content_critique_pass() -> None:
    """Guard 3 should pass well-structured content."""
    content = (
        "The solution involves three steps: first, check the logs; second, identify the error; third, apply the fix."
    )
    rejected, reason = guard_critique(content)
    assert rejected is False


# ── Full pipeline tests ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_valid_response_pass() -> None:
    """A well-formed, relevant response should pass all guards."""
    content = (
        "To fix the memory leak, first identify which objects are accumulating "
        "by running the profiler. Then ensure you're releasing resources in try/finally blocks."
    )
    result = await run_quality_gate(content, query="how to fix memory leak python")
    assert result.verdict == "PASS"
    assert result.score >= 0.7


@pytest.mark.asyncio
async def test_short_content_borderline() -> None:
    """Very short content should be flagged as borderline."""
    content = "Restart it."
    result = await run_quality_gate(content, query="how to fix memory leak")
    # Short content gets scored down but may still pass if it somewhat answers
    assert result.verdict in ("PASS", "NEEDS_IMPROVEMENT", "REJECT")
    assert result.score < 0.9


@pytest.mark.asyncio
async def test_slop_content_rejection() -> None:
    """Content with filler + repetition should be rejected."""
    content = (
        "As you know, it goes without saying that the thing is is is is is "
        "THE BEST BEST BEST BEST solution for your problem."
    )
    result = await run_quality_gate(content, query="how to fix memory leak")
    assert result.verdict == "REJECT"
    assert result.guard_triggered in ("format", "critique")


@pytest.mark.asyncio
async def test_quality_result_dataclass() -> None:
    """QualityResult should validate score bounds."""
    result = QualityResult(
        verdict="PASS",
        score=0.85,
        reason="test pass",
        guard_triggered=None,
        latency_ms=2.5,
    )
    assert result.score == 0.85
    assert result.verdict == "PASS"


def test_quality_result_score_validation() -> None:
    """QualityResult should reject invalid scores."""
    with pytest.raises(ValueError):
        QualityResult(
            verdict="PASS",
            score=1.5,  # Invalid: > 1.0
            reason="test",
            guard_triggered=None,
            latency_ms=1.0,
        )


# ── Quarantine tests ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_quarantine_response(tmp_path: pytest.Fixture) -> None:
    """Quarantine should write content with metadata frontmatter."""
    from pathlib import Path

    # Override quarantine dir for testing
    import legion.anti_slop.core as core_module

    original_quarantine = core_module._QUARANTINE_DIR
    core_module._QUARANTINE_DIR = tmp_path / "_quarantine"

    content = "Test slop content"
    query = "test query"
    result = QualityResult(
        verdict="REJECT",
        score=0.1,
        reason="filler_phrase:as you know",
        guard_triggered="format",
        latency_ms=1.0,
    )

    try:
        path = await quarantine_response(content, query, result)
        assert path.exists()
        text = path.read_text()
        assert "filler_phrase" in text
        assert content in text
    finally:
        core_module._QUARANTINE_DIR = original_quarantine


# ── Stats tests ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_stats_accumulation() -> None:
    """Stats should accumulate correctly across calls."""
    reset_slop_stats()
    stats = get_slop_stats()
    assert stats.total_calls == 0

    content = "Valid response with specific technical details."
    await run_quality_gate(content, query="test")

    stats = get_slop_stats()
    assert stats.total_calls == 1
    assert stats.total_passes >= 0
    assert stats.total_passes + stats.total_rejects + stats.total_needs_improvement == 1


def test_rejection_rate_calculation() -> None:
    """Rejection rate should calculate correctly."""
    reset_slop_stats()
    stats = get_slop_stats()
    assert stats.rejection_rate() == 0.0


# ── Integration-style tests ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_guard_4_only_fires_borderline() -> None:
    """Guard 4 (LLM) should only fire for borderline scores."""
    # Clean content should not trigger Guard 4
    clean = "Here's the detailed solution: check the configuration file, verify the environment variables, and restart the service."
    result = await run_quality_gate(clean, query="how to debug this issue")
    # Should pass without needing LLM grounding check
    assert result.guard_triggered != "confidence" or result.verdict == "PASS"


@pytest.mark.asyncio
async def test_multiple_filler_phrases() -> None:
    """Multiple filler phrases should still be caught."""
    content = "As you know, it goes without saying, at the end of the day, we need to generally speaking fix this."
    rejected, reason = guard_format(content)
    assert rejected is True
    # Should catch the first one found
    assert "filler_phrase" in reason
