#!/usr/bin/env python3
"""
MemoryLayerBridge — Live bridge between all 6 CC layers and Hermes memory.
Unified query interface, per-layer adapters, cross-layer health check.
"""
import json
import os
import sqlite3
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path("/home/newadmin/swarm-bot")
HERMES_HOME = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))
CHROMA_HERMES_NS = "hermes_shared"

CC_LAYER_PATHS = {
    "L1": PROJECT_ROOT / ".claude-flow" / "data" / "checkpoints",
    "L2": PROJECT_ROOT / "data" / "legion_chroma",
    "L3": PROJECT_ROOT / ".claude",
    "L4": PROJECT_ROOT / "data" / "observations.db",
    "L5": PROJECT_ROOT / ".claude-flow" / "data" / "auto-memory-store.json",
    "L6": PROJECT_ROOT / ".claude-flow" / "data" / "auto-memory-store.json",
}

LOCK = threading.Lock()

# Priority weights for context restoration
LAYER_WEIGHTS = {
    "L1": 0.30, "L2": 0.20, "L3": 0.20,
    "L4": 0.10, "L5": 0.10, "L6": 0.10
}

# L1: Checkpoints
def read_layer1(query: str = "", top_k: int = 5) -> list[dict[str, Any]]:
    """Read checkpoint files from L1."""
    cp_dir = CC_LAYER_PATHS["L1"]
    if not cp_dir.exists():
        return []
    results = []
    for f in sorted(cp_dir.glob("*.json"), key=lambda x: -x.stat().st_mtime)[:top_k]:
        try:
            data = json.loads(f.read_text())
            results.append({"source": "L1_checkpoints", "file": f.name, "data": data})
        except Exception:
            pass
    return results

def watch_layer1_new() -> str | None:
    """Return most recent checkpoint file if new since last check."""
    cp_dir = CC_LAYER_PATHS["L1"]
    if not cp_dir.exists():
        return None
    files = sorted(cp_dir.glob("*.json"), key=lambda x: -x.stat().st_mtime)
    return str(files[0]) if files else None

# L2: ChromaDB
def read_layer2(query: str, top_k: int = 5) -> list[dict[str, Any]]:
    """Query ChromaDB vector store."""
    chroma_path = CC_LAYER_PATHS["L2"]
    db_path = chroma_path / "chroma.sqlite3"
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

def write_layer2_chroma(collection: str, doc: str, metadata: dict[str, Any]) -> dict[str, Any]:
    """Write to Hermes shared ChromaDB namespace."""
    chroma_path = CC_LAYER_PATHS["L2"]
    db_path = chroma_path / "chroma.sqlite3"
    try:
        conn = sqlite3.connect(str(db_path), check_same_thread=False)
        # Create hermes_shared collection if not exists
        cid_row = conn.execute("""
            SELECT id FROM collections WHERE name = ?
        """, (CHROMA_HERMES_NS,)).fetchone()
        if not cid_row:
            conn.execute("INSERT INTO collections (name, metadata) VALUES (?, ?)",
                        (CHROMA_HERMES_NS, json.dumps({"created_by": "hermes"})))
            cid_row = conn.execute("SELECT id FROM collections WHERE name = ?",
                                  (CHROMA_HERMES_NS,)).fetchone()
        cid = cid_row[0]
        conn.execute("""
            INSERT INTO embeddings (collection_id, docUMENT, metadata)
            VALUES (?, ?, ?)
        """, (cid, doc, json.dumps(metadata)))
        conn.commit()
        conn.close()
        return {"success": True, "collection": CHROMA_HERMES_NS}
    except Exception as e:
        return {"error": str(e)}

# L3: LangMem
def read_layer3(top_k: int = 10) -> list[dict[str, Any]]:
    """Read LangMem .md files from L3."""
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
                results.append({"file": f.name, "content": content[:1000], "modified": f.stat().st_mtime})
        except Exception:
            pass
        if len(results) >= top_k:
            break
    return results

def write_layer3_langmem(title: str, content: str) -> dict[str, Any]:
    """Write content as LangMem .md file in L3."""
    langmem_dir = CC_LAYER_PATHS["L3"]
    langmem_dir.mkdir(parents=True, exist_ok=True)
    safe_name = title.replace(" ", "_").replace("/", "_").lower()[:60]
    path = langmem_dir / f"{safe_name}.md"
    path.write_text(content, encoding="utf-8")
    return {"success": True, "file": str(path)}

# L4: Observations
def read_layer4(limit: int = 20) -> list[dict[str, Any]]:
    """Query L4 observation store."""
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

def write_layer4_observation(table: str, entry: dict[str, Any]) -> dict[str, Any]:
    """Write observation entry to L4 observations.db."""
    db_path = CC_LAYER_PATHS["L4"]
    db_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        conn = sqlite3.connect(str(db_path), check_same_thread=False)
        cols = list(entry.keys())
        placeholders = ", ".join(["?"] * len(cols))
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {table} ({", ".join(cols)})
        """)
        conn.execute(f"INSERT INTO {table} VALUES ({placeholders})", list(entry.values()))
        conn.commit()
        conn.close()
        return {"success": True, "table": table}
    except Exception as e:
        return {"error": str(e)}

# L5: GraphRAG
def read_layer5() -> dict[str, Any]:
    """Read L5 GraphRAG JSON store."""
    path = CC_LAYER_PATHS["L5"]
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
        return {"source": "L5_graphrag", "entries": data if isinstance(data, list) else [data]}
    except Exception:
        return {}

def write_layer5_graphrag(entries: list[dict[str, Any]]) -> dict[str, Any]:
    """Append entries to L5 GraphRAG store."""
    path = CC_LAYER_PATHS["L5"]
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = []
    if path.exists():
        try:
            existing = json.loads(path.read_text())
            if not isinstance(existing, list):
                existing = [existing]
        except Exception:
            existing = []
    content_hashes = {json.dumps(e, sort_keys=True) for e in existing}
    for entry in entries:
        h = json.dumps(entry, sort_keys=True)
        if h not in content_hashes:
            existing.append(entry)
            content_hashes.add(h)
    path.write_text(json.dumps(existing, indent=2), encoding="utf-8")
    return {"success": True, "total_entries": len(existing)}

# L6: Mem0 (shared with L5)
def read_layer6() -> dict[str, Any]:
    """Read L6 Mem0 (shares file with L5)."""
    return read_layer5()

def write_layer6_mem0(entry: dict[str, Any]) -> dict[str, Any]:
    """Write entry to Mem0 (shared with L5)."""
    return write_layer5_graphrag([entry])

# Health check
def health_check() -> dict[str, Any]:
    """Report connectivity status for each CC layer."""
    status = {}
    for layer, path in CC_LAYER_PATHS.items():
        try:
            exists = path.exists()
            writable = path.parent.exists() and os.access(path.parent, os.W_OK) if path.is_file() else (path.exists() and os.access(path, os.W_OK))
            status[layer] = {
                "path": str(path),
                "exists": exists,
                "writable": writable,
                "status": "ok" if exists and writable else "degraded"
            }
            if layer == "L4":
                # SQLite specific check
                if exists:
                    conn = sqlite3.connect(str(path), check_same_thread=False)
                    conn.execute("SELECT 1").fetchone()
                    conn.close()
                    status[layer]["status"] = "ok"
        except Exception as e:
            status[layer] = {"path": str(path), "exists": path.exists(), "error": str(e), "status": "error"}
    return status

# Unified query
def query_memory_layers(query: str, layers: list[str] = None, top_k: int = 5) -> dict[str, Any]:
    """Query all specified CC layers with relevance scoring."""
    if layers is None:
        layers = ["L1", "L2", "L3", "L4", "L5", "L6"]
    results = {}
    weights = {}
    for layer in layers:
        layer_key = f"L{layer}" if str(layer).isdigit() else layer
        if layer_key not in CC_LAYER_PATHS:
            layer_key = f"L{layer}"
        weights[layer_key] = LAYER_WEIGHTS.get(layer_key, 0.1)
    # Execute layer reads
    for layer in layers:
        layer_key = f"L{layer}" if str(layer).isdigit() else layer
        try:
            if layer_key == "L1":
                results[layer_key] = read_layer1(query, top_k)
            elif layer_key == "L2":
                results[layer_key] = read_layer2(query, top_k)
            elif layer_key == "L3":
                results[layer_key] = read_layer3(top_k)
            elif layer_key == "L4":
                results[layer_key] = read_layer4(top_k)
            elif layer_key in ("L5", "L6"):
                data = read_layer5()
                results[layer_key] = data.get("entries", []) if data else []
        except Exception as e:
            results[layer_key] = [{"error": str(e)}]
    # Aggregate with weights
    total_weight = sum(weights.values()) or 1.0
    scored_results = {}
    for layer_key, items in results.items():
        w = weights.get(layer_key, 0.1) / total_weight
        for item in (items if isinstance(items, list) else []):
            item["_layer_weight"] = w
            item["_layer"] = layer_key
        scored_results[layer_key] = items
    return {
        "query": query,
        "layers_queried": layers,
        "weights": weights,
        "results": scored_results
    }

def handle_memory_layer_bridge(args: dict[str, Any]) -> str:
    """Handler for memory layer bridge operations."""
    action = args.get("action", "query")
    if action == "query":
        result = query_memory_layers(
            args.get("query", ""),
            args.get("layers"),
            args.get("top_k", 5)
        )
    elif action == "health":
        result = health_check()
    elif action == "read_layer":
        layer = args.get("layer", "L1")
        result = {"layer": layer, "data": read_layer1() if layer == "L1" else read_layer2(args.get("query", "")) if layer == "L2" else read_layer3(args.get("limit", 10))}
    elif action == "write_layer":
        layer = args.get("layer", "L3")
        data = args.get("data", {})
        if layer == "L2":
            result = write_layer2_chroma(data.get("collection", CHROMA_HERMES_NS), data.get("doc", ""), data.get("metadata", {}))
        elif layer == "L3":
            result = write_layer3_langmem(data.get("title", "untitled"), data.get("content", ""))
        elif layer == "L4":
            result = write_layer4_observation(data.get("table", "hermes_observations"), data.get("entry", {}))
        elif layer == "L5":
            result = write_layer5_graphrag(data.get("entries", []))
        elif layer == "L6":
            result = write_layer6_mem0(data.get("entry", {}))
        else:
            result = {"error": f"unsupported layer: {layer}"}
    elif action == "watch_l1":
        result = {"new_checkpoint": watch_layer1_new()}
    else:
        result = {"error": f"unknown action: {action}"}
    return json.dumps(result, indent=2)

LAYER_BRIDGE_SCHEMA = {
    "name": "memory_layer_bridge",
    "description": "Live bridge between Claude Code 6-layer memory system and Hermes.",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["query", "health", "read_layer", "write_layer", "watch_l1"]},
            "query": {"type": "string"},
            "layers": {"type": "array"},
            "top_k": {"type": "integer", "default": 5},
            "layer": {"type": "string"},
            "data": {"type": "object"},
        },
    },
}