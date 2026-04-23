import asyncio
import logging

from core.integrations.gptr_client import GPTResearcherClient

logger = logging.getLogger(__name__)
_client = GPTResearcherClient()

SKILL_NAME = "deep_research"
SKILL_DESCRIPTION = "Deep multi-source web research with citations. Use for: market research, competitor analysis, legal/regulatory research, data sourcing."
TRIGGER_KEYWORDS = [
    "research",
    "riset",
    "cari tahu",
    "analisis pasar",
    "market research",
    "kompetitor",
    "regulasi",
    "investigate",
    "deep dive",
    "laporan",
]


async def execute(query: str, report_type: str = "research_report") -> str:
    logger.info(f"Deep research skill triggered: {query[:50]}")
    result = await _client.research(query, report_type=report_type)
    if not result["report"] or "failed" in result["report"].lower():
        return f"⚠️ Research gagal. Coba: /search {query}"
    report = result["report"]
    sources = result["sources"]
    max_len = 3500
    if len(report) > max_len:
        report = report[:max_len] + "\n\n_[Report dipotong. Full version tersimpan di memory.]_"
    source_lines = ""
    if sources:
        top_sources = sources[:3]
        source_lines = "\n\n📚 *Sources:*\n" + "\n".join(
            f"• {s.get('url', s) if isinstance(s, dict) else s}" for s in top_sources
        )
    cost_note = f"\n_~${result['cost_estimate']} API cost_" if result["cost_estimate"] > 0 else ""
    return f"🔬 *Deep Research: {query[:40]}*\n\n{report}{source_lines}{cost_note}"


SKILL_META = {
    "name": SKILL_NAME,
    "description": SKILL_DESCRIPTION,
    "triggers": TRIGGER_KEYWORDS,
    "execute": execute,
    "requires_internet": True,
    "avg_latency_seconds": 30,
    "cost_tier": "medium",
}


def _register_deep_research_skill() -> None:
    from core.skills.registry import SKILL_REGISTRY, Skill

    SKILL_REGISTRY.register(
        Skill(
            name=SKILL_NAME,
            description=SKILL_DESCRIPTION,
            trigger_keywords=TRIGGER_KEYWORDS,
            handler=execute,
            required_env_keys=[],
            category="research",
        )
    )


_register_deep_research_skill()
