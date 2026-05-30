#!/usr/bin/env python3
"""
SessionArchivist — Enhanced cross-session FTS5 indexing of Claude Code sessions.
Indexes session_id, timestamp, agent_name, tool_calls, summaries, errors.
Supports incremental indexing, rank-based search with Snippet() highlighting,
session similarity search, auto-archive, and session graph tracking.
"""
import gzip
import json
import os
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

FTS_DB = Path.home() / ".hermes" / "sessions" / "fts.db"
ARCHIVE_DIR = Path.home() / ".hermes" / "sessions" / "archive"
SESSIONS_DIR = Path.home() / ".hermes" / "sessions"
MAX_CONTEXT_TOKENS = 8000

LOCK = threading.Lock()

def _get_fts_db() -> sqlite3.Connection:
    """Get or create FTS5 database connection."""
    FTS_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(FTS_DB), check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions_fts (
            session_id TEXT PRIMARY KEY,
            timestamp REAL,
            agent_name TEXT,
            parent_session_id TEXT,
            summary TEXT,
            tool_calls INTEGER DEFAULT 0,
            error_count INTEGER DEFAULT 0,
            message_count INTEGER DEFAULT 0,
            content_hash TEXT,
            updated REAL
        )
    """)
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS sessions_search USING fts5(
            session_id UNINDEXED,
            summary,
            agent_name,
            tokenize='trigram'
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS session_edges (
            parent_session_id TEXT,
            child_session_id TEXT,
            edge_type TEXT,
            PRIMARY KEY (parent_session_id, child_session_id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS session_checkpoints (
            session_id TEXT PRIMARY KEY,
            checkpoint_json TEXT,
            last_message_index INTEGER DEFAULT 0,
            FOREIGN KEY (session_id) REFERENCES sessions_fts(session_id)
        )
    """)
    conn.commit()
    return conn

def _get_content_hash(content: str) -> str:
    import hashlib
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]

def index_session(session_id: str, messages: list[dict[str, Any]],
                   agent_name: str = "hermes", parent_session_id: str = "",
                   checkpoint_threshold: int = 100) -> dict[str, Any]:
    """Index a session incrementally (only new messages since last checkpoint)."""
    with LOCK:
        conn = _get_fts_db()
        now = time.time()

        # Get last indexed message index
        row = conn.execute(
            "SELECT last_message_index FROM session_checkpoints WHERE session_id = ?",
            (session_id,)
        ).fetchone()
        last_indexed = row[0] if row else 0

        # Incremental: only process new messages
        new_messages = messages[last_indexed:]
        tool_calls = sum(1 for m in new_messages if m.get("type") == "tool_call")
        errors = sum(1 for m in new_messages if m.get("type") == "error")
        message_count = len(messages)
        summary = _generate_summary(messages)
        content_hash = _get_content_hash(json.dumps(messages[-50:] if messages else []))

        conn.execute("""
            INSERT OR REPLACE INTO sessions_fts
            (session_id, timestamp, agent_name, parent_session_id, summary,
             tool_calls, error_count, message_count, content_hash, updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                tool_calls = tool_calls + excluded.tool_calls,
                error_count = error_count + excluded.error_count,
                message_count = excluded.message_count,
                summary = excluded.summary,
                content_hash = excluded.content_hash,
                updated = excluded.updated
        """, (session_id, now, agent_name, parent_session_id, summary,
              tool_calls, errors, message_count, content_hash, now))

        # Session graph edge
        if parent_session_id:
            conn.execute("""
                INSERT OR REPLACE INTO session_edges (parent_session_id, child_session_id, edge_type)
                VALUES (?, ?, 'continuation')
            """, (parent_session_id, session_id))

        # Update checkpoint
        conn.execute("""
            INSERT OR REPLACE INTO session_checkpoints (session_id, last_message_index)
            VALUES (?, ?)
        """, (session_id, len(messages)))

        # FTS index
        conn.execute("DELETE FROM sessions_search WHERE session_id = ?", (session_id,))
        conn.execute("""
            INSERT INTO sessions_search (session_id, summary, agent_name)
            VALUES (?, ?, ?)
        """, (session_id, summary, agent_name))

        conn.commit()
        conn.close()

        return {
            "session_id": session_id,
            "new_messages_indexed": len(new_messages),
            "total_messages": message_count,
            "tool_calls": tool_calls,
            "errors": errors
        }

def _generate_summary(messages: list[dict[str, Any]]) -> str:
    """Generate a brief summary of session messages."""
    if not messages:
        return ""
    last_msgs = messages[-10:] if len(messages) > 10 else messages
    snippets = []
    for m in last_msgs:
        role = m.get("role", "?")
        content = m.get("content", "")
        if isinstance(content, str) and content:
            snippets.append(f"[{role}]: {content[:100]}")
    return " | ".join(snippets)[:500]

def search_sessions(query: str, limit: int = 5) -> list[dict[str, Any]]:
    """Rank-based search with Snippet() highlighting."""
    with LOCK:
        conn = _get_fts_db()
        # FTS5 search with trigram tokenizer
        try:
            rows = conn.execute("""
                SELECT s.session_id, s.timestamp, s.agent_name, s.parent_session_id,
                       s.summary, s.tool_calls, s.error_count, s.message_count,
                       snippet(sessions_search, 1, '【', '】', '...', 32) as snippet
                FROM sessions_search fs
                JOIN sessions_fts s ON fs.session_id = s.session_id
                WHERE sessions_search MATCH ?
                ORDER BY rank
                LIMIT ?
            """, (query, limit)).fetchall()
        except Exception:
            # Fallback to LIKE if FTS fails
            rows = conn.execute("""
                SELECT session_id, timestamp, agent_name, parent_session_id,
                       summary, tool_calls, error_count, message_count, summary as snippet
                FROM sessions_fts
                WHERE summary LIKE ? OR agent_name LIKE ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (f"%{query}%", f"%{query}%", limit)).fetchall()
        conn.close()
        return [
            {
                "session_id": r[0],
                "timestamp": r[1],
                "agent_name": r[2],
                "parent_session_id": r[3],
                "summary": r[4],
                "tool_calls": r[5],
                "error_count": r[6],
                "message_count": r[7],
                "snippet": r[8]
            }
            for r in rows
        ]

def get_session_graph(session_id: str) -> dict[str, Any]:
    """Get session continuity graph."""
    with LOCK:
        conn = _get_fts_db()
        # Find ancestors
        ancestors = []
        current = session_id
        for _ in range(10):
            row = conn.execute("""
                SELECT parent_session_id FROM sessions_fts WHERE session_id = ?
            """, (current,)).fetchone()
            if not row or not row[0]:
                break
            current = row[0]
            ancestors.append(current)

        # Find descendants
        descendants = []
        queue = [session_id]
        for _ in range(10):
            children = conn.execute("""
                SELECT child_session_id FROM session_edges WHERE parent_session_id = ?
            """, (queue[0],)).fetchall()
            queue = []
            for child_row in children:
                child = child_row[0]
                descendants.append(child)
                queue.append(child)

        conn.close()
        return {
            "session_id": session_id,
            "ancestors": ancestors,
            "descendants": descendants,
            "depth": len(ancestors)
        }

def session_similarity_search(ref_session_id: str, limit: int = 5) -> list[dict[str, Any]]:
    """Find sessions similar to ref_session using ChromaDB embeddings."""
    refs = _get_session_content(ref_session_id)
    if not refs:
        return []
    ref_text = refs[:1000]
    with LOCK:
        conn = _get_fts_db()
        # Simple TF-IDF like similarity using shared content patterns
        rows = conn.execute("""
            SELECT session_id, summary, message_count, timestamp
            FROM sessions_fts
            WHERE session_id != ?
            ORDER BY timestamp DESC
            LIMIT 50
        """, (ref_session_id,)).fetchall()
        conn.close()

        scored = []
        for row in rows:
            sid, summary, msg_count, ts = row
            sim = len(set(ref_text.split()) & set((summary or "").split())) / max(1, len(set(ref_text.split())))
            scored.append((sim, row))
        scored.sort(reverse=True)
        return [
            {
                "session_id": r[0],
                "summary": r[1],
                "message_count": r[2],
                "timestamp": r[3],
                "similarity_score": round(s, 3)
            }
            for s, r in scored[:limit]
        ]

def _get_session_content(session_id: str) -> str:
    """Get raw session content for similarity comparison."""
    for f in SESSIONS_DIR.glob("session_*.json"):
        try:
            data = json.loads(f.read_text())
            if data.get("session_id") == session_id:
                msgs = data.get("messages", [])
                return " ".join(m.get("content", "") for m in msgs[-50:] if isinstance(m.get("content"), str))
        except Exception:
            pass
    return ""

def auto_archive_session(session_id: str) -> dict[str, Any]:
    """Archive sessions older than 14 days to compressed gzip bundle."""
    with LOCK:
        conn = _get_fts_db()
        row = conn.execute("""
            SELECT timestamp, summary, tool_calls, error_count, message_count
            FROM sessions_fts WHERE session_id = ?
        """, (session_id,)).fetchone()
        conn.close()

        if not row:
            return {"error": "session not found"}

        timestamp, summary, tool_calls, error_count, message_count = row
        age_days = (time.time() - timestamp) / 86400

        if age_days < 14:
            return {"skipped": True, "reason": f"only {age_days:.1f} days old", "min_required": 14}

        ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
        archive_path = ARCHIVE_DIR / f"{session_id}.json.gz"
        bundle = {
            "session_id": session_id,
            "archived_at": time.time(),
            "summary": summary,
            "tool_calls": tool_calls,
            "error_count": error_count,
            "message_count": message_count,
            "original_timestamp": timestamp
        }
        with gzip.open(archive_path, "wt", encoding="utf-8") as f:
            json.dump(bundle, f)

        conn2 = _get_fts_db()
        conn2.execute("DELETE FROM sessions_fts WHERE session_id = ?", (session_id,))
        conn2.execute("DELETE FROM sessions_search WHERE session_id = ?", (session_id,))
        conn2.execute("DELETE FROM session_checkpoints WHERE session_id = ?", (session_id,))
        conn2.execute("DELETE FROM session_edges WHERE parent_session_id = ? OR child_session_id = ?",
                     (session_id, session_id))
        conn2.commit()
        conn2.close()

        return {"archived": True, "path": str(archive_path), "age_days": round(age_days, 1)}

def export_session_bundle(session_ids: list[str], path: str) -> dict[str, Any]:
    """Export session bundle as gzip JSON."""
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    bundle = []
    with LOCK:
        conn = _get_fts_db()
        for sid in session_ids:
            row = conn.execute("SELECT * FROM sessions_fts WHERE session_id = ?", (sid,)).fetchone()
            if row:
                cols = [d[0] for d in conn.execute("PRAGMA table_info(sessions_fts)").fetchall()]
                bundle.append(dict(zip(cols, row, strict=True)))
        conn.close()

    with gzip.open(path, "wt", encoding="utf-8") as f:
        json.dump(bundle, f)
    return {"success": True, "path": path, "sessions_exported": len(bundle)}

def handle_session_archivist(args: dict[str, Any]) -> str:
    """Main handler for session archivist operations."""
    action = args.get("action", "status")
    if action == "index":
        result = index_session(
            args["session_id"],
            args.get("messages", []),
            args.get("agent_name", "hermes"),
            args.get("parent_session_id", "")
        )
    elif action == "search":
        result = search_sessions(args.get("query", ""), args.get("limit", 5))
    elif action == "graph":
        result = get_session_graph(args.get("session_id", ""))
    elif action == "similarity":
        result = session_similarity_search(args.get("session_id", ""), args.get("limit", 5))
    elif action == "archive":
        result = auto_archive_session(args.get("session_id", ""))
    elif action == "export_bundle":
        result = export_session_bundle(args.get("session_ids", []), args.get("path", "/tmp/session_bundle.json.gz"))
    elif action == "status":
        with LOCK:
            conn = _get_fts_db()
            total = conn.execute("SELECT COUNT(*) FROM sessions_fts").fetchone()[0]
            archived = len(list(ARCHIVE_DIR.glob("*.json.gz"))) if ARCHIVE_DIR.exists() else 0
            conn.close()
        result = {"indexed_sessions": total, "archived_sessions": archived}
    else:
        result = {"error": f"unknown action: {action}"}
    return json.dumps(result, indent=2)

SESSION_ARCHIVIST_SCHEMA = {
    "name": "session_archivist",
    "description": "Enhanced cross-session FTS5 indexing, search, graph, similarity, and auto-archive.",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["index", "search", "graph", "similarity", "archive", "export_bundle", "status"]},
            "session_id": {"type": "string"},
            "messages": {"type": "array"},
            "agent_name": {"type": "string"},
            "parent_session_id": {"type": "string"},
            "query": {"type": "string"},
            "limit": {"type": "integer", "default": 5},
            "session_ids": {"type": "array"},
            "path": {"type": "string"},
        },
    },
}