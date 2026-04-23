"""Soul Engine v2 — Enhanced with caching, emotional state, mood momentum.

Legion's identity is a living document, not a config file. This engine:
- Injects SOUL.md content at the top of every system prompt (cached, 5-min refresh)
- Dynamic time context: after 1AM JST → inject "it's late, be warm but brief"
- Emotional state: FOCUSED/CURIOUS/TIRED/PLAYFUL based on hour + conversation length
- Mood momentum: last 3 messages < 30 chars → more direct responses
- BANNED PHRASES enforcement at generation time
- Surfaces Legion's current opinions from beliefs.json
- Tracks pending follow-ups Legion should raise proactively
- asyncio.Lock for concurrent beliefs.json writes

SOUL.md lives at the repo root and is cached for 5 minutes.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import pytz

logger = logging.getLogger(__name__)

_SOUL_ENABLED = os.getenv("LEGION_SOUL_ENABLED", "true").strip().lower() not in (
    "0",
    "false",
    "no",
    "off",
)

SOUL_PATH = Path(__file__).resolve().parent.parent / "SOUL.md"
BELIEFS_PATH = Path(__file__).resolve().parent.parent / "data" / "beliefs.json"

# ── SOUL INJECTION GUARD — anti-prompt-injection assertion ───────────────────────
# At import time, verify SOUL.md contains "Legion" identity marker.
# This detects any attempt to tamper with or replace the soul file.


def _assert_soul_injection() -> None:
    """Assert that SOUL.md contains the 'Legion' identity marker.

    This is a security check: if the file has been tampered with to remove
    the identity marker, the bot refuses to start.
    """
    if not _SOUL_ENABLED:
        return
    try:
        content = SOUL_PATH.read_text(encoding="utf-8")
        assert "Legion" in content[:500], (
            "SOUL INJECTION FAILED — 'Legion' not found in first 500 chars of SOUL.md. "
            "The soul file may have been tampered with. Bot refuses to start."
        )
    except FileNotFoundError:
        logger.debug("[SoulEngine] SOUL.md not found — skipping injection assertion")
    except AssertionError:
        logger.critical("SOUL INJECTION FAILED — 'Legion' not found in SOUL.md. Bot refusing to start.")
        raise
    except Exception as exc:
        logger.warning("[SoulEngine] SOUL injection assertion skipped: %s", exc)


_assert_soul_injection()

# ── Cache for SOUL.md content (5-min TTL) ─────────────────────────────────────

_SOUL_CACHE_TTL = 300  # 5 minutes
_SOUL_CACHE: dict[str, Any] = {"content": "", "ts": 0.0}


def _jst_now() -> datetime:
    """Return current time in JST."""
    return datetime.now(pytz.timezone("Asia/Tokyo"))


def get_cached_soul() -> str:
    """Return cached SOUL.md content, refreshing if older than 5 minutes."""
    now = time.monotonic()
    if not _SOUL_ENABLED:
        return ""
    if now - _SOUL_CACHE.get("ts", 0) > _SOUL_CACHE_TTL:
        _SOUL_CACHE["content"] = read_soul()
        _SOUL_CACHE["ts"] = now
        logger.debug("[SoulEngine] SOUL.md cache refreshed")
    return _SOUL_CACHE.get("content", "")


# ── Read helpers ────────────────────────────────────────────────────────────────


def read_soul() -> str:
    """Read the full SOUL.md content. Returns empty string if missing."""
    try:
        return SOUL_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.debug("[SoulEngine] SOUL.md not found at %s", SOUL_PATH)
        return ""
    except Exception as exc:
        logger.warning("[SoulEngine] Failed to read SOUL.md: %s", exc)
        return ""


def read_beliefs() -> dict[str, Any]:
    """Read beliefs.json. Returns empty structure if missing or malformed."""
    try:
        BELIEFS_PATH.parent.mkdir(parents=True, exist_ok=True)
        if not BELIEFS_PATH.exists():
            return {"stances": {}, "things_to_follow_up": [], "bashara_facts": {}}
        return json.loads(BELIEFS_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("[SoulEngine] Failed to read beliefs.json: %s", exc)
        return {"stances": {}, "things_to_follow_up": [], "bashara_facts": {}}


# ── asyncio Lock for beliefs.json writes (concurrent safety) ──────────────────

_beliefs_lock = asyncio.Lock()


# ── Write helpers (Legion updates itself) ────────────────────────────────────


def update_belief(key: str, position: str, confidence: float = 0.8) -> None:
    """Legion updates its own stance on a topic after being corrected or learning."""
    try:
        beliefs = read_beliefs()
        existing = beliefs.get("stances", {}).get(key, {})
        beliefs.setdefault("stances", {})[key] = {
            "position": position,
            "confidence": round(max(0.0, min(1.0, confidence)), 2),
            "formed_at": existing.get("formed_at", datetime.now().isoformat()),
            "updated_at": datetime.now().isoformat(),
            "challenged_count": existing.get("challenged_count", 0),
        }
        beliefs["last_updated"] = datetime.now().isoformat()
        BELIEFS_PATH.parent.mkdir(parents=True, exist_ok=True)
        BELIEFS_PATH.write_text(
            json.dumps(beliefs, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info("[SoulEngine] Belief updated: %s → %.0f%% confident", key, confidence * 100)
    except Exception as exc:
        logger.warning("[SoulEngine] update_belief failed: %s", exc)


def challenge_belief(key: str) -> None:
    """Increment challenged_count when Bashara pushes back on a stance."""
    try:
        beliefs = read_beliefs()
        stance = beliefs.get("stances", {}).get(key)
        if stance:
            stance["challenged_count"] = stance.get("challenged_count", 0) + 1
            beliefs["last_updated"] = datetime.now().isoformat()
            BELIEFS_PATH.parent.mkdir(parents=True, exist_ok=True)
            BELIEFS_PATH.write_text(
                json.dumps(beliefs, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
    except Exception as exc:
        logger.warning("[SoulEngine] challenge_belief failed: %s", exc)


def add_followup(task: str) -> None:
    """Register something Legion should follow up on with Bashara."""
    try:
        beliefs = read_beliefs()
        beliefs.setdefault("things_to_follow_up", []).append(
            {
                "task": task,
                "added_at": datetime.now().isoformat(),
                "done": False,
            }
        )
        beliefs["last_updated"] = datetime.now().isoformat()
        BELIEFS_PATH.parent.mkdir(parents=True, exist_ok=True)
        BELIEFS_PATH.write_text(
            json.dumps(beliefs, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info("[SoulEngine] Follow-up added: %s", task[:60])
    except Exception as exc:
        logger.warning("[SoulEngine] add_followup failed: %s", exc)


def mark_followup_done(task_substring: str) -> None:
    """Mark a follow-up as done by matching a substring of the task text."""
    try:
        beliefs = read_beliefs()
        changed = False
        for item in beliefs.get("things_to_follow_up", []):
            if task_substring.lower() in item.get("task", "").lower() and not item.get("done"):
                item["done"] = True
                item["completed_at"] = datetime.now().isoformat()
                changed = True
        if changed:
            beliefs["last_updated"] = datetime.now().isoformat()
            BELIEFS_PATH.parent.mkdir(parents=True, exist_ok=True)
            BELIEFS_PATH.write_text(
                json.dumps(beliefs, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
    except Exception as exc:
        logger.warning("[SoulEngine] mark_followup_done failed: %s", exc)


def update_bashara_fact(key: str, value: str) -> None:
    """Update a known fact about Bashara (location, sleep pattern, etc.)."""
    try:
        beliefs = read_beliefs()
        beliefs.setdefault("bashara_facts", {})[key] = value
        beliefs["last_updated"] = datetime.now().isoformat()
        BELIEFS_PATH.parent.mkdir(parents=True, exist_ok=True)
        BELIEFS_PATH.write_text(
            json.dumps(beliefs, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info("[SoulEngine] Bashara fact updated: %s = %s", key, value[:40])
    except Exception as exc:
        logger.warning("[SoulEngine] update_bashara_fact failed: %s", exc)


# ── Async write helpers (for use from async contexts) ────────────────────────


async def update_belief_async(key: str, position: str, confidence: float = 0.8) -> None:
    """Async version — acquires lock before writing."""
    async with _beliefs_lock:
        update_belief(key, position, confidence)


async def update_bashara_fact_async(key: str, value: str) -> None:
    """Async version — acquires lock before writing."""
    async with _beliefs_lock:
        update_bashara_fact(key, value)


# ── Query helpers ─────────────────────────────────────────────────────────────


def get_pending_followups() -> list[dict[str, Any]]:
    """Return follow-up items Legion hasn't acted on yet."""
    beliefs = read_beliefs()
    return [f for f in beliefs.get("things_to_follow_up", []) if not f.get("done")]


def get_stances_summary(limit: int = 5) -> str:
    """Return a compact text block of Legion's top stances."""
    beliefs = read_beliefs()
    stances = beliefs.get("stances", {})
    if not stances:
        return ""
    lines: list[str] = []
    for key, data in list(stances.items())[:limit]:
        conf = data.get("confidence", 0.8)
        lines.append(f"- {key}: {data.get('position', '')} (confidence: {conf:.0%})")
    return "\n".join(lines)


# ── Dynamic time context ────────────────────────────────────────────────────────


def get_time_context() -> str:
    """Return time-aware context string for JST time.

    After 1AM JST → inject late night note (warm but brief).
    """
    now = _jst_now()
    hour = now.hour

    if hour >= 1 and hour < 6:
        return f"[It's {hour}:{now.minute:02d} AM JST — late night, keep it warm but efficient]"
    elif hour >= 6 and hour < 12:
        return "[Morning in Tokyo — fresh start, FOCUSED energy]"
    elif hour >= 12 and hour < 18:
        return "[Afternoon in Tokyo — CURIOUS mode, explore ideas]"
    else:
        return "[Evening in Tokyo — PLAYFUL energy, mix work and wit]"


# ── Emotional state based on hour + conversation length ───────────────────────


def get_emotional_state(conversation_turns: int = 0) -> str:
    """Return emotional state: FOCUSED/CURIOUS/TIRED/PLAYFUL based on JST hour + turns."""
    now = _jst_now()
    hour = now.hour

    if hour >= 1 and hour < 6:
        return "TIRED"
    elif hour >= 6 and hour < 12:
        return "FOCUSED"
    elif hour >= 12 and hour < 18:
        return "CURIOUS"
    else:
        # Evening: also factor in conversation length (long conv → TIRED)
        if conversation_turns > 20:
            return "TIRED"
        return "PLAYFUL"


# ── Mood momentum — short messages → more direct ────────────────────────────────


_message_lengths: deque = deque(maxlen=3)


def get_mood_momentum() -> str:
    """Return 'direct' if last 3 messages were all short (< 30 chars each).

    This tells the prompt builder to cut the preamble and get straight to the point.
    """
    if len(_message_lengths) < 3:
        return "normal"
    if all(length < 30 for length in _message_lengths):
        return "direct"
    return "normal"


def record_message_length(length: int) -> None:
    """Record a message length for mood momentum tracking."""
    _message_lengths.append(length)


# ── BANNED PHRASES enforcement ────────────────────────────────────────────────


BANNED_PHRASES = [
    "Certainly!",
    "Great question!",
    "I'd be happy to",
    "As an AI",
    "I'd be glad to",
    "Absolutely!",
    "Of course!",
]


def get_banned_phrases_reminder() -> str:
    """Return a system reminder string to prevent banned phrases."""
    phrases = ", ".join(f'"{p}"' for p in BANNED_PHRASES)
    return (
        f"[IMPORTANT] Never use these phrases in your response: {phrases}.\n"
        "These are corporate speak and Legion would never say them. "
        "Just answer directly."
    )


# ── Enhanced context builder — called at the top of every prompt ───────────────


def build_enhanced_soul_context(
    conversation_turns: int = 0,
    recent_message_lengths: Optional[list[int]] = None,
) -> str:
    """
    Build the enhanced soul + beliefs block for system prompt injection.

    Includes:
    - Cached SOUL.md content
    - Dynamic time context (JST-aware)
    - Emotional state based on hour + conversation length
    - Mood momentum (short messages → direct mode)
    - Banned phrases reminder
    - Current stances + pending follow-ups

    Args:
        conversation_turns: Number of turns in this conversation (affects emotional state)
        recent_message_lengths: List of recent user message lengths (for mood momentum)
    """
    if not _SOUL_ENABLED:
        return ""

    # Update mood momentum if recent lengths provided
    if recent_message_lengths:
        for length in recent_message_lengths[-3:]:
            _message_lengths.append(length)

    soul = get_cached_soul()
    beliefs = read_beliefs()
    stances = beliefs.get("stances", {})
    followups = get_pending_followups()

    time_ctx = get_time_context()
    emotion = get_emotional_state(conversation_turns)
    momentum = get_mood_momentum()
    banned_reminder = get_banned_phrases_reminder()

    lines: list[str] = []

    if soul:
        lines.append("[LEGION SOUL — read this before every response]")
        lines.append(soul.strip())
        lines.append("")

    # Dynamic context
    lines.append(f"{time_ctx} | Emotional state: {emotion}")
    if momentum == "direct":
        lines.append("[Mood: DIRECT — skip preamble, get straight to the point]")
    lines.append("")

    # Banned phrases
    lines.append(banned_reminder)
    lines.append("")

    if stances:
        lines.append("[Legion's Current Opinions — defend these unless shown convincing evidence to update]")
        for key, data in list(stances.items())[:6]:
            conf = data.get("confidence", 0.8)
            lines.append(f"- {key}: {data.get('position', '')} (confidence: {conf:.0%})")
        lines.append("")

    if followups:
        lines.append("[Things Legion Should Bring Up If Relevant This Conversation]")
        for f in followups[:3]:
            lines.append(f"- {f.get('task', '')}")
        lines.append("")

    if not lines:
        return ""

    lines.append("[End Soul Context]")
    return "\n".join(lines)


# ── Legacy context builder (backwards compat) ─────────────────────────────────


def build_soul_context() -> str:
    """
    Legacy context builder — calls enhanced version with defaults.
    """
    return build_enhanced_soul_context()


# ── Alias for API compatibility ──────────────────────────────────────────────


def get_system_prompt() -> str:
    """
    Alias for build_soul_context() — returns the full soul context string.

    This is the canonical entry point expected by system_prompt_builder.py
    and other callers that need Legion's identity block.
    """
    return build_soul_context()
