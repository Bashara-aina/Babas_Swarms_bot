"""Unified memory context for every Legion chat turn.

Merges episodic store, MemoryManager (core/recall/profile + archival FTS),
so retrieval is not gated on a single subsystem or keyword routing.

PRIORITY 2 UPGRADE: Now includes semantic (vector) search via LongTermMemory
as the primary retrieval path, with FTS as fallback. This is the single
retrieval entry point replacing the old multi-backend concatenation.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


async def build_unified_memory_context(user_id: str, query: str) -> str:
    """Return a single prompt block with all available memory layers.

    PRIORITY 2: Uses semantic search (LongTermMemory) as primary,
    with FTS + episodic as fallback layers. Deduplicates across tiers.
    """
    if not user_id:
        return ""

    parts: list[str] = []
    q = (query or "").strip()
    search_q = q if len(q) > 2 else "projects preferences schedule work"

    # ── Tier 2: Long-Term Memory (semantic search) — PRIMARY ─────────────────
    try:
        from core.long_term_memory import LongTermMemory

        hits = await LongTermMemory().search(search_q, str(user_id), limit=5)
        if hits:
            lines = ["[LONG-TERM MEMORY (semantic)]"]
            for hit in hits:
                src_marker = f"[{hit.source}]" if hit.source != "semantic" else ""
                lines.append(f"  {src_marker} {hit.text[:300]}")
            parts.append("\n".join(lines))
    except Exception as e:
        logger.debug("[unified_context] LongTermMemory: %s", e)

    # ── Tier 1: Core + Profile + Recall (always included) ───────────────────
    try:
        from core.memory.memory_manager import MemoryManager

        mm = MemoryManager()
        base = mm.build_context_block()
        if base:
            parts.append("[WORKING MEMORY]\n" + base)
    except Exception as e:
        logger.debug("[unified_context] MemoryManager: %s", e)

    # ── Tier 2 Fallback: Archival FTS (if semantic didn't return enough) ─────
    try:
        import re

        fts_q = " ".join(re.findall(r"[\w\u0080-\uFFFF]+", search_q)) or "memory"
        try:
            from core.memory.memory_manager import MemoryManager

            mm = MemoryManager()
            archival = await mm.search(fts_q, limit=5)
        except Exception:
            archival = []

        if archival:
            # Check for duplicates against what we already have
            existing_snippets = set()
            for part in parts:
                # Extract text snippets from existing parts for dedup
                for line in part.split("\n"):
                    if line.strip().startswith(("  -", "  [", "  (")):
                        existing_snippets.add(line.strip()[:50])

            lines = ["[ARCHIVAL MEMORY — FTS matches]"]
            for row in archival[:5]:
                content = str(row.get("content", "") or row.get("summary", ""))[:280]
                created = str(row.get("created_at", ""))[:10]
                snippet_key = f"  [{created}] {content[:50]}"
                if content.strip() and snippet_key not in existing_snippets:
                    lines.append(f"  [{created}] {content}")
            if len(lines) > 1:  # only append if we have actual results
                parts.append("\n".join(lines))
    except Exception as e:
        logger.debug("[unified_context] Archival FTS: %s", e)

    return "\n\n".join(parts) if parts else ""
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

    return "\n\n".join(parts) + "\n\nUse the above naturally; cite what you used when it matters."
