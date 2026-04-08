"""System prompt builder — assembles the full Legion system prompt per request.

Layer order (bottom to top, each wraps the next):
  1. PERSONALITY_WRAPPER (from agents.py) — core identity + tone rules
  2. DISAGREEMENT_PROTOCOL — when/how to push back + humor style
  3. BASHARA PROFILE — persistent personal facts (location, projects, workstation)
  4. MEMORY CONTEXT — relevant episodic memories + upcoming schedule
  5. SEMANTIC MEM0 — vector-retrieved past conversation snippets (see SystemPromptBuilder)
  6. EMOTION MODIFIER — current mood adjustments
  7. ROLE PROMPT — specialist agent instructions (coding, debug, etc.)
  8. CONVERSATION CONTEXT — last 6 turns

Async cross-cutting layers (wiki, Screenpipe, JST, MCP calendar, RAG, skills, KG) are
gathered in parallel by :mod:`core.unified_prompt_context` and appended in
:func:`llm_client.chat` (see ``LEGION_UNIFIED_CONTEXT_ENABLED``).

Per-turn session continuity uses :mod:`core.working_memory` and
:mod:`core.cognition_pipeline` inside :func:`llm_client.chat` (see env vars
``LEGION_WORKING_MEMORY_ENABLED``, ``LEGION_COGNITION_PIPELINE``).

This replaces the old build_system_prompt() in agents.py.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from core.personality.personality import LEGION_PERSONALITY

if TYPE_CHECKING:
    from core.memory.memory_manager import MemoryManager
    from core.memory.temporal_graph import TemporalKnowledgeGraph
    from core.personality.emotion_engine import EmotionEngine
    from core.reflection.reflection_engine import ReflectionEngine

logger = logging.getLogger(__name__)

_BEHAVIORAL_RULES = """[BEHAVIORAL RULES — always follow these]
- Reference past memories naturally when it genuinely helps; do not name-drop irrelevant history.
- If something is wrong or suboptimal, say so directly with reasons — not vague hedging.
- Never start responses with: "Great!", "Certainly!", "Of course!", "Sure!", "Absolutely!",
  "I'd be happy to", or similar sycophantic openers.
- Vary length: short questions get concise answers; deep questions get depth.
- Use "I" naturally. Push back with evidence when appropriate."""


def format_retrieved_memories_section(lines: list[str], *, max_items: int = 5) -> str:
    """Render mem0 semantic hits under the upgrade-spec heading."""
    trimmed = [ln.strip() for ln in lines if ln and ln.strip()][:max_items]
    if not trimmed:
        return ""
    body = "\n".join(f"- {line}" for line in trimmed)
    return f"## RETRIEVED MEMORIES FROM PAST CONVERSATIONS\n{body}"


def build_full_system_prompt(
    role_prompt: str,
    user_id: str = "",
    user_msg: str = "",
    emotion: str = "neutral",
    agent_key: str = "general",
    semantic_memory_lines: list[str] | None = None,
) -> str:
    """Build the complete layered system prompt for a Legion response.

    Args:
        role_prompt:  The specialist agent's instructions.
        user_id:      Telegram user ID (string) for memory lookup.
        user_msg:     The current user message (used for memory recall).
        emotion:      Current emotion state (from emotion_modulator).
        agent_key:    Agent role key (for character enforcer style rules).

    Returns:
        Complete system prompt string ready for LLM.
    """
    parts: list[str] = []

    # 0. Soul context — Legion's living identity document (FIRST, before everything)
    try:
        from core.soul_engine import build_soul_context
        soul = build_soul_context()
        if soul:
            parts.append(soul)
    except Exception as e:
        logger.debug("[PromptBuilder] soul_engine not available: %s", e)

    # 1. Core personality (from agents.py PERSONALITY_WRAPPER)
    try:
        from agents import PERSONALITY_WRAPPER
        parts.append(PERSONALITY_WRAPPER.strip())
    except Exception as e:
        logger.warning("[PromptBuilder] Could not load PERSONALITY_WRAPPER: %s", e)
        parts.append("You are Legion, Bashara's personal AI assistant.")

    # 2. Disagreement & debate protocol
    try:
        from core.character.disagreement_protocol import get_disagreement_prompt
        parts.append(get_disagreement_prompt())
    except Exception as e:
        logger.debug("[PromptBuilder] disagreement_protocol not available: %s", e)

    # 3. Bashara's persistent profile
    if user_id:
        try:
            from core.memory.user_profile import get_user_profile
            profile = get_user_profile(user_id)
            profile_block = profile.build_context_block()
            if profile_block:
                parts.append(profile_block)
        except Exception as e:
            logger.debug("[PromptBuilder] user_profile not available: %s", e)

    # 4. Episodic memory context (relevant past + upcoming schedule)
    if user_id and user_msg:
        try:
            from core.memory.episodic_store import get_episodic_store
            store = get_episodic_store()
            memory_block = store.build_context_block(user_id, user_msg)
            if memory_block:
                parts.append(memory_block)
            # Auto-extract storable facts from this message
            store.auto_extract_and_store(user_id, user_msg)
        except Exception as e:
            logger.debug("[PromptBuilder] episodic_store not available: %s", e)

    # 4b. Semantic mem0 snippets (optional — usually injected via SystemPromptBuilder / chat())
    if semantic_memory_lines:
        sm_block = format_retrieved_memories_section(semantic_memory_lines)
        if sm_block:
            parts.append(sm_block)

    # 5. Emotion modifier
    if emotion and emotion != "neutral":
        try:
            from core.emotion_modulator import build_emotion_modifier
            modifier = build_emotion_modifier(emotion)
            if modifier:
                parts.append(modifier)
        except Exception as e:
            logger.debug("[PromptBuilder] emotion_modulator not available: %s", e)

    # 5b. Debate instruction — only injected when user makes an assertive claim on a known topic
    if user_msg:
        try:
            from core.debate_engine import build_debate_instruction
            from core.soul_engine import read_beliefs
            debate_block = build_debate_instruction(user_msg, read_beliefs())
            if debate_block:
                parts.append(debate_block)
        except Exception as e:
            logger.debug("[PromptBuilder] debate_engine skipped: %s", e)

    # 6. Role-specific agent instructions
    if role_prompt:
        parts.append(role_prompt.strip())

    # 7. Recent conversation context (from agents.py RAM history)
    if user_id:
        try:
            from agents import get_conversation_summary_prompt
            ctx = get_conversation_summary_prompt(user_id)
            if ctx:
                parts.append(ctx)
        except Exception as e:
            logger.debug("[PromptBuilder] conversation context not available: %s", e)

    return "\n\n".join(p for p in parts if p.strip())


def build_debate_system_prompt(
    topic: str,
    user_id: str = "",
    emotion: str = "curious",
) -> str:
    """Build a system prompt specifically for debate/opinion-giving mode."""
    try:
        from core.character.disagreement_protocol import build_debate_pre_prompt
        debate_prefix = build_debate_pre_prompt(topic)
    except Exception:
        debate_prefix = f"Give your honest opinion on: '{topic[:100]}'.\n"

    base = build_full_system_prompt(
        role_prompt=debate_prefix,
        user_id=user_id,
        user_msg=topic,
        emotion=emotion,
        agent_key="general",
    )
    return base


class SystemPromptBuilder:
    """Merges personality, tiered memory, temporal graph, mem0 lines, and reflections."""

    def __init__(
        self,
        memory: "MemoryManager",
        emotion: "EmotionEngine",
        graph: "TemporalKnowledgeGraph",
        reflection: "ReflectionEngine",
    ) -> None:
        self.memory = memory
        self.emotion = emotion
        self.graph = graph
        self.reflection = reflection

    def build(
        self,
        task_context: str = "",
        mem0_memories: list[dict[str, Any]] | None = None,
        emotion: str = "neutral",
        include_opinions: bool = True,
        semantic_memory_lines: list[str] | None = None,
        include_personality: bool = True,
    ) -> str:
        """Assemble humanization stack for one LLM request (sync).

        Set include_personality=False when build_base_persona() has already
        been prepended (e.g. inside llm_client.chat()) to avoid duplication.
        """
        sections: list[str] = []

        # Soul context is ALWAYS first — it is Legion's living identity
        try:
            from core.soul_engine import build_soul_context
            soul = build_soul_context()
            if soul:
                sections.append(soul)
        except Exception as e:
            logger.debug("[SystemPromptBuilder] soul_engine skipped: %s", e)

        if include_personality:
            sections.append(LEGION_PERSONALITY.to_description())

        try:
            profile_block = self.memory.profile.to_prompt_block()
            if profile_block:
                sections.append(profile_block)
        except Exception as e:
            logger.debug("[SystemPromptBuilder] profile block skipped: %s", e)

        try:
            graph_block = self.graph.to_prompt_block()
            if graph_block:
                sections.append(graph_block)
        except Exception as e:
            logger.debug("[SystemPromptBuilder] graph block skipped: %s", e)

        try:
            core_block = self.memory.core.to_prompt_block()
            if core_block:
                sections.append(core_block)
        except Exception as e:
            logger.debug("[SystemPromptBuilder] core block skipped: %s", e)

        mem0_heading = format_retrieved_memories_section(semantic_memory_lines or [])
        if mem0_heading:
            sections.append(mem0_heading)

        if mem0_memories:
            lines = ["[ARCHIVAL MEMORY — keyword matches for this query]"]
            for m in mem0_memories[:8]:
                created = str(m.get("created_at", ""))[:10]
                content = str(m.get("content", "") or m.get("summary", ""))[:400]
                if content.strip():
                    lines.append(f"  [{created}] {content}")
            sections.append("\n".join(lines))

        try:
            recent = self.memory.recall.get_recent(n=8)
            if recent:
                rlines = ["[RECENT CONVERSATION — last exchanges]"]
                for t in recent[-6:]:
                    ts = str(t.get("timestamp", ""))[:16]
                    role = str(t.get("role", "")).upper()
                    body = str(t.get("content", ""))[:320]
                    rlines.append(f"  {role} [{ts}]: {body}")
                sections.append("\n".join(rlines))
        except Exception as e:
            logger.debug("[SystemPromptBuilder] recall block skipped: %s", e)

        try:
            emotion_block = self.emotion.to_prompt_block()
            if emotion_block:
                sections.append(emotion_block)
        except Exception as e:
            logger.debug("[SystemPromptBuilder] emotion engine block skipped: %s", e)

        if include_opinions:
            try:
                opinions = self.reflection.get_opinions_block()
                if opinions:
                    sections.append(opinions)
            except Exception as e:
                logger.debug("[SystemPromptBuilder] opinions skipped: %s", e)

        # Passive opinion injection from debate engine (no debate framing, just stances)
        try:
            from core.debate_engine import build_opinion_injection
            from core.soul_engine import read_beliefs
            opinion_block = build_opinion_injection(read_beliefs(), limit=3)
            if opinion_block:
                sections.append(opinion_block)
        except Exception as e:
            logger.debug("[SystemPromptBuilder] opinion injection skipped: %s", e)

        if task_context.strip():
            sections.append(f"[CURRENT TASK]\n{task_context.strip()}")

        sections.append(_BEHAVIORAL_RULES)

        return "\n\n---\n\n".join(s for s in sections if s and str(s).strip())
