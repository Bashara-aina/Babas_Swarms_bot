"""Thin facade: inject EmotionEngine state into LLM prompts."""

from __future__ import annotations


def emotion_prompt_block() -> str:
    try:
        from core.personality.emotion_engine import EmotionEngine

        return EmotionEngine().to_prompt_block()
    except Exception:
        return ""
