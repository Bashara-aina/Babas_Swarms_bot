#!/usr/bin/env python3
"""
ContextRestorer — Session context restoration from all memory layers on startup.
Aggregates context from all 6 CC layers on CC startup, with priority weighting
and relevance scoring.
"""
import json
import os
import sqlite3
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = Path("/home/newadmin/swarm-bot")
HERMES_HOME = Path(os.path.expanduser("~/.hermes"))
CHROMA_HERMES_NS = "hermes_shared"

CC_LAYER_PATHS = {
    "L1": PROJECT_ROOT / ".claude-flow" / "data" / "checkpoints",
    "L2": PROJECT_ROOT / "data" / "legion_chroma",
    "L3": PROJECT_ROOT / ".claude",
    "L4": PROJECT_ROOT / "data" / "observations.db",
    "L5": PROJECT_ROOT / ".claude-flow" / "data" / "auto-memory-store.json",
    "L6": PROJECT_ROOT / ".claude-flow" / "data" / "auto-memory-store.json",
}

# Priority weights for context restoration (sum to 1.0)
LAYER_WEIGHTS = {
    "L1": 0.30,  # Checkpoints - most recent state
    "L2": 0.20,  # ChromaDB - vector context
    "L3": 0.20,  # LangMem - persistent knowledge
    "L4": 0.10,  # Observations - events
    "L5": 0.10,  # GraphRAG - relationships
    "L6": 0.10,  # Mem0 - shared context
}

MAX_CONTEXT_CHARS = 8000
LOCK = threading.Lock()

def _read_layer1(top_k: int = 5) -> list[dict[str, Any]]:
    """Read recent checkpoints."""
    cp_dir = CC_LAYER_PATHS["L1"]
    if not cp_dir.exists():
        return []
    results = []
    for f in sorted(cp_dir.glob("*.json"), key=lambda x: -x.stat().st_mtime)[:top_k]:
        try:
            data = json.loads(f.read_text())
            results.append({"file": f.name, "data": data, "modified": f.stat().st_mtime})
        except Exception:
            pass
    return results

def _read_layer2(query: str = "", top_k: int = 5) -> list[dict[str, Any]]:
    """Query ChromaDB."""
    db_path = CC_LAYER_PATHS["L2"] / "chroma.sqlite3"
    if not db_path.exists():
        return []
    try:
        conn = sqlite3.connect(str(db_path), check_same_thread=False)
        rows = conn.execute("""
            SELECT c.name, e.docUMENT, e.id
            FROM embeddings e
            JOIN collections c ON e.collection_id = c.id
            WHERE e.docUMENT LIKE ?
            LIMIT ?
        """, (f"%{query}%", top_k)).fetchall()
        conn.close()
        return [{"collection": r[0], "doc": r[1][:500]} for r in rows if r[1]]
    except Exception:
        return []

def _read_layer3(top_k: int = 10) -> list[dict[str, Any]]:
    """Read LangMem files."""
    langmem_dir = CC_LAYER_PATHS["L3"]
    if not langmem_dir.exists():
        return []
    results = []
    for f in sorted(langmem_dir.glob("*.md"), key=lambda x: -x.stat().st_mtime):
        if f.name in ("memory_bootstrap.md", "memory_inject.md"):
            continue
        try:
            content = f.read_text()
            if content.strip():
                results.append({
                    "file": f.name,
                    "content": content[:2000],
                    "modified": f.stat().st_mtime
                })
        except Exception:
            pass
        if len(results) >= top_k:
            break
    return results

def _read_layer4(limit: int = 20) -> list[dict[str, Any]]:
    """Read observations."""
    db_path = CC_LAYER_PATHS["L4"]
    if not db_path.exists():
        return []
    try:
        conn = sqlite3.connect(str(db_path), check_same_thread=False)
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
                    results.append({"table": table, "entry": entry})
            except Exception:
                pass
        conn.close()
        return results[:limit]
    except Exception:
        return []

def _read_layer5() -> list[dict[str, Any]]:
    """Read GraphRAG/Mem0."""
    path = CC_LAYER_PATHS["L5"]
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
        entries = data if isinstance(data, list) else [data]
        return entries[(-50):] if entries else []
    except Exception:
        return []

def _compute_relevance_score(item: dict[str, Any], layer: str, query: str = "") -> float:
    """Score item by layer weight and keyword overlap with query."""
    weight = LAYER_WEIGHTS.get(layer, 0.1)
    if not query:
        return weight
    query_terms = set(query.lower().split())
    item_str = json.dumps(item).lower()
    overlap = len(query_terms & set(item_str.split()))
    return weight * (1.0 + 0.1 * overlap)

def _format_layer_section(layer: str, items: list[dict[str, Any]], max_chars: int = 1500) -> str:
    """Format a layer's data as a markdown section."""
    if not items:
        return f"## {layer}\n_No entries found_\n"
    lines = [f"## {layer} ({len(items)} entries)\n"]
    for item in items:
        if layer == "L1":
            lines.append(f"### {item.get('file', 'unknown')}\n```\n{str(item.get('data', {}))[:500]}\n```\n")
        elif layer == "L2":
            lines.append(f"- [{item.get('collection', '?')}]: {item.get('doc', '')[:300]}\n")
        elif layer == "L3":
            lines.append(f"### {item.get('file', '?')}\n\n{item.get('content', '')[:500]}\n\n")
        elif layer in ("L5", "L6"):
            lines.append(f"- {str(item)[:300]}\n")
        else:
            lines.append(f"- {str(item)[:300]}\n")
    content = "".join(lines)
    return content[:max_chars]

def restore_context(session_id: str = "", query: str = "") -> dict[str, Any]:
    """
    On CC startup: query all 6 layers, aggregate relevant context.
    Returns structured markdown with headers per layer.
    Priority weighting: L1=30%, L2=20%, L3=20%, L4=10%, L5=10%, L6=10%
    """
    contributions = {}
    layered_context = {}
    total_weight = 0.0

    all_items = []  # For scoring and truncation

    # Read each layer
    layer_data = {
        "L1": _read_layer1(5),
        "L2": _read_layer2(query, 5),
        "L3": _read_layer3(10),
        "L4": _read_layer4(20),
        "L5": _read_layer5(),
        "L6": _read_layer5(),  # Shares with L5
    }

    for layer, items in layer_data.items():
        if items:
            w = LAYER_WEIGHTS.get(layer, 0.1)
            total_weight += w
            for item in (items if isinstance(items, list) else []):
                item["_layer"] = layer
                item["_weight"] = w
                item["_score"] = _compute_relevance_score(item, layer, query)
            all_items.extend(items)
            layered_context[layer] = items
            contributions[layer] = len(items) if isinstance(items, list) else 0

    # Sort by relevance score
    all_items.sort(key=lambda x: x.get("_score", 0), reverse=True)

    # Truncate to MAX_CONTEXT_CHARS
    total_chars = 0
    scored_context = []
    for item in all_items:
        item_str = str(item)
        if total_chars + len(item_str) > MAX_CONTEXT_CHARS * 2:  # Loosely
            continue
        scored_context.append(item)
        total_chars += len(item_str)

    # Build markdown sections
    sections = []
    sections.append("# Session Context Restoration\n")
    sections.append(f"_Restored at: {datetime.now().isoformat()}_\n")
    if session_id:
        sections.append(f"_Resumed from session: {session_id}_\n")
    sections.append(f"\n_Total relevance score: {total_weight:.2f}_\n")

    for layer in ["L1", "L2", "L3", "L4", "L5", "L6"]:
        items = layered_context.get(layer, [])
        if items:
            section = _format_layer_section(layer, items, max_chars=1200)
            sections.append(section + "\n")

    markdown = "".join(sections)

    # Ensure within limit via simple truncation of last sections
    if len(markdown) > MAX_CONTEXT_CHARS:
        markdown = markdown[:MAX_CONTEXT_CHARS]
        markdown += f"\n\n_[...truncated at {MAX_CONTEXT_CHARS} chars]_\n"

    return {
        "session_id": session_id,
        "contributions": contributions,
        "total_weight": round(total_weight, 2),
        "layers_active": len([l for l in contributions if contributions[l] > 0]),
        "total_items": sum(contributions.values()),
        "context": markdown,
        "context_chars": len(markdown),
    }

def restore_context_stream(session_id: str = "", query: str = "", chunk_size: int = 1000) -> list[str]:
    """Stream context in chunks for progressive loading."""
    ctx = restore_context(session_id, query)
    content = ctx["context"]
    chunks = []
    for i in range(0, len(content), chunk_size):
        chunks.append(content[i:i+chunk_size])
    return chunks

def handle_context_restorer(args: dict[str, Any]) -> str:
    """Handler for context restoration."""
    action = args.get("action", "restore")
    if action == "restore":
        result = restore_context(
            args.get("session_id", ""),
            args.get("query", "")
        )
    elif action == "stream":
        chunks = restore_context_stream(
            args.get("session_id", ""),
            args.get("query", ""),
            args.get("chunk_size", 1000)
        )
        result = {"chunks": len(chunks), "total_chars": sum(len(c) for c in chunks)}
        return json.dumps(result, indent=2)
    elif action == "status":
        contributions = {}
        for layer in ["L1", "L2", "L3", "L4", "L5", "L6"]:
            try:
                path = CC_LAYER_PATHS[layer]
                exists = path.exists()
                contributions[layer] = {
                    "exists": exists,
                    "writable": path.parent.exists() if path.is_file() else (path.exists() and __import__("os").access(path, __import__("os").W_OK))
                }
            except Exception as e:
                contributions[layer] = {"error": str(e)}
        result = {"layers": contributions, "max_context_chars": MAX_CONTEXT_CHARS}
    else:
        result = {"error": f"unknown action: {action}"}
    return json.dumps(result, indent=2)

CONTEXT_RESTORER_SCHEMA = {
    "name": "context_restorer",
    "description": "Session context restoration from all 6 CC memory layers on startup.",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["restore", "stream", "status"]},
            "session_id": {"type": "string"},
            "query": {"type": "string"},
            "chunk_size": {"type": "integer", "default": 1000},
        },
    },
}