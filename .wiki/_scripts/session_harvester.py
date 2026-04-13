#!/usr/bin/env python3
"""
Session Harvester — Option A wiki auto-ingestion
Captures session endpoints from Claude Code, OpenClaude, and Legion bot
into `.wiki/conversations/` as draft stubs for manual review.

Run via: python3 .wiki/_scripts/session_harvester.py
Schedule: every 30 min via cron or as a background task
"""

from __future__ import annotations

import json
import re
import subprocess
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

JST = timezone(timedelta(hours=9))
WIKI_CONVERSATIONS = Path(__file__).parent.parent / "conversations"
WIKI_CONVERSATIONS.mkdir(parents=True, exist_ok=True)

# ── Source 1: Claude Code history.jsonl ──────────────────────────────────────

def harvest_claude_code(since_hours: int = 24) -> list[dict[str, Any]]:
    """Read ~/.claude/history.jsonl for recent sessions."""
    hist_file = Path.home() / ".claude" / "history.jsonl"
    if not hist_file.exists():
        return []

    cutoff = datetime.now(JST) - timedelta(hours=since_hours)
    cutoff_ts = int(cutoff.timestamp() * 1000)
    sessions: dict[str, dict[str, Any]] = {}

    for line in hist_file.read_text().splitlines():
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except Exception:
            continue
        ts = entry.get("timestamp", 0)
        if ts < cutoff_ts:
            continue
        sid = entry.get("sessionId", "")
        if sid not in sessions:
            sessions[sid] = {
                "session_id": sid,
                "project": entry.get("project", ""),
                "first_seen": ts,
                "last_seen": ts,
                "messages": [],
            }
        sessions[sid]["last_seen"] = max(sessions[sid]["last_seen"], ts)
        display = entry.get("display", "")
        if display:
            sessions[sid]["messages"].append({"role": "user", "content": display, "ts": ts})

    return list(sessions.values())


# ── Source 2: OpenClaude sessions ─────────────────────────────────────────────

def harvest_opencode(since_hours: int = 24) -> list[dict[str, Any]]:
    """Read ~/.opencode/sessions/ for recent OpenClaude sessions."""
    sessions_dir = Path.home() / ".opencode" / "sessions"
    if not sessions_dir.exists():
        return []

    cutoff = datetime.now(JST) - timedelta(hours=since_hours)
    results: list[dict[str, Any]] = []

    for json_file in sorted(sessions_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:20]:
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
        except Exception:
            continue

        started = data.get("startedAt", 0)
        if started:
            session_time = datetime.fromtimestamp(started / 1000, tz=JST)
            if session_time < cutoff:
                break

        messages = data.get("messages", [])
        if not messages:
            continue

        results.append({
            "session_id": data.get("sessionId", json_file.stem),
            "project": data.get("cwd", ""),
            "started_at": started,
            "messages": [
                {"role": m.get("role", "user"), "content": str(m.get("content", ""))[:500], "ts": m.get("timestamp", "")}
                for m in messages[-10:]
                if m.get("content")
            ],
        })

    return results


# ── Source 3: Legion bot RecallMemory ──────────────────────────────────────────

def harvest_legion(since_hours: int = 24) -> list[dict[str, Any]]:
    """Read Legion's RecallMemory for recent conversations."""
    recall_db = Path.home() / ".legionswarm" / "memory" / "recall.db"
    if not recall_db.exists():
        return []

    cutoff = datetime.now(JST) - timedelta(hours=since_hours)
    cutoff_iso = cutoff.isoformat()

    try:
        conn = sqlite3.connect(str(recall_db))
        rows = conn.execute(
            """
            SELECT id, role, content, agent_used, timestamp, session_id
            FROM conversations
            WHERE timestamp > ?
            ORDER BY id DESC
            LIMIT 200
            """,
            (cutoff_iso,),
        ).fetchall()
        conn.close()
    except Exception:
        return []

    if not rows:
        return []

    # Group by session
    sessions: dict[str, dict[str, Any]] = {}
    for row in reversed(rows):
        sid = row[5] or "no_session"
        if sid not in sessions:
            sessions[sid] = {"session_id": sid, "messages": [], "started_at": row[4]}
        sessions[sid]["messages"].append({
            "role": row[1],
            "content": str(row[2])[:500],
            "agent": row[3],
            "ts": row[4],
        })

    return list(sessions.values())


# ── Draft stub writer ──────────────────────────────────────────────────────────

def write_stub(session: dict[str, Any], source: str) -> Path:
    """Write a single draft stub to .wiki/conversations/."""
    sid = session.get("session_id", "unknown")[:20]
    ts = session.get("last_seen") or session.get("started_at", 0)
    if ts:
        if isinstance(ts, (int, float)):
            dt = datetime.fromtimestamp(ts / 1000, tz=JST)
        elif isinstance(ts, str):
            # already ISO string from SQLite
            dt = datetime.fromisoformat(ts).replace(tzinfo=JST)
        else:
            dt = datetime.now(JST)
    else:
        dt = datetime.now(JST)

    slug = f"{dt.strftime('%Y%m%d-%H%M%S')}-{source}-{sid[:8]}"
    path = WIKI_CONVERSATIONS / f"{slug}.md"
    messages = session.get("messages", [])
    msg_lines = []
    for m in messages[:20]:
        role = m.get("role", "?").upper()
        content = re.sub(r'\s+', ' ', str(m.get("content", ""))[:300])
        msg_lines.append(f"- **{role}**: {content}")

    messages_md = "\n".join(msg_lines) if msg_lines else "- (no messages captured)"

    content = f"""---
title: "{slug.replace('-', ' ')}"
type: conversation
status: draft
tags: [{source}, session]
created: {dt.strftime('%Y-%m-%d')}
updated: {dt.strftime('%Y-%m-%d')}
summary: "{source}" session with {len(messages)} messages captured on {dt.strftime('%Y-%m-%d %H:%M')} JST
source: {source}
session_id: "{sid}"
confidence: low
---

## {source.title()} Session — {dt.strftime('%Y-%m-%d %H:%M')} JST

**Project/CWD**: {session.get('project', 'unknown')}

### Messages ({len(messages)})

{messages_md}

---

_This is a DRAFT stub for wiki review. Before merging to the wiki graph,_
_distill the key decision or knowledge from this session into a proper_
_{{type: concept|decision|architecture}} article with TL;DR, frontmatter, and wikilinks._
_To learn how to write wiki articles: see .wiki/SCHEMA.md_
"""
    path.write_text(content, encoding="utf-8")
    return path


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print(f"[HARVESTER] Starting session harvest at {datetime.now(JST).isoformat()}")
    total = 0

    for source, harvester_fn in [
        ("claude-code", harvest_claude_code),
        ("opencode", harvest_opencode),
        ("legion-bot", harvest_legion),
    ]:
        sessions = harvester_fn(since_hours=24)
        for session in sessions:
            path = write_stub(session, source)
            total += 1
            print(f"  Wrote: {path.name}")

    print(f"[HARVESTER] Done — {total} stubs written to {WIKI_CONVERSATIONS}")


if __name__ == "__main__":
    main()
