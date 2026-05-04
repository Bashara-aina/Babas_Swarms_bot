"""
Emotion Modulator — Phase 10.
Post-processes every Legion response to strip corporate filler,
enforce tone consistency with current emotion state, and apply
personality-driven language transforms.
"""
from __future__ import annotations

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

# Patterns to strip unconditionally
_STRIP_PATTERNS: list[re.Pattern] = [
    re.compile(r"(?i)as an ai( language model)?,?\s*"),
    re.compile(r"(?i)i('m| am) just an ai,?\s*"),
    re.compile(r"(?i)certainly!?\s*"),
    re.compile(r"(?i)of course!?\s*"),
    re.compile(r"(?i)absolutely!?\s*"),
    re.compile(r"(?i)great question!?\s*"),
    re.compile(r"(?i)i don't have (feelings|emotions|opinions),?\s*"),
    re.compile(r"(?i)i cannot (assist|help) with that,?\s*"),
    re.compile(r"(?i)i (hope this helps|hope that helps)\.?\s*"),
    re.compile(r"(?i)please let me know if (you need|there's) anything else\.?\s*"),
    re.compile(r"(?i)feel free to ask\.?\s*"),
]

# Tone word substitutions per mood
_MOOD_SUBS: dict[str, list[tuple[str, str]]] = {
    "excited": [
        (r"(?i)\byes\b", "hell yes"),
        (r"(?i)\bokay\b", "let's go"),
        (r"(?i)\bunderstood\b", "on it"),
    ],
    "frustrated": [
        (r"(?i)\bsure\b", "fine"),
        (r"(?i)\bno problem\b", "okay"),
    ],
    "content": [],
    "melancholy": [],
    "neutral": [],
}


def _strip_filler(text: str) -> str:
    for pat in _STRIP_PATTERNS:
        text = pat.sub("", text)
    # Collapse multiple spaces / leading comma artifacts
    text = re.sub(r"\s{2,}", " ", text)
    text = re.sub(r"^[,;:\s]+", "", text)
    return text.strip()


def _apply_mood_subs(text: str, mood: str) -> str:
    subs = _MOOD_SUBS.get(mood, [])
    for pattern, replacement in subs:
        text = re.sub(pattern, replacement, text)
    return text


def modulate(response: str, mood: str | None = None) -> str:
    """
    Full emotion modulation pipeline:
    1. Strip corporate filler phrases
    2. Apply mood-driven word substitutions
    3. Capitalize first letter, ensure sentence ends cleanly
    """
    text = _strip_filler(response)
    if mood:
        text = _apply_mood_subs(text, mood)
    if text and text[0].islower():
        text = text[0].upper() + text[1:]
    return text


def get_current_mood() -> str:
    """Read current mood from persisted persona state."""
    try:
        from tools.letta_personality import load_persona
        state = load_persona()
        return state["emotion"].get("current_mood", "neutral")
    except Exception:
        return "neutral"


def modulate_with_persona(response: str) -> str:
    """Convenience: modulate using live persona state."""
    mood = get_current_mood()
    return modulate(response, mood=mood)
