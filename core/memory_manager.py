"""Semantic long-term memory via mem0 (vector + optional Supabase pgvector).

This wraps :mod:`tools.mem0_client`. Tiered FTS/archival memory lives in
:class:`core.memory.memory_manager.MemoryManager` — keep the two distinct.
"""

from __future__ import annotations

import logging
from typing import Any, Sequence

logger = logging.getLogger(__name__)


class LegionSemanticMemory:
    """Async façade for mem0 search / persistence (Tier 1 memory injection)."""

    async def search_memories(self, query: str, user_id: str, *, limit: int = 5) -> list[str]:
        """Return top textual memory snippets for prompt injection."""
        from tools.mem0_client import mem0_search

        if not query.strip() or not str(user_id).strip():
            return []
        hits = await mem0_search(user_id=str(user_id), query=query, limit=limit)
        lines: list[str] = []
        for item in hits:
            text = (item.get("memory") or item.get("content") or item.get("text") or "").strip()
            if text:
                lines.append(text)
        return lines

    async def save_memory(
        self,
        messages: Sequence[dict[str, Any]],
        user_id: str,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Persist one or more chat turns. Prefers mem0 ``add(messages=...)`` when available."""
        from tools.mem0_client import get_mem0, mem0_add

        base_meta: dict[str, Any] = {"source": "legion_chat", **(metadata or {})}
        payload: list[dict[str, str]] = []
        for m in messages:
            role = str(m.get("role", "user"))
            content = str(m.get("content", "")).strip()
            if content:
                payload.append({"role": role, "content": content})
        if not payload:
            return

        mem = get_mem0()
        if mem is not None:
            try:
                mem.add(payload, user_id=str(user_id), metadata=base_meta)
                return
            except Exception as exc:
                logger.debug("mem0 batch add failed, using per-message fallback: %s", exc)

        for item in payload:
            await mem0_add(
                user_id=str(user_id),
                content=item["content"],
                metadata={**base_meta, "role": item["role"]},
            )
