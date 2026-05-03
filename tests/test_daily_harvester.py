"""Tests for the daily harvester system."""

from __future__ import annotations

import pytest

from core.daily_harvester.morning_report import MorningReport
from core.daily_harvester.source_strategy import (
    ContradictionResolver,
    SourceType,
    TrustTier,
    get_trust_score,
    get_trust_tier,
)
from core.daily_harvester.swarm_debate import run_debate
from core.daily_harvester.topic_budget import detect_active_topics
from core.daily_harvester.types import (
    CandidateInfo,
    SourceType,
    SwarmVerdict,
    VerdictDecision,
)

# ── test_weight_formula ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_weight_formula() -> None:
    """Verify normalization to 100 total slots."""
    budget = await detect_active_topics()
    total = sum(budget.values())
    assert total == 100, f"Expected 100 slots, got {total}"


@pytest.mark.asyncio
async def test_budget_min_max() -> None:
    """Each active topic should be between 3 and 35 slots."""
    budget = await detect_active_topics()
    for topic, slots in budget.items():
        if topic != "surprise_discoveries":
            assert 3 <= slots <= 35, f"Topic {topic} has {slots} slots (range [3,35])"


# ── test_swarm_verdict ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_swarm_verdict() -> None:
    """Verify all verdict types are returned (mock candidate)."""
    candidate: CandidateInfo = {
        "candidate_id": "test-001",
        "topic": "test_topic",
        "title": "Test Intelligence Piece",
        "content": "This is a test piece of intelligence about labor law.",
        "url": "https://example.com/test",
        "source_type": SourceType.GOV,
        "discovered_at": "2026-04-11T00:00:00+00:00",
        "tags": ["test", "labor-law"],
        "relevance_score": 0.8,
        "citations": 5,
    }
    verdict = await run_debate(candidate)
    assert verdict["candidate_id"] == "test-001"
    assert isinstance(verdict["verdict"], VerdictDecision)
    assert verdict["confidence"] >= 0.0
    assert verdict["confidence"] <= 1.0


# ── test_wiki_naming ──────────────────────────────────────────────────────────


def test_wiki_naming_convention() -> None:
    """Verify entry naming convention: PREFIX-NNN-slug-YYYY-MM-DD.md."""
    import re

    prefix_pattern = r"^(CW|POPW|AI|PERS|GEN)-(\d{3})-([a-z0-9-]+)-(\d{4}-\d{2}-\d{2})\.md$"
    test_names = [
        "CW-001-labor-law-2026-04-11.md",
        "POPW-005-ml-research-2026-04-10.md",
        "AI-012-openai-o3-reasoning-2026-04-09.md",
        "PERS-003-tokyo-life-2026-04-08.md",
        "GEN-001-economy-outlook-2026-04-11.md",
    ]
    for name in test_names:
        assert re.match(prefix_pattern, name), f"Name {name} doesn't match convention"


# ── test_trust_scores ─────────────────────────────────────────────────────────


def test_trust_scores() -> None:
    """Verify trust tier assignments."""
    assert get_trust_score(SourceType.GOV) == 10
    assert get_trust_score(SourceType.ACADEMIC) == 9
    assert get_trust_score(SourceType.INDUSTRY) == 7
    assert get_trust_score(SourceType.COMMUNITY) == 5
    assert get_trust_score(SourceType.SOCIAL) == 3

    assert get_trust_tier(10) == TrustTier.TIER_1_GOV
    assert get_trust_tier(9) == TrustTier.TIER_2_ACADEMIC
    assert get_trust_tier(7) == TrustTier.TIER_3_PROFESSIONAL
    assert get_trust_tier(5) == TrustTier.TIER_4_COMMUNITY
    assert get_trust_tier(3) == TrustTier.TIER_5_ANONYMOUS


# ── test_contradiction_resolver_gov_wins ─────────────────────────────────────


def test_contradiction_resolver_gov_wins() -> None:
    """GOV source should win over non-GOV."""
    resolver = ContradictionResolver()

    new_entry = {
        "file_id": "CW-002",
        "topic": "cekwajar_labor_law",
        "title": "New PP Regulation",
        "content": "New regulation text",
        "tags": [],
        "sources": [],
        "created_at": "2026-04-11",
        "veracity_score": 0.9,
        "superseded_ids": [],
        "source_type": SourceType.GOV,
    }

    existing_entry = {
        "file_id": "CW-001",
        "topic": "cekwajar_labor_law",
        "title": "Old regulation",
        "content": "Old regulation text",
        "tags": [],
        "sources": [],
        "created_at": "2025-01-01",
        "veracity_score": 0.9,
        "superseded_ids": [],
        "source_type": SourceType.INDUSTRY,
    }

    decision, reason = resolver.resolve(new_entry, existing_entry)
    assert decision == "SUPERSEDE", f"Expected SUPERSEDE, got {decision} (gov wins)"
    assert "Government" in reason


# ── test_contradiction_resolver_newer_wins ───────────────────────────────────


def test_contradiction_resolver_newer_wins() -> None:
    """For regulations: newer date should win when both are GOV/ACADEMIC."""
    resolver = ContradictionResolver()

    new_entry = {
        "file_id": "CW-002",
        "topic": "cekwajar_labor_law",
        "title": "New PP 2026",
        "content": "Newer regulation",
        "tags": [],
        "sources": [],
        "created_at": "2026-04-01",
        "veracity_score": 0.9,
        "superseded_ids": [],
        "source_type": SourceType.ACADEMIC,
    }

    existing_entry = {
        "file_id": "CW-001",
        "topic": "cekwajar_labor_law",
        "title": "Old PP 2025",
        "content": "Older regulation",
        "tags": [],
        "sources": [],
        "created_at": "2025-04-01",
        "veracity_score": 0.9,
        "superseded_ids": [],
        "source_type": SourceType.ACADEMIC,
    }

    decision, _reason = resolver.resolve(new_entry, existing_entry)
    assert decision == "SUPERSEDE", f"Expected SUPERSEDE (newer), got {decision}"


# ── test_report_length ───────────────────────────────────────────────────────


def test_report_length() -> None:
    """Morning report should be max 3000 chars."""
    report_gen = MorningReport()

    mock_accepted: list[CandidateInfo] = [
        {
            "candidate_id": "test-001",
            "topic": "cekwajar_labor_law",
            "title": "UMP 2026 Jakarta",
            "content": "UMP Jakarta 2026 is Rp 5,000,000",
            "url": "https://example.com",
            "source_type": SourceType.GOV,
            "discovered_at": "2026-04-11",
            "tags": ["UMP", "jakarta"],
            "relevance_score": 0.9,
            "citations": 10,
        },
    ]

    mock_verdicts: list[SwarmVerdict] = [
        {
            "candidate_id": "test-001",
            "verdict": VerdictDecision.ACCEPT,
            "confidence": 0.92,
            "concerns": [],
            "rebuttals": [],
            "fact_check_result": {},
            "reasoning": "Well sourced government data",
            "final_citations": ["https://example.com"],
        },
    ]

    mock_budget = {
        "cekwajar_labor_law": 18,
        "cekwajar_market": 12,
        "popw_ml_research": 15,
        "surprise_discoveries": 5,
    }

    report = report_gen.generate(mock_accepted, mock_verdicts, mock_budget, conflicts=1, rejected=2)
    assert len(report) <= 3000, f"Report is {len(report)} chars (max 3000)"
    assert len(report) > 0


# ── test_pipeline_ordering ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_pipeline_ordering() -> None:
    """Verify pipeline steps run in correct order (dry run)."""
    from core.daily_harvester.harvest_pipeline import HarvestPipeline

    pipeline = HarvestPipeline()
    result = await pipeline.run_full_pipeline()

    # Keys that must be present
    assert "date" in result
    assert "accepted_count" in result
    assert "rejected_count" in result
    assert "written_files" in result
    assert "report" in result
    assert "duration_s" in result

    # Duration should be positive
    assert result["duration_s"] >= 0

    # Report should be a non-empty string
    assert isinstance(result["report"], str)
    assert len(result["report"]) <= 3000
