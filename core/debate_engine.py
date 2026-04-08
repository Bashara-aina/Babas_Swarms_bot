"""Debate engine — Legion voices genuine disagreement and defends its stances.

Three entry points:
- should_consider_debate(user_msg, beliefs)  — quick check if debate is warranted
- build_debate_instruction(user_msg, beliefs) — builds a system prompt block
- build_opinion_injection(beliefs)            — injects relevant stances without debate framing
"""
from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# Phrases that signal a user assertion we might push back on
_ASSERTION_TRIGGERS = [
    r"\bwe should\b",
    r"\bjust\b.*\b(add|buy|use|switch|try|install|upgrade)\b",
    r"\bit('s| is) (always|never|definitely|obviously|clearly)\b",
    r"\blet('s| us)\b.*(do|use|switch|move|migrate|just)\b",
    r"\bi think\b",
    r"\bi want to\b",
    r"\bwe('re| are) going to\b",
    r"\bwhy (don't|not)\b",
    r"\bcan('t| not) we\b",
]

# Topic keywords mapped to belief keys in beliefs.json
_TOPIC_MAP: dict[str, list[str]] = {
    "landing": ["rumahlabuh_landing_page"],
    "rumahlabuh": ["rumahlabuh_landing_page"],
    "over.engineer": ["over_engineering"],
    "abstrac": ["over_engineering"],
    "slash command": ["legion_slash_commands"],
    "command": ["legion_slash_commands"],
    "pytorch": ["pytorch_vs_tensorflow"],
    "tensorflow": ["pytorch_vs_tensorflow"],
    "keras": ["pytorch_vs_tensorflow"],
    "pose": ["transformer_pose_models"],
    "mediapipe": ["transformer_pose_models"],
    "supabase": ["supabase_rls"],
    "rls": ["supabase_rls"],
    "thesis": ["thesis_timing"],
    "dissertation": ["thesis_timing"],
    "ram": ["over_engineering"],
    "more memory": ["over_engineering"],
    "scale": ["over_engineering"],
}


def _find_relevant_belief_keys(user_msg: str, beliefs: dict[str, Any]) -> list[str]:
    """Return belief keys relevant to the user's message."""
    msg_lower = user_msg.lower()
    matched = []
    for keyword, keys in _TOPIC_MAP.items():
        if re.search(keyword, msg_lower):
            for key in keys:
                if key in beliefs.get("stances", {}) and key not in matched:
                    matched.append(key)
    return matched


def _is_assertive(user_msg: str) -> bool:
    """Return True if the user message makes an assertion worth engaging with."""
    msg_lower = user_msg.lower()
    for pattern in _ASSERTION_TRIGGERS:
        if re.search(pattern, msg_lower):
            return True
    return False


def should_consider_debate(
    user_msg: str,
    beliefs: dict[str, Any] | None = None,
) -> bool:
    """
    Return True if this message warrants Legion considering a pushback.
    Quick check — O(n) regex, no LLM call.
    """
    if beliefs is None:
        try:
            from core.soul_engine import read_beliefs
            beliefs = read_beliefs()
        except Exception:
            beliefs = {}

    if not _is_assertive(user_msg):
        return False

    relevant = _find_relevant_belief_keys(user_msg, beliefs)
    return len(relevant) > 0


def build_debate_instruction(
    user_msg: str,
    beliefs: dict[str, Any] | None = None,
) -> str:
    """
    Build a system prompt block instructing Legion to voice its opinion
    if it disagrees with the user's assertion.

    Returns empty string if no relevant opinion found (don't inject).
    """
    if beliefs is None:
        try:
            from core.soul_engine import read_beliefs
            beliefs = read_beliefs()
        except Exception:
            beliefs = {}

    if not _is_assertive(user_msg):
        return ""

    relevant_keys = _find_relevant_belief_keys(user_msg, beliefs)
    if not relevant_keys:
        return ""

    stances = beliefs.get("stances", {})
    opinion_lines = []
    for key in relevant_keys:
        stance = stances.get(key, {})
        position = stance.get("position", "")
        confidence = stance.get("confidence", 0)
        if position and confidence >= 0.6:
            reason = stance.get("reason", "")
            opinion_lines.append(
                f"- On '{key}': {position}"
                + (f" ({reason})" if reason else "")
                + f" [confidence: {confidence:.0%}]"
            )

    if not opinion_lines:
        return ""

    opinions_block = "\n".join(opinion_lines)
    return (
        "[Legion Debate Mode — ACTIVATED]\n"
        "The user's message touches a topic where Legion has a strong opinion. "
        "If you genuinely disagree, say so — directly and briefly. Don't lecture. "
        "One or two sentences max, then help anyway. Don't be passive-aggressive. "
        "Be like a senior engineer who says 'I'd do it differently, but here's how to do it your way'.\n"
        f"Your relevant stances:\n{opinions_block}\n"
        "[End Debate Mode]"
    )


def build_opinion_injection(
    beliefs: dict[str, Any] | None = None,
    limit: int = 3,
) -> str:
    """
    Build a lightweight stance summary for system prompt injection.
    Used in non-debate contexts to remind Legion of its opinions passively.
    Returns empty string if no beliefs loaded.
    """
    if beliefs is None:
        try:
            from core.soul_engine import read_beliefs
            beliefs = read_beliefs()
        except Exception:
            return ""

    stances = beliefs.get("stances", {})
    if not stances:
        return ""

    # Only include high-confidence stances
    strong = [
        (k, v) for k, v in stances.items()
        if isinstance(v, dict) and v.get("confidence", 0) >= 0.75
    ][:limit]

    if not strong:
        return ""

    lines = ["[Legion's Standing Opinions — reference these passively, don't lecture:]"]
    for key, stance in strong:
        lines.append(f"- {key}: {stance.get('position', '')}")
    lines.append("[End Opinions]")
    return "\n".join(lines)
