"""Legion character enforcer — strip forbidden phrases and apply mode voice.

Reads config/legion_character.json once at import time.
Used in llm_client.py after postprocess_response() to clean every response.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

_CONFIG_PATH = Path(__file__).parent.parent / "config" / "legion_character.json"
_character: dict = {}


def _load() -> dict:
    try:
        return json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("character_enforcer: could not load %s: %s", _CONFIG_PATH, exc)
        return {}


_character = _load()

_FORBIDDEN_PATTERNS: list[re.Pattern] = [
    re.compile(re.escape(phrase), re.IGNORECASE)
    for phrase in _character.get("forbidden_phrases", [])
]


def enforce_character(response: str, agent_key: str = "general") -> str:
    """Strip forbidden phrases and prepend mode-specific voice note if needed."""
    if not response:
        return response

    # Strip each forbidden phrase (replace with empty string, clean up double spaces)
    cleaned = response
    for pattern in _FORBIDDEN_PATTERNS:
        cleaned = pattern.sub("", cleaned)

    # Collapse multiple spaces/newlines introduced by removals
    cleaned = re.sub(r"  +", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = cleaned.strip()

    # If mode_notes has guidance for this agent_key and the response is very short
    # after stripping, just return as-is (avoid empty responses)
    if not cleaned and response.strip():
        return response.strip()

    return cleaned


def reload_character() -> None:
    """Reload character config from disk (useful after self-upgrade edits the JSON)."""
    global _character, _FORBIDDEN_PATTERNS
    _character = _load()
    _FORBIDDEN_PATTERNS = [
        re.compile(re.escape(phrase), re.IGNORECASE)
        for phrase in _character.get("forbidden_phrases", [])
    ]
    logger.info("character_enforcer: reloaded %d forbidden phrases", len(_FORBIDDEN_PATTERNS))
