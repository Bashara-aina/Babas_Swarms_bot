"""Load optional skill manifests from config/legion_skills.json (additive)."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_CONFIG = Path(__file__).resolve().parent.parent / "config" / "legion_skills.json"

# When the user message matches no keywords, surface these first (stable, high-utility).
_FALLBACK_ROUTE_ORDER = [
    "computer_control",
    "code_generation",
    "deep_research",
    "memory_search",
    "deep_reasoning",
    "codebase_understanding",
    "multi_agent_swarm",
    "system_control",
    "email_management",
    "business_query",
    "location_advice",
    "jarvis_orchestrate",
    "github_intel",
    "runbook_maintenance",
    "strategic_simulation",
    "whatsapp_action",
]


def load_skills() -> list[dict[str, Any]]:
    if not _CONFIG.exists():
        return []
    try:
        data = json.loads(_CONFIG.read_text(encoding="utf-8"))
        skills = data.get("skills")
        return skills if isinstance(skills, list) else []
    except Exception as exc:
        logger.debug("legion_skills.json load failed: %s", exc)
        return []


def _score_routes_for_query(query: str) -> list[tuple[str, float]]:
    try:
        from core.autonomous_router import SKILL_PATTERNS
    except Exception:
        return []

    q = (query or "").lower().strip()
    if not q:
        return []
    scores: dict[str, float] = {}
    for skill, config in SKILL_PATTERNS.items():
        if skill == "conversation":
            continue
        sc = 0.0
        for kw in config.get("keywords", []) or []:
            k = (kw or "").lower()
            if not k:
                continue
            if k in q:
                sc += max(0.25, len(k.split()) * 0.25)
        if sc > 0:
            scores[skill] = sc
    return sorted(scores.items(), key=lambda x: (-x[1], x[0]))


def _autonomous_routes_block_for_query(query: str) -> str:
    """Rank autonomous routes by keyword overlap with the user message (saves tokens)."""
    if os.getenv("LEGION_AUTONOMOUS_SKILLS_PROMPT", "1").strip().lower() in (
        "0",
        "false",
        "no",
        "off",
    ):
        return ""
    try:
        from core.autonomous_router import SKILL_PATTERNS
    except Exception as exc:
        logger.debug("autonomous routes prompt skipped: %s", exc)
        return ""

    max_items = int(os.getenv("LEGION_AUTONOMOUS_SKILLS_TOP_N", "14"))
    max_items = max(6, min(max_items, 28))

    ranked = _score_routes_for_query(query)
    picked: list[str] = []
    if ranked:
        picked = [name for name, _ in ranked[:max_items]]
    else:
        for name in _FALLBACK_ROUTE_ORDER:
            if name in SKILL_PATTERNS and name != "conversation":
                picked.append(name)
            if len(picked) >= max_items:
                break
        for name in SKILL_PATTERNS:
            if name in ("conversation",) or name in picked:
                continue
            picked.append(name)
            if len(picked) >= max_items:
                break

    lines = [
        "[AUTONOMOUS ROUTES — plain-language → tool; order biased to this message]",
    ]
    for name in picked:
        spec = SKILL_PATTERNS.get(name)
        if not isinstance(spec, dict):
            continue
        desc = (spec.get("description") or "")[:120]
        handler = spec.get("handler", "")
        lines.append(f"- {name} → {handler}: {desc}")
    return "\n".join(lines)


def skills_prompt_block_for_query(user_message: str = "") -> str:
    """Skills + ranked autonomous routes for the current user turn."""
    skills = load_skills()
    lines: list[str] = []
    auto = _autonomous_routes_block_for_query(user_message)
    if auto:
        lines.append(auto)
    if skills:
        cap = int(os.getenv("LEGION_JSON_SKILLS_PROMPT_MAX", "24"))
        cap = max(4, min(cap, 60))
        lines.append("[REGISTERED SKILLS — config/legion_skills.json]")
        for s in skills[:cap]:
            if not isinstance(s, dict):
                continue
            name = s.get("name") or s.get("id") or "skill"
            desc = (s.get("description") or s.get("summary") or "")[:160]
            lines.append(f"- {name}: {desc}")
    return "\n\n".join(lines) if lines else ""


def skills_prompt_block() -> str:
    """Backward-compatible: query-agnostic fallback ranking."""
    return skills_prompt_block_for_query("")
