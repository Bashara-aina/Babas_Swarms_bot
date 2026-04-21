"""
lib/legiona/self_evolve.py
M2.7 self-evolution pattern: after each agent session,
Legiona critiques its own performance and patches its system prompt.

Usage:
    from lib.legiona.self_evolve import record_session, evolve

Pipeline:
    1. record_session() called at end of each agent task
    2. evolve() reads last N sessions, generates new rule, appends to memory
    3. Rules accumulate in lib/legiona/memory/rules.md
    4. rules.md is prepended to system prompt on next run
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from lib.legiona.minimax_client import complete

MEMORY_DIR = Path("lib/legiona/memory")
MEMORY_DIR.mkdir(parents=True, exist_ok=True)
RULES_FILE = MEMORY_DIR / "rules.md"
GLOBAL_MEMORY_FILE = MEMORY_DIR / "global_memory.md"
SESSION_LOG = MEMORY_DIR / "sessions.jsonl"


def record_session(task: str, tool_calls: list[dict], outcome: str, success: bool) -> None:
    """Append a session record for later self-evaluation."""
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "task": task,
        "tool_call_count": len(tool_calls),
        "tool_calls_summary": [t.get("function", {}).get("name") for t in tool_calls],
        "outcome": outcome,
        "success": success,
    }
    with open(SESSION_LOG, "a") as f:
        f.write(json.dumps(record) + "\n")


def _sync_global_memory(new_rule: str, timestamp: str) -> None:
    """
    Sync a newly evolved rule into global_memory.md 'Self-Evolved Rules' section.
    Appends to the section; if the file has no such section, creates one.
    """
    marker = "## Self-Evolved Rules"
    rule_line = f"- [Evolved {timestamp}]: {new_rule}"
    if not GLOBAL_MEMORY_FILE.exists():
        content = f"{marker}\n{rule_line}\n"
        GLOBAL_MEMORY_FILE.write_text(content)
        return

    text = GLOBAL_MEMORY_FILE.read_text()
    if marker in text:
        # Append under existing marker
        new_text = text.replace(marker, f"{marker}\n{rule_line}")
    else:
        new_text = text + f"\n{marker}\n{rule_line}\n"
    GLOBAL_MEMORY_FILE.write_text(new_text)


def _normalize_rule(text: str) -> str:
    """
    Normalize rule text for deduplication comparison.
    Strips markdown comments, bullet markers, whitespace — returns lowercase canonical form.
    """
    import re
    # Remove <!-- ... --> comments
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    # Remove bullet markers like "- [RULE N]:" or "- [Evolved ...]:"
    text = re.sub(r"-\s*\[.*?\]:\s*", "", text)
    # Collapse whitespace and lowercase
    text = re.sub(r"\s+", " ", text).strip().lower()
    return text


def _rule_exists(new_rule: str) -> bool:
    """
    Check if a rule with identical semantic content already exists
    in rules.md or global_memory.md. Uses normalized comparison.
    """
    normalized = _normalize_rule(new_rule)
    if not normalized:
        return True  # empty rules should never be added

    # Check rules.md
    if RULES_FILE.exists():
        for line in RULES_FILE.read_text().splitlines():
            if _normalize_rule(line) == normalized:
                return True

    # Check global_memory.md
    if GLOBAL_MEMORY_FILE.exists():
        for line in GLOBAL_MEMORY_FILE.read_text().splitlines():
            if _normalize_rule(line) == normalized:
                return True

    return False


def evolve(last_n: int = 5) -> str | None:
    """
    Read last N sessions. Ask M2.7 to:
    1. Identify what went wrong or could be improved
    2. Propose ONE concrete new rule
    3. Append it to rules.md (deduplicated — never overwrite)
    """
    if not SESSION_LOG.exists():
        print("[evolve] No sessions recorded yet.")
        return None

    sessions = SESSION_LOG.read_text().strip().splitlines()[-last_n:]
    if not sessions:
        print("[evolve] No sessions recorded yet.")
        return None

    sessions_text = "\n".join(sessions)
    existing_rules = RULES_FILE.read_text() if RULES_FILE.exists() else "(none yet)"

    messages = [
        {
            "role": "system",
            "content": (
                "You are Legiona's self-improvement module. "
                "You analyze past agent sessions and propose exactly ONE new rule "
                "to improve future performance. Rules must be concrete and actionable. "
                "Do not repeat existing rules."
            ),
        },
        {
            "role": "user",
            "content": (
                f"EXISTING RULES:\n{existing_rules}\n\n"
                f"LAST {last_n} SESSIONS:\n{sessions_text}\n\n"
                "Based on these sessions, propose ONE new rule to add. "
                "Format: '- [RULE N]: <rule text>' where N is the next number."
            ),
        },
    ]

    result = complete(messages, preset="research")
    new_rule = result.answer.strip()

    # Gap 2 fix: deduplicate before appending
    if _rule_exists(new_rule):
        print(f"[evolve] Rule already exists (deduplicated): {new_rule[:80]}...")
        return None

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    rule_entry = f"\n<!-- evolved: {timestamp} -->\n{new_rule}\n"
    with open(RULES_FILE, "a") as f:
        f.write(rule_entry)

    # Also sync to global_memory.md "Self-Evolved Rules" section
    _sync_global_memory(new_rule, timestamp)

    print(f"[evolve] New rule added: {new_rule[:80]}...")
    return new_rule


def load_evolved_rules() -> str:
    """
    Returns evolved rules from both session-scoped rules.md
    and cross-session global_memory.md, concatenated.
    """
    parts = []
    if RULES_FILE.exists():
        parts.append(f"## SESSION RULES\n{RULES_FILE.read_text()}\n")
    if GLOBAL_MEMORY_FILE.exists():
        parts.append(f"## GLOBAL RULES\n{GLOBAL_MEMORY_FILE.read_text()}\n")
    if not parts:
        return ""
    return "\n## SELF-EVOLVED RULES\n" + "".join(parts)


def _analyze_failure_patterns(sessions: list[dict]) -> dict:
    """
    Analyze failed or degraded sessions to extract failure pattern statistics.
    Reads sessions.jsonl directly to build a pattern report.

    Returns dict with keys:
        - total_sessions: int
        - failure_rate: float
        - common_errors: list[tuple[str, int]]  (error, count) sorted desc
        - tool_call_failures: dict[str, int]
        - avg_tool_calls: float
    """
    import json

    if not SESSION_LOG.exists():
        return {
            "total_sessions": 0,
            "failure_rate": 0.0,
            "common_errors": [],
            "tool_call_failures": {},
            "avg_tool_calls": 0.0,
        }

    # Read and parse all session records from sessions.jsonl
    raw_lines = SESSION_LOG.read_text().strip().splitlines()
    all_sessions = [json.loads(line) for line in raw_lines if line.strip()]

    if not all_sessions:
        return {
            "total_sessions": 0,
            "failure_rate": 0.0,
            "common_errors": [],
            "tool_call_failures": {},
            "avg_tool_calls": 0.0,
        }

    total = len(all_sessions)
    failed = sum(1 for s in all_sessions if not s.get("success", False))
    failure_rate = failed / total if total > 0 else 0.0

    # Build error keyword frequency
    error_counter: dict[str, int] = {}
    tool_failure_counter: dict[str, int] = {}
    total_tool_calls = 0

    for session in all_sessions:
        outcome = session.get("outcome", "")
        if not session.get("success", False) and outcome:
            # Lowercase and tokenize for error keyword aggregation
            import re
            words = re.findall(r"[a-z_]+", outcome.lower())
            for word in words:
                if len(word) > 3:  # skip short tokens
                    error_counter[word] = error_counter.get(word, 0) + 1

        # Track tool call failures by tool name
        tool_summary = session.get("tool_calls_summary", [])
        total_tool_calls += len(tool_summary)

    # Sort errors by frequency
    common_errors = sorted(error_counter.items(), key=lambda x: x[1], reverse=True)[:10]

    avg_tool_calls = total_tool_calls / total if total > 0 else 0.0

    return {
        "total_sessions": total,
        "failure_rate": failure_rate,
        "common_errors": common_errors,
        "tool_call_failures": tool_failure_counter,
        "avg_tool_calls": avg_tool_calls,
    }


def _auto_search_related_files(error_keyword: str) -> list[str]:
    """
    Search codebase for files related to an error keyword using grep.
    Returns a sorted list of unique file paths that contain the keyword.
    """
    import subprocess

    if not error_keyword or not error_keyword.strip():
        return []

    keyword = error_keyword.strip()
    results: set[str] = set()

    # Search Python files, excluding test files and venv
    for ext in ["*.py", "*.md", "*.yaml", "*.yml"]:
        try:
            result = subprocess.run(
                ["grep", "-rl", "--include=" + ext, keyword, "."],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0 and result.stdout.strip():
                for path in result.stdout.strip().splitlines():
                    # Filter out noise: tests/, .venv/, __pycache__, .git/
                    if not any(
                        noise in path
                        for noise in ["/tests/", ".venv/", "__pycache__/", ".git/", "node_modules/"]
                    ):
                        results.add(path)
        except (subprocess.TimeoutExpired, OSError):
            pass

    return sorted(results)


def _compare_and_revert(before_score: float, after_score: float, rule_text: str) -> bool:
    """
    Compare score before/after applying a new rule.
    If after_score is worse (lower) than before_score by more than 5%, revert the rule.

    Revert means removing the rule from both rules.md and global_memory.md.
    Returns True if reverted, False if the rule was kept.
    """
    DEGRADATION_THRESHOLD = 0.05  # 5% score drop triggers revert

    if before_score <= 0 or after_score <= 0:
        return False

    change_ratio = (after_score - before_score) / before_score

    # Only revert if score degraded beyond threshold
    if change_ratio >= -DEGRADATION_THRESHOLD:
        # No significant degradation — keep the rule
        return False

    # Score degraded — revert the rule from both files
    normalized = _normalize_rule(rule_text)

    # Revert from rules.md
    if RULES_FILE.exists():
        lines = RULES_FILE.read_text().splitlines()
        kept_lines = []
        reverted = False
        for line in lines:
            if _normalize_rule(line) == normalized:
                reverted = True
                continue  # drop this line
            kept_lines.append(line)
        if reverted:
            RULES_FILE.write_text("\n".join(kept_lines) + "\n")

    # Revert from global_memory.md
    if GLOBAL_MEMORY_FILE.exists():
        text = GLOBAL_MEMORY_FILE.read_text()
        for line in text.splitlines():
            if _normalize_rule(line) == normalized:
                text = text.replace(line + "\n", "").replace(line, "")
        GLOBAL_MEMORY_FILE.write_text(text)

    print(f"[revert] Rule reverted due to score degradation: {rule_text[:80]}...")
    return True
