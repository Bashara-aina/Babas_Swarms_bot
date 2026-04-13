#!/usr/bin/env python3
"""
Batch fix wikilinks in .wiki directory.
Based on planner audit: 119 broken links across categories.
"""

import re
from pathlib import Path

WIKI_DIR = Path("/home/newadmin/swarm-bot/.wiki")

CATEGORIES = {
    # Category 1: Missing ./concepts/ prefix
    "concept_links": {
        "bayesian-blending": "./concepts/bayesian-blending",
        "bpjs-reference": "./concepts/bpjs-reference",
        "intent-router": "./concepts/intent-routing",
        "context-window-budget": "./concepts/context-window-budget",
        "freemium-gate": "./concepts/freemium-gate",
        "karpathy-kb-pattern": "./concepts/karpathy-kb-pattern",
        "labor-law-indonesia": "./concepts/labor-law-indonesia",
        "litellm": "./entities/litellm",
        "llm-cost-routing": "./concepts/llm-cost-routing",
        "market-data-indonesia": "./concepts/market-data-indonesia",
        "multi-agent-orchestration": "./concepts/multi-agent-orchestration",
        "reasoning-loop": "./concepts/reasoning-loop",
        "self-improvement-loop": "./concepts/self-improvement-loop",
        "skill-registry": "./concepts/skill-registry",
        "tax-indonesia": "./concepts/tax-indonesia",
        "vector-search": "./concepts/vector-search",
    },
    # Category 2: Wrong wiki/ prefix - remove it
    "wrong_prefix": ["wiki/", ".wiki/"],
    # Category 3: Directory-style links - remove trailing /
    "dir_links": ["agents/", "architecture/", "decisions/", "issues/", "logs/", "prompts/", "research/"],
    # Category 6: Entities need ./entities/ prefix
    "entity_links": {
        "opencode": "./entities/opencode",
        "cursor": "./entities/cursor",
        "supabase": "./entities/supabase",
        "dify": "./entities/dify",
        "chromadb": "./entities/chromadb",
        "gpt-researcher": "./entities/gpt-researcher",
        "openrouter": "./entities/openrouter",
        "minimax-m2-7": "./entities/minimax-m2-7",
        "midtrans": "./entities/midtrans",
    },
}


def fix_wikilinks_in_file(filepath: Path) -> tuple[int, list[str]]:
    """Fix wikilinks in a single file. Returns (count, list of fixes)."""
    content = filepath.read_text()
    original = content
    fixes = []

    # Fix wikilinks: [[link]] or [[link|display]]
    def replace_wikilink(m):
        full_match = m.group(0)
        link = m.group(1)
        display = m.group(2) if m.group(2) else ""

        # Skip if already has ./ or / prefix
        if link.startswith("./") or link.startswith("/"):
            return full_match

        # Check concept_links
        if link in CATEGORIES["concept_links"]:
            new_link = CATEGORIES["concept_links"][link]
            display_part = f"|{display}" if display else ""
            result = f"[[{new_link}{display_part}]]"
            fixes.append(f"  {link} -> {new_link}")
            return result

        # Check entity_links
        if link in CATEGORIES["entity_links"]:
            new_link = CATEGORIES["entity_links"][link]
            display_part = f"|{display}" if display else ""
            result = f"[[{new_link}{display_part}]]"
            fixes.append(f"  {link} -> {new_link}")
            return result

        # Remove wrong wiki/ prefix
        for prefix in CATEGORIES["wrong_prefix"]:
            if link.startswith(prefix):
                new_link = link[len(prefix) :]
                display_part = f"|{display}" if display else ""
                result = f"[[{new_link}{display_part}]]"
                fixes.append(f"  {link} -> {new_link}")
                return result

        # Remove trailing / from directory links
        for dlink in CATEGORIES["dir_links"]:
            if link == dlink or link == dlink.rstrip("/"):
                new_link = dlink.rstrip("/")
                if new_link != link:
                    display_part = f"|{display}" if display else ""
                    result = f"[[{new_link}{display_part}]]"
                    fixes.append(f"  {link} -> {new_link}")
                    return result

        return full_match

    # Match [[link]] or [[link|display]]
    content = re.sub(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]", replace_wikilink, content)

    if content != original:
        filepath.write_text(content)

    return len(fixes), fixes


def main():
    md_files = list(WIKI_DIR.rglob("*.md"))
    md_files = [f for f in md_files if not f.name.startswith("_")]

    total_fixes = 0
    files_changed = 0

    for filepath in sorted(md_files):
        try:
            count, fixes = fix_wikilinks_in_file(filepath)
            if count > 0:
                print(f"\n{filepath.relative_to(WIKI_DIR)}: {count} fixes")
                for fix in fixes:
                    print(fix)
                files_changed += 1
                total_fixes += count
        except Exception as e:
            print(f"ERROR in {filepath}: {e}")

    print(f"\n=== SUMMARY ===")
    print(f"Files changed: {files_changed}")
    print(f"Total wikilinks fixed: {total_fixes}")


if __name__ == "__main__":
    main()
