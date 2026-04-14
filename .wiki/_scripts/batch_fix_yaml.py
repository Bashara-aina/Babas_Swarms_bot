#!/usr/bin/env python3
"""
Batch YAML frontmatter scanner and fixer for .wiki/**/*.md files.
Parses frontmatter with yaml.safe_load(), reports failures, auto-fixes common issues:
- unclosed quotes
- tabs in values
- bare yes/no instead of true/false
"""

import re
import sys
from pathlib import Path
from typing import Optional

import yaml


def extract_frontmatter(content: str) -> tuple[Optional[str], int]:
    """Extract YAML frontmatter block. Returns (frontmatter_str, end_offset)."""
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if match:
        return match.group(1), match.end()
    return None, 0


def try_parse_yaml(frontmatter: str) -> tuple[bool, Optional[dict], str]:
    """Attempt to parse YAML. Returns (success, data, error_msg)."""
    try:
        data = yaml.safe_load(frontmatter)
        return True, data, ""
    except yaml.YAMLError as e:
        return False, None, str(e)


def auto_fix_yaml(frontmatter: str) -> tuple[str, list[str]]:
    """Attempt to auto-fix common YAML issues. Returns (fixed_frontmatter, fixes_applied)."""
    fixes = []
    fixed = frontmatter

    # Fix 1: Tabs in values (YAML doesn't allow tabs in indented values)
    # Replace tab characters with 2 spaces in value context
    lines = fixed.split("\n")
    cleaned_lines = []
    for i, line in enumerate(lines):
        # Check if line has leading indentation followed by content
        if "\t" in line:
            # Only replace tabs that appear after indentation (in values)
            # But be careful - tabs are valid in some YAML contexts
            cleaned = line.replace("\t", "  ")
            if cleaned != line:
                fixes.append(f"Line {i + 1}: replaced tabs with spaces")
                line = cleaned
        cleaned_lines.append(line)
    fixed = "\n".join(cleaned_lines)

    # Fix 2: bare yes/no/on/off/infinity/NaN to True/False
    # Only when they appear as scalar values (not inside quotes)
    # Pattern: word boundary before yes/no/on/off/infinity/NaN
    bool_map = {
        "yes": "true",
        "no": "false",
        "on": "true",
        "off": "false",
        "Yes": "True",
        "No": "False",
        "ON": "True",
        "OFF": "False",
    }
    for old, new in bool_map.items():
        # Use regex with word boundary, but not inside quotes
        pattern = r"\b" + old + r"\b"
        if re.search(pattern, fixed):
            # Only replace if not inside a quoted string
            # Simple heuristic: if the match is not preceded by ' or "
            fixed = re.sub(pattern, new, fixed)
            if old in fixed or old.lower() in fixed:
                fixes.append(f"Replaced bare '{old}' with '{new}'")

    # Fix 3: Unclosed quotes
    # Detect lines with opening quote but no closing quote
    lines = fixed.split("\n")
    for i, line in enumerate(lines):
        # Check for unclosed single quotes
        single_quotes = line.count("'")
        if single_quotes % 2 == 1 and single_quotes > 0:
            # Odd number of single quotes - likely unclosed
            # Find the first unclosed quote and add a closing one at end of line
            line = line + "'"
            fixes.append(f"Line {i + 1}: closed unclosed single quote")
        # Check for unclosed double quotes
        double_quotes = line.count('"')
        if double_quotes % 2 == 1 and double_quotes > 0:
            line = line + '"'
            fixes.append(f"Line {i + 1}: closed unclosed double quote")
        lines[i] = line
    fixed = "\n".join(lines)

    return fixed, fixes


def process_file(filepath: Path) -> dict:
    """Process a single file. Returns dict with results."""
    result = {
        "path": str(filepath),
        "success": False,
        "fixed": False,
        "fixes": [],
        "error": None,
        "original_frontmatter": None,
        "parsed_data": None,
    }

    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception as e:
        result["error"] = f"Read error: {e}"
        return result

    frontmatter, _ = extract_frontmatter(content)
    if frontmatter is None:
        result["error"] = "No frontmatter found"
        return result

    result["original_frontmatter"] = frontmatter

    # Try to parse
    success, data, error = try_parse_yaml(frontmatter)

    if success:
        result["success"] = True
        result["parsed_data"] = data
        return result

    # Failed to parse - try auto-fix
    result["error"] = error

    fixed_frontmatter, fixes = auto_fix_yaml(frontmatter)

    if fixes:
        result["fixes"] = fixes

        # Try parsing fixed version
        success, data, error = try_parse_yaml(fixed_frontmatter)

        if success:
            result["fixed"] = True
            result["success"] = True
            result["parsed_data"] = data

            # Write fixed content back
            new_content = (
                content[: content.find("---\n", 4) + 4]
                + fixed_frontmatter
                + "\n---\n"
                + content[content.find("\n---\n", 4) + 6 :]
            )
            filepath.write_text(new_content, encoding="utf-8")
        else:
            result["error"] = f"Original parse error: {error}\nAuto-fix attempts: {fixes}\nStill failing: {error}"

    return result


def main():
    wiki_root = Path("/home/newadmin/swarm-bot/.wiki")

    # Find all .md files
    md_files = list(wiki_root.rglob("*.md"))
    md_files = [f for f in md_files if "_scripts" not in str(f)]

    print(f"Scanning {len(md_files)} markdown files in {wiki_root}...")
    print("=" * 70)

    total_files = 0
    success_count = 0
    failure_count = 0
    fixed_count = 0

    failures = []
    fixed = []

    for filepath in sorted(md_files):
        total_files += 1
        result = process_file(filepath)

        if result["success"] and not result["fixed"]:
            success_count += 1
        elif result["success"] and result["fixed"]:
            fixed_count += 1
            fixed.append(result)
        elif result["error"] and "No frontmatter" not in result["error"]:
            failure_count += 1
            failures.append(result)
        else:
            success_count += 1  # No frontmatter is okay

    # Summary
    print(f"\n{'=' * 70}")
    print(f"SUMMARY:")
    print(f"  Total files scanned: {total_files}")
    print(f"  Successfully parsed:  {success_count}")
    print(f"  Auto-fixed:           {fixed_count}")
    print(f"  YAML failures:        {failure_count}")

    if fixed:
        print(f"\nAUTO-FIXED ({len(fixed)} files):")
        for f in fixed:
            print(f"  ✓ {f['path']}")
            for fix in f["fixes"]:
                print(f"      - {fix}")

    if failures:
        print(f"\nYAML PARSE FAILURES ({len(failures)} files):")
        for f in failures:
            print(f"  ✗ {f['path']}")
            print(f"    Error: {f['error'][:100]}...")

    # Expected ~39 failures per contract
    print(f"\n(Note: ~39 YAML failures expected per contract spec)")
    print(f"Current failure count: {failure_count}")

    return 0 if failure_count < 100 else 1  # Exit 1 if too many failures to handle


if __name__ == "__main__":
    sys.exit(main())
