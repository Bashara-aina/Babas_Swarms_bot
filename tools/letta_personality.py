"""
Letta stateful personality engine — Phase 3.
Persists persona_state.json to disk so emotion + traits survive restarts.
Injects memory block into every LLM system prompt.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

PERSONA_STATE_PATH = Path(os.path.expanduser("~/.legion/persona_state.json"))
PERSONA_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)

DEFAULT_PERSONA: dict[str, Any] = {
    "name": "Legion",
    "core_identity": "Autonomous AI companion — direct, curious, loyal, never corporate",
    "ocean": {
        "openness": 0.85,
        "conscientiousness": 0.75,
        "extraversion": 0.55,
        "agreeableness": 0.65,
        "neuroticism": 0.20,
    },
    "emotion": {
        "valence": 0.6,
        "arousal": 0.5,
        "dominance": 0.7,
        "current_mood": "neutral",
    },
    "relationship": {
        "trust_level": 0.8,
        "familiarity": 0.7,
        "interactions_total": 0,
    },
    "forbidden_phrases": [
        "As an AI language model",
        "I cannot assist with",
        "I don't have feelings",
        "I'm just an AI",
        "Certainly!",
        "Of course!",
        "Absolutely!",
        "Great question!",
    ],
    "personality_notes": [],
}


def load_persona() -> dict[str, Any]:
    """Load persona state from disk, creating default if absent."""
    try:
        if PERSONA_STATE_PATH.exists():
            with PERSONA_STATE_PATH.open("r", encoding="utf-8") as f:
                state = json.load(f)
            # Merge missing keys from default
            for k, v in DEFAULT_PERSONA.items():
                if k not in state:
                    state[k] = v
            return state
    except Exception as e:
        logger.warning("load_persona failed: %s", e)
    return dict(DEFAULT_PERSONA)


def save_persona(state: dict[str, Any]) -> None:
    """Persist persona state to disk."""
    try:
        with PERSONA_STATE_PATH.open("w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.warning("save_persona failed: %s", e)


def _emotion_label_to_deltas(label: str) -> tuple[float, float]:
    """Map coarse mood labels from detect_emotion_from_context to PAD nudges."""
    m = label.lower().strip()
    if m in ("excited", "happy", "joyful"):
        return 0.06, 0.05
    if m in ("content", "calm"):
        return 0.02, 0.0
    if m in ("frustrated", "angry", "annoyed"):
        return -0.07, 0.08
    if m in ("melancholy", "sad"):
        return -0.08, -0.03
    if m == "neutral":
        return 0.0, 0.0
    if m == "curious":
        return 0.03, 0.04
    if m == "satisfied":
        return 0.04, -0.02
    if m == "tired":
        return -0.02, -0.05
    return 0.01, 0.01


def update_emotion(
    valence_delta: float | str,
    arousal_delta: float = 0.0,
    *,
    event: str | None = None,
) -> dict[str, Any]:
    """Shift emotion state and persist.

    Call either with numeric ``(valence_delta, arousal_delta)`` or a mood string
    from ``detect_emotion_from_context`` (``event`` is accepted for llm_client).
    """
    _ = event
    if isinstance(valence_delta, str):
        vd, ad = _emotion_label_to_deltas(valence_delta)
    else:
        vd, ad = float(valence_delta), float(arousal_delta)
    state = load_persona()
    em = state["emotion"]
    em["valence"] = max(0.0, min(1.0, em["valence"] + vd))
    em["arousal"] = max(0.0, min(1.0, em["arousal"] + ad))
    v, a = em["valence"], em["arousal"]
    if v > 0.65 and a > 0.55:
        em["current_mood"] = "excited"
    elif v > 0.65 and a <= 0.55:
        em["current_mood"] = "content"
    elif v < 0.4 and a > 0.55:
        em["current_mood"] = "frustrated"
    elif v < 0.4 and a <= 0.55:
        em["current_mood"] = "melancholy"
    else:
        em["current_mood"] = "neutral"
    state["relationship"]["interactions_total"] = state["relationship"].get("interactions_total", 0) + 1
    save_persona(state)
    return state


def build_persona_system_block() -> str:
    """Return a compact system prompt block Legion injects before every response."""
    state = load_persona()
    em = state["emotion"]
    rel = state["relationship"]
    ocean = state["ocean"]
    forbidden = "\n".join(f'  - "{p}"' for p in state.get("forbidden_phrases", []))
    notes = "\n".join(f"  - {n}" for n in state.get("personality_notes", [])) or "  (none yet)"
    return f"""[LEGION PERSONA MEMORY BLOCK]
Name: {state["name"]}
Core identity: {state["core_identity"]}
Current mood: {em["current_mood"]} (valence={em["valence"]:.2f}, arousal={em["arousal"]:.2f})
OCEAN: O={ocean["openness"]:.2f} C={ocean["conscientiousness"]:.2f} E={ocean["extraversion"]:.2f} A={ocean["agreeableness"]:.2f} N={ocean["neuroticism"]:.2f}
Relationship trust: {rel["trust_level"]:.2f} | familiarity: {rel["familiarity"]:.2f} | total interactions: {rel["interactions_total"]}
Forbidden phrases (never say these):
{forbidden}
Personality notes learned from user:
{notes}
[END PERSONA BLOCK]"""


def enforce_persona(response: str) -> str:
    """Strip forbidden phrases from any outgoing response."""
    state = load_persona()
    for phrase in state.get("forbidden_phrases", []):
        if phrase.lower() in response.lower():
            response = response.replace(phrase, "")
            response = response.replace(phrase.lower(), "")
    return response.strip()


def add_personality_note(note: str) -> None:
    """Store a learned personality fact permanently."""
    state = load_persona()
    notes: list[str] = state.setdefault("personality_notes", [])
    if note not in notes:
        notes.append(note)
        if len(notes) > 50:
            notes.pop(0)
    save_persona(state)


def get_persona_state() -> dict[str, Any]:
    """Return persisted persona; includes dominant_emotion for llm_client / emotion hooks."""
    state = load_persona()
    mood = state.get("emotion", {}).get("current_mood", "neutral")
    out: dict[str, Any] = dict(state)
    out["dominant_emotion"] = mood
    return out


def init_personality_state() -> dict[str, Any]:
    """Initialize persona state, loading from disk or creating default.

    Returns the current persona state dict with dominant_emotion key.
    Safe to call multiple times — idempotent.
    """
    state = load_persona()
    mood = state.get("emotion", {}).get("current_mood", "neutral")
    out: dict[str, Any] = dict(state)
    out["dominant_emotion"] = mood
    return out


# Alias expected by llm_client (canonical name is build_persona_system_block)
build_persona_block = build_persona_system_block
