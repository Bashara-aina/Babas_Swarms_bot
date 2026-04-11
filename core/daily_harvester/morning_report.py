"""MorningReport — generate the daily Telegram intelligence digest."""

from __future__ import annotations

import logging
from typing import Any

from core.daily_harvester.types import CandidateInfo, SwarmVerdict

logger = logging.getLogger(__name__)

MAX_REPORT_CHARS = 3000
MAX_TOPICS = 5


class MorningReport:
    """
    Generates the morning Telegram intelligence digest.

    Format constraints:
    - max 3000 characters
    - max 5 topics covered
    - emoji anchors for quick scanning
    """

    def generate(
        self,
        accepted: list[CandidateInfo],
        verdicts: list[SwarmVerdict],
        budget: dict[str, int],
        conflicts: int,
        rejected: int,
    ) -> str:
        """
        Generate the morning report string.
        """
        sections: list[str] = []

        # Header
        sections.append("🌅 <b>Legion Daily Intel</b>")
        sections.append("")

        # TOP FINDINGS section
        sections.append("📊 <b>TOP FINDINGS</b>")
        sections.append("")

        # Group by topic
        topic_groups: dict[str, list[CandidateInfo]] = {}
        for candidate in accepted:
            topic = candidate.get("topic", "unknown")
            if topic not in topic_groups:
                topic_groups[topic] = []
            topic_groups[topic].append(candidate)

        sorted_topics = sorted(topic_groups.items(), key=lambda x: -len(x[1]))[:MAX_TOPICS]

        for topic, candidates in sorted_topics:
            emoji_map = {
                "cekwajar_labor_law": "⚖️",
                "cekwajar_market": "📊",
                "cekwajar_engineering": "🔧",
                "popw_ml_research": "🤖",
                "babas_bot_ai": "🤖",
                "ai_tools_llm": "🛠️",
                "indonesia_economy": "🇮🇩",
                "personal_life": "🏠",
                "surprise_discoveries": "🔍",
            }
            emoji = emoji_map.get(topic, "📌")
            titles = [c.get("title", "Untitled")[:50] for c in candidates[:3]]
            titles_str = "; ".join(titles)
            sections.append(f"{emoji} <b>{topic}</b> ({len(candidates)} entries): {titles_str}")

        sections.append("")

        # Conflicts
        sections.append(f"⚠️ <b>CONFLICTS FOUND</b>: {conflicts}")
        sections.append("")

        # Rejected today
        sections.append(f"❌ <b>REJECTED TODAY</b>: {rejected}")
        sections.append("")

        # Topic budget visualization
        sections.append("💼 <b>TOPIC BUDGET</b>")
        sorted_budget = sorted(budget.items(), key=lambda x: -x[1])[:8]
        bar_max = 20
        for topic, slots in sorted_budget:
            bar = "█" * min(slots, bar_max)
            sections.append(f"{bar} {topic} ({slots})")
        sections.append("")

        # Footer
        sections.append("_Harvested by Legion · 04:00 WIB daily_")

        report = "\n".join(sections)

        if len(report) > MAX_REPORT_CHARS:
            # Truncate gracefully
            report = report[: MAX_REPORT_CHARS - 20] + "\n…_[truncated]_"
            logger.warning("Morning report truncated to %d chars", MAX_REPORT_CHARS)

        return report
