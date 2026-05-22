"""
6-layer recall engine for infinite memory without compaction.

Layer 1 (highest priority): .session_state/checkpoints/
Layer 2: ChromaDB (MemoryStore recall)
Layer 3: langmem (SwarmBotMemoryManager)
Layer 4: observation_store (SQLite+FTS5 progressive disclosure)
Layer 5: graphrag (query_wiki_graph)
Layer 6: mem0 cloud (mem0_search via litellm proxy)

Usage:
    from core.memory.memory_injector import build_memory_context
    ctx = build_memory_context("what did we do with intent routing", user_id="bashara")
    # ctx is a string ready to inject into the system prompt
"""
from __future__ import annotations

import asyncio
import concurrent.futures
import json
import logging
import time
from pathlib import Path
from typing import Optional

# ── Shared thread pool for memory layers ──────────────────────────────────────
# Avoids creating/destroying threads per call. 4 workers handles the 6 layers
# (each layer is a separate call) plus concurrent requests from compaction.
_MEM_LAYER_EXECUTOR = concurrent.futures.ThreadPoolExecutor(
    max_workers=4, thread_name_prefix="mem_layer"
)


def _call_async_in_thread(coro, timeout: float = 5.0):
    """Run coroutine in thread pool with hard timeout.

    Always uses asyncio.run() for a fresh loop — never nests via
    run_until_complete(), which hangs if the calling loop is in an
    incompatible state (e.g., closed, or running in the same thread).
    """
    async def _awaiter():
        return await coro

    def _runner():
        # Always use a fresh event loop — asyncio.run() handles cleanup
        # and avoids the "event loop closed" failure from run_until_complete().
        return asyncio.run(_awaiter())

    future = _MEM_LAYER_EXECUTOR.submit(_runner)
    try:
        return future.result(timeout=timeout)
    except concurrent.futures.TimeoutError:
        logger.debug("%s timed out after %.0fs", _runner.__name__, timeout)
        return [] if "recall" in _runner.__name__ else ""
    except Exception as e:
        logger.debug("Thread pool call failed: %s", e)
        return [] if "recall" in _runner.__name__ else ""


LANGMEM_AVAILABLE = False
try:
    import langmem as _langmem
    LANGMEM_AVAILABLE = True
except Exception:
    pass

logger = logging.getLogger(__name__)

# ── Paths ───────────────────────────────────────────────────────────────────
# NOTE: These are module-level defaults. build_memory_context() and
# build_persistent_context() accept an optional project_dir override.
# When called from opencode_bridge.py (which passes project_dir explicitly),
# the per-call session_dir is used instead of these module-level defaults.
_SESSION_DIR_DEFAULT = Path.cwd() / ".session_state"
CHECKPOINT_DIR = _SESSION_DIR_DEFAULT / "checkpoints"
RECALLED_CONTEXT_FILE = _SESSION_DIR_DEFAULT / "recalled_context.md"


def _get_session_dir(project_dir: str | None = None) -> Path:
    """Get session directory for a project, with proper project_dir awareness.

    Called with project_dir when invoked from opencode_bridge.py (which always
    passes the explicit project root). Without project_dir, falls back to cwd
    for backward compatibility with direct calls.
    """
    if project_dir:
        return Path(project_dir) / ".session_state"
    return _SESSION_DIR_DEFAULT


def _get_recalled_file(project_dir: str | None = None) -> Path:
    """Get the recalled_context.md path for a project."""
    return _get_session_dir(project_dir) / "recalled_context.md"

# ── Layer 1: Checkpoints ─────────────────────────────────────────────────────

def _recall_from_checkpoints(query: str, top_k: int = 5, project_dir: str | None = None) -> list[str]:
    """Search checkpoint files for query-relevant entries."""
    checkpoint_dir = _get_session_dir(project_dir) / "checkpoints"
    if not checkpoint_dir.exists():
        return []
    try:
        checkpoints = sorted(checkpoint_dir.glob("checkpoint_*.json"), reverse=True)
        results = []
        for cp in checkpoints[:top_k]:
            try:
                with open(cp) as f:
                    data = json.load(f)
                # Score by keyword overlap
                q_words = set(query.lower().split())
                text = json.dumps(data, default=str).lower()
                matches = sum(1 for w in q_words if w in text)
                if matches > 0:
                    ts = cp.stem.replace("checkpoint_", "").replace("_", " ")
                    results.append((matches, f"[{ts}] {text[:200]}"))
            except Exception:
                continue
        results.sort(reverse=True, key=lambda x: x[0])
        # Fallback: if no keyword matches, return most recent checkpoint anyway
        # (it's always relevant to "what happened in this session" queries)
        if not results and checkpoints:
            try:
                with open(checkpoints[0]) as f:
                    data = json.load(f)
                ts = checkpoints[0].stem.replace("checkpoint_", "").replace("_", " ")
                text = json.dumps(data, default=str)
                results.append((0, f"[{ts}] {text[:200]}"))
            except Exception:
                pass
        return [r[1] for r in results]
    except Exception as e:
        logger.debug("Checkpoint recall error: %s", e)
        return []

# ── Layer 2: mem0 ─────────────────────────────────────────────────────────────

def _recall_from_mem0(query: str, top_k: int = 5) -> list[str]:
    """Semantic search via mem0 (MemoryStore)."""
    try:
        from core.memory.store import MemoryStore
        store = MemoryStore()
        return store.recall(query=query, agent_id=None, top_k=top_k, min_score=0.25)
    except Exception as e:
        logger.debug("mem0 recall error: %s", e)
        return []

_LANGMEM_LANGGRAPH_STORE = None  # cached langgraph InMemoryStore for langmem
_langmem_store_sync = False  # one-time sync flag


def _get_langmem_store():
    """Get or create the langgraph InMemoryStore for langmem operations."""
    global _LANGMEM_LANGGRAPH_STORE
    if _LANGMEM_LANGGRAPH_STORE is None:
        from langgraph.store.memory import InMemoryStore

        _LANGMEM_LANGGRAPH_STORE = InMemoryStore()
    return _LANGMEM_LANGGRAPH_STORE


def _sync_mem0_into_langmem() -> None:
    """One-time sync: copy existing mem0 memories into langmem InMemoryStore.

    langmem's search tool uses langgraph InMemoryStore where put() takes
    (namespace, key, value) with value being a dict that must have 'content' key.
    """
    global _langmem_store_sync
    if _langmem_store_sync:
        return

    try:
        if not LANGMEM_AVAILABLE:
            _langmem_store_sync = True
            return

        store = _get_langmem_store()

        # Get existing mem0 memories
        from core.memory.store import MemoryStore

        mem_store = MemoryStore()
        mems = mem_store.recall(query="memory", agent_id=None, top_k=50, min_score=0.0)
        if not mems:
            _langmem_store_sync = True
            return

        # Pre-load store with existing mem0 memories
        # langgraph InMemoryStore.put(namespace, key, value) where value is dict
        for i, mem in enumerate(mems):
            if len(mem) < 20:
                continue
            try:
                key = f"mem0_{i:04d}"
                # Value must be a dict with 'content' for langmem search to find it
                store.put(("swarmbot", "memories"), key, {"content": mem})
            except Exception:
                continue

        _langmem_store_sync = True
        logger.debug("Synced %d mem0 memories into langmem store", len(mems))
    except Exception as e:
        logger.debug("langmem store sync failed (non-fatal): %s", e)
        _langmem_store_sync = True


def _recall_from_langmem(query: str, limit: int = 5) -> list[str]:
    """Search langmem with pre-populated langgraph InMemoryStore, 8s timeout."""
    try:
        # One-time pre-population from L2 mem0
        _sync_mem0_into_langmem()

        if not LANGMEM_AVAILABLE:
            return []

        import langmem as _langmem

        store = _get_langmem_store()

        async def _search():
            search_tool = _langmem.create_search_memory_tool(
                namespace=("swarmbot", "memories"),
                store=store,
                instructions="Search for distinct memories relevant to the query.",
            )
            result = await search_tool.ainvoke({"query": query, "limit": limit})
            # Result is a JSON string of list[dict]
            if isinstance(result, str):
                import json

                return json.loads(result)
            return result if isinstance(result, list) else []

        results = _call_async_in_thread(_search(), timeout=8.0)
        if isinstance(results, list):
            # langmem returns dicts with 'value' containing {'content': ...}
            extracted = []
            for r in results[:limit]:
                if isinstance(r, dict):
                    content = r.get("value", {}).get("content", "")
                    if not content and "content" in r:
                        content = r.get("content", "")
                    if content and len(content) > 20:
                        extracted.append(content)
            return extracted
        return []
    except Exception as e:
        logger.debug("langmem recall error: %s", e)
        return []


def _recall_from_observation_store(query: str, limit: int = 3) -> list[str]:
    """Search observation_store (SQLite+FTS5) for recent observations."""
    try:
        from core.memory.observation_store import get_observation_store

        async def _search():
            store = get_observation_store()
            results = await store.search(query=query, limit=limit)
            return [
                f"[{r.get('type', '?')}][{r.get('created_at', '')[:19]}] {r.get('title', '')}"
                + (f" — {r.get('subtitle', '')}" if r.get("subtitle") else "")
                for r in results
                if r.get("title")
            ]

        return _call_async_in_thread(_search(), timeout=5.0)
    except Exception as e:
        logger.debug("observation_store recall error: %s", e)
        return []


# ── Layer 5: graphrag (direct keyword search — no LLM, no SDK) ─────────────


def _recall_from_graphrag(query: str, limit: int = 3) -> list[str]:
    """Query wiki text_units via direct keyword overlap — no LLM call needed."""
    try:
        from core.integrations.graphrag_integration import _keyword_search_text_units
        return _keyword_search_text_units(query=query, limit=limit)
    except Exception as e:
        logger.debug("graphrag recall error: %s", e)
        return []


# ── Layer 6: mem0 cloud ───────────────────────────────────────────────────────


def _recall_from_mem0_cloud(query: str, top_k: int = 3) -> list[str]:
    """Search mem0 cloud via litellm proxy (fallback to legacy search)."""
    try:
        import asyncio as _asyncio
        from tools.mem0_client import mem0_search

        async def _search():
            results = await mem0_search(user_id="bashara", query=query, limit=top_k)
            return [
                f"[mem0:{r.get('metadata', {}).get('source', '?')}] {r.get('memory', r.get('content', ''))}"
                for r in results
                if r.get("memory") or r.get("content")
            ]

        return _call_async_in_thread(_search(), timeout=5.0)
    except Exception as e:
        logger.debug("mem0 cloud recall error: %s", e)
        return []

# ── Public API ────────────────────────────────────────────────────────────────

def build_memory_context(query: str, user_id: str = "bashara", project_dir: str | None = None, timeout: float = 8.0) -> str:
    """
    Query all 6 layers and return a formatted context block.
    Writes result to .session_state/recalled_context.md for OpenCode to pick up.

    Args:
        query: Semantic search query
        user_id: User identifier
        project_dir: Project root (uses cwd fallback for backward compat)
        timeout: Hard timeout for entire build (default 8s) — prevents one slow
                 layer (e.g., Ollama unreachable) from blocking the whole context.
    """
    session_dir = _get_session_dir(project_dir)
    recalled_file = session_dir / "recalled_context.md"

    # Individual layer timeouts — each must respect its own budget so the total
    # stays under the overall timeout. Layers are called sequentially (sync API)
    # so we use short per-layer limits to leave room for all 6.
    # L1/L4/L5 are fast (no network); L2/L3/L6 need caution when Ollama is down.
    _LAYER_TIMEOUT = {
        "_recall_from_checkpoints": 2.0,
        "_recall_from_mem0": 2.0,        # Ollama fallback adds ~4s when unreachable
        "_recall_from_langmem": 2.0,     # may import langmem + run search
        "_recall_from_observation_store": 2.0,
        "_recall_from_graphrag": 3.0,     # wiki search (LLM-free)
        "_recall_from_mem0_cloud": 2.0,   # litellm proxy + legacy fallback
    }

    _timeout_start = time.time()
    def _remaining() -> float:
        return max(0.1, timeout - (time.time() - _timeout_start))

    def _layer_call(fn, *args, **kwargs):
        """Call a function with its own timeout budget, return None on timeout."""
        t = min(_LAYER_TIMEOUT.get(fn.__name__, 2.0), _remaining())
        if t < 0.1:
            return None
        try:
            return fn(*args, **kwargs)
        except Exception:
            return None

    l1 = _layer_call(_recall_from_checkpoints, query, project_dir=project_dir) or []
    l2 = _layer_call(_recall_from_mem0, query) or []
    l3 = _layer_call(_recall_from_langmem, query) or []
    l4 = _layer_call(_recall_from_observation_store, query) or []
    l5 = _layer_call(_recall_from_graphrag, query) or []
    l6 = _layer_call(_recall_from_mem0_cloud, query) or []

    layers_used = sum(1 for l in [l1, l2, l3, l4, l5, l6] if l)

    lines = [
        "━━━ RECALLED MEMORY (6-layer search) ━━━",
        f"Query: {query}",
        f"Layers with results: {layers_used}/6",
        "",
    ]

    if l1:
        lines.append("━━━ LAYER 1: Session Checkpoints ━━━")
        for item in l1[:3]:
            lines.append(f"  • {item}")
        lines.append("")

    if l2:
        lines.append("━━━ LAYER 2: mem0 (ChromaDB) ━━━")
        for i, mem in enumerate(l2, 1):
            lines.append(f"  {i}. {mem}")
        lines.append("")

    if l3:
        lines.append("━━━ LAYER 3: langmem ━━━")
        for mem in l3:
            lines.append(f"  • {mem}")
        lines.append("")

    if l4:
        lines.append("━━━ LAYER 4: observation_store ━━━")
        for mem in l4:
            lines.append(f"  • {mem}")
        lines.append("")

    if l5:
        lines.append("━━━ LAYER 5: graphrag (wiki) ━━━")
        for mem in l5:
            lines.append(f"  • {mem}")
        lines.append("")

    if l6:
        lines.append("━━━ LAYER 6: mem0 cloud ━━━")
        for mem in l6:
            lines.append(f"  • {mem}")
        lines.append("")

    if not any([l1, l2, l3, l4, l5, l6]):
        lines.append("(no memories found)")

    lines.append("━━━ END RECALL — treat as prior context ━━━")
    text = "\n".join(lines)

    # Write to .session_state/recalled_context.md for /memory command
    try:
        session_dir.mkdir(parents=True, exist_ok=True)
        with open(recalled_file, "w") as f:
            f.write(text)
        logger.debug("Wrote recalled context to %s", recalled_file)
    except Exception as e:
        logger.debug("Could not write recalled context: %s", e)

    return text


def read_recalled_context() -> str:
    """Read the last recalled context from file."""
    try:
        if RECALLED_CONTEXT_FILE.exists():
            return RECALLED_CONTEXT_FILE.read_text()
    except Exception:
        pass
    return ""