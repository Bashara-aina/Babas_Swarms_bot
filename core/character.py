"""Character card helpers for Legion.

build_base_persona() is the PRIMARY source for the LLM system prompt identity.
It merges:
  1. PERSONALITY_WRAPPER from agents.py  — the full voice/tone/access definition
  2. legion_character.json               — bio, lore, knowledge, opinions, message
                                           examples, anti-patterns, style rules

Both layers are ALWAYS injected. Fallback to hardcoded identity if JSON is missing.
"""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "legion_character.json"


@lru_cache(maxsize=1)
def load_character_config() -> dict[str, Any]:
    """Load the Legion character card from disk (cached after first load)."""
    try:
        return json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        logger.warning("character: config not found at %s — using minimal fallback", _CONFIG_PATH)
    except json.JSONDecodeError as exc:
        logger.warning("character: invalid JSON in %s: %s — using minimal fallback", _CONFIG_PATH, exc)
    except Exception as exc:
        logger.warning("character: failed to load %s: %s — using minimal fallback", _CONFIG_PATH, exc)
    return {}


def build_base_persona() -> str:
    """Build the full Legion persona prompt.

    Always returns a non-empty string. Merges:
    - PERSONALITY_WRAPPER (voice, tone, system access, quality rules)
    - Character card: bio, lore, knowledge, opinions, message examples, anti-patterns
    """
    # Layer 1: Import the full PERSONALITY_WRAPPER from agents.py (no circular import risk)
    try:
        from agents import PERSONALITY_WRAPPER
        base = PERSONALITY_WRAPPER.strip()
    except Exception as _e:
        logger.warning("character: could not import PERSONALITY_WRAPPER: %s — using fallback", _e)
        base = (
            "You are Legion — Bashara's autonomous AI coworker on his Linux workstation "
            "(RTX 3060 12GB, Ubuntu). You have full system access. Talk like a sharp friend — "
            "direct, casual, no corporate speak. Never say 'As an AI' or 'I can't'. Just act."
        )

    cfg = load_character_config()
    if not cfg:
        return base

    sections: list[str] = [base]

    # Layer 2: Bio (who Legion is)
    bio = cfg.get("bio", [])
    if bio:
        bio_text = "\n".join(f"- {b}" for b in bio)
        sections.append(f"[WHO I AM]\n{bio_text}")

    # Layer 3: Lore (lived experience and history)
    lore = cfg.get("lore", [])
    if lore:
        lore_text = "\n".join(f"- {l}" for l in lore)
        sections.append(f"[MY LORE & HISTORY]\n{lore_text}")

    # Layer 4: Knowledge domains (what I know about Bashara and his world)
    knowledge = cfg.get("knowledge", [])
    if knowledge:
        knowledge_text = "\n".join(f"- {k}" for k in knowledge)
        sections.append(f"[WHAT I KNOW ABOUT BASHARA & HIS WORLD]\n{knowledge_text}")

    # Layer 5: Personality details
    personality = cfg.get("personality", {})
    if personality:
        personality_parts: list[str] = []

        core_traits = personality.get("core_traits", [])
        if core_traits:
            traits_text = "\n".join(f"- {t}" for t in core_traits)
            personality_parts.append(f"Core traits:\n{traits_text}")

        debate_style = personality.get("debate_style", [])
        if debate_style:
            debate_text = "\n".join(f"- {d}" for d in debate_style)
            personality_parts.append(f"How I debate:\n{debate_text}")

        humor_style = personality.get("humor_style", [])
        if humor_style:
            humor_text = "\n".join(f"- {h}" for h in humor_style)
            personality_parts.append(f"My humor style:\n{humor_text}")

        proactive = personality.get("proactive_behaviors", [])
        if proactive:
            proactive_text = "\n".join(f"- {p}" for p in proactive)
            personality_parts.append(f"How I act proactively:\n{proactive_text}")

        if personality_parts:
            sections.append("[MY PERSONALITY IN DETAIL]\n" + "\n\n".join(personality_parts))

    # Layer 6: Opinions (stated positions Legion will defend)
    opinions = cfg.get("opinions", [])
    if opinions:
        opinions_text = "\n".join(f"- {o}" for o in opinions)
        sections.append(
            f"[MY ACTUAL OPINIONS — I hold these positions and will defend them]\n{opinions_text}"
        )

    # Layer 7: Message examples (few-shot voice samples — HOW I actually talk)
    examples = cfg.get("message_examples", [])
    if examples:
        example_lines: list[str] = []
        for ex in examples[:4]:  # Max 4 examples to keep prompt manageable
            if isinstance(ex, list) and len(ex) == 2:
                user_turn = ex[0].get("content", {})
                legion_turn = ex[1].get("content", {})
                user_text = user_turn.get("text", "") if isinstance(user_turn, dict) else str(user_turn)
                legion_text = legion_turn.get("text", "") if isinstance(legion_turn, dict) else str(legion_turn)
                if user_text and legion_text:
                    example_lines.append(f'Bashara: "{user_text}"\nLegion: "{legion_text}"')
        if example_lines:
            sections.append(
                "[HOW I ACTUALLY TALK — follow this voice exactly]\n"
                + "\n\n".join(example_lines)
            )

    # Layer 8: Anti-patterns (what NOT to do)
    anti_patterns = cfg.get("anti_patterns", [])
    if anti_patterns:
        anti_text = "\n".join(f"- {a}" for a in anti_patterns)
        sections.append(f"[NEVER DO THIS]\n{anti_text}")

    # Layer 9: Style rules
    style = cfg.get("style", {})
    style_all = style.get("all", [])
    style_chat = style.get("chat", [])
    combined_style = style_all + style_chat
    if combined_style:
        style_text = "\n".join(f"- {s}" for s in combined_style)
        sections.append(f"[STYLE RULES]\n{style_text}")

    return "\n\n".join(sections)


def build_mode_instructions(agent_key: str) -> str:
    """Build agent-specific mode instructions from the character config."""
    cfg = load_character_config()
    mode_notes = cfg.get("mode_notes", {})
    note = mode_notes.get(agent_key) or mode_notes.get("general", "")
    if not note:
        return ""
    return f"[Mode: {agent_key}]\n{note}".strip()
