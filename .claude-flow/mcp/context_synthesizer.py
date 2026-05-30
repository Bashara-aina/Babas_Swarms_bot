#!/usr/bin/env python3
"""
ContextSynthesizer — LLM-powered context synthesis for session resumption.
Queries all 6 memory layers and synthesizes a coherent briefing via MiniMax-M2.7,
with LLM-free fallback.
"""
import json
import os
import sqlite3
import threading
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path("/home/newadmin/swarm-bot")
SYNTHESIS_HISTORY = Path("/tmp/hermes_synthesis_history.jsonl")
MINIMAX_API_URL = "http://localhost:4000/v1/chat/completions"
MINIMAX_API_KEY = "legion-proxy-key"
MINIMAX_MODEL = "MiniMax-M2.7"
MAX_SYNTHESIS_TOKENS = 2000

CC_LAYER_PATHS = {
    "L1": PROJECT_ROOT / ".claude-flow" / "data" / "checkpoints",
    "L2": PROJECT_ROOT / "data" / "legion_chroma",
    "L3": PROJECT_ROOT / ".claude",
    "L4": PROJECT_ROOT / "data" / "observations.db",
    "L5": PROJECT_ROOT / ".claude-flow" / "data" / "auto-memory-store.json",
    "L6": PROJECT_ROOT / ".claude-flow" / "data" / "auto-memory-store.json",
}
LAYER_WEIGHTS = {"L1": 0.30, "L2": 0.20, "L3": 0.20, "L4": 0.10, "L5": 0.10, "L6": 0.10}

LOCK = threading.Lock()
_STATS = {"total_syntheses": 0, "llm_fallbacks": 0, "tokens_used": 0, "entries_processed": 0}


# ---------------------------------------------------------------------------
# Layer readers
# ---------------------------------------------------------------------------

def _read_layer1(top_k: int = 5) -> list[dict]:
    cp_dir = CC_LAYER_PATHS["L1"]
    if not cp_dir.exists(): return []
    results = []
    for f in sorted(cp_dir.glob("*.json"), key=lambda x: -x.stat().st_mtime)[:top_k]:
        try:
            data = json.loads(f.read_text())
            results.append({"source": "L1", "file": f.name, "data": data, "ts": f.stat().st_mtime})
        except Exception: pass
    return results


def _read_layer2(query: str, top_k: int = 5) -> list[dict]:
    db_path = CC_LAYER_PATHS["L2"] / "chroma.sqlite3"
    if not db_path.exists(): return []
    try:
        conn = sqlite3.connect(str(db_path), check_same_thread=False)
        rows = conn.execute("""
            SELECT c.name, e.docUMENT, e.id FROM embeddings e
            JOIN collections c ON e.collection_id = c.id
            WHERE e.docUMENT LIKE ? LIMIT ?""", (f"%{query}%", top_k)).fetchall()
        conn.close()
        return [{"source": "L2", "collection": r[0], "doc": r[1][:500]} for r in rows if r[1]]
    except Exception: return []


def _read_layer3(top_k: int = 10) -> list[dict]:
    langmem_dir = CC_LAYER_PATHS["L3"]
    if not langmem_dir.exists(): return []
    results = []
    for f in sorted(langmem_dir.glob("*.md"), key=lambda x: -x.stat().st_mtime):
        if f.name in ("memory_bootstrap.md", "memory_inject.md"): continue
        try:
            content = f.read_text()
            if content.strip():
                results.append({"source": "L3", "file": f.name, "content": content[:2000], "ts": f.stat().st_mtime})
        except Exception: pass
        if len(results) >= top_k: break
    return results


def _read_layer4(limit: int = 20) -> list[dict]:
    db_path = CC_LAYER_PATHS["L4"]
    if not db_path.exists(): return []
    try:
        conn = sqlite3.connect(str(db_path), check_same_thread=False)
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        results = []
        for table in tables:
            if table.startswith("sqlite_"): continue
            try:
                rows = conn.execute(f"SELECT * FROM {table} LIMIT ?", (limit,)).fetchall()
                cols = [d[0] for d in conn.execute(f"PRAGMA table_info({table})").fetchall()]
                for row in rows:
                    results.append({"source": "L4", "table": table, "entry": dict(zip(cols, row, strict=True))})
            except Exception: pass
        conn.close()
        return results[:limit]
    except Exception: return []


def _read_layer5() -> list[dict]:
    path = CC_LAYER_PATHS["L5"]
    if not path.exists(): return []
    try:
        data = json.loads(path.read_text())
        entries = data if isinstance(data, list) else [data]
        return [{"source": "L5", "entry": e} for e in entries[-50:]]
    except Exception: return []


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

def _aggregate_layers(session_id: str = "", current_task: str = "") -> list[dict]:
    query = current_task or session_id
    layer_data = {
        "L1": _read_layer1(5), "L2": _read_layer2(query, 5),
        "L3": _read_layer3(10), "L4": _read_layer4(20),
        "L5": _read_layer5(), "L6": _read_layer5(),
    }
    all_entries = []
    for layer, items in layer_data.items():
        w = LAYER_WEIGHTS.get(layer, 0.1)
        for item in (items if isinstance(items, list) else []):
            item["_layer"] = layer; item["_weight"] = w
            all_entries.append(item)
    all_entries.sort(key=lambda x: (x.get("ts", 0), x.get("_weight", 0)), reverse=True)
    return all_entries


def _entries_to_prompt(entries: list[dict], max_chars: int = 6000) -> str:
    chunks, total = [], 0
    for e in entries:
        chunk = _format_entry(e)
        if total + len(chunk) > max_chars: break
        chunks.append(chunk); total += len(chunk)
    return "\n".join(chunks) or "[no memory entries found]"


def _format_entry(entry: dict) -> str:
    layer = entry.get("_layer", "?")
    if layer == "L1":
        data = entry.get("data", {})
        s = json.dumps(data)[:300] if isinstance(data, dict) else str(data)[:300]
        return f"[L1-checkpoint] {entry.get('file','?')}: {s}"
    elif layer == "L2":
        return f"[L2-chroma:{entry.get('collection','?')}]: {entry.get('doc','')[:200]}"
    elif layer == "L3":
        return f"[L3-langmem:{entry.get('file','?')}]: {entry.get('content','')[:200]}"
    elif layer == "L4":
        return f"[L4-obs:{entry.get('table','?')}]: {str(entry.get('entry',{}))[:200]}"
    return f"[{layer}]: {str(entry.get('entry', entry))[:200]}"


# ---------------------------------------------------------------------------
# LLM synthesis
# ---------------------------------------------------------------------------

def _call_minimax(system: str, user: str, max_tokens: int = MAX_SYNTHESIS_TOKENS) -> str | None:
    payload = {
        "model": MINIMAX_MODEL,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "max_tokens": max_tokens, "temperature": 0.3,
    }
    try:
        req = urllib.request.Request(
            MINIMAX_API_URL, data=json.dumps(payload).encode(),
            headers={"Authorization": f"Bearer {MINIMAX_API_KEY}", "Content-Type": "application/json"},
            method="POST")
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            with LOCK:
                _STATS["tokens_used"] += result.get("usage", {}).get("total_tokens", 0)
            return content
    except Exception: return None


SYNTHESIS_SYSTEM = """You are a senior software engineer summarizing a coding session context.
Given memory entries from multiple layers, produce a 1-2 paragraph coherent briefing.
Follow this EXACT format — reproduce the headers exactly:

# Session Context Brief

## Last Session Summary
[2-3 sentences: what was being worked on, key decisions made]

## Active Work
[current task, what's left to do, pending decisions]

## Recent Discoveries
[patterns found, bugs fixed, conventions learned]

## Project State
[relevant project conventions, tech stack, ongoing changes]

Be concise. Merge duplicates. Prioritize recent entries. Do not invent information."""


def _build_prompt(entries: list[dict], current_task: str) -> str:
    formatted = _entries_to_prompt(entries)
    task_line = f"\nCurrent task description: {current_task}" if current_task else ""
    return (f"Memory entries from all 6 layers (chronologically recent first):\n{formatted}"
            f"{task_line}\n\nSynthesize into the briefing format. Aim for 1-2 paragraphs total.")


# ---------------------------------------------------------------------------
# LLM-free fallback
# ---------------------------------------------------------------------------

def _synthesize_fallback(entries: list[dict], current_task: str = "") -> str:
    sorted_e = sorted(entries, key=lambda x: (x.get("ts", 0), x.get("_weight", 0)), reverse=True)
    top = sorted_e[:20]
    lines = ["# Session Context Brief", "_Synthesized without LLM (fallback mode)_", "",
             "## Last Session Summary"]
    l1 = [e for e in top if e.get("_layer") == "L1"]
    if l1:
        sums = []
        for e in l1[:3]:
            d = e.get("data", {})
            sums.append((d.get("summary", d.get("description", str(d)[:200])) if isinstance(d, dict) else str(d))[:200])
        lines.append(" ".join(sums[:2]) if sums else "Session data available in checkpoints.")
    else:
        lines.append("No checkpoint data available for this session.")
    lines.extend(["", "## Active Work", ""])
    lines.append(f"Current task: {current_task}" if current_task else "No specific current task provided.")
    l4 = [e for e in top if e.get("_layer") == "L4"]
    if l4:
        lines.append("Recent observations:")
        for e in l4[:3]: lines.append(f"- [{e.get('table','?')}]: {str(e.get('entry',{}))[:150]}")
    lines.extend(["", "## Recent Discoveries", ""])
    l3 = [e for e in top if e.get("_layer") == "L3"]
    if l3:
        for e in l3[:3]: lines.append(f"- [{e.get('file','?')}]: {e.get('content','')[:200]}")
    else:
        lines.append("No recent discoveries recorded in memory layers.")
    lines.extend(["", "## Project State", ""])
    l2 = [e for e in top if e.get("_layer") == "L2"]
    if l2:
        lines.append("Relevant vector context:")
        for e in l2[:3]: lines.append(f"- [{e.get('collection','?')}]: {e.get('doc','')[:200]}")
    else:
        lines.append("No project state context retrieved.")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------

def _record(session_id: str, current_task: str, entries: list[dict], result: str, used_llm: bool):
    try:
        SYNTHESIS_HISTORY.parent.mkdir(parents=True, exist_ok=True)
        with open(SYNTHESIS_HISTORY, "a") as f:
            f.write(json.dumps({
                "timestamp": datetime.now().isoformat(), "session_id": session_id,
                "current_task": current_task, "entries_used": len(entries),
                "layers_used": sorted(set(e.get("_layer","?") for e in entries)),
                "result_chars": len(result), "used_llm": used_llm,
            }) + "\n")
    except Exception: pass


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def synthesize_context(session_id: str = "", current_task: str = "") -> str:
    entries = _aggregate_layers(session_id, current_task)
    with LOCK:
        _STATS["total_syntheses"] += 1; _STATS["entries_processed"] += len(entries)
    if not entries:
        return ("# Session Context Brief\n\n## Last Session Summary\n"
                "No memory entries found for this session.\n\n## Active Work\n"
                "No active work context available.\n\n## Recent Discoveries\n"
                "No discoveries recorded.\n\n## Project State\nNo project state context available.\n")
    result = _call_minimax(SYNTHESIS_SYSTEM, _build_prompt(entries, current_task))
    if result:
        _record(session_id, current_task, entries, result, True)
        return result
    with LOCK: _STATS["llm_fallbacks"] += 1
    fb = _synthesize_fallback(entries, current_task)
    _record(session_id, current_task, entries, fb, False)
    return fb


def synthesize_from_memories(memory_entries: list[dict]) -> str:
    if not memory_entries:
        return ("# Session Context Brief\n\n## Last Session Summary\n"
                "No memory entries provided.\n\n## Active Work\n"
                "No context available.\n\n## Recent Discoveries\n"
                "No discoveries recorded.\n\n## Project State\nNo project state context available.\n")
    for e in memory_entries:
        e["_weight"] = LAYER_WEIGHTS.get(e.get("source","?"), 0.1)
        if "ts" not in e: e["ts"] = e.get("modified", e.get("_weight", 0))
    result = _call_minimax(SYNTHESIS_SYSTEM, _build_prompt(memory_entries, ""))
    with LOCK: _STATS["total_syntheses"] += 1; _STATS["entries_processed"] += len(memory_entries)
    if result:
        _record("", "", memory_entries, result, True)
        return result
    with LOCK: _STATS["llm_fallbacks"] += 1
    fb = _synthesize_fallback(memory_entries, "")
    _record("", "", memory_entries, fb, False)
    return fb


def get_synthesis_stats() -> dict:
    with LOCK:
        ts = _STATS["total_syntheses"]
        fb = _STATS["llm_fallbacks"]
        return {
            "total_syntheses": ts, "llm_fallbacks": fb,
            "tokens_used": _STATS["tokens_used"], "entries_processed": _STATS["entries_processed"],
            "llm_success_rate": round((ts - fb) / max(ts, 1) * 100, 1),
        }


def handle_context_synthesizer(args: dict) -> str:
    action = args.get("action", "synthesize")
    if action == "synthesize":
        return synthesize_context(args.get("session_id", ""), args.get("current_task", ""))
    if action == "synthesize_from_memories":
        return synthesize_from_memories(args.get("memory_entries", []))
    if action == "stats":
        return json.dumps(get_synthesis_stats(), indent=2)
    if action == "aggregate":
        entries = _aggregate_layers(args.get("session_id", ""), args.get("current_task", ""))
        return json.dumps({"entries": entries, "count": len(entries)}, indent=2, default=str)
    return json.dumps({"error": f"unknown action: {action}"}, indent=2)


CONTEXT_SYNTHESIZER_SCHEMA = {
    "name": "context_synthesizer",
    "description": "LLM-powered context synthesis for session resumption. Synthesizes a coherent 1-2 paragraph briefing from all 6 memory layers.",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["synthesize", "synthesize_from_memories", "stats", "aggregate"]},
            "session_id": {"type": "string"},
            "current_task": {"type": "string"},
            "memory_entries": {"type": "array", "items": {"type": "object"}},
        },
    },
}
