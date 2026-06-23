#!/usr/bin/env python3
"""Index session JSON files into FTS DB for dreaming pattern detection.
Runs as a SessionEnd hook — fully automatic, no LLM cost."""

import json
import sqlite3
import re
import hashlib
import sys
from pathlib import Path

HERMES_HOME = Path.home() / ".hermes"
SESSIONS_DIR = HERMES_HOME / "sessions"
FTS_DB = HERMES_HOME / "sessions" / "fts.db"

# Also index claude-flow sessions (written by session.js)
CLAUDEFLOW_SESSIONS_DIR = Path.cwd() / ".claude-flow" / "data" / "sessions"

ERROR_PATTERNS = re.compile(
    r"(Error|Exception|Traceback|failed|FAILED|crashed|CRASHED|SyntaxError|"
    r"ImportError|TypeError|ValueError|NameError|AttributeError|RuntimeError|"
    r"KeyError|IndexError|ModuleNotFoundError|ConnectionError)", re.IGNORECASE
)


def _extract_summary(messages: list) -> str:
    """Extract a useful summary from the first meaningful user message."""
    for msg in messages:
        if msg.get("role") in ("user", "human") and msg.get("content"):
            text = msg["content"]
            if isinstance(text, list):
                text = " ".join(p.get("text", "") for p in text if isinstance(p, dict))
            if isinstance(text, str) and len(text.strip()) > 10:
                return text.strip().replace("\n", " ")[:500]
    return ""


def _count_errors(messages: list) -> int:
    """Count messages that contain error-like patterns."""
    count = 0
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, list):
            content = " ".join(p.get("text", "") for p in content if isinstance(p, dict))
        if isinstance(content, str) and ERROR_PATTERNS.search(content):
            count += 1
    return count


def _count_tool_calls(messages: list) -> int:
    """Count tool_use blocks in messages."""
    count = 0
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str):
            count += content.count('"tool_use"')
            count += content.count("tool_use_id")
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    count += 1
    return count


def _content_hash(messages: list) -> str:
    """Generate a content hash for dedup."""
    text = json.dumps([(m.get("role"), m.get("content")) for m in messages], sort_keys=True)
    return hashlib.md5(text.encode()).hexdigest()[:16]


def index_sessions() -> dict:
    """Index all session JSON files into the FTS DB."""
    if not SESSIONS_DIR.exists():
        return {"status": "no_sessions_dir", "indexed": 0, "total": 0}

    session_files = sorted(SESSIONS_DIR.glob("session_*.json"),
                           key=lambda f: f.stat().st_mtime, reverse=True)

    # Also index claude-flow sessions (different dir, dash-separated IDs)
    cf_files = sorted(CLAUDEFLOW_SESSIONS_DIR.glob("session-*.json"),
                      key=lambda f: f.stat().st_mtime, reverse=True) if CLAUDEFLOW_SESSIONS_DIR.exists() else []

    # Merge both lists, dedup by path
    seen_paths = set()
    all_files = []
    for f in session_files + cf_files:
        if f not in seen_paths:
            seen_paths.add(f)
            all_files.append(f)

    if not session_files:
        return {"status": "no_files", "indexed": 0, "total": 0}

    # Ensure FTS DB directory exists
    FTS_DB.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(FTS_DB))
    conn.execute("PRAGMA journal_mode=WAL")

    # Create tables if missing
    conn.executescript("""
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
        );
        CREATE VIRTUAL TABLE IF NOT EXISTS sessions_search
            USING fts5(session_id UNINDEXED, summary, agent_name, tokenize='trigram');
    """)

    indexed = 0
    skipped = 0
    new_ids = set()

    for f in all_files:
        try:
            data = json.loads(f.read_text())
            # Handle both hermes (session_id) and claude-flow (id) formats
            sid = data.get("session_id") or data.get("id") or f.stem
            new_ids.add(sid)

            # Parse timestamp from claude-flow (startedAt) or hermes (session_start) format
            ts = 0.0
            start_str = data.get("startedAt") or data.get("session_start", "")
            if start_str:
                try:
                    from datetime import datetime
                    ts = datetime.fromisoformat(start_str).timestamp()
                except (ValueError, TypeError):
                    ts = f.stat().st_mtime

            messages = data.get("messages", [])
            if not messages and "context" in data:
                # claude-flow format: context.tasks + context.decisions
                context = data.get("context", {})
                summaries = []
                if context.get("lastUserQuery"):
                    summaries.append(context["lastUserQuery"])
                messages = [{"role": "user", "content": s} for s in summaries if s]
            mcount = data.get("message_count", len(messages))
            ch = _content_hash(messages)

            # Check if this session already exists with same hash
            existing = conn.execute(
                "SELECT content_hash FROM sessions_fts WHERE session_id = ?", (sid,)
            ).fetchone()
            if existing and existing[0] == ch:
                skipped += 1
                continue

            summary = _extract_summary(messages)
            errors = _count_errors(messages)
            tool_calls = _count_tool_calls(messages)
            agent = data.get("model", "").split("/")[-1] if "/" in data.get("model", "") else data.get("model", "")
            agent = agent or "unknown"

            conn.execute("""
                INSERT OR REPLACE INTO sessions_fts
                (session_id, timestamp, agent_name, parent_session_id, summary,
                 tool_calls, error_count, message_count, content_hash, updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (sid, ts, agent, "", summary, tool_calls, errors, mcount, ch, ts))

            # Also insert into FTS5 search index
            try:
                conn.execute("""
                    INSERT INTO sessions_search (session_id, summary, agent_name)
                    VALUES (?, ?, ?)
                """, (sid, summary, agent))
            except sqlite3.IntegrityError:
                conn.execute("""
                    UPDATE sessions_search SET summary = ?, agent_name = ?
                    WHERE session_id = ?
                """, (summary, agent, sid))

            indexed += 1

        except (json.JSONDecodeError, KeyError, Exception):
            skipped += 1

    conn.commit()
    total = len(all_files)

    # Report stats
    db_count = conn.execute("SELECT COUNT(*) FROM sessions_fts").fetchone()[0]
    fts_count = conn.execute("SELECT COUNT(*) FROM sessions_search").fetchone()[0]
    error_total = conn.execute("SELECT COALESCE(SUM(error_count), 0) FROM sessions_fts").fetchone()[0]
    conn.close()

    return {
        "status": "ok",
        "indexed": indexed,
        "skipped": skipped,
        "total": total,
        "db_entries": db_count,
        "fts_entries": fts_count,
        "total_errors": error_total,
    }


def main():
    result = index_sessions()
    print(f"[SESSION-INDEX] {result['status']}: "
          f"{result['indexed']} new, {result['skipped']} unchanged, "
          f"{result['db_entries']} total in DB, "
          f"{result['total_errors']} error messages indexed")
    if result.get("indexed", 0) == 0 and result.get("total", 0) > 0:
        print(f"[SESSION-INDEX] All {result['total']} session files already indexed (up to date)")
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
