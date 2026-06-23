#!/usr/bin/python3
"""
Claude Code Session Status — tracks current task, subtask checklist, files, elapsed time.
Persistently stores state across context windows in ~/.claude/session/state.json.

Usage:
    status                          # show full status report
    status new <task>               # set current task
    status done                     # mark current task complete
    status add <subtask>            # add subtask to checklist
    status complete <subtask>        # mark subtask done
    status clear                    # reset session state
"""

import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

STATE_FILE = Path.home() / ".claude" / "session" / "state.json"
STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

# ── state helpers ────────────────────────────────────────────────────────────

def _read() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"session_start": time.time()}

def _write(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2))

def _fmtdur(s: float) -> str:
    if s < 60:
        return f"{s:.0f}s"
    if s < 3600:
        return f"{s/60:.1f}m"
    return f"{s/3600:.1f}h"

# ── commands ────────────────────────────────────────────────────────────────

def cmd_new(task: str) -> str:
    state = _read()
    if "current_task" in state:
        return f"❗ Task already in progress: {state['current_task']}\n  Finish it first with: status done"
    state["current_task"] = task
    state["task_started_at"] = time.time()
    _write(state)
    return f"✅ Task started: {task}"

def cmd_done() -> str:
    state = _read()
    task = state.pop("current_task", None)
    if not task:
        return "❗ No task in progress."
    started = state.pop("task_started_at", None)
    completed = state.get("completed_tasks", [])
    completed.append({"task": task, "started_at": started, "completed_at": time.time()})
    state["completed_tasks"] = completed[-20:]
    _write(state)
    return f"✅ Task completed: {task}"

def cmd_add(subtask: str) -> str:
    state = _read()
    checklist = state.get("checklist", [])
    checklist.append({"task": subtask, "done": False, "added_at": time.time()})
    state["checklist"] = checklist
    _write(state)
    idx = len(checklist)
    return f"✅ Added [{idx}] {subtask}"

def cmd_complete(subtask: str) -> str:
    state = _read()
    checklist = state.get("checklist", [])
    matched = None
    for item in checklist:
        if item["task"] == subtask and not item.get("done"):
            item["done"] = True
            item["completed_at"] = time.time()
            matched = item["task"]
    if not matched:
        return f"❗ Subtask not found or already done: {subtask}"
    state["checklist"] = checklist
    _write(state)
    return f"✅ Done: {matched}"

def cmd_clear() -> str:
    if STATE_FILE.exists():
        STATE_FILE.unlink()
    return "🗑 Session state cleared."

def cmd_status() -> str:
    state = _read()
    session_start = state.get("session_start", time.time())
    elapsed = time.time() - session_start

    lines = ["```\n━━━ Claude Code Session ━━━\n"]

    # Session
    start_hr = datetime.fromtimestamp(session_start, tz=UTC).strftime("%H:%M:%S UTC")
    lines.append(f"Duration  : {_fmtdur(elapsed)}")
    lines.append(f"Started   : {start_hr}")

    # Current task
    current = state.get("current_task")
    if current:
        ta = state.get("task_started_at")
        ta_fmt = _fmtdur(time.time() - ta) if ta else "?"
        lines.append(f"\n▶ Task    : {current}")
        lines.append(f"  Elapsed : {ta_fmt}")
    else:
        lines.append("\n▶ Task    : (none)")

    # Checklist
    checklist = state.get("checklist", [])
    if checklist:
        lines.append(f"\n⬜ Tasks  : {len([x for x in checklist if not x.get('done')])}/{len(checklist)} remaining")
        for i, item in enumerate(checklist, 1):
            mark = "✅" if item.get("done") else "⬜"
            lines.append(f"  {mark} [{i}] {item['task']}")

    # Completed
    completed = state.get("completed_tasks", [])
    if completed:
        lines.append(f"\n✅ Done   : {len(completed)} total")
        for item in completed[-3:]:
            lines.append(f"  ✓ {item['task'][:55]}")

    # Recent files
    recent = state.get("recent_files", [])
    if recent:
        lines.append(f"\n📁 Files  : {len(recent)} accessed")
        for f in recent[-4:]:
            lines.append(f"  • {f}")

    lines.append(f"\nState file: {STATE_FILE}")
    lines.append("```")
    return "\n".join(lines)

# ── main ──────────────────────────────────────────────────────────────────────

USAGE = """usage: status [<command>]

Commands:
  status              show full status report
  status new <task>   start a new task
  status done         mark current task complete
  status add <task>   add subtask to checklist
  status complete <task>  mark subtask done
  status clear        reset all state
"""

def main() -> int:
    args = sys.argv[1:]

    if not args or args[0] == "status":
        print(cmd_status())
        return 0

    cmd = args[0]

    if cmd == "new":
        if len(args) < 2:
            print("usage: status new <task>")
            return 1
        print(cmd_new(" ".join(args[1:])))

    elif cmd == "done":
        print(cmd_done())

    elif cmd == "add":
        if len(args) < 2:
            print("usage: status add <subtask>")
            return 1
        print(cmd_add(" ".join(args[1:])))

    elif cmd == "complete":
        if len(args) < 2:
            print("usage: status complete <subtask>")
            return 1
        print(cmd_complete(" ".join(args[1:])))

    elif cmd == "clear":
        print(cmd_clear())

    else:
        print(f"unknown command: {cmd}\n{USAGE}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
