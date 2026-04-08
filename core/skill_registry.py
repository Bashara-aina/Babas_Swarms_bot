"""Load optional skill manifests from config/legion_skills.json (additive)."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_CONFIG = Path(__file__).resolve().parent.parent / "config" / "legion_skills.json"


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


def skills_prompt_block() -> str:
    skills = load_skills()
    if not skills:
        return ""
    lines = ["[REGISTERED SKILLS — use when relevant]"]
    for s in skills[:40]:
        if not isinstance(s, dict):
            continue
        name = s.get("name") or s.get("id") or "skill"
        desc = (s.get("description") or s.get("summary") or "")[:160]
        lines.append(f"- {name}: {desc}")
    return "\n".join(lines)
