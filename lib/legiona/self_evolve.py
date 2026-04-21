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


def evolve(last_n: int = 5) -> str | None:
    """
    Read last N sessions. Ask M2.7 to:
    1. Identify what went wrong or could be improved
    2. Propose ONE concrete new rule
    3. Append it to rules.md
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

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    with open(RULES_FILE, "a") as f:
        f.write(f"\n<!-- evolved: {timestamp} -->\n{new_rule}\n")

    print(f"[evolve] New rule added: {new_rule[:80]}...")
    return new_rule


def load_evolved_rules() -> str:
    """Returns current rules as a string to prepend to system prompts."""
    if not RULES_FILE.exists():
        return ""
    return f"\n## SELF-EVOLVED RULES (do not override)\n{RULES_FILE.read_text()}\n"
