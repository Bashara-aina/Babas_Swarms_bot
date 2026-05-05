"""Claude Code /status skill — Session progress dashboard."""

from __future__ import annotations

import json
import os
import time
from datetime import UTC, datetime, timezone
from pathlib import Path
from typing import Any

# Session state file (persists across context windows)
STATE_FILE = Path.home() / ".claude" / "session" / "state.json"
STATE_FILE.parent.mkdir(parents=True, exist_ok=True)


def get_session_start() -> float | None:
    """Get session start timestamp."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text()).get("session_start")
        except Exception:
            pass
    return None


def set_current_task(task: str) -> None:
    """Record current task."""
    _update_state({"current_task": task, "task_started_at": time.time()})


def set_task_complete() -> None:
    """Mark current task as complete."""
    state = _read_state()
    if "current_task" in state:
        completed = state.get("completed_tasks", [])
        completed.append({
            "task": state["current_task"],
            "started_at": state.get("task_started_at"),
            "completed_at": time.time(),
        })
        state["completed_tasks"] = completed[-10:]  # keep last 10
    state.pop("current_task", None)
    state.pop("task_started_at", None)
    _write_state(state)


def add_subtask(subtask: str) -> None:
    """Add a subtask to the checklist."""
    state = _read_state()
    checklist = state.get("checklist", [])
    checklist.append({"task": subtask, "done": False, "added_at": time.time()})
    state["checklist"] = checklist
    _write_state(state)


def complete_subtask(subtask: str) -> None:
    """Mark a subtask as done."""
    state = _read_state()
    checklist = state.get("checklist", [])
    for item in checklist:
        if item["task"] == subtask:
            item["done"] = True
            item["completed_at"] = time.time()
    state["checklist"] = checklist
    _write_state(state)


def record_files_accessed(files: list[str]) -> None:
    """Record files read or written."""
    state = _read_state()
    state["recent_files"] = files[-20:]  # last 20
    _write_state(state)


def _update_state(updates: dict[str, Any]) -> None:
    """Merge updates into current state and persist."""
    state = _read_state()
    state.update(updates)
    _write_state(state)


def _read_state() -> dict[str, Any]:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"session_start": time.time()}


def _write_state(state: dict[str, Any]) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2))


def _format_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}m"
    else:
        return f"{seconds/3600:.1f}h"


def build_status_report() -> str:
    """Build the full status report."""
    state = _read_state()
    session_start = state.get("session_start", time.time())
    elapsed = time.time() - session_start

    lines = ["## Claude Code Session Status\n"]

    # Session info
    datetime.now(UTC).astimezone().tzname()
    lines.append(f"**Session duration**: {_format_duration(elapsed)}")
    lines.append(f"**Started**: {datetime.fromtimestamp(session_start, tz=UTC).strftime('%H:%M:%S UTC')}")

    # Current task
    current_task = state.get("current_task")
    if current_task:
        task_started = state.get("task_started_at")
        task_elapsed = time.time() - task_started if task_started else 0
        lines.append(f"\n**Current task**: {current_task}")
        lines.append(f"**Running for**: {_format_duration(task_elapsed)}")
    else:
        lines.append("\n**Current task**: (none)")

    # Checklist
    checklist = state.get("checklist", [])
    if checklist:
        lines.append("\n**Sub-tasks:**")
        for item in checklist:
            status = "✅" if item.get("done") else "⬜"
            lines.append(f"  {status} {item['task']}")

    # Completed tasks
    completed = state.get("completed_tasks", [])
    if completed:
        lines.append(f"\n**Completed ({len(completed)}):**")
        for item in completed[-3:]:  # show last 3
            lines.append(f"  ✅ {item['task'][:60]}")

    # Recent files
    recent = state.get("recent_files", [])
    if recent:
        lines.append(f"\n**Recent files ({len(recent)}):**")
        for f in recent[-5:]:
            lines.append(f"  - `{f}`")

    lines.append(f"\n---\n*State file: `{STATE_FILE}`*")
    return "\n".join(lines)


SKILL_METADATA = {
    "name": "session-status",
    "description": "Track Claude Code session progress — current task, subtask checklist, files accessed, elapsed time",
    "keywords": ["status", "progress", "session", "task", "checklist", "todo"],
}
