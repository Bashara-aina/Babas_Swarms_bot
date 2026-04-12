"""Central memory manager for Legion humanization layer."""

from __future__ import annotations

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
        logger.info("[Memory] Loaded. Archival: %s memories.", self.archival.total_count())

    async def save(
        self,
        content: str,
        summary: str = "",
        tags: list[str] | None = None,
        importance: float = 0.5,
        source: str = "agent",
    ) -> int:
        mem_id = self.archival.store(content, summary, tags, importance, source)
        if importance >= 0.85:
            key = (summary or content)[:50].replace(" ", "_").lower()
            self.core.set(key, content[:200])
        logger.info("[Memory] Saved (importance=%.1f): %s...", importance, content[:60])
        return mem_id

    async def search(self, query: str, limit: int = 8) -> list[dict[str, Any]]:
        results = self.archival.search(query, limit)
        logger.debug("[Memory] Search '%s' -> %s results", query, len(results))
        return results

    def add_conversation_turn(
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
        self.recall.add(role, content, agent_used, emotion_state, session_id, importance)

    def build_context_block(self) -> str:
        core_block = self.core.to_prompt_block()
        profile_block = self.profile.to_prompt_block()
        recent = self.recall.get_recent(n=10)
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

    def get_memory_stats(self) -> dict[str, int]:
        return {
            "archival_total": self.archival.total_count(),
            "core_keys": len(self.core.all()),
            "profile_facts": len(self.profile.get("known_facts", [])),
            "profile_patterns": len(self.profile.get("interaction_patterns", [])),
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
