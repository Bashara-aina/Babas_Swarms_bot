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

# ── Query expansion for short/vague queries ──────────────────────────────────

# Map of query anchors → expanded terms (no LLM needed, just domain knowledge)
_QUERY_EXPANSION = {
    "project": ["code", "implementation", "feature", "task", "agent", "workflow"],
    "task": ["todo", "issue", "ticket", "implementation", "feature", "bugfix"],
    "bug": ["error", "fix", "crash", "issue", "debug", "exception"],
    "fix": ["bug", "error", "patch", "debug", "repair"],
    "memory": ["context", "recall", "persistence", "store", "remember"],
    "code": ["implementation", "function", "class", "module", "api"],
    "test": ["pytest", "testing", "spec", "verification", "qa"],
    "deploy": ["deployment", "production", "release", "pipeline", "ci"],
    "design": ["architecture", "schema", "api", "pattern", "structure"],
    "review": ["feedback", "critique", "audit", "analysis"],
    "wiki": ["documentation", "knowledge", "note", "reference"],
    "agent": ["worker", "task", "swarm", "orchestration", "llm"],
    "swarm": ["multi-agent", "coordination", "parallel", "orchestration"],
    "memory": ["context", "recall", "persistence", "store"],
    "what did we": ["session", "history", "progress", "checkpoint", "last work"],
    "done": ["completed", "finished", "shipped", "implemented"],
    "next": ["todo", "remaining", "pending", "plan"],
    "error": ["exception", "crash", "bug", "failure", "traceback"],
    "config": ["settings", "env", "yaml", "json", "options"],
}

# Project-specific anchors
_PROJECT_ANCHORS = {
    "rumahlabuh": ["boarding", "rental", "kos", "kost", "room", "booking", "tenant"],
    "cekwajar": ["salary", "pajak", "gaji", "tax", "pph", "ptkp", "bpjs"],
    "swarm-bot": ["agent", "telegram", "handler", "mcp", "orchestration"],
}


def _expand_query(query: str) -> str:
    """Expand short/vague queries with related terms for better recall.

    Uses simple keyword expansion — no LLM needed. For queries ≤ 3 words,
    adds domain-relevant synonyms and related terms from project context.
    """
    q = query.lower().strip()
    words = q.split()

    # No expansion needed for long queries
    if len(words) >= 4:
        return query

    # Check project context from cwd
    try:
        cwd = Path.cwd().name
        if project_terms := _PROJECT_ANCHORS.get(cwd):
            # Inject project-specific terms for all queries in known project dirs
            expanded = q + " " + " ".join(project_terms[:3])
            return expanded
    except Exception:
        pass

    # Expand single words with known related terms
    for anchor, terms in _QUERY_EXPANSION.items():
        if anchor in q:
            extra = " ".join(terms[:3])
            return f"{q} {extra}"

    # Short queries get generic boost
    if len(words) <= 2:
        return f"{q} project task code implementation"

    return query

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

# ── Async executor: persistent loop thread for MCP layers ─────────────────────
#
# stdio_client uses async generators that CANNOT be run via fresh loop +
# run_until_complete() because __aexit__ raises GeneratorExit in a different
# task than the one that entered the cancel scope.  Solution: one persistent
# event loop running in a dedicated daemon thread, shared by all callers.
#
# The worker thread runs loop.run_forever().  It waits on a threading.Queue
# (not asyncio.Queue) so q.get() is a plain blocking call — but we use
# run_in_executor to make it non-blocking to the loop, and process items
# via call_soon_threadsafe so cancellations propagate correctly.

import threading
import queue as _queue
from concurrent.futures import Future

_mcp_loop: asyncio.AbstractEventLoop | None = None
_mcp_loop_thread: threading.Thread | None = None
_mcp_work_queue: _queue.Queue | None = None
_mcp_loop_ready = threading.Event()


def _mcp_worker(q: _queue.Queue) -> None:
    """Dedicated thread: owns the event loop, runs it forever, processes MCP calls."""
    global _mcp_loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    _mcp_loop = loop
    _mcp_loop_ready.set()

    async def _run_coroutine(coro, future, timeout) -> None:
        """Run one coroutine with timeout, set future result in this thread."""
        try:
            res = await asyncio.wait_for(coro, timeout=timeout)
            future.set_result(res)
        except asyncio.TimeoutError:
            future.set_result([])
        except asyncio.CancelledError:
            future.set_result([])
        except Exception as e:
            try:
                future.set_exception(e)
            except Exception:
                pass

    def process_next() -> None:
        """Called by loop via call_soon_threadsafe: read queue and schedule work."""
        try:
            item = q.get_nowait()
        except _queue.Empty:
            return
        if item is None:
            loop.call_soon(loop.stop)
            return
        coro, future, timeout = item
        asyncio.create_task(_run_coroutine(coro, future, timeout))

    # Use a periodic callback so the loop stays alive between queue reads.
    # run_in_executor makes q.get() non-blocking to the event loop.
    def poll_queue() -> None:
        try:
            item = q.get_nowait()
        except _queue.Empty:
            pass
        else:
            if item is None:
                loop.call_soon(loop.stop)
                return
            coro, future, timeout = item
            asyncio.create_task(_run_coroutine(coro, future, timeout))
        finally:
            # Re-schedule ourselves
            loop.call_later(0.05, poll_queue)

    poll_queue()
    loop.run_forever()
    global _mcp_loop
    _mcp_loop = None


def _get_mcp_loop_queue() -> _queue.Queue:
    """Start the MCP worker thread lazily. Returns the work queue."""
    global _mcp_loop_thread, _mcp_work_queue
    if _mcp_loop_thread is None:
        q: _queue.Queue = _queue.Queue()
        _mcp_work_queue = q
        t = threading.Thread(target=_mcp_worker, args=(q,), daemon=True, name="mcp-async-loop")
        t.start()
        _mcp_loop_thread = t
        _mcp_loop_ready.wait(timeout=5.0)
    return _mcp_work_queue


def _mcp_async_submit(coro, timeout: float = 5.0) -> list:
    """Submit an async coroutine to the shared MCP loop thread, block for result.

    This is the ONLY function that should be used to run MCP async coroutines.
    It submits to a persistent loop thread (avoiding stdio_client GeneratorExit)
    and waits for the result within the timeout.
    """
    q = _get_mcp_loop_queue()
    future: Future = Future()
    q.put_nowait((coro, future, timeout))
    return future.result(timeout=timeout + 3.0)


# ── Thread pool for sync-only layer functions ───────────────────────────────────
_EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=5, thread_name_prefix="mem-sync")

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


# ── Circuit breaker for flaky MCP layers ────────────────────────────────────

class _CircuitBreaker:
    """Per-layer circuit breaker. Trips after 3 consecutive failures.

    Resets on a successful call. Prevents repeated hammer on broken layers
    (e.g., MCP stderr injection, gitnexus timeouts).
    """
    def __init__(self, name: str):
        self.name = name
        self.failures = 0
        self.tripped = False

    def record_success(self):
        self.failures = 0
        self.tripped = False

    def record_failure(self):
        self.failures += 1
        if self.failures >= 3:
            self.tripped = True
            logger.debug("Circuit breaker TRIPPED for layer %s after %d failures", self.name, self.failures)

    def is_open(self) -> bool:
        return self.tripped


_breakers: dict[str, _CircuitBreaker] = {}


def _get_breaker(name: str) -> _CircuitBreaker:
    if name not in _breakers:
        _breakers[name] = _CircuitBreaker(name)
    return _breakers[name]


def _safe_json(raw: str | None) -> Any:
    """Parse JSON with multiple fallback strategies.

    1. Try direct json.loads
    2. Try finding first '[' or '{' and parsing from there
    3. Return None
    """
    if not raw or not isinstance(raw, str):
        return None
    raw = raw.strip()
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        pass
    for start in range(len(raw)):
        if raw[start] in ('[', '{'):
            try:
                return json.loads(raw[start:])
            except Exception:
                continue
    return None


# ── Safe asyncio.run wrapper (fixes anyio cancel-scope issues) ─────────────────

def _run_async(coro, timeout: float = 5.0):
    """Run an async coroutine via the shared MCP loop thread (thread-safe)."""
    return _mcp_async_submit(coro, timeout=timeout)


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
    brk = _get_breaker("obsidian_mcp")
    if brk.is_open():
        return []
    try:
        raw = await pool.call_tool("obsidian", "search_notes", {"query": query, "limit": limit})
        if not raw or "Error" in str(raw)[:50]:
            brk.record_failure()
            return []
        # Filter obsidian's stderr injection + find JSON boundary
        cleaned = _filter_obsidian_text(str(raw))
        items = _safe_json(cleaned)
        if not items:
            brk.record_failure()
            return []
        if not isinstance(items, list):
            items = [items]
        results = []
        for item in items[:limit]:
            if not isinstance(item, dict):
                continue
            content = item.get("content", "") or item.get("snippet", "")
            if content:
                fn = item.get("filename", "note")
                results.append(MemoryResult(
                    content=f"[obsidian:{fn}] {content[:300]}",
                    layer="obsidian_mcp",
                    confidence=_LAYER_PRIORITY["obsidian_mcp"],
                    fp=_fingerprint(content),
                ))
        brk.record_success()
        return results
    except Exception as e:
        brk.record_failure()
        logger.debug("obsidian MCP recall error: %s", e)
        return []


def _recall_obsidian(query: str) -> list[MemoryResult]:
    return _run_async(_recall_obsidian_async(query), timeout=4.0)


# ── Layer 7: gitnexus MCP ─────────────────────────────────────────────────────

async def _recall_gitnexus_async(query: str, limit: int = 3) -> list[MemoryResult]:
    pool = _get_mcp_pool()
    if not pool:
        return []
    brk = _get_breaker("gitnexus_mcp")
    if brk.is_open():
        return []
    try:
        raw = await pool.call_tool(
            "gitnexus", "query",
            {"query": query, "limit": limit, "include_content": True},
        )
        if not raw or "Error" in str(raw)[:50]:
            brk.record_failure()
            return []
        data = _safe_json(str(raw))
        if not data:
            brk.record_failure()
            return []
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
        brk.record_success()
        return results
    except Exception as e:
        brk.record_failure()
        logger.debug("gitnexus MCP recall error: %s", e)
        return []


def _recall_gitnexus(query: str) -> list[MemoryResult]:
    return _run_async(_recall_gitnexus_async(query), timeout=4.0)


# ── Layer 8: ruflo MCP memory ─────────────────────────────────────────────────

async def _recall_ruflo_async(query: str, limit: int = 3) -> list[MemoryResult]:
    pool = _get_mcp_pool()
    if not pool:
        return []
    brk = _get_breaker("ruflo_mcp")
    if brk.is_open():
        return []
    try:
        raw = await pool.call_tool(
            "ruflo", "memory_search",
            {"query": query, "namespace": "default", "top_k": limit, "threshold": 0.25},
        )
        if not raw or "Error" in str(raw)[:50]:
            brk.record_failure()
            return []
        items = _safe_json(str(raw))
        if not items:
            brk.record_failure()
            return []
        if not isinstance(items, list):
            items = [items]
        results = [
            MemoryResult(
                content=f"[ruflo:{item.get('namespace', 'default')}] "
                        f"{item.get('value', item.get('key', ''))[:200]}",
                layer="ruflo_mcp",
                confidence=_LAYER_PRIORITY["ruflo_mcp"],
                fp=_fingerprint(str(item)),
            )
            for item in items[:limit]
            if isinstance(item, dict) and (item.get("value") or item.get("key"))
        ]
        brk.record_success()
        return results
    except Exception as e:
        brk.record_failure()
        logger.debug("ruflo MCP recall error: %s", e)
        return []


def _recall_ruflo(query: str) -> list[MemoryResult]:
    return _run_async(_recall_ruflo_async(query), timeout=3.0)


# ── Layer 9: symphony tasks ──────────────────────────────────────────────────

async def _recall_symphony_async(query: str, limit: int = 3) -> list[MemoryResult]:
    pool = _get_mcp_pool()
    if not pool:
        return []
    brk = _get_breaker("symphony_tasks")
    if brk.is_open():
        return []
    try:
        raw = await pool.call_tool("symphony", "get_tasks", {"limit": limit})
        if not raw or "Error" in str(raw)[:50]:
            brk.record_failure()
            return []
        tasks = _safe_json(str(raw))
        if not tasks:
            brk.record_failure()
            return []
        if not isinstance(tasks, list):
            tasks = [tasks]
        results = [
            MemoryResult(
                content=f"[symphony:{t.get('title', t.get('id', '?'))}] "
                        f"status={t.get('status', '?')} priority={t.get('priority', '?')}",
                layer="symphony_tasks",
                confidence=_LAYER_PRIORITY["symphony_tasks"],
                fp=_fingerprint(t.get("title", "")),
            )
            for t in tasks[:limit]
            if isinstance(t, dict)
        ]
        brk.record_success()
        return results
    except Exception as e:
        brk.record_failure()
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

    # Expand short queries for better layer coverage
    expanded_query = _expand_query(query)

    # Fire all 10 layers concurrently via thread pool
    futures = {
        "checkpoints":    _EXECUTOR.submit(_recall_checkpoints, expanded_query, project_dir),
        "mem0":           _EXECUTOR.submit(_recall_mem0, expanded_query),
        "langmem":         _EXECUTOR.submit(_recall_langmem, expanded_query),
        "observation":     _EXECUTOR.submit(_recall_observation, expanded_query),
        "graphrag":        _EXECUTOR.submit(_recall_graphrag, expanded_query),
        "obsidian_mcp":    _EXECUTOR.submit(_recall_obsidian, expanded_query),
        "gitnexus_mcp":    _EXECUTOR.submit(_recall_gitnexus, expanded_query),
        "ruflo_mcp":       _EXECUTOR.submit(_recall_ruflo, expanded_query),
        "symphony_tasks":  _EXECUTOR.submit(_recall_symphony, expanded_query),
        "mem0_cloud":      _EXECUTOR.submit(_recall_mem0_cloud, expanded_query),
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
