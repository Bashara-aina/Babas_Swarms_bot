#!/usr/bin/env python3
"""End-to-end context tracking bridge — called from hooks on every tool use.

This is the glue that makes context tracking work end-to-end.
Called from PostToolUse and UserPromptSubmit hooks to:

1. Register messages with ContextCompactor (creates session_messages.json)
2. Update context utilization estimates
3. Log current status for the statusline
4. Auto-trigger compaction warnings when thresholds are hit

Usage:
    python scripts/track_context.py register     -- Record a tool use event
    python scripts/track_context.py message      -- Record a user/assistant message
    python scripts/track_context.py status       -- Print current utilization

Designed to run in <100ms.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", Path.cwd()))
DATA_DIR = PROJECT_ROOT / ".claude-flow" / "data"
SESSION_MSGS_PATH = DATA_DIR / "session_messages.json"
CURRENT_JSON_PATH = DATA_DIR / "current.json"
SESSION_STATE_PATH = DATA_DIR / "session_state.json"
MAX_TOKENS = 1_048_576  # deepseek-v4-flash


def _ensure_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _read_msgs() -> list[dict]:
    if SESSION_MSGS_PATH.exists():
        try:
            return json.loads(SESSION_MSGS_PATH.read_text())
        except Exception:
            pass
    return []


def _write_msgs(msgs: list[dict]) -> None:
    _ensure_dir()
    # Keep last 200 messages
    if len(msgs) > 200:
        msgs = msgs[-200:]
    SESSION_MSGS_PATH.write_text(json.dumps(msgs))


def _update_utilization(msgs: list[dict]) -> dict:
    """Calculate and persist current context utilization."""
    total_chars = sum(len(m.get("content", "")) for m in msgs)
    total_tok = total_chars // 4
    pct = min(100.0, (total_tok / MAX_TOKENS) * 100)

    state = {
        "context_length": total_chars,
        "context_tokens": total_tok,
        "max_tokens": MAX_TOKENS,
        "utilization_pct": round(pct, 1),
        "message_count": len(msgs),
        "last_updated": time.time(),
    }

    _ensure_dir()
    SESSION_STATE_PATH.write_text(json.dumps(state, indent=2))
    return state


def _read_session_metadata() -> dict:
    """Read session metadata from current.json."""
    if CURRENT_JSON_PATH.exists():
        try:
            return json.loads(CURRENT_JSON_PATH.read_text())
        except Exception:
            pass
    return {}


def register_tool_event(tool_name: str = "") -> None:
    """Register a tool use event — called from PostToolUse hook."""
    msgs = _read_msgs()
    meta = _read_session_metadata()

    # Record the tool event as a system message
    entry = {
        "role": "tool",
        "content": f"[tool:{tool_name}]",
        "timestamp": time.time(),
    }
    msgs.append(entry)
    _write_msgs(msgs)
    state = _update_utilization(msgs)

    # Warn if approaching limits
    if state["utilization_pct"] >= 80:
        msg = f"[CONTEXT] {state['utilization_pct']}% — approaching 1M limit ({state['context_tokens']:,} / {MAX_TOKENS:,} tokens)"
        print(msg, file=sys.stderr)


def register_message(role: str = "user", content: str = "") -> None:
    """Register a user or assistant message — called from UserPromptSubmit hook.

    Args:
        role: "user" or "assistant"
        content: Message text (empty = auto-read from stdin or current.json)
    """
    if not content:
        # Try reading from stdin (UserPromptSubmit passes the full prompt)
        import sys as _sys
        try:
            stdin_data = _sys.stdin.read() if not _sys.stdin.isatty() else ""
            if stdin_data:
                try:
                    parsed = json.loads(stdin_data)
                    prompt = parsed.get("prompt", "") or parsed.get("toolInput", {}).get("prompt", "") or parsed.get("tool_input", {}).get("prompt", "")
                    if prompt and len(prompt) > len(content):
                        content = prompt
                except (json.JSONDecodeError, Exception):
                    pass
        except Exception:
            pass

    if not content:
        # Fallback: read from current.json (may be truncated to 500 chars)
        meta = _read_session_metadata()
        ctx = meta.get("context", {})
        content = ctx.get("lastUserQuery", "")

    if not content:
        return

    msgs = _read_msgs()
    entry = {
        "role": role,
        "content": content,
        "timestamp": time.time(),
    }
    msgs.append(entry)
    _write_msgs(msgs)
    state = _update_utilization(msgs)

    # Print to stderr for statusline consumption
    pct = state["utilization_pct"]
    bar_len = 20
    filled = int(pct / 100 * bar_len)
    bar = "█" * filled + "░" * (bar_len - filled)
    print(f"[CONTEXT] {bar} {pct:.1f}% ({state['context_tokens']:,} / {MAX_TOKENS:,} tokens, {state['message_count']} msgs)",
          file=sys.stderr)


def print_status() -> None:
    """Print current context utilization."""
    state_path = SESSION_STATE_PATH
    if state_path.exists():
        try:
            state = json.loads(state_path.read_text())
            pct = state.get("utilization_pct", 0)
            tok = state.get("context_tokens", 0)
            msgs = state.get("message_count", 0)
            bar_len = 20
            filled = int(pct / 100 * bar_len)
            bar = "█" * filled + "░" * (bar_len - filled)
            print(f"[CONTEXT] {bar} {pct:.1f}% ({tok:,} / {MAX_TOKENS:,} tokens, {msgs} msgs)")
            return
        except Exception:
            pass

    # Fallback: calculate from messages
    msgs = _read_msgs()
    if msgs:
        state = _update_utilization(msgs)
        pct = state["utilization_pct"]
        tok = state["context_tokens"]
        bar_len = 20
        filled = int(pct / 100 * bar_len)
        bar = "█" * filled + "░" * (bar_len - filled)
        print(f"[CONTEXT] {bar} {pct:.1f}% ({tok:,} / {MAX_TOKENS:,} tokens, {len(msgs)} msgs)")
    else:
        print("[CONTEXT] No session data yet — tracking starts after first message.")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: track_context.py <register|message|status> [args...]", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]

    if command == "register":
        tool_name = sys.argv[2] if len(sys.argv) > 2 else ""
        register_tool_event(tool_name)
    elif command == "message":
        role = sys.argv[2] if len(sys.argv) > 2 else "user"
        content = sys.argv[3] if len(sys.argv) > 3 else ""
        register_message(role, content)
    elif command == "status":
        print_status()
    elif command == "init":
        # Initialize empty tracking at session start — always reset
        _ensure_dir()
        SESSION_MSGS_PATH.write_text("[]")
        state = _update_utilization([])
        print(f"[CONTEXT] Tracking initialized: 0 / {MAX_TOKENS:,} tokens (0%)", file=sys.stderr)
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
