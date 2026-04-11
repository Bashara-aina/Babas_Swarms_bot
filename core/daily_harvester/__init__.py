"""core.daily_harvester — Daily Intelligence Harvester for Legion.

Exports the main public interface.
"""

from core.daily_harvester.harvest_pipeline import HarvestPipeline
from core.daily_harvester.morning_report import MorningReport
from core.daily_harvester.scheduler import DailyHarvesterScheduler
from core.daily_harvester.source_strategy import (
    ContradictionResolver,
    fetch_source,
    get_trust_score,
    get_trust_tier,
    search_sources,
)
from core.daily_harvester.swarm_debate import run_debate, run_debate_batch
from core.daily_harvester.topic_budget import detect_active_topics
from core.daily_harvester.topic_evolution import TopicEvolution
from core.daily_harvester.types import (
    CandidateInfo,
    SourceInfo,
    SourceType,
    SwarmVerdict,
    TopicBudget,
    TrustTier,
    VerdictDecision,
    WikiEntry,
)
from core.daily_harvester.wiki_storage import WikiStorage

__all__ = [
    # Types
    "CandidateInfo",
    "SourceInfo",
    "SourceType",
    "SwarmVerdict",
    "TopicBudget",
    "TrustTier",
    "VerdictDecision",
    "WikiEntry",
    # Core classes
    "DailyHarvester",
    "DailyHarvesterScheduler",
    "HarvestPipeline",
    "MorningReport",
    "SwarmDebate",
    "TopicBudgetEngine",
    "WikiStorage",
    # Functions
    "detect_active_topics",
    "fetch_source",
    "get_trust_score",
    "get_trust_tier",
    "run_debate",
    "run_debate_batch",
    "search_sources",
    "ContradictionResolver",
    "TopicEvolution",
]


class DailyHarvester:
    """Main entry point for the daily intelligence harvester."""

    def __init__(self) -> None:
        self.pipeline = HarvestPipeline()
        self.wiki_storage = WikiStorage()

    async def run(self) -> dict[str, object]:
        """Run the full daily harvest pipeline."""
        return await self.pipeline.run_full_pipeline()


# Alias for compatibility
class SwarmDebate:
    """Swarm debate wrapper for backwards compatibility."""

    @staticmethod
    async def run(candidate: CandidateInfo) -> SwarmVerdict:
        return await run_debate(candidate)

    @staticmethod
    async def run_batch(candidates: list[CandidateInfo]) -> list[SwarmVerdict]:
        return await run_debate_batch(candidates)


class TopicBudgetEngine:
    """Topic budget engine wrapper."""

    @staticmethod
    async def detect(telegram_days: int = 7, git_days: int = 3) -> dict[str, int]:
        return await detect_active_topics(telegram_days=telegram_days, git_days=git_days)
