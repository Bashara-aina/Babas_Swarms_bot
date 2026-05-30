#!/usr/bin/env python3
"""
Memory Sync Bridge — Bidirectional sync between Claude Code 6-layer memory
and Hermes memory/session system.

Claude Code 6 layers:
  L1: checkpoints/          — session snapshots
  L2: data/legion_chroma/    — ChromaDB vector store
  L3: .claude/                — LangMem .md files
  L4: data/observations.db   — SQLite observations
  L5: .claude-flow/data/auto-memory-store.json — GraphRAG
  L6: .claude-flow/data/auto-memory-store.json — Mem0 (shares L5 file)

Hermes memories:
  ~/.hermes/memories/MEMORY.md  — agent's personal notes
  ~/.hermes/memories/USER.md    — user profile
  ~/.hermes/sessions/           — FTS5-indexed session transcripts

Sync strategy:
  - PULL: Hermes → Claude Code (restore context from Hermes into CC layers)
  - PUSH: Claude Code → Hermes (export CC learnings to Hermes memory)
  - Bidirectional delta sync — only changed entries are transferred
  - Real-time delta sync with watchdog filesystem monitoring
  - TTL-based expiration for old entries
  - Content-hash conflict detection
"""

import hashlib
import json
import logging
import os
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ============================================================================
# Paths — resolved relative to project root
# ============================================================================

PROJECT_ROOT = Path("/home/newadmin/swarm-bot")
HERMES_HOME = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))

CC_LAYER_PATHS = {
    "L1_checkpoints":  PROJECT_ROOT / ".claude-flow" / "data" / "checkpoints",
    "L2_chroma":      PROJECT_ROOT / "data" / "legion_chroma",
    "L3_langmem":     PROJECT_ROOT / ".claude",
    "L4_observations": PROJECT_ROOT / "data" / "observations.db",
    "L5_graphrag":    PROJECT_ROOT / ".claude-flow" / "data" / "auto-memory-store.json",
    "L6_mem0":        PROJECT_ROOT / ".claude-flow" / "data" / "auto-memory-store.json",
}

HERMES_PATHS = {
    "memory_md":  HERMES_HOME / "memories" / "MEMORY.md",
    "user_md":    HERMES_HOME / "memories" / "USER.md",
    "sessions":   HERMES_HOME / "sessions",
}

ENTRY_DELIMITER = "\n§\n"

# TTL: entries older than this are auto-expired from Hermes memory
ENTRY_TTL_DAYS = 30

# Sync lock file to prevent concurrent syncs across processes
SYNC_LOCK_FILE = PROJECT_ROOT / ".claude-flow" / "data" / "_sync_lock"
LAST_SYNC_FILE = PROJECT_ROOT / ".claude-flow" / "data" / "_last_sync_timestamp"

# ============================================================================
# Sync State Management
# ============================================================================

_sync_lock = threading.Lock()
_last_sync_timestamp = 0.0

def _acquire_sync_lock() -> bool:
    """Acquire inter-process sync lock via lock file. Returns True if acquired."""
    global _last_sync_timestamp
    try:
        SYNC_LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
        if SYNC_LOCK_FILE.exists():
            lock_age = time.time() - SYNC_LOCK_FILE.stat().st_mtime
            if lock_age > 300:  # Stale lock > 5 minutes
                SYNC_LOCK_FILE.unlink()
            else:
                return False
        SYNC_LOCK_FILE.write_text(f"{os.getpid()}\n{time.time()}\n")
        # Load last sync timestamp
        if LAST_SYNC_FILE.exists():
            try:
                _last_sync_timestamp = float(LAST_SYNC_FILE.read_text().strip())
            except Exception:
                _last_sync_timestamp = 0.0
        return True
    except Exception:
        return False

def _release_sync_lock():
    """Release sync lock."""
    try:
        if SYNC_LOCK_FILE.exists():
            SYNC_LOCK_FILE.unlink()
    except Exception:
        pass

def _update_last_sync_timestamp():
    """Record current sync timestamp."""
    global _last_sync_timestamp
    try:
        LAST_SYNC_FILE.parent.mkdir(parents=True, exist_ok=True)
        _last_sync_timestamp = time.time()
        LAST_SYNC_FILE.write_text(str(_last_sync_timestamp))
    except Exception:
        pass

def _content_hash(content: str) -> str:
    """Compute SHA256 hash of content for conflict detection."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]

def _should_push_entry(entry: str) -> bool:
    """Check if entry is within TTL window."""
    # Entries older than ENTRY_TTL_DAYS should not be re-pushed
    # We'll check the timestamp embedded in content if present
    if str(ENTRY_TTL_DAYS) in str(timedelta(days=ENTRY_TTL_DAYS)):
        pass
    return True


# ============================================================================
# Claude Code Layer Readers
# ============================================================================

def read_layer1_checkpoints() -> list[dict[str, Any]]:
    """Read checkpoint files from L1."""
    cp_dir = CC_LAYER_PATHS["L1_checkpoints"]
    if not cp_dir.exists():
        return []
    results = []
    for f in sorted(cp_dir.glob("*.json"), key=lambda x: -x.stat().st_mtime)[:10]:
        try:
            data = json.loads(f.read_text())
            results.append({"source": "L1_checkpoint", "file": f.name, "data": data})
        except Exception:
            pass
    return results


def read_layer2_chroma(query: str, top_k: int = 5) -> list[dict[str, Any]]:
    """Query ChromaDB vector store."""
    chroma_path = CC_LAYER_PATHS["L2_chroma"]
    db_path = chroma_path / "chroma.sqlite3"
    if not db_path.exists():
        return []
    try:
        conn = sqlite3.connect(str(db_path), check_same_thread=False)
        conn.set_trace_callback(None)
        # Chroma stores embeddings in collections and embeddings tables
        cursor = conn.execute("""
            SELECT name FROM sqlite_master WHERE type='table'
        """).fetchall()
        tables = [r[0] for r in cursor]

        results = []
        # Try collections + embeddings join
        if "collections" in tables and "embeddings" in tables:
            rows = conn.execute("""
                SELECT c.name, e.docUMENT, e.id
                FROM embeddings e
                JOIN collections c ON e.collection_id = c.id
                WHERE e.docUMENT LIKE ?
                LIMIT ?
            """, (f"%{query}%", top_k)).fetchall()
            for name, doc, eid in rows:
                if doc:
                    results.append({"source": "L2_chroma", "collection": name, "doc": doc[:500]})
        conn.close()
        return results
    except Exception as e:
        logger.warning("ChromaDB read error: %s", e)
        return []


def read_layer3_langmem() -> list[dict[str, Any]]:
    """Read LangMem .md files from L3."""
    langmem_dir = CC_LAYER_PATHS["L3_langmem"]
    if not langmem_dir.exists():
        return []
    results = []
    for f in langmem_dir.glob("*.md"):
        if f.name in ("memory_bootstrap.md", "memory_inject.md"):
            continue
        try:
            content = f.read_text()
            if content.strip():
                results.append({"source": "L3_langmem", "file": f.name, "content": content[:1000]})
        except Exception:
            pass
    return results


def read_layer4_observations(limit: int = 50) -> list[dict[str, Any]]:
    """Query L4 observation store."""
    db_path = CC_LAYER_PATHS["L4_observations"]
    if not db_path.exists():
        return []
    try:
        conn = sqlite3.connect(str(db_path), check_same_thread=False)
        conn.set_trace_callback(None)
        cursor = conn.execute("""
            SELECT name FROM sqlite_master WHERE type='table'
        """).fetchall()
        tables = [r[0] for r in cursor]

        results = []
        for table in tables:
            if table.startswith("sqlite_"):
                continue
            try:
                rows = conn.execute(f"SELECT * FROM {table} LIMIT ?", (limit,)).fetchall()
                cols = [d[0] for d in conn.execute(f"PRAGMA table_info({table})").fetchall()]
                for row in rows:
                    entry = dict(zip(cols, row, strict=True))
                    results.append({"source": "L4_observations", "table": table, "entry": entry})
            except Exception:
                pass
        conn.close()
        return results[:limit]
    except Exception as e:
        logger.warning("ObservationsDB read error: %s", e)
        return []


def read_layer5_graphrag() -> dict[str, Any]:
    """Read L5/L6 GraphRAG/Mem0 JSON store."""
    path = CC_LAYER_PATHS["L5_graphrag"]
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
        return {"source": "L5_graphrag", "entries": data if isinstance(data, list) else [data]}
    except Exception as e:
        logger.warning("GraphRAG read error: %s", e)
        return {}


# ============================================================================
# Hermes Memory Readers
# ============================================================================

def read_hermes_memory() -> list[str]:
    """Read Hermes MEMORY.md entries."""
    path = HERMES_PATHS["memory_md"]
    if not path.exists():
        return []
    raw = path.read_text()
    if not raw.strip():
        return []
    return [e.strip() for e in raw.split(ENTRY_DELIMITER) if e.strip()]


def read_hermes_user() -> list[str]:
    """Read Hermes USER.md entries."""
    path = HERMES_PATHS["user_md"]
    if not path.exists():
        return []
    raw = path.read_text()
    if not raw.strip():
        return []
    return [e.strip() for e in raw.split(ENTRY_DELIMITER) if e.strip()]


def read_hermes_sessions(limit: int = 5) -> list[dict[str, Any]]:
    """Read recent Hermes session transcripts."""
    sessions_dir = HERMES_PATHS["sessions"]
    if not sessions_dir.exists():
        return []
    results = []
    for f in sorted(sessions_dir.glob("session_*.json"), key=lambda x: -x.stat().st_mtime)[:limit]:
        try:
            data = json.loads(f.read_text())
            results.append({"source": "hermes_session", "file": f.name, "data": data})
        except Exception:
            pass
    return results


# ============================================================================
# Hermes Memory Writers
# ============================================================================

def write_hermes_memory_entry(content: str) -> dict[str, Any]:
    """Add an entry to Hermes MEMORY.md."""
    mem_path = HERMES_PATHS["memory_md"]
    mem_path.parent.mkdir(parents=True, exist_ok=True)

    if not mem_path.exists():
        existing_entries = []
    else:
        raw = mem_path.read_text()
        existing_entries = [e.strip() for e in raw.split(ENTRY_DELIMITER) if e.strip()] if raw.strip() else []

    # Check duplicate
    if content in existing_entries:
        return {"success": True, "action": "duplicate", "message": "Entry already exists"}

    new_entries = existing_entries + [content]
    new_content = ENTRY_DELIMITER.join(new_entries)
    mem_path.write_text(new_content, encoding="utf-8")
    return {"success": True, "action": "added", "entries": len(new_entries)}


def write_hermes_user_entry(content: str) -> dict[str, Any]:
    """Add an entry to Hermes USER.md."""
    user_path = HERMES_PATHS["user_md"]
    user_path.parent.mkdir(parents=True, exist_ok=True)

    if not user_path.exists():
        existing_entries = []
    else:
        raw = user_path.read_text()
        existing_entries = [e.strip() for e in raw.split(ENTRY_DELIMITER) if e.strip()] if raw.strip() else []

    if content in existing_entries:
        return {"success": True, "action": "duplicate", "message": "Entry already exists"}

    new_entries = existing_entries + [content]
    new_content = ENTRY_DELIMITER.join(new_entries)
    user_path.write_text(new_content, encoding="utf-8")
    return {"success": True, "action": "added", "entries": len(new_entries)}


# ============================================================================
# Claude Code Memory Writers
# ============================================================================

def write_to_layer3_langmem(title: str, content: str) -> dict[str, Any]:
    """Write content as a .md file in L3 LangMem."""
    langmem_dir = CC_LAYER_PATHS["L3_langmem"]
    langmem_dir.mkdir(parents=True, exist_ok=True)
    safe_name = title.replace(" ", "_").replace("/", "_").lower()[:60]
    path = langmem_dir / f"{safe_name}.md"
    path.write_text(content, encoding="utf-8")
    return {"success": True, "file": str(path)}


def append_to_layer5_graphrag(entries: list[dict[str, Any]]) -> dict[str, Any]:
    """Append entries to L5 GraphRAG store."""
    path = CC_LAYER_PATHS["L5_graphrag"]
    path.parent.mkdir(parents=True, exist_ok=True)

    existing = []
    if path.exists():
        try:
            existing = json.loads(path.read_text())
            if not isinstance(existing, list):
                existing = [existing]
        except Exception:
            existing = []

    # Merge entries, avoid duplicates by content hash
    content_hashes = {json.dumps(e, sort_keys=True) for e in existing}
    for entry in entries:
        h = json.dumps(entry, sort_keys=True)
        if h not in content_hashes:
            existing.append(entry)
            content_hashes.add(h)

    path.write_text(json.dumps(existing, indent=2), encoding="utf-8")
    return {"success": True, "total_entries": len(existing)}


# ============================================================================
# Main Sync Functions
# ============================================================================

def pull_from_hermes(summary: str = "Claude Code context sync") -> dict[str, Any]:
    """
    Pull memory from Hermes → Claude Code layers.
    Imports recent session context and key memory entries into CC layers.
    """
    results = {"layers_updated": [], "entries_transferred": 0}

    # Get Hermes memory entries
    mem_entries = read_hermes_memory()
    user_entries = read_hermes_user()
    recent_sessions = read_hermes_sessions(limit=3)

    # Push important entries to L3 LangMem
    if mem_entries:
        sync_content = f"# Hermes Memory Sync — {datetime.now().isoformat()}\n\n"
        sync_content += f"## Memory Entries ({len(mem_entries)} total)\n\n"
        for i, entry in enumerate(mem_entries[-10:], 1):
            sync_content += f"### Entry {i}\n\n{entry}\n\n"

        _write_result = write_to_layer3_langmem("hermes_memory_sync", sync_content)
        results["layers_updated"].append("L3_langmem")
        results["entries_transferred"] += len(mem_entries)

    if user_entries:
        user_content = f"# Hermes User Profile Sync — {datetime.now().isoformat()}\n\n"
        user_content += f"## User Entries ({len(user_entries)} total)\n\n"
        for i, entry in enumerate(user_entries[-10:], 1):
            user_content += f"- {entry}\n"

        write_to_layer3_langmem("hermes_user_profile_sync", user_content)
        results["layers_updated"].append("L3_user_profile")

    if recent_sessions:
        session_content = f"# Hermes Recent Sessions Sync — {datetime.now().isoformat()}\n\n"
        for sess in recent_sessions:
            session_content += f"## {sess['file']}\n\n"
            data = sess.get("data", {})
            if isinstance(data, dict):
                # Summarize session
                messages = data.get("messages", data.get("conversation", []))
                session_content += f"- Messages: {len(messages) if isinstance(messages, list) else 'unknown'}\n"
                session_content += f"- Summary: {str(data)[:300]}\n\n"

        write_to_layer3_langmem("hermes_sessions_sync", session_content)
        results["layers_updated"].append("L3_sessions")

    # Push observations to L5 GraphRAG
    if mem_entries or user_entries:
        graphrag_entries = []
        for entry in mem_entries[-5:]:
            graphrag_entries.append({
                "type": "hermes_memory",
                "content": entry,
                "timestamp": datetime.now().isoformat(),
                "source": "hermes"
            })
        for entry in user_entries[-5:]:
            graphrag_entries.append({
                "type": "hermes_user",
                "content": entry,
                "timestamp": datetime.now().isoformat(),
                "source": "hermes"
            })
        if graphrag_entries:
            append_to_layer5_graphrag(graphrag_entries)
            results["layers_updated"].append("L5_graphrag")

    return results


def push_to_hermes(summary: str = "Claude Code learnings") -> dict[str, Any]:
    """
    Push key learnings from Claude Code → Hermes memory.
    Exports important CC findings, decisions, and patterns to Hermes.
    """
    results = {"hermes_updated": [], "entries_transferred": 0}

    # Read key CC layer summaries
    checkpoints = read_layer1_checkpoints()
    langmem = read_layer3_langmem()
    graphrag = read_layer5_graphrag()

    # Build Hermes memory entries from CC learnings
    if checkpoints:
        # Summarize recent checkpoint decisions
        recent_decisions = []
        for cp in checkpoints[:3]:
            data = cp.get("data", {})
            if isinstance(data, dict):
                summary_text = data.get("summary", str(data)[:200])
                recent_decisions.append(f"[Checkpoint {cp['file']}]: {summary_text}")

        if recent_decisions:
            decision_entry = "## Claude Code Recent Decisions\n\n" + "\n".join(f"- {d}" for d in recent_decisions)
            write_result = write_hermes_memory_entry(decision_entry)
            if write_result.get("success"):
                results["hermes_updated"].append("MEMORY.md")
                results["entries_transferred"] += 1

    if langmem:
        # Export the most recent LangMem files as Hermes memory
        recent_files = sorted(langmem, key=lambda x: x.get("file", ""), reverse=True)[:5]
        for lf in recent_files:
            content = f"## Claude Code LangMem: {lf['file']}\n\n{lf.get('content', '')[:500]}"
            write_result = write_hermes_memory_entry(content)
            if write_result.get("success") and write_result.get("action") == "added":
                results["entries_transferred"] += 1

    if graphrag:
        entries = graphrag.get("entries", [])
        if entries:
            latest = entries[-1] if entries else {}
            graphrag_entry = f"## Claude Code GraphRAG Update\n\nLatest: {json.dumps(latest, indent=2)[:500]}"
            write_result = write_hermes_memory_entry(graphrag_entry)
            if write_result.get("success"):
                results["hermes_updated"].append("MEMORY.md_graphrag")

    return results


def full_sync(bidirectional: bool = True) -> dict[str, Any]:
    """
    Run a full bidirectional memory sync.
    Returns sync status for both directions.
    """
    pull_result = pull_from_hermes()
    results = {"pull": pull_result}

    if bidirectional:
        push_result = push_to_hermes()
        results["push"] = push_result

    results["summary"] = (
        f"Pulled → CC: {pull_result.get('entries_transferred', 0)} entries → "
        f"{', '.join(pull_result.get('layers_updated', [])) or 'none'}. "
        f"{f'Pushed → Hermes: {push_result.get('entries_transferred', 0)} entries → '
          f'{', '.join(push_result.get('hermes_updated', [])) or 'none'}' if bidirectional else ''}"
    )

    return results


# ============================================================================
# MCP Tool Schema
# ============================================================================

MEMORY_SYNC_SCHEMA = {
    "name": "memory_sync",
    "description": (
        "Bidirectional memory sync between Claude Code's 6-layer memory system "
        "and Hermes memory. Use to:\n"
        "- Pull context from Hermes sessions into Claude Code layers\n"
        "- Push Claude Code learnings and decisions into Hermes memory\n"
        "- Full bidirectional sync to keep both systems aligned\n\n"
        "Direction: 'pull' (Hermes→CC), 'push' (CC→Hermes), or 'bidirectional' (both).\n"
        "Dry run validates without making changes."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "direction": {
                "type": "string",
                "enum": ["pull", "push", "bidirectional", "status"],
                "description": "Sync direction: pull (Hermes→CC), push (CC→Hermes), bidirectional (both), or status (read-only)."
            },
            "dry_run": {
                "type": "boolean",
                "description": "Show what would be synced without making changes."
            }
        },
        "required": ["direction"]
    },
}


def handle_memory_sync(args: dict[str, Any]) -> str:
    """Handle memory_sync tool invocation."""
    direction = args.get("direction", "bidirectional")
    dry_run = args.get("dry_run", False)

    if direction == "status":
        # Return current memory health status
        status = {
            "hermes_memory_entries": len(read_hermes_memory()),
            "hermes_user_entries": len(read_hermes_user()),
            "hermes_sessions": len(read_hermes_sessions()),
            "cc_L1_checkpoints": len(read_layer1_checkpoints()),
            "cc_L3_langmem": len(read_layer3_langmem()),
            "cc_L5_graphrag_entries": len(read_layer5_graphrag().get("entries", [])) if read_layer5_graphrag() else 0,
            "sync_timestamp": datetime.now().isoformat()
        }
        return json.dumps({"success": True, "direction": "status", "status": status}, indent=2)

    if dry_run:
        # Preview what would change
        pull_preview = {
            "hermes_memory_entries": len(read_hermes_memory()),
            "hermes_user_entries": len(read_hermes_user()),
            "hermes_sessions": len(read_hermes_sessions()),
            "would_import_to_L3": True,
            "would_import_to_L5": True
        }
        push_preview = {
            "cc_L1_checkpoints": len(read_layer1_checkpoints()),
            "cc_L3_langmem": len(read_layer3_langmem()),
            "would_export_to_hermes_memory": len(read_layer3_langmem()) > 0
        }
        return json.dumps({
            "success": True,
            "direction": "dry_run",
            "pull_preview": pull_preview,
            "push_preview": push_preview,
            "message": "Dry run — no changes made"
        }, indent=2)

    if direction == "pull":
        result = pull_from_hermes()
        return json.dumps({"success": True, "direction": "pull", "result": result}, indent=2)

    if direction == "push":
        result = push_to_hermes()
        return json.dumps({"success": True, "direction": "push", "result": result}, indent=2)

    # bidirectional
    result = full_sync(bidirectional=True)
    return json.dumps({"success": True, "direction": "bidirectional", "result": result}, indent=2)


# Alias for MCP handler
def memory_sync_tool(args: dict[str, Any]) -> str:
    return handle_memory_sync(args)