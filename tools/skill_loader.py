"""tools/skill_loader.py — Load and inject domain knowledge into agent prompts.

Skills are markdown files in the skills/ directory. Each skill teaches the agent
a specific behaviour (security review, debugging, cost optimisation, E2E testing, etc.).

Agent → skill mappings are defined in _AGENT_SKILLS. Skills are loaded once
and cached in memory with mtime-based live-reload support.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)

SKILLS_DIR = Path(__file__).parent.parent / "skills"

# ---------------------------------------------------------------------------
# Agent → skill file mapping (name = filename without .md inside skills/)
# ---------------------------------------------------------------------------
_AGENT_SKILLS: dict[str, list[str]] = {
    "coding":     [
        "python-patterns",
        "testing-patterns",
        "debugging-strategies",
        "tool-use-guardian",
        "api-cost-optimizer",
        "supabase-engineer",
    ],
    "debug":      [
        "debugging-strategies",
        "python-patterns",
        "security-auditor",
        "tool-use-guardian",
        "supabase-engineer",
    ],
    "architect":  [
        "brainstorming",
        "python-patterns",
        "security-auditor",
        "rag-engineer",
        "supabase-engineer",
    ],
    "analyst":    [
        "brainstorming",
        "rag-engineer",
        "prompt-engineer",
        "python-patterns",
        "supabase-engineer",
    ],
    "researcher": [
        "rag-engineer",
        "prompt-engineer",
        "brainstorming",
    ],
    "reviewer":   [
        "security-auditor",
        "python-patterns",
        "testing-patterns",
        "debugging-strategies",
        "e2e-tester",
    ],
    "devops":     [
        "security-auditor",
        "tool-use-guardian",
        "api-cost-optimizer",
        "supabase-engineer",
        "e2e-tester",
    ],
    "general":    [
        "brainstorming",
        "prompt-engineer",
        "api-cost-optimizer",
        "recallmax",
        "supabase-engineer",
    ],
    "pm":         [
        "brainstorming",
        "prompt-engineer",
    ],
    "marketer":   [
        "brainstorming",
        "prompt-engineer",
    ],
    "e2e":        [
        "e2e-tester",
        "supabase-engineer",
        "debugging-strategies",
        "security-auditor",
    ],
    "database":   [
        "supabase-engineer",
        "security-auditor",
        "debugging-strategies",
    ],
}

# Cache: name -> (content, mtime)
_cache: dict[str, tuple[str, float]] = {}


def _load_skill(name: str) -> str:
    """Load a skill file, using mtime-based cache invalidation for live-reload."""
    # Support both flat (skills/name.md) and nested (skills/name/SKILL.md)
    # Also support underscore variants (python_patterns vs python-patterns)
    candidates = [
        SKILLS_DIR / f"{name}.md",
        SKILLS_DIR / name / "SKILL.md",
        SKILLS_DIR / f"{name.replace('-', '_')}.md",
        SKILLS_DIR / f"{name.replace('_', '-')}.md",
    ]
    path: Path | None = None
    for c in candidates:
        if c.exists():
            path = c
            break
    if path is None:
        logger.debug("Skill not found: %s (tried %s)", name, [str(c) for c in candidates])
        return ""

    try:
        mtime = path.stat().st_mtime
    except OSError:
        return ""

    cached = _cache.get(name)
    if cached and cached[1] == mtime:
        return cached[0]

    text = path.read_text(errors="replace").strip()
    _cache[name] = (text, mtime)
    return text


def get_skills_for_agent(agent_key: str, max_chars: int = 6000) -> str:
    """Return concatenated skill text for an agent, capped at max_chars.

    Returns empty string if no skills mapped or files missing.
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
            remaining = max_chars - used
            if remaining > 300:
                parts.append(content[:remaining] + "\n\u2026(truncated)")
            break
        parts.append(content)
        used += len(content)

    if not parts:
        return ""
    header = f"## Reference Skills ({len(parts)} loaded)\n\n"
    return header + "\n\n---\n\n".join(parts) + "\n"


def list_skills() -> List[str]:
    """Return all available skill names (for /skills command)."""
    if not SKILLS_DIR.exists():
        return []
    names: list[str] = []
    for p in sorted(SKILLS_DIR.iterdir()):
        if p.is_file() and p.suffix == ".md":
            names.append(p.stem)
        elif p.is_dir() and (p / "SKILL.md").exists():
            names.append(p.name)
    return names


def get_skill_content(name: str) -> str:
    """Get raw content of a single named skill (for /skill <name> command)."""
    return _load_skill(name)


def invalidate_cache() -> None:
    """Force-clear the in-memory skill cache (for hot-reload)."""
    _cache.clear()
    logger.info("Skill cache invalidated")
