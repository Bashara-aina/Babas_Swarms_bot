"""tools/skill_loader.py — Load and inject domain knowledge into agent prompts.

Skills are markdown files in the skills/ directory. The loader maps agent keys
to relevant skills and injects them into the system prompt before LLM calls.
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

SKILLS_DIR = Path(__file__).parent.parent / "skills"

# Map agent keys to relevant skill files (by filename without .md)
_AGENT_SKILLS: dict[str, list[str]] = {
    "coding":     ["python_patterns", "testing_patterns"],
    "debug":      ["debugging", "python_patterns"],
    "architect":  ["python_patterns", "security_checklist"],
    "analyst":    ["python_patterns"],
    "researcher": [],
    "reviewer":   ["python_patterns", "security_checklist", "testing_patterns"],
    "devops":     ["security_checklist"],
    "general":    [],
}

# Cache loaded skills in memory
_cache: dict[str, str] = {}


def _load_skill(name: str) -> str:
    """Load a skill markdown file, caching the result."""
    if name in _cache:
        return _cache[name]
    path = SKILLS_DIR / f"{name}.md"
    if not path.exists():
        logger.debug("Skill file not found: %s", path)
        return ""
    text = path.read_text(errors="replace").strip()
    _cache[name] = text
    return text


def get_skills_for_agent(agent_key: str, max_chars: int = 2000) -> str:
    """Return concatenated skill text for an agent, capped at max_chars.

    Returns empty string if no skills are mapped or files don't exist.
    """
    skill_names = _AGENT_SKILLS.get(agent_key, [])
    if not skill_names:
        return ""

    parts: list[str] = []
    used = 0
    for name in skill_names:
        content = _load_skill(name)
        if not content:
            continue
        if used + len(content) > max_chars:
            # Include partial if there's room for at least 200 chars
            remaining = max_chars - used
            if remaining > 200:
                parts.append(content[:remaining] + "\n…(truncated)")
            break
        parts.append(content)
        used += len(content)

    if not parts:
        return ""
    return "## Reference Knowledge\n\n" + "\n\n---\n\n".join(parts) + "\n"
