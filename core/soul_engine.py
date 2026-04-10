"""Soul Engine — reads SOUL.md and beliefs.json on every prompt.

Legion's identity is a living document, not a config file. This engine:
- Injects SOUL.md content at the top of every system prompt
- Surfaces Legion's current opinions from beliefs.json
- Tracks pending follow-ups Legion should raise proactively
- Lets Legion update its own beliefs and follow-up list at runtime

SOUL.md lives at the repo root and is read fresh each turn (no caching —
it's small enough that the I/O cost is negligible).
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_SOUL_ENABLED = os.getenv("LEGION_SOUL_ENABLED", "true").strip().lower() not in (
    "0", "false", "no", "off",
)

SOUL_PATH = Path(__file__).resolve().parent.parent / "SOUL.md"
BELIEFS_PATH = Path(__file__).resolve().parent.parent / "data" / "beliefs.json"


# ── Read helpers ──────────────────────────────────────────────────────────────

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
        beliefs.setdefault("things_to_follow_up", []).append({
            "task": task,
            "added_at": datetime.now().isoformat(),
            "done": False,
        })
        beliefs["last_updated"] = datetime.now().isoformat()
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
        BELIEFS_PATH.write_text(
            json.dumps(beliefs, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info("[SoulEngine] Bashara fact updated: %s = %s", key, value[:40])
    except Exception as exc:
        logger.warning("[SoulEngine] update_bashara_fact failed: %s", exc)


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


# ── Context builder — called at the top of every prompt ──────────────────────

def build_soul_context() -> str:
    """
    Build the soul + beliefs block injected at the VERY TOP of every system prompt.

    This is what gives Legion a genuine identity — a living document it maintains
    itself, not static config baked into code.

    Gated by LEGION_SOUL_ENABLED env var (default: true).
    """
    if not _SOUL_ENABLED:
        return ""

    soul = read_soul()
    beliefs = read_beliefs()
    stances = beliefs.get("stances", {})
    followups = get_pending_followups()

    lines: list[str] = []

    if soul:
        lines.append("[LEGION SOUL — read this before every response]")
        lines.append(soul.strip())
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
