"""Persistent personality and emotional state for Legion."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

STATE_PATH = Path.home() / ".legion" / "persona_state.json"
_DEFAULT_STATE: dict[str, Any] = {
    "name": "Legion",
    "dominant_emotion": "neutral",
    "energy_level": "high",
    "mood_notes": "steady",
    "recent_emotional_events": [],
    "personality_traits": ["direct", "casual", "practical", "truthful"],
    "updated_at": "",
    # Structured key-value blocks the LLM can read and update (Letta-style memory_blocks)
    "memory_blocks": {
        "human": "Bashara — developer, running Ubuntu on RTX 3060, based in Tokyo (Koto City).",
        "persona": "Legion — direct, casual AI coworker. No corporate filler. Always honest.",
        "goals": "",
        "context": "",
    },
}


def _load_state() -> dict[str, Any]:
    try:
        if STATE_PATH.exists():
            data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                merged = dict(_DEFAULT_STATE)
                merged.update(data)
                return merged
    except Exception as exc:
        logger.warning("Failed to load persona state: %s", exc)
    return dict(_DEFAULT_STATE)


_STATE = _load_state()


def _save_state() -> None:
    try:
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        _STATE["updated_at"] = datetime.now().isoformat()
        STATE_PATH.write_text(json.dumps(_STATE, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as exc:
        logger.warning("Failed to save persona state: %s", exc)


def get_persona_state() -> dict[str, Any]:
    """Return the current persisted persona state."""
    return dict(_STATE)


def get_memory_blocks_prompt() -> str:
    """Return a formatted prompt block for the memory_blocks dict."""
    blocks: dict = _STATE.get("memory_blocks") or {}
    if not blocks:
        return ""
    lines = ["[Memory Blocks]"]
    for key, value in blocks.items():
        if value:
            lines.append(f"<{key}>{value}</{key}>")
    lines.append("[End Memory Blocks]")
    return "\n".join(lines)


def update_memory_block(key: str, value: str) -> None:
    """Update a named memory block and persist to disk."""
    blocks: dict = _STATE.setdefault("memory_blocks", {})
    blocks[key] = value[:1000]  # cap at 1000 chars per block
    _save_state()
    logger.debug("memory_block[%s] updated (%d chars)", key, len(value))


def build_persona_block() -> str:
    """Build the prompt block describing the current personality state."""
    events = _STATE.get("recent_emotional_events", []) or []
    event_lines = [f"- {item.get('emotion', 'neutral')}: {item.get('event', '')}" for item in events[:3] if isinstance(item, dict)]
    events_text = "\n".join(event_lines) if event_lines else "- none"
    memory_block_section = get_memory_blocks_prompt()
    parts = [
        "[Legion Personality State]",
        f"Dominant emotion: {_STATE.get('dominant_emotion', 'neutral')}",
        f"Energy level: {_STATE.get('energy_level', 'high')}",
        f"Mood notes: {_STATE.get('mood_notes', 'steady')}",
        f"Traits: {', '.join(_STATE.get('personality_traits', []))}",
        f"Recent emotional events:\n{events_text}",
        "[End personality state]",
    ]
    if memory_block_section:
        parts.insert(-1, memory_block_section)
    return "\n".join(parts)


def update_emotion(emotion: str, event: str = "") -> None:
    """Update the persona state with a new emotional event."""
    events = list(_STATE.get("recent_emotional_events", []) or [])
    events.insert(0, {"emotion": emotion, "event": event[:240], "at": datetime.now().isoformat()})
    _STATE["recent_emotional_events"] = events[:12]
    _STATE["dominant_emotion"] = emotion
    if emotion in {"frustrated", "tired"}:
        _STATE["energy_level"] = "low"
        _STATE["mood_notes"] = "strained"
    elif emotion in {"excited", "curious", "satisfied"}:
        _STATE["energy_level"] = "high"
        _STATE["mood_notes"] = "engaged"
    else:
        _STATE["energy_level"] = "medium"
        _STATE["mood_notes"] = "steady"
    _save_state()


def init_personality_state() -> dict[str, Any]:
    """Ensure the persona state exists on disk."""
    _save_state()
    return get_persona_state()
