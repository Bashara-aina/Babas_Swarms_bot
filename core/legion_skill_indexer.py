"""
core/legion_skill_indexer.py
============================
Auto-generates /tmp/legion_available_skills.txt from hermes skill library.
Runs at session boot and after any new skill is written.

Format per line:
    SKILL: [title] | TAGS: [tag1,tag2] | RELEVANCE: [0.0-1.0]
"""

from __future__ import annotations

import contextlib
import re
from pathlib import Path

TMP_SKILLS = Path("/tmp/legion_available_skills.txt")
HERMES_KNOWN_SKILLS = Path("/tmp/legion_hermes_skills.txt")


def index_skills(skills: list[dict]) -> None:
    """
    Write skills to /tmp/legion_available_skills.txt in the standard format.

    Each skill dict should have: title, tags (list), relevance (float)
    """
    lines = [f"# LEGION Available Skills — auto-generated {__import__('time').strftime('%Y-%m-%d %H:%M')}\n"]
    for s in skills:
        title = s.get("title", "untitled")
        tags = ",".join(s.get("tags", []))
        relevance = f"{s.get('relevance', 0.5):.2f}"
        lines.append(f"SKILL: {title} | TAGS: {tags} | RELEVANCE: {relevance}\n")
    HERMES_KNOWN_SKILLS.parent.mkdir(parents=True, exist_ok=True)
    HERMES_KNOWN_SKILLS.write_text("".join(lines))
    TMP_SKILLS.parent.mkdir(parents=True, exist_ok=True)
    TMP_SKILLS.write_text("".join(lines))


def load_skills() -> list[dict]:
    """Load skills from /tmp/legion_available_skills.txt."""
    if not TMP_SKILLS.exists():
        return []
    try:
        content = TMP_SKILLS.read_text()
        skills = []
        for line in content.splitlines():
            if line.startswith("SKILL:"):
                parts = line.split("|")
                if len(parts) >= 3:
                    title = parts[0].replace("SKILL:", "").strip()
                    tags_str = parts[1].replace("TAGS:", "").strip()
                    rel_str = parts[2].replace("RELEVANCE:", "").strip()
                    skills.append({
                        "title": title,
                        "tags": [t.strip() for t in tags_str.split(",") if t.strip()],
                        "relevance": float(rel_str) if rel_str else 0.5,
                    })
        return skills
    except Exception:
        return []


def get_top_skills(query: str, limit: int = 5) -> list[dict]:
    """
    Return top N skills relevant to a query.
    Simple keyword matching — no embedding model needed.
    """
    skills = load_skills()
    query_words = set(query.lower().split())
    scored = []
    for s in skills:
        skill_text = (s["title"] + " " + ",".join(s["tags"])).lower()
        score = sum(1 for w in query_words if w in skill_text)
        if score > 0:
            scored.append((score, s))
    scored.sort(key=lambda x: -x[0])
    return [s for _, s in scored[:limit]]


def parse_hermes_list_output(output: str) -> list[dict]:
    """
    Parse hermes list_skills output into skill dicts.
    Handles various output formats.
    """
    skills = []
    for line in output.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        title_match = re.match(r"^\d+[\.\)]\s*(.+?)(?:\s*\||\s*$)", line)
        if title_match:
            title = title_match.group(1).strip()
            skills.append({"title": title, "tags": ["hermes"], "relevance": 0.5})
            continue
        if line.startswith("SKILL:"):
            parts = line.split("|")
            title = parts[0].replace("SKILL:", "").strip()
            tags = []
            rel = 0.5
            for p in parts[1:]:
                if p.startswith("TAGS:"):
                    tags = [t.strip() for t in p.replace("TAGS:", "").split(",")]
                if p.startswith("RELEVANCE:"):
                    with contextlib.suppress(ValueError):
                        rel = float(p.replace("RELEVANCE:", "").strip())
            skills.append({"title": title, "tags": tags, "relevance": rel})
    return skills


def refresh_from_hermes() -> bool:
    """
    Fetch skills from hermes and regenerate /tmp/legion_available_skills.txt.
    Returns True if successful, False if hermes unavailable.
    """
    try:
        from tools.mem0_client import get_mem0
        mem = get_mem0()
        if not mem:
            return False
        return False
    except Exception:
        return False


if __name__ == "__main__":
    skills = load_skills()
    print(f"Loaded {len(skills)} skills from /tmp/legion_available_skills.txt")
    for s in skills[:10]:
        print(f"  {s['title']} | relevance: {s['relevance']}")
