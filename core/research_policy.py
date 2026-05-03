"""Research-first policy for chat: time-sensitive / factual queries get web evidence."""

from __future__ import annotations

import asyncio
import logging
import os
import re

logger = logging.getLogger(__name__)

# Skip research for obvious chit-chat / code-only
_CODEISH = re.compile(
    r"\b(def |class |import |async def|```|npm |pip |git |pytest|docker )\b",
    re.I,
)

_TRIGGERS = (
    "restaurant", "hotel", "makan", "kuliner", "libur", "holiday", "flight",
    "harga", "price", "terbaru", "latest", "news", "today", "besok", "tomorrow",
    "cuaca", "weather", "near me", "terdekat", "jam buka", "open now",
    "review", "rating", "berapa", "how much", "stock", "crypto", "election",
    "who won", "current", "2025", "2026", "2027", "undang-undang", "policy",
    "supabase pricing", "breaking", "ipo", "schedule for", "jadwal",
    "trending", "best practices", "self improve", "upgrade legion", "adopt",
)

_NEGATORS = (
    "explain the code", "refactor", "write a function", "debug this",
    "what does this error", "translate ", "terjemahkan ",
)


def needs_live_research(text: str) -> bool:
    """Heuristic: user likely needs crawled evidence, not parametric knowledge."""
    if not text or len(text.strip()) < 8:
        return False
    if os.getenv("LEGION_RESEARCH_FIRST", "1").strip() in ("0", "false", "no"):
        return False
    t = text.lower().strip()
    if _CODEISH.search(text):
        return False
    if any(n in t for n in _NEGATORS):
        return False
    if any(k in t for k in _TRIGGERS):
        return True
    if "?" in text and len(t.split()) >= 6 and re.search(r"\b(who|what|when|where|which|why|how much|how many)\b", t):
        return True
    return False


async def build_quick_evidence_block(topic: str, user_id: str) -> str:
    """Fetch a compact evidence bundle (bounded time)."""
    topic = (topic or "").strip()[:500]
    if not topic:
        return ""

    timeout = float(os.getenv("LEGION_RESEARCH_QUICK_TIMEOUT", "35"))

    async def _run() -> str:
        from tools.quality_guard import gather_fused_evidence

        meta = await gather_fused_evidence(
            topic,
            user_id=user_id or "0",
            min_sources=2,
            start_pages=2,
            max_pages=8,
            max_attempts=1,
        )
        evidence = str(meta.get("evidence", "") or "").strip()
        sources = meta.get("sources") or []
        if not evidence and not sources:
            return ""
        src_lines = "\n".join(f"  - {u}" for u in list(sources)[:6])
        return (
            "[LIVE RESEARCH EVIDENCE — ground your answer in this; cite URLs at end]\n"
            f"{evidence[:6000]}\n\n"
            f"Sources touched:\n{src_lines}"
        )

    try:
        return await asyncio.wait_for(_run(), timeout=timeout)
    except TimeoutError:
        logger.warning("[research_policy] quick evidence timed out")
        return (
            "[LIVE RESEARCH — timeout]\n"
            "No fresh crawl finished in time. State uncertainty; suggest /research for a deep pass."
        )
    except Exception as e:
        logger.warning("[research_policy] quick evidence failed: %s", e)
        return (
            "[LIVE RESEARCH — error]\n"
            f"Crawl failed ({str(e)[:200]}). Answer without pretending you verified live data."
        )


async def maybe_attach_research_context(
    task: str,
    user_id: str | None,
    agent_key: str,
) -> tuple[str, bool]:
    """If policy fires, return (extra_system_block, research_ran)."""
    if agent_key in ("computer", "vision", "think"):
        return "", False
    if not user_id or not needs_live_research(task):
        return "", False
    block = await build_quick_evidence_block(task, str(user_id))
    return block, bool(block and "LIVE RESEARCH" in block)
