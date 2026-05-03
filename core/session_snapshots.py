'''core/session_snapshots.py — GAP-17: Session diff/branching via wiki snapshots.

Implements session snapshotting: before risky operations or major changes,
save the conversation state to wiki as a named snapshot. Can restore later.

Usage:
    snapshot_id = await create_snapshot(user_id, "before refactoring")
    await restore_snapshot(snapshot_id, user_id)
    list_snapshots()  # returns all snapshots for user
'''
import uuid
from datetime import datetime
from typing import Any

SNAPSHOT_PREFIX = "session-snapshots"


async def create_snapshot(
    user_id: str,
    label: str = "",
    metadata: dict[str, Any] | None = None,
) -> str:
    """Save current conversation as a named wiki snapshot. Returns snapshot ID."""
    from core.conversation_interface import get_conversation_history

    snapshot_id = f"snap-{uuid.uuid4().hex[:8]}"
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    history = get_conversation_history(user_id, last_n=500)

    lines = [
        f"# Session Snapshot: {label or 'unnamed'}",
        f"**Snapshot ID**: {snapshot_id}",
        f"**Created**: {timestamp}",
        f"**User**: {user_id}",
        f"**Messages**: {len(history)}",
        "",
        "## Conversation",
        "",
    ]

    for m in history:
        role = m.get("role", "?")
        content = m.get("content", "")
        if role in ("user", "assistant", "system"):
            lines.append(f"**{role}**: {content[:500]}")
        elif role == "tool":
            lines.append(f"**[tool]**: {content[:200]}")

    if metadata:
        lines.append("")
        lines.append("## Metadata")
        for k, v in metadata.items():
            lines.append(f"- {k}: {v}")

    wiki_content = "\n".join(lines)

    try:
        from core.wiki_bridge import write_note

        filename = f"{SNAPSHOT_PREFIX}/{snapshot_id}.md"
        write_note(filename, wiki_content, folder="session-snapshots")
        return snapshot_id
    except Exception:
        pass

    return snapshot_id


async def restore_snapshot(snapshot_id: str, user_id: str) -> bool:
    """Restore a conversation from a wiki snapshot. Returns True if successful."""
    from core.conversation_interface import add_to_conversation, clear_conversation

    try:
        from core.wiki_bridge import read_note

        filename = f"{SNAPSHOT_PREFIX}/{snapshot_id}.md"
        content = read_note(filename)
        if not content:
            return False

        clear_conversation(user_id)

        in_conv = False
        for line in content.split("\n"):
            if line.startswith("## Conversation"):
                in_conv = True
                continue
            if line.startswith("## "):
                in_conv = False
                continue
            if in_conv and line.startswith("**"):
                parts = line[2:].split("**: ", 1)
                if len(parts) == 2:
                    role, text = parts
                    if role in ("user", "assistant", "system"):
                        add_to_conversation(user_id, role, text)
        return True
    except Exception:
        return False


def list_snapshots(user_id: str | None = None) -> list[dict[str, Any]]:
    """List all available session snapshots."""
    try:
        from core.wiki_bridge import list_notes

        notes = list_notes(folder=SNAPSHOT_PREFIX)
        result = []
        for note in notes:
            if note.get("filename", "").endswith(".md"):
                result.append({
                    "snapshot_id": note["filename"].replace(f"{SNAPSHOT_PREFIX}/", "").replace(".md", ""),
                    "filename": note["filename"],
                    "modified": note.get("modified", ""),
                })
        return result
    except Exception:
        return []


async def opencode_export_session(session_id: str, output_path: str) -> bool:
    """GAP-18: Wire opencode export CLI to export session data to a file."""
    import asyncio
    import os

    opencode_path = os.getenv("OPENCODE_PATH", "/home/newadmin/.opencode/bin/opencode")
    if not os.path.exists(opencode_path):
        return False

    try:
        proc = await asyncio.create_subprocess_exec(
            opencode_path, "export",
            "--session", session_id,
            "--output", output_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await asyncio.wait_for(proc.communicate(), timeout=30)
        return proc.returncode == 0
    except Exception:
        return False


# ── GAP-19: Turn-level revert ─────────────────────────────────────────────────────


async def revert_to_turn(user_id: str, turn_index: int) -> bool:
    """GAP-19: Revert conversation to a specific turn index.

    Creates a snapshot of current state before reverting.
    Returns True if successful.
    """
    from core.conversation_interface import get_conversation_history

    history = get_conversation_history(user_id, last_n=500)
    if turn_index >= len(history):
        return False

    # Snapshot before revert
    await create_snapshot(user_id, f"pre-revert-to-turn-{turn_index}", {
        "action": "revert",
        "original_turn_count": len(history),
        "revert_to": turn_index,
    })

    # Keep only turns up to turn_index
    from core.conversation_interface import add_to_conversation, clear_conversation

    clear_conversation(user_id)
    for m in history[:turn_index]:
        role = m.get("role", "user")
        content = m.get("content", "")
        if role in ("user", "assistant", "system"):
            add_to_conversation(user_id, role, content)
    return True


# ── GAP-15: Event-store-lite ──────────────────────────────────────────────────────


_COMPACTION_LOG: list[dict[str, Any]] = []


def append_compaction_event(
    event_type: str,
    session_id: str,
    details: dict[str, Any],
) -> None:
    """GAP-15: Append-only log of compaction events for session replay.

    Stores in memory. Wired to pre_compact and post_compact hooks.
    """
    _COMPACTION_LOG.append({
        "event_type": event_type,
        "session_id": session_id,
        "timestamp": datetime.utcnow().isoformat(),
        "details": details,
    })
    # Keep last 1000 events
    if len(_COMPACTION_LOG) > 1000:
        _COMPACTION_LOG[:] = _COMPACTION_LOG[-1000:]


def get_compaction_log(session_id: str | None = None) -> list[dict[str, Any]]:
    """Return compaction log entries, optionally filtered by session_id."""
    if session_id is None:
        return list(_COMPACTION_LOG)
    return [e for e in _COMPACTION_LOG if e.get("session_id") == session_id]


# ── GAP-13: Cross-session compaction cache via wiki ───────────────────────────────


def get_compaction_cache(file_path: str) -> str | None:
    """GAP-13: Get cached file context from previous sessions via wiki."""
    try:
        cache_key = file_path.replace("/", "-").replace(".", "_")
        from core.wiki_bridge import read_note
        return read_note(cache_key, folder="compaction-cache") or None
    except Exception:
        return None


def set_compaction_cache(file_path: str, context: str) -> bool:
    """GAP-13: Cache file context after compaction for cross-session reuse."""
    try:
        cache_key = file_path.replace("/", "-").replace(".", "_")
        from core.wiki_bridge import write_note
        return write_note(cache_key, context, folder="compaction-cache")
    except Exception:
        return False
