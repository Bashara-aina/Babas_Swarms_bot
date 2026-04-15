"""Central memory manager for Legion humanization layer."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from .tiers import ArchivalMemory, CoreMemory, RecallMemory
from .user_profile import UserProfile

logger = logging.getLogger(__name__)


class MemoryManager:
    """Singleton manager over core, archival, recall, and profile memory."""

    _instance: "MemoryManager | None" = None

    def __new__(cls) -> "MemoryManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self.core = CoreMemory()
        self.archival = ArchivalMemory()
        self.recall = RecallMemory()
        self.profile = UserProfile()
        self._initialized = True
        logger.info("[Memory] Loaded.")

    async def save(
        self,
        content: str,
        summary: str = "",
        tags: list[str] | None = None,
        importance: float = 0.5,
        source: str = "agent",
    ) -> int:
        mem_id = await self.archival.store(content, summary, tags, importance, source)
        if importance >= 0.85:
            key = (summary or content)[:50].replace(" ", "_").lower()
            self.core.set(key, content[:200])
        logger.info("[Memory] Saved (importance=%.1f): %s...", importance, content[:60])
        return mem_id

    async def search(self, query: str, limit: int = 8) -> list[dict[str, Any]]:
        results = await self.archival.search(query, limit)
        logger.debug("[Memory] Search '%s' -> %s results", query, len(results))
        return results

    async def add_conversation_turn(
        self,
        role: str,
        content: str,
        agent_used: str | None = None,
        emotion_state: dict[str, Any] | None = None,
        session_id: str | None = None,
    ) -> None:
        importance = 0.7 if "?" in content else 0.5
        if any(word in content.lower() for word in ["remember", "important", "always", "never"]):
            importance = 0.9
        await self.recall.add(role, content, agent_used, emotion_state, session_id, importance)

    async def build_context_block(self) -> str:
        core_block = self.core.to_prompt_block()
        profile_block = self.profile.to_prompt_block()
        recent = await self.recall.get_recent(n=10)
        recent_block = ""
        if recent:
            recent_block = "[RECENT CONVERSATION HISTORY]\n"
            for turn in recent[-5:]:
                ts = str(turn.get("timestamp", ""))[:16]
                role = str(turn.get("role", ""))
                content = str(turn.get("content", ""))[:200]
                recent_block += f"  [{ts}] {role}: {content}\n"
        return f"{profile_block}\n\n{core_block}\n\n{recent_block}".strip()

    async def auto_extract_and_save(self, user_message: str, assistant_response: str) -> None:
        save_triggers = [
            "my name is",
            "i prefer",
            "i use",
            "i have",
            "i'm working on",
            "always",
            "never",
            "remember that",
            "i live",
            "my gpu",
            "my setup",
            "i hate",
            "i love",
            "i always",
            "don't forget",
            "by the way",
        ]
        msg_lower = user_message.lower()
        if any(trigger in msg_lower for trigger in save_triggers):
            await self.save(
                content=user_message,
                summary=f"User said: {user_message[:100]}",
                tags=["auto-extracted", "user-preference"],
                importance=0.75,
                source="auto-extract",
            )

        if any(k in msg_lower for k in ["prefer", "always", "never", "hate", "love"]):
            self.profile.add_pattern(f"Preference signal: {user_message[:180]}")
        if any(k in msg_lower for k in ["i am", "i'm", "my", "we are", "i work"]):
            self.profile.add_known_fact(user_message[:220])

        _ = assistant_response

    async def progressive_search(
        self,
        query: str,
        limit: int = 5,
        type_filter: str | None = None,
    ) -> dict[str, Any]:
        """3-tier progressive search — token-efficient context retrieval.

        Layer 1: Compact index (~50-100 tokens/result) — always fetched first
        Layer 2: Timeline context (~200-300 tokens/result) — on demand
        Layer 3: Full details (~500-1000 tokens/result) — only for filtered IDs

        This replaces build_context_block() with an efficient progressive disclosure
        that respects the "context is finite" principle.

        Returns:
            {
                "index": [...],      # Layer 1: id, type, title, created_at
                "timeline": [...],   # Layer 2: id, type, title, subtitle, created_at
                "full": {...},       # Layer 3: full dict for selected IDs
            }
        """
        from .observation_store import get_observation_store

        store = get_observation_store()

        # Layer 1: always fetch compact index
        index_results = await store.search(query=query, limit=limit, type_filter=type_filter)

        # Layer 2: timeline around recent observations
        timeline_results = await store.timeline(query=query, type_filter=type_filter, limit=limit)

        # Layer 3: full details for the most relevant IDs
        # Pick top 3 IDs from index for full retrieval
        top_ids = [r["id"] for r in index_results[:3]]
        full_results = await store.get_observations(top_ids)

        return {
            "index": index_results,
            "timeline": timeline_results,
            "full": {r["id"]: r for r in full_results},
        }

    def build_progressive_context_block(self, search_results: dict[str, Any]) -> str:
        """Build a compact context block from progressive_search results.

        Uses Layer 1 (index) for overview, Layer 2 (timeline) for context.
        Layer 3 (full) is only included if explicitly needed.
        This is the token-efficient alternative to build_context_block().
        """
        index = search_results.get("index", [])
        timeline = search_results.get("timeline", [])

        if not index and not timeline:
            return ""

        block_parts = ["[MEMORY INDEX]"]
        for r in index:
            created = r.get("created_at", "")[:10]
            block_parts.append(f"  [{r['id']}] {r['type']:10} {created}  {r['title']}")

        if timeline:
            block_parts.append("\n[RECENT CONTEXT]")
            for r in timeline[:5]:
                created = r.get("created_at", "")[:10]
                subtitle = r.get("subtitle", "")[:80]
                block_parts.append(
                    f"  [{r['id']}] {r['type']:10} {created}  {r['title']}"
                )
                if subtitle:
                    block_parts.append(f"            {subtitle}")

        return "\n".join(block_parts)

    async def get_memory_stats(self) -> dict[str, int]:
        arch_count = await self.archival.total_count()
        obs_stats = {}
        try:
            from .observation_store import get_observation_store
            obs_stats = await get_observation_store().get_stats()
        except Exception:
            pass
        return {
            "archival_total": arch_count,
            "core_keys": len(self.core.all()),
            "profile_facts": len(self.profile.get("known_facts", [])),
            "profile_patterns": len(self.profile.get("interaction_patterns", [])),
            **obs_stats,
        }

    def close(self) -> None:
        """Close all SQLite connections held by this manager."""
        self.archival.close()
        self.recall.close()


_memory: MemoryManager | None = None


def get_memory() -> MemoryManager:
    global _memory
    if _memory is None:
        _memory = MemoryManager()
    return _memory
