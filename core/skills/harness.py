"""M2.7 Skill Harness — TIER 1-4 contextual skill loading system.

Built on top of core/skills/registry.py. Dynamically loads skills from
~/.claude/skills/ based on task type and domain context.

TIER DISCIPLINE (from M2.7 Full Capability Activation Section F1):
  TIER 1 (always):      next-js-app-router, typescript-strict
  TIER 2 (by type):     supabase-realtime, stripe-integration, recharts-dataviz
  TIER 3 (by domain):   indonesian-market, property-valuation, salary-benchmark
  TIER 4 (by quality):  security-audit, a11y-compliance, conventional-commits

Skill loading is MANDATORY at task start:
  "Loading skills: [list] for [task type]"

Reference: M2.7 Full Capability Activation — Skill Harness (Section F1)
"""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

SKILLS_DIR = Path.home() / ".claude" / "skills"

# ---------------------------------------------------------------------------
# TIER DEFINITIONS
# ---------------------------------------------------------------------------

# TIER 1 — Always loaded (base skills for this project)
TIER_1: dict[str, str] = {
    "typescript-strict": "TypeScript strict mode, no-any policy, Zod validation",
    "next-js-app-router": "Next.js App Router patterns, Server Components, loading.tsx",
}

# TIER 2 — By feature / task type
TIER_2: dict[str, list[str]] = {
    "feature": [
        "supabase-realtime",  # realtime features
        "stripe-integration",  # payments
        "recharts-dataviz",   # charts
        "next-api-routes",     # API endpoints
    ],
    "bugfix": [
        "debugging-best-practices",  # systematic debugging
    ],
    "refactor": [
        "refactoring-patterns",  # safe refactoring
    ],
    "security": [
        "security-audit",  # security review
    ],
    "frontend": [
        "shadcn-patterns",   # component composition
        "ui-ux-pro-max",    # design system
    ],
    "backend": [
        "supabase-rls",    # RLS patterns
        "postgres-best-practices",  # DB patterns
    ],
}

# TIER 3 — By domain (Bashara's specific context)
TIER_3: dict[str, list[str]] = {
    "cekwajar": [
        "indonesian-market",     # IDR, Bahasa Indonesia, local payments
        "property-valuation",    # NJOP, tanah, wajar-tanah
        "salary-benchmark",       # wajar-gaji, wajar-slip
    ],
    "rumahlabuh": [
        "indonesian-market",
    ],
    "legion-swarm": [
        "ai-agent-patterns",      # multi-agent systems
        "telegram-bot",           # aiogram 3.x patterns
        "litellm-routing",       # model routing
    ],
    "ml": [
        "ml-integration",        # PyTorch, model serving
        "numpy-performance",     # array ops
    ],
}

# TIER 4 — By quality gate
TIER_4: dict[str, str] = {
    "security": "security-audit",
    "a11y": "a11y-compliance",
    "commit": "conventional-commits",
    "performance": "performance-budget",
}

# Wildcard — loaded for ALL tasks
ALWAYS_TIER_4 = ["conventional-commits"]


# ---------------------------------------------------------------------------
# Skill loading
# ---------------------------------------------------------------------------


def _list_available_skills() -> list[str]:
    """List all skill files in ~/.claude/skills/."""
    if not SKILLS_DIR.exists():
        return []
    return [p.stem for p in SKILLS_DIR.glob("*.md")] + [
        p.stem for p in SKILLS_DIR.glob("*.txt")
    ]


def _suggest_similar_skill(name: str, available: list[str]) -> str:
    """Suggest a similar skill name if a close match exists."""
    from difflib import get_close_matches

    matches = get_close_matches(name, available, n=1, cutoff=0.6)
    if matches:
        return f". Did you mean '{matches[0]}'?"
    return ""


def load_skills_for_task(task_type: str, domain: str = "") -> list[str]:
    """Return ordered list of skill names to load for this task.

    Args:
        task_type: One of "feature", "bugfix", "refactor", "security", "frontend", "backend"
        domain: One of "cekwajar", "rumahlabuh", "legion-swarm", "ml", or ""

    Returns:
        Ordered list of skill names (TIER1 first, then TIER2, etc.)

    Example:
        skills = load_skills_for_task("feature", "cekwajar")
        # Returns: ["typescript-strict", "next-js-app-router", "supabase-realtime", ...]
    """
    available = _list_available_skills()
    loaded: list[str] = []

    # TIER 1 — always
    for skill in TIER_1:
        if skill in available:
            loaded.append(skill)
        else:
            logger.warning(
                f"TIER-1 skill not found: '{skill}' — {TIER_1[skill]}"
                f"{_suggest_similar_skill(skill, available)}"
            )

    # TIER 2 — by task type
    tier2_skills = TIER_2.get(task_type.lower(), [])
    for skill in tier2_skills:
        if skill in available and skill not in loaded:
            loaded.append(skill)
        else:
            logger.warning(
                f"TIER-2 skill not found: '{skill}' for task type '{task_type}'"
                f"{_suggest_similar_skill(skill, available)}"
            )

    # TIER 3 — by domain
    if domain:
        tier3_skills = TIER_3.get(domain.lower(), [])
        for skill in tier3_skills:
            if skill in available and skill not in loaded:
                loaded.append(skill)
            else:
                logger.warning(
                    f"TIER-3 skill not found: '{skill}' for domain '{domain}'"
                    f"{_suggest_similar_skill(skill, available)}"
                )

    # TIER 4 — wildcard always included
    for skill in ALWAYS_TIER_4:
        if skill in available and skill not in loaded:
            loaded.append(skill)
        else:
            logger.warning(
                f"TIER-4 (wildcard) skill not found: '{skill}'"
                f"{_suggest_similar_skill(skill, available)}"
            )

    return loaded


def describe_active_skill_context(task_type: str = "", domain: str = "") -> str:
    """Return formatted skill context for system prompt injection.

    Reads skill files and returns their content as a formatted string
    that can be injected into a system prompt.

    Args:
        task_type: Task type (feature, bugfix, etc.)
        domain: Domain context (cekwajar, legion-swarm, etc.)

    Returns:
        Formatted string: "## Active Skills\n\n[skill1 content]\n\n[skill2 content]..."
    """
    skills = load_skills_for_task(task_type, domain)
    if not skills:
        return ""

    sections = ["[SKILL HULL — M2.7 TIER-DRIVEN SKILL LOADING]"]
    sections.append(f"Task type: {task_type or 'general'} | Domain: {domain or 'all'}")
    sections.append(f"Loaded skills ({len(skills)}): {', '.join(skills)}")
    sections.append("")

    for skill_name in skills:
        skill_path = SKILLS_DIR / f"{skill_name}.md"
        if not skill_path.exists():
            skill_path = SKILLS_DIR / f"{skill_name}.txt"

        if skill_path.exists():
            try:
                content = skill_path.read_text(encoding="utf-8")
                # Include first 800 chars of each skill (trim long skills)
                excerpt = content[:800]
                if len(content) > 800:
                    excerpt += "\n[...]"
                sections.append(f"--- {skill_name.upper()} ---")
                sections.append(excerpt)
                sections.append("")
            except Exception:
                sections.append(f"--- {skill_name.upper()} ---")
                sections.append("(could not read skill file)")
                sections.append("")
        else:
            # Skill referenced but not found — still note it
            sections.append(f"--- {skill_name.upper()} ---")
            sections.append("(skill file not found — may need installation)")
            sections.append("")

    return "\n".join(sections)


def get_skill_path(skill_name: str) -> Optional[Path]:
    """Return Path to a skill file if it exists."""
    candidates = [
        SKILLS_DIR / f"{skill_name}.md",
        SKILLS_DIR / f"{skill_name}.txt",
        SKILLS_DIR / skill_name,
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def infer_task_type_from_message(message: str) -> tuple[str, str]:
    """Infer task type and domain from a natural language message.

    Returns:
        Tuple of (task_type, domain) — both may be empty string if unclear.
    """
    msg_lower = message.lower()

    # Domain inference
    domain = ""
    if any(kw in msg_lower for kw in ["cekwajar", "wajar", "njop", "tanah", "gaji", "slip"]):
        domain = "cekwajar"
    elif any(kw in msg_lower for kw in ["rumahlabuh", "rumah labuh"]):
        domain = "rumahlabuh"
    elif any(kw in msg_lower for kw in ["legion", "swarm", "telegram", "bot", "agent"]):
        domain = "legion-swarm"
    elif any(kw in msg_lower for kw in ["ml", "pytorch", "model", "training", "neural"]):
        domain = "ml"

    # Task type inference
    task_type = ""
    if any(kw in msg_lower for kw in ["fix", "bug", "error", "crash", "broken"]):
        task_type = "bugfix"
    elif any(kw in msg_lower for kw in ["refactor", "restructure", "clean up"]):
        task_type = "refactor"
    elif any(kw in msg_lower for kw in ["security", "auth", "vulnerability"]):
        task_type = "security"
    elif any(kw in msg_lower for kw in ["frontend", "ui", "component", "page", "design"]):
        task_type = "frontend"
    elif any(kw in msg_lower for kw in ["backend", "api", "database", "db", "endpoint"]):
        task_type = "backend"
    elif any(kw in msg_lower for kw in ["implement", "build", "create", "add", "new feature"]):
        task_type = "feature"

    return task_type, domain


def format_skill_declaration(task_type: str, domain: str) -> str:
    """Format the M2.7 mandatory skill loading declaration.

    Example output:
        "Loading skills: typescript-strict, next-js-app-router, indonesian-market for feature/cekwajar"
    """
    skills = load_skills_for_task(task_type, domain)
    if not skills:
        return "No skills loaded (none found in ~/.claude/skills/)"
    return f"Loading skills: {', '.join(skills)} for {task_type or 'general'}/{domain or 'all'}"
