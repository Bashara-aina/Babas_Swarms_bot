"""
core/legion_state.py
===================
Manages /tmp/legion_*.txt shared state files used for inter-agent
communication in the LEGION swarm dispatch system.

These files are the communication bus between @planner, @worker, @reviewer,
@verifier, and @hermes-agent during swarm execution.

File conventions:
  /tmp/legion_session_context.txt    — mem0 memories, session boot
  /tmp/legion_temporal_context.txt   — git changes in last 24h
  /tmp/legion_available_skills.txt  — hermes skill index (auto-generated)
  /tmp/legion_plan.md               — @planner locked spec
  /tmp/legion_build_result.md      — @worker output
  /tmp/legion_review.md            — @reviewer critique
  /tmp/legion_verify.md            — @verifier test results
  /tmp/legion_research.md          — @hermes-researcher findings
  /tmp/legion_session_summary.txt  — end-of-session summary
  /tmp/legion_precompact_checkpoint.md — pre-compaction state
  /tmp/legion_hermes_skills.txt   — cached hermes skills
  /tmp/legion_pending_skills.jsonl — skills written when hermes was down
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

TMP_DIR = Path("/tmp")
PREFIX = "legion_"

SESSION_CONTEXT = TMP_DIR / f"{PREFIX}session_context.txt"
TEMPORAL_CONTEXT = TMP_DIR / f"{PREFIX}temporal_context.txt"
AVAILABLE_SKILLS = TMP_DIR / f"{PREFIX}available_skills.txt"
PLAN = TMP_DIR / f"{PREFIX}plan.md"
BUILD_RESULT = TMP_DIR / f"{PREFIX}build_result.md"
REVIEW = TMP_DIR / f"{PREFIX}review.md"
VERIFY = TMP_DIR / f"{PREFIX}verify.md"
RESEARCH = TMP_DIR / f"{PREFIX}research.md"
SESSION_SUMMARY = TMP_DIR / f"{PREFIX}session_summary.txt"
PRECOMPACT = TMP_DIR / f"{PREFIX}precompact_checkpoint.md"
HERMES_SKILLS = TMP_DIR / f"{PREFIX}hermes_skills.txt"
PENDING_SKILLS = TMP_DIR / f"{PREFIX}pending_skills.jsonl"

STATE_FILES = {
    "session_context": SESSION_CONTEXT,
    "temporal_context": TEMPORAL_CONTEXT,
    "available_skills": AVAILABLE_SKILLS,
    "plan": PLAN,
    "build_result": BUILD_RESULT,
    "review": REVIEW,
    "verify": VERIFY,
    "research": RESEARCH,
    "session_summary": SESSION_SUMMARY,
    "precompact": PRECOMPACT,
    "hermes_skills": HERMES_SKILLS,
    "pending_skills": PENDING_SKILLS,
}

STALE_THRESHOLD_SECONDS = 4 * 3600


def read_state(name: str) -> str:
    """Read a state file. Returns empty string if missing or stale."""
    path = STATE_FILES.get(name)
    if not path or not path.exists():
        return ""
    try:
        age = time.time() - path.stat().st_mtime
        if age > STALE_THRESHOLD_SECONDS:
            return ""
        return path.read_text()
    except OSError:
        return ""


def write_state(name: str, content: str) -> None:
    """Write content to a state file. Creates parent dir if needed."""
    path = STATE_FILES.get(name)
    if not path:
        raise ValueError(f"Unknown state file: {name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def read_json_state(name: str) -> dict[str, Any]:
    """Read a state file parsed as JSON."""
    content = read_state(name)
    if not content:
        return {}
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {}


def write_json_state(name: str, data: dict[str, Any]) -> None:
    """Write a dict to a state file as JSON."""
    write_state(name, json.dumps(data, indent=2, ensure_ascii=False))


def append_state(name: str, line: str) -> None:
    """Append a single line to a state file."""
    path = STATE_FILES.get(name)
    if not path:
        raise ValueError(f"Unknown state file: {name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as f:
        f.write(line + "\n")


def clear_state(name: str) -> None:
    """Clear a state file (write empty string)."""
    write_state(name, "")


def clear_all() -> None:
    """Clear all state files. Use at session start."""
    for path in STATE_FILES.values():
        if path.exists():
            path.unlink()


def is_stale(name: str) -> bool:
    """Check if a state file is stale (>4h old) or missing."""
    path = STATE_FILES.get(name)
    if not path or not path.exists():
        return True
    return (time.time() - path.stat().st_mtime) > STALE_THRESHOLD_SECONDS


def get_session_summary() -> dict[str, Any]:
    """Parse the session summary into a structured dict."""
    content = read_state("session_summary")
    if not content:
        return {}
    return {"content": content, "age_seconds": _file_age("session_summary")}


def _file_age(name: str) -> float:
    """Get age of a state file in seconds. Returns float('inf') if missing."""
    path = STATE_FILES.get(name)
    if not path or not path.exists():
        return float("inf")
    return time.time() - path.stat().st_mtime


def write_plan(contracts: list[dict[str, Any]], locked: bool = True) -> None:
    """Write a planner spec to /tmp/legion_plan.md."""
    lines = ["# LEGION PLAN\n"]
    if locked:
        lines.append("*LOCKED — do not revise during execution*\n")
    lines.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    lines.append(f"Contracts: {len(contracts)}\n")
    for i, c in enumerate(contracts, 1):
        lines.append(f"\n## CONTRACT {i}: {c.get('title', 'untitled')}\n")
        lines.append(f"{c.get('what', '')}\n")
        reads = c.get("files", {}).get("READ", [])
        writes = c.get("files", {}).get("WRITE", [])
        lines.append(f"READ:  {reads}\n")
        lines.append(f"WRITE: {writes}\n")
        done = c.get("DONE_WHEN", [])
        for d in done:
            lines.append(f"- {d}\n")
    write_state("plan", "".join(lines))


def write_build_result(contract_n: int, status: str, proof: str, files: list[str]) -> None:
    """Append a worker build result to /tmp/legion_build_result.md."""
    entry = f"\n## CONTRACT {contract_n}: {status}\n"
    entry += f"Proof:\n{proof}\n"
    entry += f"Files: {', '.join(files)}\n"
    existing = read_state("build_result")
    write_state("build_result", existing + entry)


def write_review(contract_n: int, findings: list[str]) -> None:
    """Write @reviewer findings to /tmp/legion_review.md."""
    lines = [f"\n## CONTRACT {contract_n} REVIEW\n"]
    for f in findings:
        lines.append(f"- {f}\n")
    existing = read_state("review")
    write_state("review", existing + "".join(lines))


def write_verify(contract_n: int, passed: bool, output: str) -> None:
    """Write @verifier results to /tmp/legion_verify.md."""
    status = "PASS" if passed else "FAIL"
    entry = f"\n## CONTRACT {contract_n}: {status}\n"
    entry += f"Output:\n{output}\n"
    existing = read_state("verify")
    write_state("verify", existing + entry)


def write_research_findings(topic: str, synthesis: str, sources: list[str]) -> None:
    """Write @hermes-researcher findings to /tmp/legion_research.md."""
    entry = f"\n# RESEARCH: {topic}\n"
    entry += f"Synthesis:\n{synthesis}\n"
    entry += f"\nSources:\n"
    for s in sources:
        entry += f"- {s}\n"
    existing = read_state("research")
    write_state("research", existing + entry)


def write_precompact_checkpoint(
    in_progress: str,
    files: list[str],
    decisions: list[str],
    blockers: list[str],
    next_action: str,
) -> None:
    """Write pre-compaction checkpoint to /tmp/legion_precompact_checkpoint.md."""
    content = f"""# PRE-COMPACTION CHECKPOINT
Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}

## IN PROGRESS
{in_progress}

## ACTIVE FILES
"""
    for f in files:
        content += f"- {f}\n"
    content += "\n## RECENT DECISIONS\n"
    for d in decisions:
        content += f"- {d}\n"
    content += "\n## BLOCKERS\n"
    for b in blockers:
        content += f"- {b}\n"
    content += f"\n## NEXT ACTION\n{next_action}\n"
    write_state("precompact", content)


def write_session_summary(
    accomplished: list[str],
    decisions: list[str],
    files_changed: list[str],
    errors: list[str],
    open_questions: list[str],
    tool_calls: int,
) -> None:
    """Write end-of-session summary to /tmp/legion_session_summary.txt."""
    content = f"""# SESSION SUMMARY
Date: {time.strftime('%Y-%m-%d %H:%M:%S')}

## ACCOMPLISHED
"""
    for a in accomplished:
        content += f"- {a}\n"
    content += "\n## KEY DECISIONS\n"
    for d in decisions:
        content += f"- {d}\n"
    content += "\n## FILES CHANGED\n"
    for f in files_changed:
        content += f"- {f}\n"
    content += "\n## ERRORS\n"
    for e in errors:
        content += f"- {e}\n"
    content += "\n## OPEN QUESTIONS\n"
    for q in open_questions:
        content += f"- {q}\n"
    content += f"\n## METRICS\nTool calls: {tool_calls}\n"
    if len(content) > 2000:
        content = content[:2000] + "\n[TRUNCATED]\n"
    write_state("session_summary", content)
