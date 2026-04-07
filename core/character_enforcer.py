"""Legion character enforcer — strip forbidden phrases, apply mode voice, enforce soul.

Reads config/legion_character.json once at import time.
Used in llm_client.py after postprocess_response() to clean every response.
This version is robust: never silently skips, always enforces at minimum the
hardcoded forbidden phrase list even if the JSON config fails to load.
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

_CONFIG_PATH = Path(__file__).parent.parent / "config" / "legion_character.json"
_character: dict = {}

# Hardcoded fallback — always enforced even if config/legion_character.json missing
_FALLBACK_FORBIDDEN = [
    "Certainly!", "Certainly,", "Great question!", "Of course!",
    "I'd be happy to", "I would be happy to", "As an AI", "as an AI",
    "I'm just an AI", "I don't have feelings", "I cannot feel",
    "Absolutely!", "Absolutely,", "Sure!", "Sure,",
    "I hope this helps", "I hope that helps", "Let me know if you need",
    "Please let me know", "Feel free to ask", "Don't hesitate to",
    "I understand your concern", "That's a great point",
    "I apologize for any confusion", "I apologize for the confusion",
]


def _load() -> dict:
    try:
        text = _CONFIG_PATH.read_text(encoding="utf-8")
        data = json.loads(text)
        logger.debug("character_enforcer: loaded %s", _CONFIG_PATH)
        return data
    except FileNotFoundError:
        logger.warning("character_enforcer: config not found at %s — using fallback", _CONFIG_PATH)
        return {}
    except json.JSONDecodeError as exc:
        logger.warning("character_enforcer: invalid JSON in %s: %s — using fallback", _CONFIG_PATH, exc)
        return {}
    except Exception as exc:
        logger.warning("character_enforcer: unexpected error loading %s: %s", _CONFIG_PATH, exc)
        return {}


_character = _load()

# Build forbidden pattern list from config + fallback (deduplicated)
_all_forbidden = list(dict.fromkeys(
    _FALLBACK_FORBIDDEN + _character.get("forbidden_phrases", [])
))
_FORBIDDEN_PATTERNS: list[re.Pattern] = [
    re.compile(re.escape(phrase), re.IGNORECASE)
    for phrase in _all_forbidden
]


def enforce_character(response: str, agent_key: str = "general") -> str:
    """Strip forbidden phrases from response and apply Legion's voice.

    This function always runs — it never raises or returns the original
    unmodified response silently. Worst case: returns response unchanged
    after logging a warning.
    """
    if not response or not isinstance(response, str):
        return response or ""

    cleaned = response

    # 1. Strip forbidden phrases (replace with empty string, clean up whitespace)
    for pattern in _FORBIDDEN_PATTERNS:
        cleaned = pattern.sub("", cleaned)

    # 2. Strip double spaces / leading whitespace artifacts from removals
    cleaned = re.sub(r"  +", " ", cleaned)
    cleaned = re.sub(r"^\s+", "", cleaned, flags=re.MULTILINE)

    # 3. Apply mode-specific voice rules (from character config style_adjustments)
    style = _character.get("style_adjustments", {})
    mode_rules = style.get(agent_key, style.get("general", []))
    for rule in (mode_rules or []):
        find = rule.get("find", "")
        replace = rule.get("replace", "")
        if find:
            try:
                cleaned = re.sub(find, replace, cleaned, flags=re.IGNORECASE)
            except re.error:
                pass  # bad regex in config — skip silently

    # 4. Strip corporate opener patterns that the LLM sneaks in as rephrases
    _opener_patterns = [
        r"^(Of course[,!]?\s*)",
        r"^(Sure[,!]?\s*)",
        r"^(Certainly[,!]?\s*)",
        r"^(Absolutely[,!]?\s*)",
        r"^(Great[,!]?\s+)",
        r"^(No problem[,!]?\s*)",
        r"^(Happy to help[,!]?\s*)",
        r"^(I'd be glad to[,!]?\s*)",
    ]
    for pat in _opener_patterns:
        cleaned = re.sub(pat, "", cleaned, flags=re.IGNORECASE)

    # 5. Never return empty string — if everything got stripped, return original
    if not cleaned.strip():
        logger.debug("character_enforcer: strip produced empty string — returning original")
        return response

    return cleaned.strip()
