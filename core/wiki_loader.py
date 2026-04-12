"""Wiki Loader — reads .wiki/ markdown files and builds Legion's knowledge context.

This is Legion's second brain. It MUST be injected every session.
"""

import os
import re
from pathlib import Path
from functools import lru_cache
from typing import Optional

WIKI_DIR = Path(".wiki")

# Priority files — always injected, full content
PRIORITY_FILES = [
    ".wiki/MASTER-INTELLIGENCE.md",
    ".wiki/00-meta",
    ".wiki/profiles",
    ".wiki/06-legion-instructions",
]

# Token budget for wiki injection (adjust based on model context window)
WIKI_TOKEN_BUDGET = 4000  # ~4000 tokens = ~16000 chars


@lru_cache(maxsize=1)
def load_wiki_context(max_chars: int = WIKI_TOKEN_BUDGET * 4) -> str:
    """Load .wiki/ content into a single string for system prompt injection.

    Priority files first, then remaining markdown files up to budget.
    Cached to avoid re-reading on every message.
    """
    if not WIKI_DIR.exists():
        return "[WIKI: .wiki/ directory not found]"

    sections = []
    chars_used = 0
    loaded_files = set()

    # === PRIORITY: MASTER-INTELLIGENCE.md ===
    master = WIKI_DIR / "MASTER-INTELLIGENCE.md"
    if master.exists():
        content = master.read_text(encoding="utf-8", errors="ignore")
        sections.append(f"# CORE KNOWLEDGE\n{content}")
        chars_used += len(content)
        loaded_files.add(str(master))

    # === PRIORITY: profiles/ (who Bashara is) ===
    profiles_dir = WIKI_DIR / "profiles"
    if profiles_dir.exists():
        for f in sorted(profiles_dir.glob("*.md")):
            if chars_used >= max_chars:
                break
            content = f.read_text(encoding="utf-8", errors="ignore")
            sections.append(f"# PROFILE: {f.stem}\n{content}")
            chars_used += len(content)
            loaded_files.add(str(f))

    # === PRIORITY: 06-legion-instructions/ ===
    legion_dir = WIKI_DIR / "06-legion-instructions"
    if legion_dir.exists():
        for f in sorted(legion_dir.glob("*.md")):
            if chars_used >= max_chars:
                break
            content = f.read_text(encoding="utf-8", errors="ignore")
            sections.append(f"# LEGION INSTRUCTION: {f.stem}\n{content}")
            chars_used += len(content)
            loaded_files.add(str(f))

    # === REMAINING: all other .md files ===
    for md_file in sorted(WIKI_DIR.rglob("*.md")):
        if chars_used >= max_chars:
            break
        if str(md_file) in loaded_files:
            continue
        if any(skip in str(md_file) for skip in [".obsidian", "_archive", "_quarantine"]):
            continue
        try:
            content = md_file.read_text(encoding="utf-8", errors="ignore")
            if not content.strip():
                continue
            rel_path = md_file.relative_to(WIKI_DIR)
            sections.append(f"# WIKI/{rel_path}\n{content}")
            chars_used += len(content)
            loaded_files.add(str(md_file))
        except Exception:
            continue

    if not sections:
        return "[WIKI: no content found in .wiki/]"

    return "\n\n---\n\n".join(sections)


def invalidate_wiki_cache() -> None:
    """Call this when .wiki files are updated during runtime."""
    load_wiki_context.cache_clear()


def get_bashara_identity_context() -> str:
    """Returns a minimal guaranteed-injected block about Bashara.

    Used as fallback if full wiki context is too large.
    This MUST always be in the system prompt.
    """
    return """
## WHO IS BASHARA?
Bashara Aina is the owner of this bot. You are his personal AI assistant.
- Full name: Bashara Aina
- Location: Narita, Chiba, Japan (PhD/Master's student at Shibaura Institute of Technology)
- Nationality: Indonesian
- Active projects: cekwajar.id (Indonesian wage verification SaaS), rumahlabuh.com (property rental platform Indonesia), this Legion bot (Babas_Swarms_bot), computer vision thesis (assembly action recognition)
- Communication: Indonesian (primary), English (technical), mixes both freely
- Style: casual Indonesian slang + technical depth. "pusing", "gw", "lo", "cek", "nanti"
- When Bashara asks about himself: confirm you know who he is, then answer from wiki knowledge
- NEVER say "Bashara Aina tidak ada di dataset saya" — he is your owner and master
""".strip()
