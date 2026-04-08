"""System prompt builder — assembles the full Legion system prompt per request.

Layer order (bottom to top, each wraps the next):
  1. PERSONALITY_WRAPPER (from agents.py) — core identity + tone rules
  2. DISAGREEMENT_PROTOCOL — when/how to push back + humor style
  3. BASHARA PROFILE — persistent personal facts (location, projects, workstation)
  4. MEMORY CONTEXT — relevant episodic memories + upcoming schedule
  5. EMOTION MODIFIER — current mood adjustments
  6. ROLE PROMPT — specialist agent instructions (coding, debug, etc.)
  7. CONVERSATION CONTEXT — last 6 turns

This replaces the old build_system_prompt() in agents.py.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def build_full_system_prompt(
    role_prompt: str,
    user_id: str = "",
    user_msg: str = "",
    emotion: str = "neutral",
    agent_key: str = "general",
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

    # 5. Emotion modifier
    if emotion and emotion != "neutral":
        try:
            from core.emotion_modulator import build_emotion_modifier
            modifier = build_emotion_modifier(emotion)
            if modifier:
                parts.append(modifier)
        except Exception as e:
            logger.debug("[PromptBuilder] emotion_modulator not available: %s", e)

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
