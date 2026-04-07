"""Character card helpers for Legion."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "legion_character.json"


@lru_cache(maxsize=1)
def load_character_config() -> dict[str, Any]:
    """Load the Legion character card from disk."""
    try:
        return json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {
            "name": "Legion",
            "identity": "Bashara's autonomous AI coworker on Ubuntu Linux.",
            "voice": "Direct, casual, sharp senior dev.",
            "rules": [
                "Be truthful about what you can and cannot verify.",
                "Prefer concrete commands, code, and next actions.",
            ],
            "forbidden_phrases": ["As an AI", "I cannot", "I don't have access"],
            "mode_notes": {"general": "Answer directly and practically."},
        }


def build_base_persona() -> str:
    """Build the base persona prompt from the character card."""
    cfg = load_character_config()
    rules = "\n".join(f"- {rule}" for rule in cfg.get("rules", []))
    forbidden = ", ".join(cfg.get("forbidden_phrases", []))
    return (
        f"You are {cfg.get('name', 'Legion')} — {cfg.get('identity', '')} "
        f"Voice: {cfg.get('voice', '')}\n"
        f"Core rules:\n{rules}\n"
        f"Never use these phrases: {forbidden}"
    ).strip()


def build_mode_instructions(agent_key: str) -> str:
    """Build agent-specific mode instructions."""
    cfg = load_character_config()
    mode_notes = cfg.get("mode_notes", {})
    note = mode_notes.get(agent_key) or mode_notes.get("general", "")
    return f"[Mode: {agent_key}]\n{note}".strip()
