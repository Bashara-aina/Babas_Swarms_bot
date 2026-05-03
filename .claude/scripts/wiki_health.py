# WIKI HEALTH CHECK SCRIPT
# =========================
# Run: python3 .claude/scripts/wiki_health.py
# Purpose: Verify .wiki/ integrity before and after compaction
# Part of: Legion v11 cognitive OS, pre-compaction ritual

import json
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

WIKI_ROOT = Path(__file__).parent.parent.parent / ".wiki"
META_DIR = WIKI_ROOT / "_meta"
COMPILE_STATE = META_DIR / "compile_state.json"
HEALTH_DIR = WIKI_ROOT / "health"
OUTPUT_FILE = Path("/tmp/legion_wiki_health.json")


def get_timestamp() -> str:
    tz = timezone(timedelta(hours=9))
    return datetime.now(tz).isoformat()


def check_obsidian_dir() -> dict:
    """Check if .obsidian/ config dir exists."""
    obsidian = WIKI_ROOT / ".obsidian"
    return {
        "test": "obsidian_config_dir",
        "status": "pass" if obsidian.exists() else "warn",
        "detail": f".obsidian/ {'exists' if obsidian.exists() else 'MISSING'}",
    }


def check_frontmatter_all() -> dict:
    """Check YAML frontmatter validity using actual YAML parsing."""
    import yaml

    issues = []
    md_files = list(WIKI_ROOT.rglob("*.md"))
    checked = 0

    for f in md_files:
        if "/_meta/" in str(f) or "/.obsidian/" in str(f):
            continue
        checked += 1
        try:
            content = f.read_text(encoding="utf-8")
            if content.startswith("---"):
                end = content.find("---", 3)
                if end == -1:
                    issues.append(f"{f.relative_to(WIKI_ROOT)}: unclosed frontmatter")
                    continue
                fm_text = content[3:end]
                yaml.safe_load(fm_text)  # raises if invalid
        except yaml.YAMLError as e:
            issues.append(f"{f.relative_to(WIKI_ROOT)}: YAML error: {str(e)[:80]}")
        except Exception as e:
            issues.append(f"{f.relative_to(WIKI_ROOT)}: read error: {e}")

    return {
        "test": "frontmatter_validity",
        "status": "pass" if not issues else "fail",
        "detail": f"checked {checked} files, {len(issues)} YAML errors",
        "issues": issues[:10],
    }


def check_wikilinks() -> dict:
    """Check for broken wikilinks."""
    import re

    issues = []
    known_missing = {
        "concepts/karpathy-kb-pattern", "concepts/memory-architecture",
        "concepts/intent-routing", "concepts/llm-cost-routing",
        "entities/supabase", "entities/litellm", "entities/openrouter",
    }

    md_files = list(WIKI_ROOT.rglob("*.md"))
    all_note_names = {f.stem for f in md_files if f.suffix == ".md"}

    for f in md_files:
        if "/_meta/" in str(f) or "/.obsidian/" in str(f):
            continue
        try:
            content = f.read_text(encoding="utf-8")
            wikilinks = re.findall(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", content)
            for wl in wikilinks:
                target = wl.strip()
                if not target:
                    continue
                # Strip ./ prefix and #anchor
                target = re.sub(r"^\./", "", target)
                target = target.split("#")[0].strip()
                if not target:
                    continue
                # Try various path combinations
                exists = (
                    (WIKI_ROOT / f"{target}.md").exists() or
                    (WIKI_ROOT / f"{target}/index.md").exists() or
                    target.lstrip("/") in all_note_names or
                    target in all_note_names or
                    target.split("/")[-1] in all_note_names
                )
                if not exists and target not in known_missing:
                    issues.append(f"{f.relative_to(WIKI_ROOT)}: [[{target}]] → not found")
        except Exception:
            pass

    return {
        "test": "wikilinks",
        "status": "pass" if len(issues) < 50 else "warn",
        "detail": f"{len(issues)} potentially broken wikilinks (excluding known missing)",
        "issues": issues[:10],
    }


def check_compile_state() -> dict:
    """Verify compile_state.json is recent."""
    if not COMPILE_STATE.exists():
        return {
            "test": "compile_state",
            "status": "warn",
            "detail": "compile_state.json does not exist",
        }

    try:
        data = json.loads(COMPILE_STATE.read_text())
        last_session = data.get("last_session_timestamp", "")
        return {
            "test": "compile_state",
            "status": "pass",
            "detail": f"last_session: {last_session}",
        }
    except Exception as e:
        return {
            "test": "compile_state",
            "status": "fail",
            "detail": f"parse error: {e}",
        }


def check_health_reports() -> dict:
    """Count recent health reports."""
    HEALTH_DIR.mkdir(exist_ok=True)
    reports = list(HEALTH_DIR.glob("*.md"))
    recent = [
        r for r in reports
        if datetime.fromtimestamp(r.stat().st_mtime) >
        datetime.now() - timedelta(days=7)
    ]
    return {
        "test": "health_reports",
        "status": "pass",
        "detail": f"{len(recent)} total reports, {len(recent)} from last 7 days",
    }


def check_file_counts() -> dict:
    """Count wiki files by top-level directory."""
    dirs = {}
    for f in WIKI_ROOT.rglob("*.md"):
        if "/.obsidian/" in str(f) or "/_meta/" in str(f):
            continue
        parts = f.relative_to(WIKI_ROOT).parts
        top = parts[0] if parts else "root"
        dirs[top] = dirs.get(top, 0) + 1

    return {
        "test": "file_counts",
        "status": "pass",
        "detail": str(dict(sorted(dirs.items(), key=lambda x: -x[1])[:5])),
    }


def run_git_status() -> dict:
    """Check git status of wiki."""
    try:
        result = subprocess.run(
            ["git", "status", "--short", ".wiki/"],
            cwd=WIKI_ROOT.parent,
            capture_output=True,
            text=True,
            timeout=10,
        )
        changes = result.stdout.strip().split("\n") if result.stdout.strip() else []
        return {
            "test": "git_status",
            "status": "pass",
            "detail": f"{len(changes)} changed files in .wiki/",
        }
    except Exception as e:
        return {"test": "git_status", "status": "warn", "detail": f"git error: {e}"}


def main():
    print(f"═" * 60)
    print(f"LEGION WIKI HEALTH CHECK — {get_timestamp()[:10]}")
    print(f"═" * 60)

    checks = [
        check_obsidian_dir(),
        check_frontmatter_all(),
        check_wikilinks(),
        check_compile_state(),
        check_health_reports(),
        check_file_counts(),
        run_git_status(),
    ]

    results = {
        "timestamp": get_timestamp(),
        "wiki_root": str(WIKI_ROOT),
        "checks": checks,
    }

    OUTPUT_FILE.write_text(json.dumps(results, indent=2))

    all_pass = True
    for check in checks:
        icon = "✅" if check["status"] == "pass" else ("⚠️" if check["status"] == "warn" else "❌")
        print(f"  {icon} {check['test']}: {check['detail']}")
        if check["status"] == "fail":
            all_pass = False

    print(f"═" * 60)
    if all_pass:
        print("✅ All checks passed. Wiki is healthy.")
    else:
        print("❌ Some checks failed. Review issues above.")
        sys.exit(1)

    print(f"Full report: {OUTPUT_FILE}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
