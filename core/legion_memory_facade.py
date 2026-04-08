"""
Unified memory read surface — mem0 + wiki + Screenpipe for tools and orchestration.

Does not replace :class:`core.memory.memory_manager.MemoryManager` (tiered FTS);
this is a convenience compositor for RAG-style context blocks.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


class LegionMemoryFacade:
    async def contextual_snapshot(self, query: str, user_id: str) -> str:
        """Return a single markdown-ish block combining semantic, wiki, and Screenpipe."""
        parts: list[str] = []
        q = (query or "").strip()
        uid = str(user_id or "").strip()
        if uid and q:
            try:
                from core.memory_manager import LegionSemanticMemory

                lines = await LegionSemanticMemory().search_memories(q, uid, limit=4)
                if lines:
                    parts.append("## MEM0 (semantic)\n" + "\n".join(f"- {ln}" for ln in lines))
            except Exception as exc:
                logger.debug("facade mem0 skipped: %s", exc)

        if q and os.getenv("LEGION_WIKI_ENABLED", "1").strip().lower() not in ("0", "false", "no", "off"):
            try:
                from core.wiki_manager import get_wiki_manager

                w = await get_wiki_manager().query(q, top_k=2)
                if w:
                    parts.append(w)
            except Exception as exc:
                logger.debug("facade wiki skipped: %s", exc)

        if os.getenv("SCREENPIPE_ENABLED", "0").strip().lower() in ("1", "true", "yes", "on") and q:
            try:
                from tools.screenpipe_tool import get_screenpipe_tool

                sp = await get_screenpipe_tool().search(q, limit=2, hours_back=48)
                if sp:
                    parts.append(sp)
            except Exception as exc:
                logger.debug("facade screenpipe skipped: %s", exc)

        return "\n\n".join(parts) if parts else ""


_facade: LegionMemoryFacade | None = None


def get_memory_facade() -> LegionMemoryFacade:
    global _facade
    if _facade is None:
        _facade = LegionMemoryFacade()
    return _facade
