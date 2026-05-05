"""Daily Harvester — type definitions and enums."""

from __future__ import annotations

from enum import Enum
from typing import TypedDict


class StrEnum(str, Enum):  # noqa: UP042
    """StrEnum backport for Python < 3.11."""
    pass


class VerdictDecision(StrEnum):
    """Swarm debate verdict decisions."""

    ACCEPT = "ACCEPT"
    ACCEPT_WITH_CAVEAT = "ACCEPT_WITH_CAVEAT"
    SUPERSEDE = "SUPERSEDE"
    REJECT = "REJECT"
    NEEDS_MORE_RESEARCH = "NEEDS_MORE_RESEARCH"


class SourceType(StrEnum):
    """Source type classification."""

    GOV = "GOV"
    ACADEMIC = "ACADEMIC"
    INDUSTRY = "INDUSTRY"
    COMMUNITY = "COMMUNITY"
    SOCIAL = "SOCIAL"


class TrustTier(StrEnum):
    """Trust tier levels for source validation."""

    TIER_1_GOV = "TIER_1_GOV"  # Score 10
    TIER_2_ACADEMIC = "TIER_2_ACADEMIC"  # Score 9
    TIER_3_PROFESSIONAL = "TIER_3_PROFESSIONAL"  # Score 7
    TIER_4_COMMUNITY = "TIER_4_COMMUNITY"  # Score 5-6
    TIER_5_ANONYMOUS = "TIER_5_ANONYMOUS"  # Score 3


class CandidateInfo(TypedDict):
    """Information about a candidate intelligence piece."""

    candidate_id: str
    topic: str
    title: str
    content: str
    url: str | None
    source_type: SourceType
    discovered_at: str  # ISO8601 timestamp
    tags: list[str]
    relevance_score: float  # 0.0-1.0
    citations: int


class SwarmVerdict(TypedDict):
    """Result of the 4-agent swarm debate."""

    candidate_id: str
    verdict: VerdictDecision
    confidence: float  # 0.0-1.0
    concerns: list[str]
    rebuttals: list[str]
    fact_check_result: dict
    reasoning: str
    final_citations: list[str]


class TopicBudget(TypedDict):
    """Topic budget allocation for a daily harvest."""

    date: str  # YYYY-MM-DD
    total_slots: int
    topics: dict[str, int]  # topic -> slots allocated
    surprised_slots: int


class SourceInfo(TypedDict):
    """Information about a source for intelligence gathering."""

    url: str
    source_type: SourceType
    trust_score: int
    title: str | None
    snippet: str | None


class WikiEntry(TypedDict):
    """A wiki entry written by the harvester."""

    file_id: str
    topic: str
    title: str
    content: str
    tags: list[str]
    sources: list[str]
    created_at: str  # ISO8601
    veracity_score: float  # 0.0-1.0
    superseded_ids: list[str]  # file_ids this entry supersedes


class FeedbackReason(StrEnum):
    """Reason codes for harvest candidate feedback."""

    TOPIC_DRIFT = "topic_drift"
    LOW_QUALITY = "low_quality"
    DUPLICATE = "duplicate"
    NOT_RELEVANT = "not_relevant"
    OUTDATED = "outdated"
    UNRELIABLE_SOURCE = "unreliable_source"
    ACCEPTED = "accepted"


class HarvestCandidate(TypedDict):
    """A single candidate in a harvest session log entry."""

    candidate_id: str
    source: str  # e.g. "arxiv/cs.AI/2504.01999" or "duckduckgo/123"
    title: str
    url: str
    score: float  # 0.0-1.0
    decision: str  # "pending" | "accepted" | "rejected" | "skipped"
    reason: str  # FeedbackReason value or "pending"
    reason_detail: str
    tags: list[str]


class HarvestMetadata(TypedDict):
    """Metadata block within a harvest session log entry."""

    candidates_found: int
    candidates_reviewed: int
    pending: int
    review_mode: str  # "telegram" | "auto" | "none"


class HarvestSession(TypedDict):
    """A structured harvest session log entry — one per harvester run."""

    date: str  # YYYY-MM-DD
    session_id: str  # UUID
    candidates_reviewed: list[HarvestCandidate]
    metadata: HarvestMetadata
