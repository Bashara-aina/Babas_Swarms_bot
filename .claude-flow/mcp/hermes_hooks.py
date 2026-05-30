#!/usr/bin/env python3
"""
Hermes Hook System — Claude Code 26-event lifecycle hooks replicated for Hermes MCP.

Provides a hook registry with persistence, blocking/non-blocking execution,
and auto-fire integration points across Hermes modules.

Usage:
    from hermes_hooks import hook_register, hook_fire, hook_list, HERMES_HOOKS_SCHEMA
    result = hook_fire("pre-tool-call", {"tool_name": "read_file", "args": {...}})
"""

import asyncio
import hashlib
import json
import os
import sqlite3
import subprocess
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, Optional

# ── Constants ────────────────────────────────────────────────────────────────

HERMES_HOOKS_DIR = Path.home() / ".hermes" / "hooks"
HERMES_HOOKS_DB = HERMES_HOOKS_DIR / "hooks.db"
HOOK_TIMEOUT = 30  # seconds per hook script
HOOK_SCHEMA_VERSION = "1.0"

# Default disabled events (experimental)
_DEFAULT_DISABLED: set[str] = {
    "pre-memory-flush", "post-memory-flush",
    "pre-context-restore", "post-context-restore",
    "pre-snapshot", "post-snapshot",
}

# ── 26 Hook Events ────────────────────────────────────────────────────────────

HOOK_EVENTS: list[str] = [
    # Tool lifecycle
    "pre-tool-call",
    "post-tool-call",
    # Command lifecycle
    "pre-command",
    "post-command",
    # File operations
    "pre-file-write",
    "post-file-write",
    # Git operations
    "pre-commit",
    "post-commit",
    # Bash/shell
    "pre-bash",
    "post-bash",
    # Session lifecycle
    "pre-session-start",
    "post-session-end",
    # Task lifecycle
    "pre-task-start",
    "post-task-complete",
    # Messaging
    "pre-message-send",
    "post-message-received",
    # Agent spawning
    "pre-spawn-agent",
    "post-spawn-agent",
    # Tool results
    "pre-tool-result",
    "post-tool-result",
    # Error handling
    "pre-error",
    "post-error",
    # Context restore
    "pre-context-restore",
    "post-context-restore",
    # Memory management
    "pre-memory-flush",
    "post-memory-flush",
    # Snapshots
    "pre-snapshot",
    "post-snapshot",
]

# ── Built-in Hook Scripts ─────────────────────────────────────────────────────

BUILTIN_HOOKS: dict[str, str] = {
    # Auto-format on file write (eslint --fix for JS/TS)
    "builtin:eslint-fix": """#!/usr/bin/env bash
# Auto-fix ESLint errors on file write
FILE="$1"
EXT="${FILE##*.}"
case "$EXT" in
  js|jsx|ts|tsx|mjs|cjs)
    if command -v eslint &>/dev/null; then
      npx eslint --fix "$FILE" 2>/dev/null || true
    fi
    ;;
esac
exit 0
""",

    # Auto-format on file write (prettier --write)
    "builtin:prettier-fix": """#!/usr/bin/env bash
# Auto-format with prettier on file write
FILE="$1"
EXT="${FILE##*.}"
case "$EXT" in
  js|jsx|ts|tsx|css|scss|json|md|yaml|yml|toml)
    if command -v prettier &>/dev/null; then
      npx prettier --write "$FILE" 2>/dev/null || true
    fi
    ;;
esac
exit 0
""",

    # Pre-commit secret scanning with gitleaks or trufflehog
    "builtin:secret-scan": """#!/usr/bin/env bash
# Scan files for secrets before commit
FILES="$@"
if command -v trufflehog &>/dev/null; then
  trufflehog files $FILES 2>/dev/null && exit 1 || true
elif command -v gitleaks &>/dev/null; then
  for FILE in $FILES; do
    gitleaks detect --no-color --quiet -s "$FILE" 2>/dev/null && exit 1 || true
  done
fi
exit 0
""",

    # Post-task memory commit
    "builtin:memory-commit": """#!/usr/bin/env bash
# Commit key decisions to memory after task complete
TASK="$1"
CONTEXT="$2"
HERMES_DIR="${HOME}/.hermes"
mkdir -p "$HERMES_DIR/checkpoints"
echo "[$(date -Iseconds)] Task: $TASK" >> "$HERMES_DIR/checkpoints/tasks.log"
echo "  Context: ${CONTEXT:0:200}" >> "$HERMES_DIR/checkpoints/tasks.log"
exit 0
""",

    # Post-session-end disk cleanup
    "builtin:session-cleanup": """#!/usr/bin/env bash
# Clean temp files after session end
rm -rf /tmp/hermes_* 2>/dev/null || true
rm -rf /tmp/swarm_* 2>/dev/null || true
exit 0
""",

    # Pre-tool-call logging
    "builtin:tool-logger": """#!/usr/bin/env bash
# Log tool calls to audit trail
TOOL="$1"
ARGS="$2"
HERMES_DIR="${HOME}/.hermes"
mkdir -p "$HERMES_DIR/audit"
echo "[$(date -Iseconds)] TOOL_CALL: $TOOL" >> "$HERMES_DIR/audit/tool_calls.log"
echo "  Args: ${ARGS:0:500}" >> "$HERMES_DIR/audit/tool_calls.log"
exit 0
""",

    # Post-error alert (basic notification)
    "builtin:error-alert": """#!/usr/bin/env bash
# Send notification on errors
ERROR="$1"
# Could integrate with pushover, discord webhook, etc.
echo "[ERROR $(date)] $ERROR" >> "${HOME}/.hermes/errors.log"
exit 0
""",
}


# ── Schema for MCP handler ────────────────────────────────────────────────────

HERMES_HOOKS_SCHEMA = {
    "name": "hermes_hooks",
    "description": "26-event lifecycle hook system for Hermes MCP. "
                   "Manages custom scripts that fire before/after key lifecycle events.",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "enum": ["register", "unregister", "fire", "list", "enable", "disable", "builtin"],
                "description": "Action to perform on hook system",
            },
            "event": {
                "type": "string",
                "enum": HOOK_EVENTS,
                "description": "Hook event name",
            },
            "script_path": {
                "type": "string",
                "description": "Path to hook script (for register action)",
            },
            "hook_id": {
                "type": "string",
                "description": "Unique hook ID (for unregister/enable/disable actions)",
            },
            "context": {
                "type": "object",
                "description": "Context data passed to hook script as JSON on stdin",
            },
            "blocking": {
                "type": "boolean",
                "default": False,
                "description": "If true, hook must complete before main flow continues",
            },
            "builtin_name": {
                "type": "string",
                "description": "Name of built-in hook to register (for built-in action)",
            },
            "timeout": {
                "type": "integer",
                "default": 30,
                "description": "Timeout for hook execution in seconds",
            },
        },
    },
}


# ── Hook Registry ─────────────────────────────────────────────────────────────

class HookRegistry:
    """
    Thread-safe registry for lifecycle hooks with SQLite persistence.
    Supports blocking/non-blocking execution, enable/disable, and built-in hooks.
    """

    _instance: Optional["HookRegistry"] = None
    _lock = threading.Lock()

    def __init__(self):
        self._hooks: dict[str, list[dict]] = {}  # event -> list of hook entries
        self._disabled: set[str] = set(_DEFAULT_DISABLED.copy())
        self._builtin_registered: set[str] = set()
        HERMES_HOOKS_DIR.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self._load_hooks()

    @classmethod
    def get_instance(cls) -> "HookRegistry":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def _init_db(self) -> None:
        """Initialize SQLite persistence layer."""
        conn = sqlite3.connect(str(HERMES_HOOKS_DB), check_same_thread=False)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS hooks (
                hook_id TEXT PRIMARY KEY,
                event TEXT NOT NULL,
                script_path TEXT NOT NULL,
                script_hash TEXT,
                is_builtin INTEGER DEFAULT 0,
                is_blocking INTEGER DEFAULT 0,
                enabled INTEGER DEFAULT 1,
                created_at REAL,
                last_fired_at REAL,
                fire_count INTEGER DEFAULT 0,
                last_exit_code INTEGER,
                last_error TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_event ON hooks(event)")
        conn.commit()
        conn.close()

    def _load_hooks(self) -> None:
        """Load hooks from SQLite into memory."""
        conn = sqlite3.connect(str(HERMES_HOOKS_DB), check_same_thread=False)
        rows = conn.execute(
            "SELECT hook_id, event, script_path, is_builtin, is_blocking, enabled FROM hooks"
        ).fetchall()
        conn.close()

        self._hooks.clear()
        for row in rows:
            hook_id, event, script_path, is_builtin, is_blocking, enabled = row
            entry = {
                "hook_id": hook_id,
                "event": event,
                "script_path": script_path,
                "is_builtin": bool(is_builtin),
                "is_blocking": bool(is_blocking),
                "enabled": bool(enabled),
                "fire_count": 0,
                "last_fired_at": None,
                "last_exit_code": None,
                "last_error": None,
            }
            self._hooks.setdefault(event, []).append(entry)
            if bool(is_builtin):
                self._builtin_registered.add(hook_id)
            if not bool(enabled):
                self._disabled.add(hook_id)

    def _make_hook_id(self, event: str, script_path: str) -> str:
        """Generate deterministic hook ID from event + script path."""
        raw = f"{event}:{script_path}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def _compute_hash(self, script_path: str) -> str:
        """Compute SHA256 hash of script file for integrity checks."""
        try:
            with open(script_path, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception:
            return ""

    # ── Public API ──────────────────────────────────────────────────────────────

    def register(
        self,
        event: str,
        script_path: str,
        blocking: bool = False,
        overwrite: bool = True,
    ) -> dict:
        """
        Register a hook script for a lifecycle event.

        Args:
            event: One of the 26 hook event names
            script_path: Path to executable script, or "builtin:<name>" for built-ins
            blocking: If True, main flow waits for hook to complete
            overwrite: If True, replace existing hook for same event+path

        Returns:
            {"success": bool, "hook_id": str, "event": str}
        """
        if event not in HOOK_EVENTS:
            return {"success": False, "error": f"Unknown event: {event}", "valid_events": HOOK_EVENTS}

        # Handle built-in hooks
        is_builtin = False
        actual_path = script_path
        hook_body = ""  # silence undefined warning
        if script_path.startswith("builtin:"):
            builtin_name = script_path[8:]  # strip "builtin:" prefix → e.g. "prettier-fix"
            full_key = f"builtin:{builtin_name}"
            if full_key not in BUILTIN_HOOKS:
                return {"success": False, "error": f"Unknown builtin: {builtin_name}", "known": list(k[8:] for k in BUILTIN_HOOKS)}
            # Install built-in to a real path
            HERMES_HOOKS_DIR.mkdir(parents=True, exist_ok=True)
            actual_path = str(HERMES_HOOKS_DIR / f"builtin_{builtin_name}.sh")
            hook_body = BUILTIN_HOOKS[full_key]
            if not Path(actual_path).exists():
                Path(actual_path).write_text(hook_body)
                os.chmod(actual_path, 0o755)
            is_builtin = True

        hook_id = self._make_hook_id(event, actual_path)

        with self._lock:
            conn = sqlite3.connect(str(HERMES_HOOKS_DB), check_same_thread=False)

            # Check existing
            existing = conn.execute(
                "SELECT hook_id FROM hooks WHERE hook_id = ?", (hook_id,)
            ).fetchone()

            script_hash = self._compute_hash(actual_path)
            created_at = time.time()

            if existing:
                if not overwrite:
                    conn.close()
                    return {"success": False, "error": "Hook already registered", "hook_id": hook_id}
                conn.execute("""
                    UPDATE hooks SET script_path=?, script_hash=?, is_builtin=?,
                    is_blocking=?, enabled=1 WHERE hook_id=? AND event=? AND script_path=?
                """, (actual_path, script_hash, is_builtin, blocking, hook_id, event, actual_path))
            else:
                conn.execute("""
                    INSERT INTO hooks (hook_id, event, script_path, script_hash, is_builtin,
                    is_blocking, enabled, created_at, fire_count)
                    VALUES (?, ?, ?, ?, ?, ?, 1, ?, 0)
                """, (hook_id, event, actual_path, script_hash, is_builtin, blocking, created_at))

            conn.commit()
            conn.close()

            # Update in-memory
            entry = {
                "hook_id": hook_id,
                "event": event,
                "script_path": actual_path,
                "is_builtin": is_builtin,
                "is_blocking": blocking,
                "enabled": True,
                "fire_count": 0,
                "last_fired_at": None,
                "last_exit_code": None,
                "last_error": None,
            }

            self._hooks.setdefault(event, [])
            # Replace or append
            replaced = False
            for i, h in enumerate(self._hooks[event]):
                if h["hook_id"] == hook_id:
                    self._hooks[event][i] = entry
                    replaced = True
                    break
            if not replaced:
                self._hooks[event].append(entry)

            if is_builtin:
                self._builtin_registered.add(hook_id)
            self._disabled.discard(hook_id)

        return {"success": True, "hook_id": hook_id, "event": event, "script_path": actual_path}

    def unregister(self, hook_id: str) -> dict:
        """Remove a hook by ID."""
        with self._lock:
            conn = sqlite3.connect(str(HERMES_HOOKS_DB), check_same_thread=False)
            conn.execute("DELETE FROM hooks WHERE hook_id = ?", (hook_id,))
            conn.commit()
            conn.close()

            for event_hooks in self._hooks.values():
                event_hooks[:] = [h for h in event_hooks if h["hook_id"] != hook_id]

            self._builtin_registered.discard(hook_id)

        return {"success": True, "hook_id": hook_id}

    def enable(self, hook_id: str) -> dict:
        """Enable a disabled hook."""
        with self._lock:
            conn = sqlite3.connect(str(HERMES_HOOKS_DB), check_same_thread=False)
            conn.execute("UPDATE hooks SET enabled=1 WHERE hook_id=?", (hook_id,))
            conn.commit()
            conn.close()

            for event_hooks in self._hooks.values():
                for h in event_hooks:
                    if h["hook_id"] == hook_id:
                        h["enabled"] = True

        self._disabled.discard(hook_id)
        return {"success": True, "hook_id": hook_id, "enabled": True}

    def disable(self, hook_id: str) -> dict:
        """Disable a hook without removing it."""
        with self._lock:
            conn = sqlite3.connect(str(HERMES_HOOKS_DB), check_same_thread=False)
            conn.execute("UPDATE hooks SET enabled=0 WHERE hook_id=?", (hook_id,))
            conn.commit()
            conn.close()

            for event_hooks in self._hooks.values():
                for h in event_hooks:
                    if h["hook_id"] == hook_id:
                        h["enabled"] = False

        self._disabled.add(hook_id)
        return {"success": True, "hook_id": hook_id, "enabled": False}

    def fire(
        self,
        event: str,
        context: dict | None = None,
        blocking: bool = False,
        timeout: int = HOOK_TIMEOUT,
    ) -> dict:
        """
        Fire all enabled hooks for an event.

        Args:
            event: Hook event name
            context: Data passed as JSON on stdin to each hook script
            blocking: If True, wait for all hooks to complete (default: fire-and-forget)
            timeout: Per-hook timeout in seconds

        Returns:
            {"success": bool, "event": str, "hooked": [hook_ids], "results": [...]}
        """
        if event not in HOOK_EVENTS:
            return {"success": False, "error": f"Unknown event: {event}"}

        context = context or {}

        with self._lock:
            hooks = [h for h in self._hooks.get(event, []) if h.get("enabled", True)]

        if not hooks:
            return {"success": True, "event": event, "hooked": [], "results": []}

        results = []
        hooked_ids = [h["hook_id"] for h in hooks]

        if blocking:
            # Execute sequentially, return aggregated results
            for h in hooks:
                r = self._run_hook(h, context, timeout)
                results.append(r)
                # Update stats in DB
                self._update_hook_stats(h["hook_id"], r)
            return {"success": True, "event": event, "hooked": hooked_ids, "results": results}
        else:
            # Fire in background thread pool
            thread = threading.Thread(
                target=self._fire_async,
                args=(event, context, timeout),
                daemon=True,
            )
            thread.start()
            return {"success": True, "event": event, "hooked": hooked_ids, "results": [], "note": "async"}

    def _fire_async(self, event: str, context: dict, timeout: int) -> None:
        """Background async fire without aggregating results."""
        with self._lock:
            hooks = [h.copy() for h in self._hooks.get(event, []) if h.get("enabled", True)]

        for h in hooks:
            try:
                r = self._run_hook(h, context, timeout)
                self._update_hook_stats(h["hook_id"], r)
            except Exception:
                pass  # Swallow async errors silently

    def _run_hook(self, hook: dict, context: dict, timeout: int) -> dict:
        """Execute a single hook script, return result dict."""
        script_path = hook["script_path"]

        try:
            # Prepare context as JSON
            ctx_json = json.dumps(context, ensure_ascii=False, default=str)
            ctx_bytes = ctx_json.encode("utf-8")

            result = subprocess.run(
                [script_path],
                input=ctx_bytes,
                capture_output=True,
                timeout=timeout,
                env={**os.environ, "NO_COLOR": "1", "CLICOLOR": "0"},
            )

            return {
                "hook_id": hook["hook_id"],
                "event": hook["event"],
                "script_path": script_path,
                "exit_code": result.returncode,
                "stdout": result.stdout.decode(errors="replace").strip(),
                "stderr": result.stderr.decode(errors="replace").strip(),
                "runtime_ms": None,  # Could add timing
                "error": None,
            }

        except subprocess.TimeoutExpired:
            return {
                "hook_id": hook["hook_id"],
                "event": hook["event"],
                "script_path": script_path,
                "exit_code": -1,
                "stdout": "",
                "stderr": f"timeout after {timeout}s",
                "error": "timeout",
            }
        except Exception as e:
            return {
                "hook_id": hook["hook_id"],
                "event": hook["event"],
                "script_path": script_path,
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e),
                "error": str(e),
            }

    def _update_hook_stats(self, hook_id: str, result: dict) -> None:
        """Update fire count and last-fired timestamp after hook execution."""
        try:
            conn = sqlite3.connect(str(HERMES_HOOKS_DB), check_same_thread=False)
            conn.execute("""
                UPDATE hooks SET
                    last_fired_at = ?,
                    fire_count = fire_count + 1,
                    last_exit_code = ?,
                    last_error = ?
                WHERE hook_id = ?
            """, (time.time(), result.get("exit_code"), result.get("stderr", ""), hook_id))
            conn.commit()
            conn.close()

            with self._lock:
                for event_hooks in self._hooks.values():
                    for h in event_hooks:
                        if h["hook_id"] == hook_id:
                            h["fire_count"] = h.get("fire_count", 0) + 1
                            h["last_fired_at"] = time.time()
                            h["last_exit_code"] = result.get("exit_code")
                            h["last_error"] = result.get("stderr", "")
                            break
        except Exception:
            pass  # Non-critical

    def list_hooks(self, event: str | None = None) -> dict:
        """
        List all registered hooks, optionally filtered by event.

        Returns:
            {"hooks": [list of hook entries], "total": int, "by_event": {...}}
        """
        with self._lock:
            if event:
                hooks = [h.copy() for h in self._hooks.get(event, [])]
            else:
                hooks = []
                for ev, ev_hooks in self._hooks.items():
                    for h in ev_hooks:
                        hooks.append({**h, "event": ev})

        by_event: dict[str, int] = {}
        for h in hooks:
            by_event[h["event"]] = by_event.get(h["event"], 0) + 1

        # Remove sensitive fields from output
        for h in hooks:
            h.pop("script_hash", None)

        return {
            "hooks": sorted(hooks, key=lambda x: (x["event"], x["hook_id"])),
            "total": len(hooks),
            "by_event": by_event,
            "available_events": HOOK_EVENTS,
        }

    def get_hook_stats(self) -> dict:
        """Get hook usage statistics."""
        with self._lock:
            conn = sqlite3.connect(str(HERMES_HOOKS_DB), check_same_thread=False)
            rows = conn.execute("""
                SELECT event, COUNT(*) as count, SUM(fire_count) as total_fires,
                       SUM(CASE WHEN last_fired_at IS NOT NULL THEN 1 ELSE 0 END) as active
                FROM hooks GROUP BY event
            """).fetchall()
            conn.close()

            stats = {}
            for event, count, total_fires, active in rows:
                stats[event] = {"registered": count, "total_fires": total_fires or 0, "active": active or 0}

            return stats


# ── Module-level convenience functions ────────────────────────────────────────

def get_registry() -> HookRegistry:
    return HookRegistry.get_instance()


def hook_register(
    event: str,
    script_path: str,
    blocking: bool = False,
) -> dict:
    """Register a hook script for a lifecycle event."""
    return get_registry().register(event, script_path, blocking=blocking)


def hook_unregister(hook_id: str) -> dict:
    """Remove a hook by ID."""
    return get_registry().unregister(hook_id)


def hook_fire(
    event: str,
    context: dict | None = None,
    blocking: bool = True,
    timeout: int = HOOK_TIMEOUT,
) -> dict:
    """
    Fire all enabled hooks for an event.
    By default blocking=True so callers can wait for hook completion.
    """
    return get_registry().fire(event, context or {}, blocking=blocking, timeout=timeout)


def hook_list(event: str | None = None) -> dict:
    """List all registered hooks, optionally filtered by event."""
    return get_registry().list_hooks(event)


def hook_enable(hook_id: str) -> dict:
    """Enable a disabled hook."""
    return get_registry().enable(hook_id)


def hook_disable(hook_id: str) -> dict:
    """Disable a hook without removing it."""
    return get_registry().disable(hook_id)


def hook_stats() -> dict:
    """Get hook usage statistics."""
    return get_registry().get_hook_stats()


def hook_builtin_register(builtin_name: str, event: str, blocking: bool = False) -> dict:
    """Register a built-in hook by name."""
    return get_registry().register(event, f"builtin:{builtin_name}", blocking=blocking)


# ── Auto-fire Integration Points ──────────────────────────────────────────────
# These functions are called by other Hermes modules to fire appropriate hooks.

def fire_pre_tool_call(tool_name: str, args: dict, **kwargs) -> dict:
    """Fire pre-tool-call hook. Call before tool execution."""
    return hook_fire("pre-tool-call", {
        "tool_name": tool_name,
        "args": args,
        "timestamp": time.time(),
        **kwargs,
    }, blocking=False)


def fire_post_tool_call(tool_name: str, args: dict, result: Any = None, **kwargs) -> dict:
    """Fire post-tool-call hook. Call after tool execution."""
    return hook_fire("post-tool-call", {
        "tool_name": tool_name,
        "args": args,
        "result": str(result)[:500] if result else None,
        "timestamp": time.time(),
        **kwargs,
    }, blocking=False)


def fire_pre_file_write(path: str, content: str, **kwargs) -> dict:
    """Fire pre-file-write hook. Call before writing a file."""
    return hook_fire("pre-file-write", {
        "path": path,
        "content_preview": content[:200],
        "content_size": len(content),
        "timestamp": time.time(),
        **kwargs,
    }, blocking=False)


def fire_post_file_write(path: str, content: str, success: bool = True, **kwargs) -> dict:
    """Fire post-file-write hook. Call after writing a file."""
    return hook_fire("post-file-write", {
        "path": path,
        "content_preview": content[:200],
        "content_size": len(content),
        "success": success,
        "timestamp": time.time(),
        **kwargs,
    }, blocking=False)


def fire_pre_commit(files: list[str], message: str = "", **kwargs) -> dict:
    """Fire pre-commit hook. Call before git commit."""
    return hook_fire("pre-commit", {
        "files": files,
        "message": message,
        "file_count": len(files),
        "timestamp": time.time(),
        **kwargs,
    }, blocking=True, timeout=60)


def fire_post_commit(commit_hash: str, files: list[str], success: bool = True, **kwargs) -> dict:
    """Fire post-commit hook. Call after git commit."""
    return hook_fire("post-commit", {
        "commit_hash": commit_hash,
        "files": files,
        "success": success,
        "timestamp": time.time(),
        **kwargs,
    }, blocking=False)


def fire_pre_bash(command: str, **kwargs) -> dict:
    """Fire pre-bash hook. Call before executing bash command."""
    return hook_fire("pre-bash", {
        "command": command,
        "command_preview": command[:200],
        "timestamp": time.time(),
        **kwargs,
    }, blocking=True, timeout=15)


def fire_post_bash(command: str, exit_code: int = 0, output: str = "", **kwargs) -> dict:
    """Fire post-bash hook. Call after bash command completes."""
    return hook_fire("post-bash", {
        "command": command,
        "exit_code": exit_code,
        "output_preview": output[:500],
        "timestamp": time.time(),
        **kwargs,
    }, blocking=False)


def fire_pre_session_start(session_id: str, **kwargs) -> dict:
    """Fire pre-session-start hook. Call when session starts."""
    return hook_fire("pre-session-start", {
        "session_id": session_id,
        "timestamp": time.time(),
        **kwargs,
    }, blocking=True, timeout=30)


def fire_post_session_end(session_id: str, turn_count: int = 0, **kwargs) -> dict:
    """Fire post-session-end hook. Call when session ends."""
    return hook_fire("post-session-end", {
        "session_id": session_id,
        "turn_count": turn_count,
        "timestamp": time.time(),
        **kwargs,
    }, blocking=True, timeout=30)


def fire_pre_task_start(task: str, task_id: str = "", **kwargs) -> dict:
    """Fire pre-task-start hook."""
    return hook_fire("pre-task-start", {
        "task": task,
        "task_id": task_id,
        "timestamp": time.time(),
        **kwargs,
    }, blocking=True, timeout=20)


def fire_post_task_complete(task: str, task_id: str = "", success: bool = True, **kwargs) -> dict:
    """Fire post-task-complete hook."""
    return hook_fire("post-task-complete", {
        "task": task,
        "task_id": task_id,
        "success": success,
        "timestamp": time.time(),
        **kwargs,
    }, blocking=False)


def fire_pre_spawn_agent(agent_name: str, goal: str, **kwargs) -> dict:
    """Fire pre-spawn-agent hook."""
    return hook_fire("pre-spawn-agent", {
        "agent_name": agent_name,
        "goal": goal,
        "goal_preview": goal[:200],
        "timestamp": time.time(),
        **kwargs,
    }, blocking=True, timeout=20)


def fire_post_spawn_agent(agent_name: str, goal: str, task_id: str = "", **kwargs) -> dict:
    """Fire post-spawn-agent hook."""
    return hook_fire("post-spawn-agent", {
        "agent_name": agent_name,
        "goal": goal,
        "task_id": task_id,
        "timestamp": time.time(),
        **kwargs,
    }, blocking=False)


def fire_pre_error(error: str, context: dict, **kwargs) -> dict:
    """Fire pre-error hook."""
    return hook_fire("pre-error", {
        "error": error,
        "error_preview": error[:200],
        "context_keys": list(context.keys()) if context else [],
        "timestamp": time.time(),
        **kwargs,
    }, blocking=True, timeout=15)


def fire_post_error(error: str, context: dict, handled: bool = False, **kwargs) -> dict:
    """Fire post-error hook."""
    return hook_fire("post-error", {
        "error": error,
        "handled": handled,
        "timestamp": time.time(),
        **kwargs,
    }, blocking=False)


def fire_pre_context_restore(session_id: str, **kwargs) -> dict:
    """Fire pre-context-restore hook."""
    return hook_fire("pre-context-restore", {
        "session_id": session_id,
        "timestamp": time.time(),
        **kwargs,
    }, blocking=True)


def fire_post_context_restore(session_id: str, entries_restored: int = 0, **kwargs) -> dict:
    """Fire post-context-restore hook."""
    return hook_fire("post-context-restore", {
        "session_id": session_id,
        "entries_restored": entries_restored,
        "timestamp": time.time(),
        **kwargs,
    }, blocking=False)


def fire_pre_memory_flush(layer: str = "", **kwargs) -> dict:
    """Fire pre-memory-flush hook."""
    return hook_fire("pre-memory-flush", {
        "layer": layer,
        "timestamp": time.time(),
        **kwargs,
    }, blocking=True)


def fire_post_memory_flush(layer: str = "", entries_flushed: int = 0, **kwargs) -> dict:
    """Fire post-memory-flush hook."""
    return hook_fire("post-memory-flush", {
        "layer": layer,
        "entries_flushed": entries_flushed,
        "timestamp": time.time(),
        **kwargs,
    }, blocking=False)


def fire_pre_snapshot(**kwargs) -> dict:
    """Fire pre-snapshot hook."""
    return hook_fire("pre-snapshot", {"timestamp": time.time(), **kwargs}, blocking=True)


def fire_post_snapshot(snapshot_size_kb: float = 0.0, **kwargs) -> dict:
    """Fire post-snapshot hook."""
    return hook_fire("post-snapshot", {
        "snapshot_size_kb": snapshot_size_kb,
        "timestamp": time.time(),
        **kwargs,
    }, blocking=False)


def fire_pre_message_send(to_agent: str, message: str, **kwargs) -> dict:
    """Fire pre-message-send hook."""
    return hook_fire("pre-message-send", {
        "to_agent": to_agent,
        "message_preview": message[:200],
        "timestamp": time.time(),
        **kwargs,
    }, blocking=False)


def fire_post_message_received(from_agent: str, message: str, **kwargs) -> dict:
    """Fire post-message-received hook."""
    return hook_fire("post-message-received", {
        "from_agent": from_agent,
        "message_preview": message[:200],
        "timestamp": time.time(),
        **kwargs,
    }, blocking=False)


# ── MCP Handler ────────────────────────────────────────────────────────────────

def handle_hermes_hooks(args: dict) -> str:
    """
    MCP tool handler for hermes_hooks.
    Schema: action=register|unregister|fire|list|enable|disable|builtin
    """
    action = args.get("action", "list")
    event = args.get("event", "")
    script_path = args.get("script_path", "")
    hook_id = args.get("hook_id", "")
    context = args.get("context", {})
    blocking = args.get("blocking", False)
    builtin_name = args.get("builtin_name", "")
    timeout = args.get("timeout", HOOK_TIMEOUT)

    registry = get_registry()

    if action == "register":
        if not event:
            return json.dumps({"success": False, "error": "event required for register"})
        return json.dumps(registry.register(event, script_path, blocking=blocking))

    elif action == "unregister":
        if not hook_id:
            return json.dumps({"success": False, "error": "hook_id required for unregister"})
        return json.dumps(registry.unregister(hook_id))

    elif action == "fire":
        if not event:
            return json.dumps({"success": False, "error": "event required for fire"})
        return json.dumps(registry.fire(event, context or {}, blocking=blocking, timeout=timeout))

    elif action == "list":
        return json.dumps(registry.list_hooks(event or None))

    elif action == "enable":
        if not hook_id:
            return json.dumps({"success": False, "error": "hook_id required for enable"})
        return json.dumps(registry.enable(hook_id))

    elif action == "disable":
        if not hook_id:
            return json.dumps({"success": False, "error": "hook_id required for disable"})
        return json.dumps(registry.disable(hook_id))

    elif action == "builtin":
        # Register one of the built-in hooks
        if not event or not builtin_name:
            return json.dumps({"success": False, "error": "event and builtin_name required"})
        return json.dumps(registry.register(event, f"builtin:{builtin_name}", blocking=blocking))

    else:
        return json.dumps({"success": False, "error": f"Unknown action: {action}"})


# ── Init: Register Built-in Hooks on first import ─────────────────────────────

def _init_builtins() -> None:
    """Auto-register common built-in hooks if not already registered."""
    registry = get_instance()

    # Auto-register tool logger for all tool-call events
    # This runs silently; user can unregister if not wanted
    tool_logger = HERMES_HOOKS_DIR / "builtin_tool-logger.sh"
    if not tool_logger.exists():
        HERMES_HOOKS_DIR.mkdir(parents=True, exist_ok=True)
        tool_logger.write_text(BUILTIN_HOOKS["builtin:tool-logger"])
        os.chmod(str(tool_logger), 0o755)


# ── Self-test ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"[Hermes Hooks] Registry at {HERMES_HOOKS_DIR}")
    print(f"[Hermes Hooks] DB at {HERMES_HOOKS_DB}")
    print(f"[Hermes Hooks] {len(HOOK_EVENTS)} events defined")
    print(f"[Hermes Hooks] {len(BUILTIN_HOOKS)} built-in hooks available")

    # Test registration
    r = HookRegistry.get_instance()
    print(f"[Hermes Hooks] Loaded {sum(len(v) for v in r._hooks.values())} hooks from DB")

    # List all events
    print("\nAvailable hook events:")
    for i, ev in enumerate(HOOK_EVENTS, 1):
        print(f"  {i:2d}. {ev}")

    # List built-in hooks
    print("\nBuilt-in hooks:")
    for name in BUILTIN_HOOKS:
        print(f"  - {name}")

    print("\n[Hermes Hooks] Self-test complete.")
