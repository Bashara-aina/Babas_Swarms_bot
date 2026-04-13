"""HarvestPipeline — orchestrates the daily intelligence harvest pipeline."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from core.daily_harvester.morning_report import MorningReport
from core.daily_harvester.swarm_debate import run_debate_batch
from core.daily_harvester.topic_budget import detect_active_topics
from core.daily_harvester.types import CandidateInfo, SwarmVerdict, TopicBudget, WikiEntry
from core.daily_harvester.wiki_storage import WikiStorage

logger = logging.getLogger(__name__)

FEATURE_BRIEFING_CONSOLIDATION_ENABLED = False


class HarvestPipeline:
    """
    Orchestrates the full daily intelligence harvest.

    Pipeline timestamps (JST):
    - 04:00  → context_read (load topic budget)
    - 04:15  → parallel_harvest (gather candidates)
    - 04:45  → swarm_debate (4-agent debate)
    - 05:00  → write_to_wiki (persist accepted entries)
    - 05:15  → generate_report + send_telegram
    """

    def __init__(self) -> None:
        self.wiki_storage = WikiStorage()

    async def _context_read(self) -> dict[str, int]:
        """Load topic budget from topic_budget engine."""
        budget = await detect_active_topics()
        logger.info("Context loaded: %d topics", len(budget))
        return budget

    async def _parallel_harvest(self, budget: dict[str, int]) -> list[CandidateInfo]:
        """
        Harvest candidate info pieces across topics in parallel.

        Real web search is wired via source_strategy.search_sources()
        (DuckDuckGo primary, arXiv fallback).
        """
        from core.daily_harvester.source_strategy import search_sources

        candidates: list[CandidateInfo] = []

        async def _harvest_topic(topic: str, slots: int) -> list[CandidateInfo]:
            results: list[CandidateInfo] = []
            sources = await search_sources(query=topic, topic=topic)
            for src in sources:
                # Convert SourceInfo → CandidateInfo
                results.append(
                    CandidateInfo(
                        candidate_id=f"{topic}_{src['url'][:30]}",
                        topic=topic,
                        title=src.get("title", "Untitled"),
                        content=src.get("snippet", ""),
                        url=src["url"],
                        source_type=src["source_type"],
                        discovered_at=datetime.now(timezone.utc).isoformat(),
                        tags=[topic],
                        relevance_score=0.5,
                        citations=0,
                    )
                )
            return results[:slots]

        tasks = [_harvest_topic(topic, slots) for topic, slots in budget.items()]
        results = await asyncio.gather(*tasks)
        for r in results:
            candidates.extend(r)

        logger.info("Harvested %d candidates", len(candidates))
        return candidates

    async def _swarm_debate(self, candidates: list[CandidateInfo]) -> list[SwarmVerdict]:
        """Run 4-agent swarm debate on all candidates."""
        if not candidates:
            return []
        verdicts = await run_debate_batch(candidates, batch_size=10)
        logger.info("Swarm debate complete: %d verdicts", len(verdicts))
        return verdicts

    async def _write_to_wiki(self, candidates: list[CandidateInfo], verdicts: list[SwarmVerdict]) -> list[str]:
        """Write accepted entries to wiki, return list of file_ids written."""
        from core.daily_harvester.types import VerdictDecision

        written: list[str] = []
        accepted: list[CandidateInfo] = []
        rejected_count = 0

        verdict_map = {v["candidate_id"]: v for v in verdicts}

        for candidate in candidates:
            verdict = verdict_map.get(candidate["candidate_id"])
            if not verdict:
                continue

            if verdict["verdict"] in (VerdictDecision.ACCEPT, VerdictDecision.ACCEPT_WITH_CAVEAT):
                entry: WikiEntry = {
                    "file_id": "",
                    "topic": candidate["topic"],
                    "title": candidate["title"],
                    "content": candidate["content"],
                    "tags": candidate["tags"],
                    "sources": verdict.get("final_citations", []),
                    "created_at": candidate["discovered_at"],
                    "veracity_score": verdict["confidence"],
                    "superseded_ids": [],
                }
                file_id = await self.wiki_storage.write_entry(entry)
                await self.wiki_storage.update_index(candidate["topic"])
                written.append(file_id)
                accepted.append(candidate)
            elif verdict["verdict"] == VerdictDecision.SUPERSEDE:
                # Write with supersede link
                entry = WikiEntry(
                    file_id="",
                    topic=candidate["topic"],
                    title=f"[SUPERSEDES] {candidate['title']}",
                    content=candidate["content"],
                    tags=candidate["tags"],
                    sources=verdict.get("final_citations", []),
                    created_at=candidate["discovered_at"],
                    veracity_score=verdict["confidence"],
                    superseded_ids=[],
                )
                file_id = await self.wiki_storage.write_entry(entry)
                await self.wiki_storage.update_index(candidate["topic"])
                written.append(file_id)
            else:
                reason = f"Verdict: {verdict['verdict']} — {verdict.get('reasoning', 'no reason')}"
                await self.wiki_storage.append_rejected_log(candidate, reason)
                rejected_count += 1

        # Log the harvest
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        await self.wiki_storage.append_harvest_log(len(accepted), rejected_count, date_str)

        logger.info("Wiki write complete: %d accepted, %d rejected", len(accepted), rejected_count)
        return written

    async def _generate_report(
        self,
        accepted: list[CandidateInfo],
        verdicts: list[SwarmVerdict],
        budget: dict[str, int],
        conflicts: int,
        rejected: int,
    ) -> str:
        """Generate the morning Telegram report."""
        if not FEATURE_BRIEFING_CONSOLIDATION_ENABLED:
            logger.info("Briefing consolidation feature is planned for v2.0 — not yet available.")
        report_gen = MorningReport()
        return report_gen.generate(accepted, verdicts, budget, conflicts, rejected)

    async def _send_telegram_report(self, report: str) -> None:
        """
        Log the morning report.

        Actual Telegram delivery is handled by DailyHarvesterScheduler,
        which calls _notify(result['report']) after run_full_pipeline() completes.
        """
        logger.info("Morning report (delivery via scheduler callback):\n%s", report)

    async def run_full_pipeline(self) -> dict[str, Any]:
        """
        Run the complete daily harvest pipeline.

        Returns a HarvestResult dict with keys:
        - date, accepted_count, rejected_count, written_files, report, duration_s
        """
        t0 = datetime.now(timezone.utc)
        logger.info("Harvest pipeline START at %s", t0.isoformat())

        # Step 1: load topic budget
        budget = await self._context_read()
        await asyncio.sleep(0.2)

        # Step 2: harvest candidates
        candidates = await self._parallel_harvest(budget)

        # Step 3: swarm debate
        verdicts = await self._swarm_debate(candidates)

        # Step 4: write to wiki
        written_files = await self._write_to_wiki(candidates, verdicts)

        # Step 5: generate report
        accepted = [
            c
            for c in candidates
            if any(
                v["candidate_id"] == c["candidate_id"] and v["verdict"] in ("ACCEPT", "ACCEPT_WITH_CAVEAT")
                for v in verdicts
            )
        ]
        conflicts = sum(1 for v in verdicts if v["verdict"] == "SUPERSEDE")
        rejected = len(candidates) - len(accepted)
        report = await self._generate_report(accepted, verdicts, budget, conflicts, rejected)

        # Step 6: send Telegram report
        await self._send_telegram_report(report)

        duration = (datetime.now(timezone.utc) - t0).total_seconds()

        result = {
            "date": t0.strftime("%Y-%m-%d"),
            "accepted_count": len(accepted),
            "rejected_count": rejected,
            "conflicts_count": conflicts,
            "written_files": written_files,
            "report": report,
            "duration_s": duration,
        }

        logger.info("Harvest pipeline DONE in %.1fs: %s", duration, result)
        return result
