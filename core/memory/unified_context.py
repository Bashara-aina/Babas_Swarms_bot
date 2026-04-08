"""Unified memory context for every Legion chat turn.

Merges episodic store, MemoryManager (core/recall/profile + archival FTS),
so retrieval is not gated on a single subsystem or keyword routing.
"""

from __future__ import annotations

import logging
logger = logging.getLogger(__name__)


async def build_unified_memory_context(user_id: str, query: str) -> str:
    """Return a single prompt block with all available memory layers."""
    if not user_id:
        return ""

    parts: list[str] = []
    q = (query or "").strip()
    search_q = q if len(q) > 2 else "projects preferences schedule work"

    # 1) Episodic + schedule (Supabase or local JSON)
    try:
        from core.memory.episodic_store import get_episodic_store

        store = get_episodic_store()
        ep_block = store.build_context_block(user_id, search_q)
        if ep_block:
            parts.append(ep_block)
    except Exception as e:
        logger.debug("[unified_context] episodic: %s", e)

    # 2) Core + profile + short recall + archival FTS
    try:
        from core.memory.memory_manager import MemoryManager

        mm = MemoryManager()
        base = mm.build_context_block()
        if base:
            parts.append("[LOCAL MEMORY TIERS]\n" + base)

        import re

        fts_q = " ".join(re.findall(r"[\w\u0080-\uFFFF]+", search_q)) or "memory"
        try:
            archival = await mm.search(fts_q, limit=8)
        except Exception:
            archival = []
        if archival:
            lines = ["[ARCHIVAL MEMORY — FTS matches]"]
            for row in archival[:8]:
                content = str(row.get("content", "") or row.get("summary", ""))[:320]
                created = str(row.get("created_at", ""))[:10]
                if content.strip():
                    lines.append(f"  [{created}] {content}")
            parts.append("\n".join(lines))
    except Exception as e:
        logger.debug("[unified_context] MemoryManager: %s", e)

    # 3) Thin profile extras (schedule / travel) — avoids duplicating full profile block
    try:
        from core.memory.user_profile import get_user_profile

        prof = get_user_profile(str(user_id))
        extras: list[str] = []
        sn = prof.get("schedule_notes") or []
        if sn:
            extras.append("Schedule notes: " + "; ".join(str(x) for x in sn[:5]))
        world = prof.get("world") if isinstance(prof.get("world"), dict) else {}
        if world.get("planned_travel"):
            extras.append(f"Planned travel: {world.get('planned_travel')}")
        bp = world.get("business_priorities") or []
        if bp:
            extras.append("Biz focus: " + "; ".join(str(x) for x in bp[:3]))
        if extras:
            parts.append("[PROFILE EXTRAS]\n" + "\n".join(extras))
    except Exception as e:
        logger.debug("[unified_context] profile extras: %s", e)

    if not parts:
        return ""

    return (
        "\n\n".join(parts)
        + "\n\nUse the above naturally; cite what you used when it matters."
    )
