#!/usr/bin/env python3
"""
batch_fix_frontmatter.py — Scans all .wiki/**/*.md files and adds minimal Legion frontmatter
to files that are missing it. Does NOT modify files with valid existing frontmatter.

Legion frontmatter schema (from .wiki/SCHEMA.md):
---
title: Page Title
type: concept | entity | project | decision | architecture | timeline | person | skill | reference
status: active | completed | deprecated | legacy
tags: [tag1, tag2, tag3]
created: 2026-04-13
updated: 2026-04-13
summary: 2-3 sentence TL;DR for Dataview indexing
wikilinks: []
confidence: high | medium | low
source: conversation | research | implementation | external
---
"""

import os
import re
from datetime import date
from pathlib import Path
from typing import Optional

import yaml

WIKI_ROOT = Path("/home/newadmin/swarm-bot/.wiki")
FRONTMATTER_REQUIRED = {"title", "type", "status", "tags", "created", "updated", "summary"}
FRONTMATTER_OPTIONAL = {"wikilinks", "confidence", "source"}

# Directories to skip
SKIP_DIRS = {"_scripts", "_meta", "_quality_report.md"}


def has_legion_frontmatter(content: str) -> bool:
    """Check if file has valid Legion frontmatter with required fields."""
    if not content.startswith("---"):
        return False
    # Find the closing ---
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return False
    try:
        data = yaml.safe_load(match.group(1))
        if not isinstance(data, dict):
            return False
        # Check required fields exist
        if not FRONTMATTER_REQUIRED.issubset(data.keys()):
            return False
        return True
    except yaml.YAMLError:
        return False


def extract_title_from_filename(filepath: Path) -> str:
    """Derive title from filename."""
    name = filepath.stem
    # Remove date prefix like "058-" or "2026-04-11-"
    name = re.sub(r"^\d{2,3}-", "", name)
    name = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", name)
    # Convert dashes/underscores to spaces, title case
    title = name.replace("-", " ").replace("_", " ").title()
    return title if title else name.title()


def infer_type_from_path(filepath: Path) -> str:
    """Infer type from file path structure."""
    path_str = str(filepath)
    if "/concepts/" in path_str or "/knowledge/" in path_str:
        return "concept"
    if "/entities/" in path_str:
        return "entity"
    if "/projects/" in path_str:
        return "project"
    if "/decisions/" in path_str or "adr-" in path_str.lower():
        return "decision"
    if "/architecture/" in path_str:
        return "architecture"
    if "/timelines/" in path_str or "/legion/harvester/" in path_str:
        return "timeline"
    if "/people/" in path_str:
        return "person"
    if "/raw/" in path_str or "/docs/" in path_str:
        return "reference"
    return "concept"


def infer_status(filepath: Path, content: str) -> str:
    """Infer status from path and content."""
    path_str = str(filepath)
    if "/legion/" in path_str and ("refactoring" in path_str or "audit" in path_str):
        return "completed"
    if "/decisions/" in path_str:
        return "active"
    if "deprecated" in content.lower() or "[deprecated]" in content.lower():
        return "deprecated"
    if "legacy" in content.lower():
        return "legacy"
    return "active"


def extract_tags_from_path(filepath: Path) -> list:
    """Extract tags from path components."""
    tags = []
    parts = filepath.parts
    # Get relevant directory names
    for part in parts:
        if part not in (".wiki", "knowledge", "raw"):
            cleaned = re.sub(r"\d{2,3}-", "", part)
            if cleaned not in ("INDEX", "index"):
                tags.append(cleaned.lower().replace(" ", "-"))
    return tags[:5]  # Limit to 5 tags


def extract_summary_from_content(content: str, title: str) -> str:
    """Extract or generate summary from content."""
    # Remove frontmatter if present
    clean_content = re.sub(r"^---.*?---\n", "", content, flags=re.DOTALL)

    # Look for first paragraph after title
    lines = clean_content.split("\n")
    summary_parts = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Skip headers
        if line.startswith("#"):
            continue
        # Skip table separators
        if line.startswith("|") and ("---" in line or "===" in line):
            continue
        # Take first substantive line
        if len(line) > 20:
            summary_parts.append(line)
            break

    if summary_parts:
        summary = summary_parts[0]
        # Truncate to ~200 chars
        if len(summary) > 200:
            summary = summary[:197] + "..."
        return summary

    return f"Landing page for {title}"


def generate_frontmatter(filepath: Path, content: str) -> dict:
    """Generate frontmatter dict from file info."""
    title = extract_title_from_filename(filepath)
    ftype = infer_type_from_path(filepath)
    status = infer_status(filepath, content)
    tags = extract_tags_from_path(filepath)
    summary = extract_summary_from_content(content, title)
    today = date.today().isoformat()

    fm = {
        "title": title,
        "type": ftype,
        "status": status,
        "tags": tags if tags else ["untagged"],
        "created": today,
        "updated": today,
        "summary": summary,
        "wikilinks": [],
        "confidence": "medium",
        "source": "research",
    }
    return fm


def fix_file(filepath: Path) -> tuple[bool, str]:
    """
    Fix frontmatter in a single file.
    Returns (was_modified, message)
    """
    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception as e:
        return False, f"Error reading: {e}"

    # Skip if already has valid Legion frontmatter
    if has_legion_frontmatter(content):
        return False, "already has valid frontmatter"

    # Check if file has any frontmatter at all
    has_any_frontmatter = content.startswith("---")

    # Generate new frontmatter
    fm = generate_frontmatter(filepath, content)
    fm_yaml = yaml.dump(fm, default_flow_style=False, sort_keys=False, allow_unicode=True)
    new_fm = f"---\n{fm_yaml}---\n"

    if has_any_frontmatter:
        # Replace existing frontmatter block
        match = re.match(r"^---.*?\n---\n", content, re.DOTALL)
        if match:
            new_content = content[match.end() :]
            new_content = new_fm + new_content
        else:
            # Malformed frontmatter, prepend at start
            new_content = new_fm + content
    else:
        # No frontmatter - prepend
        new_content = new_fm + content

    filepath.write_text(new_content, encoding="utf-8")

    action = "replaced existing" if has_any_frontmatter else "added to"
    return True, f"{action} frontmatter"


def main():
    """Main entry point."""
    print("=" * 60)
    print("batch_fix_frontmatter.py — Legion Wiki Frontmatter Fixer")
    print("=" * 60)
    print()

    md_files = list(WIKI_ROOT.rglob("*.md"))
    print(f"Found {len(md_files)} .md files in {WIKI_ROOT}")
    print()

    fixed_count = 0
    skipped_count = 0
    error_count = 0
    sample_file = None

    for filepath in sorted(md_files):
        # Skip certain directories
        if any(skip in filepath.parts for skip in SKIP_DIRS):
            skipped_count += 1
            continue

        modified, msg = fix_file(filepath)

        if modified:
            fixed_count += 1
            rel_path = filepath.relative_to(WIKI_ROOT)
            print(f"  FIXED: {rel_path} — {msg}")

            # Save first fixed file for sample verification
            if sample_file is None:
                sample_file = filepath
        elif msg == "already has valid frontmatter":
            skipped_count += 1
        else:
            error_count += 1
            print(f"  ERROR: {filepath} — {msg}")

    print()
    print("-" * 60)
    print(f"SUMMARY: {fixed_count} fixed, {skipped_count} skipped (valid frontmatter), {error_count} errors")
    print("-" * 60)
    print()

    if sample_file:
        print("SAMPLE VERIFICATION — First fixed file:")
        print(f"  File: {sample_file.relative_to(WIKI_ROOT)}")
        print()
        content = sample_file.read_text(encoding="utf-8")
        # Show first 40 lines
        lines = content.split("\n")[:40]
        for i, line in enumerate(lines, 1):
            print(f"  {i:2d}: {line}")
            if i >= 39 and len(lines) > 39:
                print("  ...")
                break
        print()

    return fixed_count


if __name__ == "__main__":
    count = main()
    exit(0 if count >= 0 else 1)
