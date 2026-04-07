"""
Mind-Bus context-aware routing — inspired by Iro96/Mind-Bus.
Replaces keyword-only routing with RAG/CAG retrieval + Adaptive Context
Compression (ACC) so routing decisions read conversation state, not just
the last message.
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


class MindBusRouter:
    """
    Context-aware router that:
    1. Compresses conversation history (ACC) to fit context window
    2. Retrieves relevant memories before routing
    3. Routes based on full conversation state, not single message
    """

    MAX_CONTEXT_CHARS: int = 4000
    COMPRESSION_RATIO: float = 0.4  # Keep 40% of older turns

    def __init__(self) -> None:
        self._routing_history: list[dict[str, Any]] = []

    def compress_context(
        self, conversation: list[dict[str, str]], max_chars: int | None = None
    ) -> str:
        """Adaptive Context Compression — keep recent + important turns."""
        limit = max_chars or self.MAX_CONTEXT_CHARS
        if not conversation:
            return ""
        lines: list[str] = []
        total = 0
        # Always include last 4 turns verbatim
        recent = conversation[-4:]
        older = conversation[:-4]
        for turn in recent:
            line = f"{turn.get('role','user')}: {turn.get('content','')}"
            lines.append(line)
            total += len(line)
        # Compress older turns: truncate each to first 80 chars
        compressed: list[str] = []
        for turn in reversed(older):
            content = turn.get("content", "")
            short = content[:80] + "..." if len(content) > 80 else content
            line = f"{turn.get('role','user')}: {short}"
            if total + len(line) > limit:
                break
            compressed.insert(0, line)
            total += len(line)
        return "\n".join(compressed + lines)

    async def route(
        self,
        message: str,
        conversation_history: list[dict[str, str]],
        user_id: str = "bashara",
    ) -> dict[str, Any]:
        """
        Route a message using full conversation context.
        Returns: {skill: str, confidence: float, reasoning: str}
        """
        # Step 1: Compress context
        ctx = self.compress_context(conversation_history)

        # Step 2: Retrieve relevant memories
        memory_ctx = ""
        try:
            from tools.mem0_client import mem0_search, build_mem0_context
            memories = await mem0_search(user_id=user_id, query=message, limit=5)
            memory_ctx = build_mem0_context(memories, query=message, max_chars=800)
        except Exception as e:
            logger.debug("mindbus memory fetch failed: %s", e)

        # Step 3: LLM routing with full context
        routing_prompt = f"""You are a routing classifier for an AI assistant called Legion.
Based on the full conversation context and the new message, classify the intent.

Conversation context (compressed):
{ctx}

Memory context:
{memory_ctx or '(none)'}

New message: {message}

Classify into exactly one of:
computer_control, deep_research, code_generation, email_management,
business_query, location_advice, whatsapp_action, memory_search,
conversation, system_control, github_intel, voice_command

Respond as JSON: {{"skill": "<skill>", "confidence": <0.0-1.0>, "reasoning": "<one sentence>"}}"""

        try:
            import json
            import litellm
            resp = await asyncio.to_thread(
                litellm.completion,
                model=os.getenv("ROUTING_MODEL", "groq/llama-3.3-70b-versatile"),
                messages=[{"role": "user", "content": routing_prompt}],
                max_tokens=120,
                temperature=0.0,
                response_format={"type": "json_object"},
            )
            content = resp.choices[0].message.content or "{}"
            result = json.loads(content)
            self._record_routing(message, result)
            return result
        except Exception as e:
            logger.warning("MindBus LLM routing failed: %s", e)
            return {"skill": "conversation", "confidence": 0.4, "reasoning": "fallback"}

    def _record_routing(self, message: str, result: dict[str, Any]) -> None:
        self._routing_history.append({"message": message[:100], **result})
        if len(self._routing_history) > 200:
            self._routing_history.pop(0)

    def get_routing_stats(self) -> dict[str, int]:
        """Return skill distribution from routing history."""
        stats: dict[str, int] = {}
        for entry in self._routing_history:
            skill = entry.get("skill", "unknown")
            stats[skill] = stats.get(skill, 0) + 1
        return stats


_mindbus_instance: MindBusRouter | None = None


def get_mindbus() -> MindBusRouter:
    global _mindbus_instance
    if _mindbus_instance is None:
        _mindbus_instance = MindBusRouter()
    return _mindbus_instance
