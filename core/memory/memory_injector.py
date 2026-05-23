"""
10-Layer Recall Engine — OpenCode Memory System
==============================================

Priority order (1 = highest, used first; 10 = lowest, last resort):
  L1:  Session checkpoints  — .session_state/checkpoints/ (most recent = most relevant)
  L2:  mem0 ChromaDB        — MemoryStore recall (semantic vector, live memories)
  L3:  langmem              — SwarmBotMemoryManager + langgraph InMemoryStore
  L4:  observation_store   — SQLite+FTS5 progressive disclosure
  L5:  graphrag             — wiki text_units (keyword, no LLM)
  L6:  obsidian MCP        — 121-tool vault search via MCP
  L7:  gitnexus MCP        — 68k+ symbol code knowledge graph via MCP
  L8:  ruflo MCP memory    — HNSW semantic vector search via MCP
  L9:  symphony tasks      — active task state via MCP
  L10: mem0 cloud          — litellm proxy (external)

All 10 layers fire CONCURRENTLY. Results are deduplicated and ranked by
confidence = (layer_priority_score * 0.7) + (keyword_overlap_score * 0.3).
The top N results are returned in a compact, LLM-friendly format.

Usage:
    from core.memory.memory_injector import build_memory_context
    ctx = build_memory_context("what did we do with intent routing", user_id="bashara")
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
import concurrent.futures
import hashlib
import json
import logging
import re
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ── Layer priority weights (higher = more trusted) ──────────────────────────────
_LAYER_PRIORITY = {
    "checkpoints":      10.0,   # Most recent session state
    "mem0":             9.0,   # Live semantic memory
    "langmem":          8.0,   # Graph-structured memory
    "observation":      7.0,   # Recent observations
    "graphrag":         6.0,   # Wiki knowledge base
    "obsidian_mcp":     5.5,   # Personal vault
    "gitnexus_mcp":     5.0,   # Code knowledge graph
    "ruflo_mcp":       4.5,   # Learned patterns
    "symphony_tasks":  4.0,   # Active tasks (ephemeral)
    "mem0_cloud":       3.0,   # External cloud (lower confidence)
}

# ── Thread pool for sync-only layer functions ───────────────────────────────────
_EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=6, thread_name_prefix="mem")

# ── MCP client singleton ─────────────────────────────────────────────────────────
_mcp_pool: Any = None


def _get_mcp_pool():
    global _mcp_pool
    if _mcp_pool is None:
        try:
            from core.mcp_client import MCPClientPool
            _mcp_pool = MCPClientPool()
        except Exception as e:
            logger.debug("MCPClientPool not available: %s", e)
            _mcp_pool = False  # deliberate False sentinel, not None
    return _mcp_pool or None


# ── Content fingerprint for deduplication ───────────────────────────────────────

def _fingerprint(text: str) -> str:
    """Content-stable hash for deduping across layers."""
    return hashlib.sha1(text.lower().encode()).hexdigest()[:16]


def _keyword_score(text: str, query: str) -> float:
    """Keyword overlap score 0..1."""
    if not query or not text:
        return 0.0
    q_words = set(query.lower().split())
    t_words = set(text.lower().split())
    if not q_words:
        return 0.0
    return sum(1 for w in q_words if w in t_words) / len(q_words)


# ── Safe asyncio.run wrapper (fixes anyio cancel-scope issues) ─────────────────

def _run_async(coro, timeout: float = 5.0):
    """Run coroutine in thread pool using loop.run_until_complete().

    Uses a fresh event loop per call with run_until_complete(), which is
    safe for stdio_client (async generator) and avoids the anyio cancel-scope
    GeneratorExit errors that asyncio.run() triggers when the loop is closed
    by a thread-pool timeout.

    The fresh loop per call also prevents cross-call contamination when
    the pool has active sessions in the main loop.
    """
    def _runner():
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(coro)
            finally:
                # Don't close the loop here — run_until_complete already
                # finished and handles cleanup. Setting the loop back to
                # the default prevents warnings about unenclosed loops.
                asyncio.set_event_loop(None)
                loop.close()
        except (asyncio.CancelledError, GeneratorExit):
            return []
        except Exception as e:
            logger.debug("Async runner error: %s", e)
            return []

    try:
        future = _EXECUTOR.submit(_runner)
        return future.result(timeout=timeout)
    except (concurrent.futures.TimeoutError, asyncio.CancelledError):
        return []
    except Exception:
        return []


# ── Obsidian stderr line filter ───────────────────────────────────────────────

_IGNORE_PATTERNS = [
    re.compile(r"^Obsidian MCP server running on stdio"),
    re.compile(r"^Reading config"),
    re.compile(r"^Loaded tools:"),
    re.compile(r"^Info: "),
    re.compile(r"^[^\s{\"]{2,}$"),  # single-word non-JSON lines
]


def _filter_obsidian_text(raw: str) -> str:
    """Strip known non-JSON stderr/stdout injection lines from obsidian output."""
    lines = raw.splitlines()
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        skip = False
        for pat in _IGNORE_PATTERNS:
            if pat.match(stripped):
                skip = True
                break
        if not skip:
            cleaned.append(line)
    return "\n".join(cleaned)


# ── Result container ────────────────────────────────────────────────────────────

@dataclass
class MemoryResult:
    content: str
    layer: str
    confidence: float
    fp: str  # fingerprint

    def __str__(self) -> str:
        return self.content


# ── Layer 1: Session checkpoints ───────────────────────────────────────────────

def _recall_checkpoints(query: str, project_dir: str | None = None) -> list[MemoryResult]:
    """Search .session_state/checkpoints/ for query-relevant entries."""
    from core.memory.memory_injector import _get_session_dir
    checkpoint_dir = _get_session_dir(project_dir) / "checkpoints"
    if not checkpoint_dir.exists():
        return []
    try:
        cps = sorted(checkpoint_dir.glob("checkpoint_*.json"), reverse=True)
        results = []
        for cp in cps[:5]:
            try:
                data = json.loads(cp.read_text())
                text = json.dumps(data, default=str)
                score = _keyword_score(text, query)
                if score > 0 or cps.index(cp) == 0:  # always include most recent
                    ts = cp.stem.replace("checkpoint_", "").replace("_", " ")
                    results.append(MemoryResult(
                        content=f"[{ts}] {text[:250]}",
                        layer="checkpoints",
                        confidence=_LAYER_PRIORITY["checkpoints"] * (0.5 + score * 0.5),
                        fp=_fingerprint(text),
                    ))
            except Exception:
                continue
        return sorted(results, key=lambda r: r.confidence, reverse=True)[:5]
    except Exception as e:
        logger.debug("Checkpoint recall error: %s", e)
        return []


# ── Layer 2: mem0 ChromaDB ────────────────────────────────────────────────────

def _recall_mem0(query: str) -> list[MemoryResult]:
    """Semantic search via MemoryStore (ChromaDB)."""
    try:
        from core.memory.store import MemoryStore
        store = MemoryStore()
        memories = store.recall(query=query, agent_id=None, top_k=5, min_score=0.25)
        return [
            MemoryResult(
                content=m,
                layer="mem0",
                confidence=_LAYER_PRIORITY["mem0"],
                fp=_fingerprint(m),
            )
            for m in memories if len(m) > 20
        ]
    except Exception as e:
        logger.debug("mem0 recall error: %s", e)
        return []


# ── Layer 3: langmem ─────────────────────────────────────────────────────────

_LANGMEM_STORE = None
_LANGMEM_SYNCED = False


def _get_langmem_store():
    global _LANGMEM_STORE
    if _LANGMEM_STORE is None:
        from langgraph.store.memory import InMemoryStore
        _LANGMEM_STORE = InMemoryStore()
    return _LANGMEM_STORE


def _sync_mem0_into_langmem() -> None:
    global _LANGMEM_SYNCED
    if _LANGMEM_SYNCED:
        return
    _LANGMEM_SYNCED = True
    try:
        from core.memory.store import MemoryStore
        from langgraph.store.memory import InMemoryStore
        store = _get_langmem_store()
        mems = MemoryStore().recall(query="memory", agent_id=None, top_k=50, min_score=0.0)
        for i, mem in enumerate(mems):
            if len(mem) < 20:
                continue
            try:
                store.put(("swarmbot", "memories"), f"mem0_{i:04d}", {"content": mem})
            except Exception:
                continue
        logger.debug("Synced %d mem0 memories into langmem", len(mems))
    except Exception as e:
        logger.debug("langmem sync error (non-fatal): %s", e)


async def _recall_langmem_async(query: str, limit: int = 5) -> list[MemoryResult]:
    """Async langmem search."""
    try:
        import langmem as _lm
    except Exception:
        return []
    _sync_mem0_into_langmem()
    try:
        store = _get_langmem_store()
        search_tool = _lm.create_search_memory_tool(
            namespace=("swarmbot", "memories"),
            store=store,
            instructions="Find distinct memories relevant to the query.",
        )
        raw = await search_tool.ainvoke({"query": query, "limit": limit})
        items = json.loads(raw) if isinstance(raw, str) else (raw if isinstance(raw, list) else [])
        results = []
        for item in items[:limit]:
            content = ""
            if isinstance(item, dict):
                content = item.get("value", {}).get("content", "") or item.get("content", "")
            elif isinstance(item, str) and len(item) > 20:
                content = item
            if content:
                results.append(MemoryResult(
                    content=content[:400],
                    layer="langmem",
                    confidence=_LAYER_PRIORITY["langmem"],
                    fp=_fingerprint(content),
                ))
        return results
    except Exception as e:
        logger.debug("langmem recall error: %s", e)
        return []


def _recall_langmem(query: str) -> list[MemoryResult]:
    return _run_async(_recall_langmem_async(query), timeout=8.0)


# ── Layer 4: observation_store ─────────────────────────────────────────────────

async def _recall_observation_async(query: str, limit: int = 3) -> list[MemoryResult]:
    """Async observation_store search via SQLite+FTS5."""
    try:
        from core.memory.observation_store import get_observation_store
        store = get_observation_store()
        rows = await store.search(query=query, limit=limit)
        return [
            MemoryResult(
                content=(
                    f"[{r.get('type', '?')}][{r.get('created_at', '')[:19]}] "
                    f"{r.get('title', '')}"
                    + (f" — {r.get('subtitle', '')}" if r.get("subtitle") else "")
                ),
                layer="observation",
                confidence=_LAYER_PRIORITY["observation"],
                fp=_fingerprint(r.get("title", "")),
            )
            for r in rows if r.get("title")
        ]
    except Exception as e:
        logger.debug("observation_store recall error: %s", e)
        return []


def _recall_observation(query: str) -> list[MemoryResult]:
    return _run_async(_recall_observation_async(query), timeout=5.0)


# ── Layer 5: graphrag (wiki keyword) ────────────────────────────────────────────

def _recall_graphrag(query: str) -> list[MemoryResult]:
    """Wiki text_units via keyword overlap — no LLM call."""
    try:
        from core.integrations.graphrag_integration import _keyword_search_text_units
        units = _keyword_search_text_units(query=query, limit=3)
        return [
            MemoryResult(
                content=u,
                layer="graphrag",
                confidence=_LAYER_PRIORITY["graphrag"] * (0.5 + _keyword_score(u, query) * 0.5),
                fp=_fingerprint(u),
            )
            for u in units
        ]
    except Exception as e:
        logger.debug("graphrag recall error: %s", e)
        return []


# ── Layer 6: obsidian MCP ──────────────────────────────────────────────────────

async def _recall_obsidian_async(query: str, limit: int = 3) -> list[MemoryResult]:
    pool = _get_mcp_pool()
    if not pool:
        return []
    try:
        raw = await pool.call_tool("obsidian", "search_notes", {"query": query, "limit": limit})
        if not raw or "Error" in raw or raw.startswith("error"):
            return []
        # Filter obsidian's stderr injection lines
        cleaned = _filter_obsidian_text(raw)
        if not cleaned or not cleaned.strip().startswith("["):
            return []
        items = json.loads(cleaned)
        results = []
        for item in items[:limit]:
            content = item.get("content", "") or item.get("snippet", "")
            if content:
                fn = item.get("filename", "note")
                results.append(MemoryResult(
                    content=f"[obsidian:{fn}] {content[:300]}",
                    layer="obsidian_mcp",
                    confidence=_LAYER_PRIORITY["obsidian_mcp"],
                    fp=_fingerprint(content),
                ))
        return results
    except json.JSONDecodeError:
        return []
    except Exception as e:
        logger.debug("obsidian MCP recall error: %s", e)
        return []


def _recall_obsidian(query: str) -> list[MemoryResult]:
    return _run_async(_recall_obsidian_async(query), timeout=4.0)


# ── Layer 7: gitnexus MCP ─────────────────────────────────────────────────────

async def _recall_gitnexus_async(query: str, limit: int = 3) -> list[MemoryResult]:
    pool = _get_mcp_pool()
    if not pool:
        return []
    try:
        raw = await pool.call_tool(
            "gitnexus", "query",
            {"query": query, "limit": limit, "include_content": True},
        )
        if not raw or raw.startswith("Error:"):
            return []
        data = json.loads(raw)
        results = []
        if isinstance(data, dict):
            for proc in data.get("processes", [])[:limit]:
                symbols = [s.get("name", "?") for s in proc.get("symbols", [])[:5]]
                label = proc.get("heuristicLabel", proc.get("name", "?"))
                content = f"[gitnexus:{label}] symbols={symbols}"
                results.append(MemoryResult(
                    content=content,
                    layer="gitnexus_mcp",
                    confidence=_LAYER_PRIORITY["gitnexus_mcp"],
                    fp=_fingerprint(content),
                ))
        elif isinstance(data, list):
            for item in data[:limit]:
                content = f"[gitnexus] {str(item)[:200]}"
                results.append(MemoryResult(
                    content=content,
                    layer="gitnexus_mcp",
                    confidence=_LAYER_PRIORITY["gitnexus_mcp"] * 0.7,
                    fp=_fingerprint(content),
                ))
        return results
    except Exception as e:
        logger.debug("gitnexus MCP recall error: %s", e)
        return []


def _recall_gitnexus(query: str) -> list[MemoryResult]:
    return _run_async(_recall_gitnexus_async(query), timeout=4.0)


# ── Layer 8: ruflo MCP memory ─────────────────────────────────────────────────

async def _recall_ruflo_async(query: str, limit: int = 3) -> list[MemoryResult]:
    pool = _get_mcp_pool()
    if not pool:
        return []
    try:
        raw = await pool.call_tool(
            "ruflo", "memory_search",
            {"query": query, "namespace": "default", "top_k": limit, "threshold": 0.25},
        )
        if not raw or raw.startswith("Error:"):
            return []
        items = json.loads(raw) if raw.strip().startswith("[") else []
        return [
            MemoryResult(
                content=f"[ruflo:{item.get('namespace', 'default')}] "
                        f"{item.get('value', item.get('key', ''))[:200]}",
                layer="ruflo_mcp",
                confidence=_LAYER_PRIORITY["ruflo_mcp"],
                fp=_fingerprint(str(item)),
            )
            for item in items[:limit]
            if item.get("value") or item.get("key")
        ]
    except Exception as e:
        logger.debug("ruflo MCP recall error: %s", e)
        return []


def _recall_ruflo(query: str) -> list[MemoryResult]:
    return _run_async(_recall_ruflo_async(query), timeout=3.0)


# ── Layer 9: symphony tasks ──────────────────────────────────────────────────

async def _recall_symphony_async(query: str, limit: int = 3) -> list[MemoryResult]:
    pool = _get_mcp_pool()
    if not pool:
        return []
    try:
        raw = await pool.call_tool("symphony", "get_tasks", {"limit": limit})
        if not raw or raw.startswith("Error:"):
            return []
        tasks = json.loads(raw) if raw.strip().startswith("[") else []
        return [
            MemoryResult(
                content=f"[symphony:{t.get('title', t.get('id', '?'))}] "
                        f"status={t.get('status', '?')} priority={t.get('priority', '?')}",
                layer="symphony_tasks",
                confidence=_LAYER_PRIORITY["symphony_tasks"],
                fp=_fingerprint(t.get("title", "")),
            )
            for t in tasks[:limit]
        ]
    except Exception as e:
        logger.debug("symphony tasks recall error: %s", e)
        return []


def _recall_symphony(query: str) -> list[MemoryResult]:
    return _run_async(_recall_symphony_async(query), timeout=3.0)


# ── Layer 10: mem0 cloud ────────────────────────────────────────────────────

async def _recall_mem0_cloud_async(query: str, top_k: int = 3) -> list[MemoryResult]:
    try:
        from tools.mem0_client import mem0_search
        results = await mem0_search(user_id="bashara", query=query, limit=top_k)
        return [
            MemoryResult(
                content=f"[mem0-cloud:{r.get('metadata', {}).get('source', '?')}] "
                        f"{r.get('memory', r.get('content', ''))}",
                layer="mem0_cloud",
                confidence=_LAYER_PRIORITY["mem0_cloud"],
                fp=_fingerprint(str(r)),
            )
            for r in results
            if r.get("memory") or r.get("content")
        ]
    except Exception as e:
        logger.debug("mem0 cloud recall error: %s", e)
        return []


def _recall_mem0_cloud(query: str) -> list[MemoryResult]:
    return _run_async(_recall_mem0_cloud_async(query), timeout=5.0)


# ── Public API ────────────────────────────────────────────────────────────────

def build_memory_context(
    query: str,
    user_id: str = "bashara",
    project_dir: str | None = None,
    timeout: float = 10.0,
    top_n: int = 20,
) -> str:
    """
    Fire all 10 layers CONCURRENTLY, deduplicate, rank by confidence, return
    a compact LLM-friendly context string.

    Architecture:
      L1:  Session checkpoints      (file glob, keyword scoring)
      L2:  mem0 ChromaDB           (semantic vector recall)
      L3:  langmem                 (langgraph InMemoryStore)
      L4:  observation_store       (SQLite+FTS5)
      L5:  graphrag wiki           (keyword text_units)
      L6:  obsidian MCP            (vault search, 121 tools)
      L7:  gitnexus MCP            (68k+ symbol code graph)
      L8:  ruflo MCP memory        (HNSW semantic)
      L9:  symphony tasks          (active task state)
      L10: mem0 cloud              (litellm proxy)

    Confidence = (layer_priority_weight * 0.7) + (keyword_overlap * 0.3)
    Results deduplicated via SHA1 content fingerprint (first 16 hex chars).
    Top N (default 20) results returned in priority order.

    Writes result to .session_state/recalled_context.md for /memory command.
    """
    from core.memory.memory_injector import _get_session_dir, _get_recalled_file
    session_dir = _get_session_dir(project_dir)
    recalled_file = _get_recalled_file(project_dir)

    t0 = time.monotonic()

    # Fire all 10 layers concurrently via thread pool
    futures = {
        "checkpoints":    _EXECUTOR.submit(_recall_checkpoints, query, project_dir),
        "mem0":           _EXECUTOR.submit(_recall_mem0, query),
        "langmem":         _EXECUTOR.submit(_recall_langmem, query),
        "observation":     _EXECUTOR.submit(_recall_observation, query),
        "graphrag":        _EXECUTOR.submit(_recall_graphrag, query),
        "obsidian_mcp":    _EXECUTOR.submit(_recall_obsidian, query),
        "gitnexus_mcp":    _EXECUTOR.submit(_recall_gitnexus, query),
        "ruflo_mcp":       _EXECUTOR.submit(_recall_ruflo, query),
        "symphony_tasks":  _EXECUTOR.submit(_recall_symphony, query),
        "mem0_cloud":      _EXECUTOR.submit(_recall_mem0_cloud, query),
    }

    # Wait for all with overall timeout
    all_results: list[MemoryResult] = []
    seen_fps: set[str] = set()
    layer_timings: dict[str, float] = {}

    try:
        for name, future in futures.items():
            lt0 = time.monotonic()
            try:
                results: list[MemoryResult] = future.result(timeout=timeout)
                layer_timings[name] = time.monotonic() - lt0
                # Deduplicate inline
                for r in results:
                    if r.fp not in seen_fps:
                        seen_fps.add(r.fp)
                        all_results.append(r)
            except Exception as e:
                layer_timings[name] = time.monotonic() - lt0
                logger.debug("Layer %s failed: %s", name, e)
    except Exception:
        pass

    total_time = time.monotonic() - t0

    # Sort by confidence descending
    all_results.sort(key=lambda r: r.confidence, reverse=True)
    top_results = all_results[:top_n]

    # Build compact output
    layers_with_results = {r.layer for r in top_results}
    lines = [
        f"━━━ MEMORY CONTEXT ━━━  query: «{query}»  layers: {len(layers_with_results)}/10  results: {len(top_results)}  time: {total_time:.2f}s ━━━",
        "",
    ]

    # Group by layer for clean output
    from collections import defaultdict
    by_layer: dict[str, list[MemoryResult]] = defaultdict(list)
    for r in top_results:
        by_layer[r.layer].append(r)

    layer_labels = {
        "checkpoints":    "📌 L1  Session Checkpoints",
        "mem0":           "🧠 L2  mem0 ChromaDB",
        "langmem":        "🔗 L3  langmem",
        "observation":    "📝 L4  observation_store",
        "graphrag":       "📚 L5  graphrag wiki",
        "obsidian_mcp":   "🏛️ L6  obsidian vault (MCP)",
        "gitnexus_mcp":   "🔍 L7  gitnexus code graph (MCP)",
        "ruflo_mcp":      "🧬 L8  ruflo HNSW memory (MCP)",
        "symphony_tasks": "✅ L9  symphony tasks (MCP)",
        "mem0_cloud":     "☁️ L10 mem0 cloud",
    }

    for layer_name, results in by_layer.items():
        label = layer_labels.get(layer_name, layer_name)
        lines.append(f"{label}  (confidence={results[0].confidence:.1f})")
        for r in results:
            snippet = r.content.replace("\n", " ")[:300]
            lines.append(f"  • {snippet}")
        lines.append("")

    if not top_results:
        lines.append("(no memories found across any layer)")

    lines.append("━━━ END MEMORY CONTEXT ━━━")
    text = "\n".join(lines)

    # Persist for /memory command
    try:
        session_dir.mkdir(parents=True, exist_ok=True)
        recalled_file.write_text(text)
        logger.debug("Wrote %d results from %s layers to %s in %.2fs",
                     len(top_results), len(layers_with_results), recalled_file, total_time)
    except Exception as e:
        logger.debug("Could not write recalled context: %s", e)

    return text


def read_recalled_context(project_dir: str | None = None) -> str:
    """Read last recalled context from file."""
    from core.memory.memory_injector import _get_recalled_file
    try:
        path = _get_recalled_file(project_dir)
        if path.exists():
            return path.read_text()
    except Exception:
        pass
    return ""


# ── Backward-compat shims ────────────────────────────────────────────────────

def _get_session_dir(project_dir: str | None = None) -> Path:
    """Get .session_state directory for project."""
    from core.memory.memory_injector import _SESSION_DIR_DEFAULT
    if project_dir:
        return Path(project_dir) / ".session_state"
    return _SESSION_DIR_DEFAULT


def _get_recalled_file(project_dir: str | None = None) -> Path:
    """Get recalled_context.md path."""
    return _get_session_dir(project_dir) / "recalled_context.md"


_SESSION_DIR_DEFAULT = Path.cwd() / ".session_state"
RECALLED_CONTEXT_FILE = _SESSION_DIR_DEFAULT / "recalled_context.md"
CHECKPOINT_DIR = _SESSION_DIR_DEFAULT / "checkpoints"
