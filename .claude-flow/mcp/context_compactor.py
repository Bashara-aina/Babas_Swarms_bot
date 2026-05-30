#!/usr/bin/env python3
"""
ContextCompactor — Intelligent context utilization monitoring and compaction.
Monitors context length vs max (128k tokens), triggers compaction at thresholds,
and manages checkpoint restoration.
"""
import json
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

PROJECT_ROOT = Path("/home/newadmin/swarm-bot")
DATA_DIR = PROJECT_ROOT / ".claude-flow" / "data"
CHECKPOINT_PATH = DATA_DIR / "compact_checkpoint.md"
HISTORY_PATH = DATA_DIR / "compact_history.json"
SESSION_STATE_PATH = DATA_DIR / "session_state.json"

# Configurable memory limits - can be overridden via environment variables or config file
_MAX_TOKENS_ENV = os.environ.get("HERMES_MAX_CONTEXT_TOKENS")
_MAX_TOKENS_CONFIG = None  # Loaded from config file if available

def _get_max_tokens() -> int:
    """Get configured max tokens with priority: env > config > default."""
    if _MAX_TOKENS_ENV:
        return int(_MAX_TOKENS_ENV)
    if _MAX_TOKENS_CONFIG is not None:
        return _MAX_TOKENS_CONFIG
    return 128000

def _load_config_limits() -> None:
    """Load memory limits from config file if available."""
    global _MAX_TOKENS_CONFIG
    config_path = PROJECT_ROOT / ".claude-flow" / "config.yaml"
    if config_path.exists():
        try:
            import yaml
            with open(config_path) as f:
                cfg = yaml.safe_load(f)
            memory_cfg = cfg.get("memory", {})
            if "maxTokens" in memory_cfg:
                _MAX_TOKENS_CONFIG = int(memory_cfg["maxTokens"])
            elif "contextLimit" in memory_cfg:
                _MAX_TOKENS_CONFIG = int(memory_cfg["contextLimit"])
        except Exception:
            pass  # Use defaults

# Try to load config at module init
_load_config_limits()

MAX_TOKENS = _get_max_tokens()
TRIGGERS = {"light": 0.70, "medium": 0.85, "aggressive": 0.95}
LOCK = threading.Lock()

def _load_history() -> list[dict[str, Any]]:
    """Load compaction history."""
    if not HISTORY_PATH.exists():
        return []
    try:
        return json.loads(HISTORY_PATH.read_text())
    except Exception:
        return []

def _save_history(history: list[dict[str, Any]]) -> None:
    """Save compaction history."""
    HISTORY_PATH.write_text(json.dumps(history[-50:], indent=2))

def _load_session_state() -> dict[str, Any]:
    """Load current session state (context utilization tracking)."""
    if not SESSION_STATE_PATH.exists():
        return _default_state()
    try:
        return json.loads(SESSION_STATE_PATH.read_text())
    except Exception:
        return _default_state()

def _default_state() -> dict[str, Any]:
    """Default session state."""
    return {
        "context_length": 0,
        "max_tokens": MAX_TOKENS,
        "utilization_pct": 0.0,
        "last_compaction": None,
        "compaction_count": 0,
        "last_checkpoint_path": None,
    }

def _save_session_state(state: dict[str, Any]) -> None:
    """Save session state."""
    SESSION_STATE_PATH.write_text(json.dumps(state, indent=2))

def _estimate_tokens(text: str) -> int:
    """Estimate token count using simple heuristic (~4 chars per token)."""
    return len(text) // 4

def _determine_level(utilization: float) -> str:
    """Determine compaction level based on utilization."""
    if utilization >= TRIGGERS["aggressive"]:
        return "aggressive"
    elif utilization >= TRIGGERS["medium"]:
        return "medium"
    elif utilization >= TRIGGERS["light"]:
        return "light"
    return "none"

def _load_session_messages() -> list[dict[str, Any]]:
    """Load current session messages from session state."""
    msgs_path = DATA_DIR / "session_messages.json"
    if not msgs_path.exists():
        return []
    try:
        return json.loads(msgs_path.read_text())
    except Exception:
        return []

def _preserve_current_file(msgs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Preserve: current file being edited, recent tool results, active task."""
    preserved = []
    for m in msgs[-20:]:
        content = m.get("content", "")
        if isinstance(content, str):
            if any(kw in content.lower() for kw in ["current file", "editing", "active task"]):
                preserved.append(m)
        if len(preserved) >= 10:
            break
    return preserved[-5:] if preserved else msgs[-3:]

def _condense_messages(msgs: list[dict[str, Any]], level: str) -> list[dict[str, Any]]:
    """Condense: older messages, repeated patterns, verbose tool outputs."""
    if level == "none":
        return msgs
    keep_ratio = {"light": 0.6, "medium": 0.4, "aggressive": 0.2}.get(level, 0.5)
    if not msgs:
        return []
    keep_count = max(3, int(len(msgs) * keep_ratio))
    condensed = []
    for i, m in enumerate(msgs):
        role = m.get("role", "")
        content = m.get("content", "")
        if isinstance(content, str):
            if role == "tool" and len(content) > 2000:
                content = content[:1500] + f"\n...[truncated {len(content)-1500} chars]"
        condensed.append({"role": role, "content": content})
    return condensed[-keep_count:] if len(condensed) > keep_count else condensed

def _summarize_discussion(msgs: list[dict[str, Any]]) -> str:
    """Summarize long discussions into key points."""
    if len(msgs) <= 5:
        return ""
    summaries = []
    for m in msgs[:-5]:
        role = m.get("role", "?")
        content = m.get("content", "")
        if isinstance(content, str) and content:
            summaries.append(f"[{role}]: {content[:150]}...")
    return "\n".join(summaries[-10:])

def _build_checkpoint(msgs: list[dict[str, Any]], level: str, reason: str) -> str:
    """Build checkpoint markdown compatible with CLAUDE.md reload."""
    sections = []
    sections.append("# Context Compaction Checkpoint\n")
    sections.append(f"_Compacted at: {datetime.now().isoformat()}_\n")
    sections.append(f"_Level: {level} | Reason: {reason}_\n\n")

    # Active tasks
    active = [m for m in msgs[-10:] if m.get("role") == "user"]
    if active:
        sections.append("## Active Tasks\n")
        for a in active[-3:]:
            c = a.get("content", "")
            if isinstance(c, str):
                sections.append(f"- {c[:200]}\n")
        sections.append("\n")

    # Recent decisions (from assistant responses)
    decisions = [m for m in msgs[-20:] if m.get("role") == "assistant" and len(m.get("content", "")) > 300]
    if decisions:
        sections.append("## Recent Decisions\n")
        for d in decisions[-3:]:
            c = d.get("content", "")[:300]
            sections.append(f"- {c}...\n")
        sections.append("\n")

    # Summary of earlier context
    summary = _summarize_discussion(msgs)
    if summary:
        sections.append("## Earlier Context Summary\n")
        sections.append(summary + "\n\n")

    # Condensed messages
    condensed = _condense_messages(msgs, level)
    sections.append("## Condensed Messages\n")
    for m in condensed:
        role = m.get("role", "?")
        content = m.get("content", "")
        if isinstance(content, str):
            sections.append(f"**[{role}]**: {content[:400]}\n\n")

    return "".join(sections)

def _write_checkpoint(content: str, level: str) -> str:
    """Write checkpoint to disk, return path."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = DATA_DIR / f"compact_checkpoint_{ts}.md"
    path.write_text(content)
    CHECKPOINT_PATH.write_text(content)
    return str(path)

def update_context_length(text_length: int) -> dict[str, Any]:
    """Update current context length and return utilization state."""
    with LOCK:
        state = _load_session_state()
        state["context_length"] = text_length
        state["utilization_pct"] = min(100.0, (text_length / MAX_TOKENS) * 100)
        _save_session_state(state)
        return {
            "context_length": text_length,
            "max_tokens": MAX_TOKENS,
            "utilization_pct": round(state["utilization_pct"], 1),
            "level": _determine_level(state["utilization_pct"] / 100),
            "last_compaction": state.get("last_compaction"),
        }

def compactor_status() -> dict[str, Any]:
    """Get current utilization and last compaction info."""
    with LOCK:
        state = _load_session_state()
        history = _load_history()
        last = history[-1] if history else None
        return {
            "context_length": state["context_length"],
            "max_tokens": MAX_TOKENS,
            "utilization_pct": round(state["utilization_pct"], 1),
            "trigger_levels": TRIGGERS,
            "current_level": _determine_level(state["utilization_pct"] / 100),
            "last_compaction": state.get("last_compaction"),
            "compaction_count": state.get("compaction_count", 0),
            "last_checkpoint": state.get("last_checkpoint_path"),
            "checkpoint_exists": CHECKPOINT_PATH.exists(),
            "history_entries": len(history),
            "last_compaction_info": last,
        }

def compactor_compact(level: str = "auto", reason: str = "") -> dict[str, Any]:
    """Trigger compaction at specified or auto-determined level."""
    with LOCK:
        state = _load_session_state()
        if level == "auto":
            level = _determine_level(state["utilization_pct"] / 100)
        if level == "none":
            return {"skipped": True, "reason": "below threshold", "utilization": round(state["utilization_pct"], 1)}

        msgs = _load_session_messages()
        if not msgs:
            return {"skipped": True, "reason": "no messages to compact"}

        reason = reason or f"auto:{level} trigger at {round(state['utilization_pct'], 1)}%"
        checkpoint_content = _build_checkpoint(msgs, level, reason)
        checkpoint_path = _write_checkpoint(checkpoint_content, level)

        # Update state
        state["last_compaction"] = datetime.now().isoformat()
        state["compaction_count"] = state.get("compaction_count", 0) + 1
        state["last_checkpoint_path"] = checkpoint_path
        _save_session_state(state)

        # Save to history
        history = _load_history()
        history.append({
            "timestamp": state["last_compaction"],
            "level": level,
            "reason": reason,
            "message_count": len(msgs),
            "checkpoint_path": checkpoint_path,
            "utilization_before": round(state["utilization_pct"], 1),
        })
        _save_history(history)

        return {
            "success": True,
            "level": level,
            "reason": reason,
            "message_count": len(msgs),
            "checkpoint_path": checkpoint_path,
            "checkpoint_exists": CHECKPOINT_PATH.exists(),
            "compaction_count": state["compaction_count"],
        }

def compactor_restore() -> dict[str, Any]:
    """Restore context from last checkpoint."""
    if not CHECKPOINT_PATH.exists():
        return {"error": "no checkpoint found"}
    try:
        content = CHECKPOINT_PATH.read_text()
        history = _load_history()
        last = history[-1] if history else None
        return {
            "success": True,
            "checkpoint_content": content,
            "checkpoint_time": last.get("timestamp") if last else None,
            "restored_from": str(CHECKPOINT_PATH),
        }
    except Exception as e:
        return {"error": str(e)}

def compactor_history() -> dict[str, Any]:
    """Get list of past compactions."""
    history = _load_history()
    return {
        "compaction_count": len(history),
        "compact_history": history,
        "checkpoint_dir": str(DATA_DIR),
    }

def compactor_register_message(role: str, content: str) -> None:
    """Register a message from the session to track context."""
    with LOCK:
        state = _load_session_state()
        msgs_path = DATA_DIR / "session_messages.json"
        msgs = []
        if msgs_path.exists():
            try:
                msgs = json.loads(msgs_path.read_text())
            except Exception:
                msgs = []
        msgs.append({"role": role, "content": content, "timestamp": time.time()})
        # Keep last 200 messages
        msgs = msgs[-200:] if len(msgs) > 200 else msgs
        msgs_path.write_text(json.dumps(msgs))
        # Update utilization
        total_len = sum(len(m.get("content", "")) for m in msgs)
        state["context_length"] = total_len
        state["utilization_pct"] = min(100.0, (total_len / MAX_TOKENS) * 100)
        _save_session_state(state)

def handle_context_compactor(args: dict[str, Any]) -> str:
    """Handler for context compactor operations."""
    action = args.get("action", "status")
    if action == "status":
        result = compactor_status()
    elif action == "compact":
        result = compactor_compact(
            level=args.get("level", "auto"),
            reason=args.get("reason", "")
        )
    elif action == "restore":
        result = compactor_restore()
    elif action == "history":
        result = compactor_history()
    elif action == "update_length":
        result = update_context_length(args.get("text_length", 0))
    elif action == "register_message":
        result = {"registered": True}
        compactor_register_message(args.get("role", "user"), args.get("content", ""))
    elif action == "set_limits":
        # Update memory limits at runtime
        global MAX_TOKENS, _MAX_TOKENS_CONFIG
        new_max = args.get("max_tokens")
        if new_max is not None:
            MAX_TOKENS = int(new_max)
            _MAX_TOKENS_CONFIG = MAX_TOKENS
        new_triggers = args.get("triggers")
        if new_triggers:
            TRIGGERS.update(new_triggers)
        result = {
            "max_tokens": MAX_TOKENS,
            "triggers": TRIGGERS,
            "source": "config" if _MAX_TOKENS_CONFIG else "env",
        }
    else:
        result = {"error": f"unknown action: {action}"}
    return json.dumps(result, indent=2)

CONTEXT_COMPACTOR_SCHEMA = {
    "name": "context_compactor",
    "description": "Intelligent context utilization monitoring and compaction system.",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["status", "compact", "restore", "history", "update_length", "register_message", "set_limits"]},
            "level": {"type": "string", "enum": ["auto", "light", "medium", "aggressive"]},
            "reason": {"type": "string"},
            "text_length": {"type": "integer"},
            "role": {"type": "string"},
            "content": {"type": "string"},
            "max_tokens": {"type": "integer", "description": "New max token limit"},
            "triggers": {"type": "object", "description": "New trigger thresholds"},
        },
    },
}

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        action = sys.argv[1]
        args = {"action": action}
        if len(sys.argv) > 2:
            args["level"] = sys.argv[2]
        print(handle_context_compactor(args))
    else:
        print("ContextCompactor CLI")
        print("Actions: status | compact | restore | history")
        print(handle_context_compactor({"action": "status"}))