#!/usr/bin/env python3
"""
Cross-Session Memory — Persistent memory with provenance, forgetting curves, and versioning.

Features:
  - Provenance tracking: file path, commit, PR ID, timestamp, source agent/session, version
  - Ebbinghaus-style forgetting: usage frequency, last access, decay priority
  - Versioned entries: history, rollback, conflict detection
  - Write triggers: PR creation, test failure/success, approval, periodic checkpoint (every 50 turns)
  - MCP tools: memory_save, memory_recall, memory_forget, memory_sync_from_session

Storage: SQLite with transactions. JSON fields for metadata. Max 500 lines.
"""

import hashlib
import json
import logging
import os
import sqlite3
import threading
import time
from datetime import UTC, datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ============================================================================
# Paths
# ============================================================================

PROJECT_ROOT = Path("/home/newadmin/swarm-bot")
HERMES_HOME = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))
MEMORY_DB = HERMES_HOME / "memories" / "cross_session_memory.db"
ARCHIVE_DB = HERMES_HOME / "memories" / "cross_session_memory_archive.db"

LOCK = threading.Lock()

# Ebbinghaus forgetting curve constants
DECAY_BASE = 0.5
DECAY_RATE = 0.1  # per day since last access
MIN_PRIORITY_THRESHOLD = 0.1  # auto-archive below this
USAGE_BOOST = 0.05  # per access within decay window

# Checkpoint trigger
TURNS_PER_CHECKPOINT = 50


# ============================================================================
# Database Schema
# ============================================================================

def _get_db() -> sqlite3.Connection:
    """Get or create cross-session memory database."""
    MEMORY_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(MEMORY_DB), check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    # Main memory entries table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS memory_entries (
            entry_key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            version INTEGER DEFAULT 1,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL,
            last_accessed_at REAL NOT NULL,
            access_count INTEGER DEFAULT 0,
            priority REAL DEFAULT 0.5,
            is_archived INTEGER DEFAULT 0,
            metadata_json TEXT DEFAULT '{}',
            provenance_json TEXT DEFAULT '{}'
        )
    """)

    # Version history for rollback
    conn.execute("""
        CREATE TABLE IF NOT EXISTS entry_history (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_key TEXT NOT NULL,
            version INTEGER NOT NULL,
            value TEXT NOT NULL,
            changed_at REAL NOT NULL,
            changed_by TEXT DEFAULT 'unknown',
            change_reason TEXT DEFAULT '',
            metadata_json TEXT DEFAULT '{}',
            FOREIGN KEY (entry_key) REFERENCES memory_entries(entry_key)
        )
    """)

    # Sync state for multi-session coordination
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sync_state (
            session_id TEXT PRIMARY KEY,
            last_sync_at REAL NOT NULL,
            turn_count INTEGER DEFAULT 0,
            last_commit_sha TEXT DEFAULT '',
            pending_entries TEXT DEFAULT '[]'
        )
    """)

    # Trigger log for write triggers
    conn.execute("""
        CREATE TABLE IF NOT EXISTS trigger_log (
            trigger_id INTEGER PRIMARY KEY AUTOINCREMENT,
            trigger_type TEXT NOT NULL,
            trigger_payload TEXT DEFAULT '{}',
            fired_at REAL NOT NULL,
            entries_created INTEGER DEFAULT 0
        )
    """)

    # Indexes
    conn.execute("CREATE INDEX IF NOT EXISTS idx_priority ON memory_entries(priority)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_last_access ON memory_entries(last_accessed_at)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_history_key ON entry_history(entry_key, version)")

    conn.commit()
    return conn


# ============================================================================
# Provenance Tracking
# ============================================================================

def _make_provenance(
    file_path: str = "",
    commit_sha: str = "",
    pr_id: str = "",
    agent_name: str = "",
    session_id: str = ""
) -> dict[str, Any]:
    """Build a provenance record."""
    return {
        "file_path": file_path,
        "commit_sha": commit_sha,
        "pr_id": pr_id,
        "agent_name": agent_name,
        "session_id": session_id,
        "timestamp": datetime.now(UTC).isoformat(),
    }


def _compute_priority(
    last_accessed_at: float,
    access_count: int,
    decay_rate: float = DECAY_RATE
) -> float:
    """
    Compute Ebbinghaus-inspired priority.
    Priority = recency_component + usage_component
    recency_component = DECAY_BASE ** (days_since_access * decay_rate)
    usage_component = min(access_count * USAGE_BOOST, 0.4)
    """
    days_since = (time.time() - last_accessed_at) / 86400
    recency = DECAY_BASE ** (days_since * decay_rate)
    usage = min(access_count * USAGE_BOOST, 0.4)
    return max(0.0, min(1.0, recency + usage))


# ============================================================================
# Core Memory Operations
# ============================================================================

def memory_save(
    key: str,
    value: str,
    provenance: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
    session_id: str = ""
) -> dict[str, Any]:
    """
    Save a memory entry with provenance. Creates version history entry.
    Returns dict with success status and version number.
    """
    with LOCK:
        conn = _get_db()
        now = time.time()
        provenance = provenance or {}
        metadata = metadata or {}

        # Get existing entry for versioning
        existing = conn.execute(
            "SELECT version, value FROM memory_entries WHERE entry_key = ? AND is_archived = 0",
            (key,)
        ).fetchone()

        if existing:
            old_version, old_value = existing
            new_version = old_version + 1

            # Save history before updating
            conn.execute("""
                INSERT INTO entry_history (entry_key, version, value, changed_at, changed_by, change_reason, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                key, old_version, old_value, now,
                provenance.get("agent_name", "unknown"),
                provenance.get("change_reason", "update"),
                json.dumps(metadata)
            ))
        else:
            new_version = 1

        priority = 0.5  # Initial priority for new entries

        conn.execute("""
            INSERT OR REPLACE INTO memory_entries
            (entry_key, value, version, created_at, updated_at, last_accessed_at,
             access_count, priority, is_archived, metadata_json, provenance_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
            ON CONFLICT(entry_key) DO UPDATE SET
                value = excluded.value,
                version = excluded.version,
                updated_at = excluded.updated_at,
                last_accessed_at = excluded.last_accessed_at,
                priority = excluded.priority,
                metadata_json = excluded.metadata_json,
                provenance_json = excluded.provenance_json
        """, (
            key, value, new_version, now, now, now,
            0, priority,
            json.dumps(metadata),
            json.dumps(provenance)
        ))

        conn.commit()
        conn.close()

        return {"success": True, "key": key, "version": new_version}


def memory_recall(
    key: str,
    min_priority: float = 0.5,
    session_id: str = ""
) -> dict[str, Any] | None:
    """
    Recall a memory entry, updating access stats and priority.
    Returns None if not found or below min_priority threshold.
    """
    with LOCK:
        conn = _get_db()
        now = time.time()

        row = conn.execute("""
            SELECT value, version, created_at, updated_at, access_count, priority,
                   metadata_json, provenance_json
            FROM memory_entries
            WHERE entry_key = ? AND is_archived = 0
        """, (key,)).fetchone()

        if not row:
            conn.close()
            return None

        value, version, created_at, updated_at, access_count, priority, metadata_json, provenance_json = row

        # Update access stats
        new_access_count = access_count + 1
        new_priority = _compute_priority(updated_at, new_access_count)

        conn.execute("""
            UPDATE memory_entries
            SET last_accessed_at = ?, access_count = ?, priority = ?
            WHERE entry_key = ?
        """, (now, new_access_count, new_priority, key))

        conn.commit()
        conn.close()

        # Filter by priority threshold
        if new_priority < min_priority:
            return None

        return {
            "key": key,
            "value": value,
            "version": version,
            "priority": round(new_priority, 4),
            "access_count": new_access_count,
            "created_at": created_at,
            "updated_at": updated_at,
            "metadata": json.loads(metadata_json or "{}"),
            "provenance": json.loads(provenance_json or "{}"),
        }


def memory_forget(key: str, cascade: bool = True) -> dict[str, Any]:
    """
    Mark a memory entry for decay/archival.
    If cascade=True, also archive all version history.
    """
    with LOCK:
        conn = _get_db()
        now = time.time()

        result = conn.execute("""
            UPDATE memory_entries
            SET is_archived = 1, updated_at = ?, priority = 0
            WHERE entry_key = ? AND is_archived = 0
        """, (now, key)).rowcount

        if cascade:
            conn.execute("DELETE FROM entry_history WHERE entry_key = ?", (key,))

        conn.commit()
        conn.close()

        return {"success": result > 0, "key": key, "archived": result > 0}


def memory_get_history(key: str) -> list[dict[str, Any]]:
    """Get version history for rollback support."""
    with LOCK:
        conn = _get_db()
        rows = conn.execute("""
            SELECT version, value, changed_at, changed_by, change_reason, metadata_json
            FROM entry_history
            WHERE entry_key = ?
            ORDER BY version DESC
        """, (key,)).fetchall()
        conn.close()

        return [
            {
                "version": r[0],
                "value": r[1],
                "changed_at": r[2],
                "changed_by": r[3],
                "change_reason": r[4],
                "metadata": json.loads(r[5] or "{}"),
            }
            for r in rows
        ]


def memory_rollback(key: str, target_version: int) -> dict[str, Any]:
    """Rollback to a specific version."""
    with LOCK:
        conn = _get_db()
        now = time.time()

        # Get target version
        hist_row = conn.execute("""
            SELECT value, metadata_json FROM entry_history
            WHERE entry_key = ? AND version = ?
        """, (key, target_version)).fetchone()

        if not hist_row:
            conn.close()
            return {"success": False, "error": f"version {target_version} not found"}

        old_value, old_metadata = hist_row
        current = conn.execute("""
            SELECT version, value FROM memory_entries WHERE entry_key = ?
        """, (key,)).fetchone()

        if not current:
            conn.close()
            return {"success": False, "error": "current entry not found"}

        current_version, current_value = current
        new_version = current_version + 1

        # Save current as history before rollback
        conn.execute("""
            INSERT INTO entry_history (entry_key, version, value, changed_at, changed_by, change_reason, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            key, current_version, current_value, now,
            "memory_system", f"rollback to v{target_version}",
            old_metadata
        ))

        # Apply rollback
        conn.execute("""
            UPDATE memory_entries
            SET value = ?, version = ?, updated_at = ?, priority = 0.5
            WHERE entry_key = ?
        """, (old_value, new_version, now, key))

        conn.commit()
        conn.close()

        return {"success": True, "key": key, "rolled_back_to": target_version, "new_version": new_version}


# ============================================================================
# Decay and Auto-Archive
# ============================================================================

def run_decay_cycle() -> dict[str, Any]:
    """
    Run Ebbinghaus decay cycle.
    Recalculates priority for all entries and archives below threshold.
    Returns count of archived entries.
    """
    with LOCK:
        conn = _get_db()
        now = time.time()

        rows = conn.execute("""
            SELECT entry_key, last_accessed_at, access_count
            FROM memory_entries WHERE is_archived = 0
        """).fetchall()

        archived = 0
        for key, last_access, count in rows:
            new_priority = _compute_priority(last_access, count)
            conn.execute("""
                UPDATE memory_entries SET priority = ? WHERE entry_key = ?
            """, (new_priority, key))

            if new_priority < MIN_PRIORITY_THRESHOLD:
                conn.execute("""
                    UPDATE memory_entries SET is_archived = 1, updated_at = ?
                    WHERE entry_key = ?
                """, (now, key))
                archived += 1

        conn.commit()
        conn.close()

        return {"success": True, "archived_count": archived, "total_checked": len(rows)}


def get_all_entries(min_priority: float = 0.0, include_archived: bool = False) -> list[dict[str, Any]]:
    """Get all memory entries with optional filtering."""
    with LOCK:
        conn = _get_db()

        query = """
            SELECT entry_key, value, version, created_at, updated_at,
                   last_accessed_at, access_count, priority, is_archived,
                   metadata_json, provenance_json
            FROM memory_entries
        """
        if not include_archived:
            query += " WHERE is_archived = 0"
        query += " ORDER BY priority DESC"

        rows = conn.execute(query).fetchall()
        conn.close()

        results = []
        for r in rows:
            priority = r[7]
            if priority >= min_priority:
                results.append({
                    "key": r[0],
                    "value": r[1],
                    "version": r[2],
                    "created_at": r[3],
                    "updated_at": r[4],
                    "last_accessed_at": r[5],
                    "access_count": r[6],
                    "priority": round(priority, 4),
                    "is_archived": bool(r[8]),
                    "metadata": json.loads(r[9] or "{}"),
                    "provenance": json.loads(r[10] or "{}"),
                })

        return results


# ============================================================================
# Write Triggers
# ============================================================================

def fire_trigger(
    trigger_type: str,
    payload: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Fire a write trigger. Supported types:
      - pr_created: On PR creation
      - test_failure: On test failure
      - test_success: On test success
      - developer_approval: On developer approval
      - checkpoint: On periodic checkpoint
    """
    trigger_type = trigger_type.lower()
    valid_triggers = {"pr_created", "test_failure", "test_success", "developer_approval", "checkpoint"}
    if trigger_type not in valid_triggers:
        return {"success": False, "error": f"unknown trigger: {trigger_type}"}

    payload = payload or {}
    now = time.time()

    with LOCK:
        conn = _get_db()

        # Log the trigger
        conn.execute("""
            INSERT INTO trigger_log (trigger_type, trigger_payload, fired_at)
            VALUES (?, ?, ?)
        """, (trigger_type, json.dumps(payload), now))

        # Create appropriate memory entry based on trigger
        entry_key = f"trigger:{trigger_type}:{int(now)}"
        entry_value = json.dumps({
            "trigger_type": trigger_type,
            "payload": payload,
            "fired_at": now,
        })
        provenance = _make_provenance(
            file_path=payload.get("file_path", ""),
            commit_sha=payload.get("commit_sha", ""),
            pr_id=payload.get("pr_id", ""),
            agent_name=payload.get("agent_name", "trigger_system"),
            session_id=payload.get("session_id", "")
        )

        conn.execute("""
            INSERT OR REPLACE INTO memory_entries
            (entry_key, value, version, created_at, updated_at, last_accessed_at,
             access_count, priority, is_archived, metadata_json, provenance_json)
            VALUES (?, ?, 1, ?, ?, ?, 0, 0.5, 0, '{}', ?)
        """, (
            entry_key, entry_value, now, now, now,
            json.dumps(provenance)
        ))

        conn.commit()
        conn.close()

        return {
            "success": True,
            "trigger_type": trigger_type,
            "entry_key": entry_key,
            "fired_at": now
        }


def get_trigger_history(limit: int = 20) -> list[dict[str, Any]]:
    """Get recent trigger history."""
    with LOCK:
        conn = _get_db()
        rows = conn.execute("""
            SELECT trigger_type, trigger_payload, fired_at, entries_created
            FROM trigger_log
            ORDER BY fired_at DESC
            LIMIT ?
        """, (limit,)).fetchall()
        conn.close()

        return [
            {
                "trigger_type": r[0],
                "payload": json.loads(r[1] or "{}"),
                "fired_at": r[2],
                "entries_created": r[3],
            }
            for r in rows
        ]


# ============================================================================
# Session Sync
# ============================================================================

def memory_sync_from_session(
    session_id: str,
    turn_count: int,
    entries: list[dict[str, Any]] | None = None,
    commit_sha: str = ""
) -> dict[str, Any]:
    """
    Sync entries from current session.
    Updates sync state and applies turn-count checkpoint trigger.
    """
    with LOCK:
        conn = _get_db()
        now = time.time()

        # Update sync state
        existing = conn.execute("""
            SELECT turn_count FROM sync_state WHERE session_id = ?
        """, (session_id,)).fetchone()

        if existing:
            old_turn_count = existing[0]
            conn.execute("""
                UPDATE sync_state
                SET last_sync_at = ?, turn_count = ?, last_commit_sha = ?
                WHERE session_id = ?
            """, (now, turn_count, commit_sha, session_id))
        else:
            old_turn_count = 0
            conn.execute("""
                INSERT INTO sync_state (session_id, last_sync_at, turn_count, last_commit_sha)
                VALUES (?, ?, ?, ?)
            """, (session_id, now, turn_count, commit_sha))

        # Sync provided entries
        synced = 0
        if entries:
            for entry in entries:
                key = entry.get("key", "")
                value = entry.get("value", "")
                provenance = entry.get("provenance", {})
                provenance["session_id"] = session_id
                metadata = entry.get("metadata", {})

                if key and value:
                    memory_save(key, value, provenance, metadata, session_id)
                    synced += 1

        # Check for checkpoint trigger
        checkpoint_fired = False
        if turn_count > 0 and turn_count % TURNS_PER_CHECKPOINT == 0:
            fire_trigger("checkpoint", {
                "session_id": session_id,
                "turn_count": turn_count,
                "commit_sha": commit_sha,
            })
            checkpoint_fired = True

        conn.commit()
        conn.close()

        return {
            "success": True,
            "session_id": session_id,
            "synced_entries": synced,
            "turn_count": turn_count,
            "checkpoint_fired": checkpoint_fired,
            "delta_turns": turn_count - old_turn_count,
        }


def get_sync_state(session_id: str) -> dict[str, Any] | None:
    """Get sync state for a session."""
    with LOCK:
        conn = _get_db()
        row = conn.execute("""
            SELECT session_id, last_sync_at, turn_count, last_commit_sha, pending_entries
            FROM sync_state WHERE session_id = ?
        """, (session_id,)).fetchone()
        conn.close()

        if not row:
            return None

        return {
            "session_id": row[0],
            "last_sync_at": row[1],
            "turn_count": row[2],
            "last_commit_sha": row[3],
            "pending_entries": json.loads(row[4] or "[]"),
        }


# ============================================================================
# Conflict Detection
# ============================================================================

def detect_conflicts(
    key: str,
    expected_version: int,
    expected_value_hash: str
) -> dict[str, Any]:
    """
    Detect conflicts when merging from different sessions.
    Returns conflict info if local version differs from expected.
    """
    with LOCK:
        conn = _get_db()
        row = conn.execute("""
            SELECT version, value FROM memory_entries WHERE entry_key = ?
        """, (key,)).fetchone()
        conn.close()

        if not row:
            return {"has_conflict": False, "reason": "entry_not_found"}

        local_version, local_value = row
        local_hash = hashlib.sha256(local_value.encode()).hexdigest()[:16]

        if local_version != expected_version or local_hash != expected_value_hash:
            history = memory_get_history(key)
            return {
                "has_conflict": True,
                "key": key,
                "local_version": local_version,
                "expected_version": expected_version,
                "local_value": local_value[:200] if local_value else "",
                "history": history[:5],  # Last 5 versions
            }

        return {"has_conflict": False, "key": key}


# ============================================================================
# Status
# ============================================================================

def get_memory_status() -> dict[str, Any]:
    """Get overall memory system status."""
    with LOCK:
        conn = _get_db()

        total = conn.execute("SELECT COUNT(*) FROM memory_entries").fetchone()[0]
        active = conn.execute("SELECT COUNT(*) FROM memory_entries WHERE is_archived = 0").fetchone()[0]
        archived = conn.execute("SELECT COUNT(*) FROM memory_entries WHERE is_archived = 1").fetchone()[0]

        avg_priority = conn.execute("""
            SELECT AVG(priority) FROM memory_entries WHERE is_archived = 0
        """).fetchone()[0] or 0.0

        history_count = conn.execute("SELECT COUNT(*) FROM entry_history").fetchone()[0]
        trigger_count = conn.execute("SELECT COUNT(*) FROM trigger_log").fetchone()[0]
        sync_count = conn.execute("SELECT COUNT(*) FROM sync_state").fetchone()[0]

        conn.close()

        return {
            "total_entries": total,
            "active_entries": active,
            "archived_entries": archived,
            "avg_priority": round(avg_priority, 4),
            "history_entries": history_count,
            "trigger_events": trigger_count,
            "tracked_sessions": sync_count,
            "decay_threshold": MIN_PRIORITY_THRESHOLD,
            "turns_per_checkpoint": TURNS_PER_CHECKPOINT,
        }


# ============================================================================
# MCP Tool Handlers
# ============================================================================

def handle_cross_session_memory(args: dict[str, Any]) -> str:
    """Main handler for cross_session_memory MCP tool."""
    action = args.get("action", "status")

    if action == "save":
        result = memory_save(
            key=args["key"],
            value=args["value"],
            provenance=args.get("provenance"),
            metadata=args.get("metadata"),
            session_id=args.get("session_id", "")
        )

    elif action == "recall":
        entry = memory_recall(
            key=args["key"],
            min_priority=args.get("min_priority", 0.5),
            session_id=args.get("session_id", "")
        )
        result = {"found": entry is not None, "entry": entry}

    elif action == "forget":
        result = memory_forget(
            key=args["key"],
            cascade=args.get("cascade", True)
        )

    elif action == "history":
        result = {"key": args["key"], "history": memory_get_history(args["key"])}

    elif action == "rollback":
        result = memory_rollback(args["key"], args["version"])

    elif action == "decay":
        result = run_decay_cycle()

    elif action == "list":
        result = {
            "entries": get_all_entries(
                min_priority=args.get("min_priority", 0.0),
                include_archived=args.get("include_archived", False)
            )
        }

    elif action == "sync":
        result = memory_sync_from_session(
            session_id=args["session_id"],
            turn_count=args.get("turn_count", 0),
            entries=args.get("entries"),
            commit_sha=args.get("commit_sha", "")
        )

    elif action == "sync_state":
        state = get_sync_state(args.get("session_id", ""))
        result = {"found": state is not None, "state": state}

    elif action == "trigger":
        result = fire_trigger(
            trigger_type=args["trigger_type"],
            payload=args.get("payload")
        )

    elif action == "trigger_history":
        result = {"triggers": get_trigger_history(args.get("limit", 20))}

    elif action == "conflict":
        result = detect_conflicts(
            key=args["key"],
            expected_version=args.get("expected_version", 1),
            expected_value_hash=args.get("expected_value_hash", "")
        )

    elif action == "status":
        result = get_memory_status()

    else:
        result = {"error": f"unknown action: {action}"}

    return json.dumps(result, indent=2)


CROSS_SESSION_MEMORY_SCHEMA = {
    "name": "cross_session_memory",
    "description": (
        "Persistent cross-session memory with provenance, Ebbinghaus forgetting curves, "
        "and version control. Supports: save with provenance, recall with priority filtering, "
        "forget/decay, version history/rollback, write triggers (PR/test/checkpoint), "
        "session sync, and conflict detection."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "save", "recall", "forget", "history", "rollback",
                    "decay", "list", "sync", "sync_state",
                    "trigger", "trigger_history", "conflict", "status"
                ],
                "description": "The memory operation to perform."
            },
            "key": {"type": "string", "description": "Memory entry key."},
            "value": {"type": "string", "description": "Memory entry value (for save)."},
            "provenance": {
                "type": "object",
                "description": "Provenance info: file_path, commit_sha, pr_id, agent_name, session_id."
            },
            "metadata": {"type": "object", "description": "Additional metadata."},
            "session_id": {"type": "string", "description": "Session identifier."},
            "min_priority": {"type": "number", "description": "Minimum priority for recall (default 0.5)."},
            "cascade": {"type": "boolean", "description": "Also archive history on forget (default True)."},
            "version": {"type": "integer", "description": "Target version for rollback."},
            "include_archived": {"type": "boolean", "description": "Include archived entries in list."},
            "turn_count": {"type": "integer", "description": "Current turn count for checkpoint triggers."},
            "entries": {
                "type": "array",
                "description": "Entries to sync from session.",
                "items": {"type": "object"}
            },
            "commit_sha": {"type": "string", "description": "Current git commit SHA."},
            "trigger_type": {
                "type": "string",
                "enum": ["pr_created", "test_failure", "test_success", "developer_approval", "checkpoint"],
                "description": "Type of trigger to fire."
            },
            "payload": {"type": "object", "description": "Trigger payload data."},
            "expected_version": {"type": "integer", "description": "Expected version for conflict detection."},
            "expected_value_hash": {"type": "string", "description": "Expected value hash for conflict detection."},
            "limit": {"type": "integer", "description": "Limit for history/list results."},
        },
        "required": ["action"]
    },
}


# Alias for MCP handler
def cross_session_memory_tool(args: dict[str, Any]) -> str:
    return handle_cross_session_memory(args)
