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

# ── Query expansion: semantic anchors (no LLM needed) ─────────────────────────
#
# Strategy: N-gram matching against project keywords, not just single words.
# Also expand "what did we do / what happened / history" → session history patterns
# And "what's next / todo / remaining" → active task patterns.
#
# Key insight: the _QUERY_EXPANSION dictionary below gets parsed character-by-
# character in _expand_query. Keys with spaces (e.g. "what did we") fire first.
# Order matters: more specific keys before general ones.

_QUERY_EXPANSION = {
    # Session / history queries → checkpoint + mem0 heavy
    "what did we":   ["session", "history", "progress", "checkpoint", "last work", "recent", "yesterday"],
    "what happened": ["session", "history", "events", "progress", "changes", "decisions"],
    "show me":        ["session", "history", "checkpoint", "context", "recall"],
    "status":        ["progress", "checkpoint", "todo", "pending", "current", "state"],
    "progress":      ["checkpoint", "session", "todo", "pending", "completed"],
    "history":        ["session", "checkpoint", "past", "previous", "earlier"],

    # Task / planning queries → symphony heavy
    "next":          ["todo", "remaining", "pending", "plan", "upcoming", "will do"],
    "todo":          ["task", "issue", "ticket", "pending", "remaining", "plan"],
    "remaining":     ["todo", "task", "pending", "not done", "incomplete"],
    "pending":       ["todo", "task", "not done", "waiting", "in progress"],

    # Implementation queries → gitnexus + checkpoints heavy
    "project":       ["code", "implementation", "feature", "task", "agent", "workflow", "architecture"],
    "implementation":["code", "function", "class", "module", "api", "structure"],
    "feature":       ["code", "implementation", "task", "handler", "workflow"],
    "refactor":      ["code", "architecture", "restructure", "improve", "design"],
    "api":           ["endpoint", "route", "handler", "request", "response", "http"],

    # Error / debugging queries → observation + checkpoints heavy
    "bug":           ["error", "fix", "crash", "debug", "exception", "traceback", "issue"],
    "fix":           ["bug", "error", "patch", "debug", "repair", "resolve"],
    "error":         ["exception", "crash", "bug", "failure", "traceback", "issue"],
    "crash":         ["error", "exception", "traceback", "bug", "failure"],
    "debug":         ["error", "traceback", "investigation", "root cause", "diagnose"],

    # Code queries → gitnexus heavy
    "code":          ["implementation", "function", "class", "module", "api", "file"],
    "function":      ["code", "implementation", "method", "class", "module"],
    "class":         ["code", "implementation", "method", "function", "structure"],
    "module":        ["code", "implementation", "file", "import", "structure"],

    # Testing queries
    "test":          ["pytest", "testing", "spec", "verification", "qa", "coverage"],
    "testing":       ["pytest", "test", "spec", "verification", "qa", "validate"],

    # Deployment / config
    "deploy":        ["deployment", "production", "release", "pipeline", "ci", "staging"],
    "config":        ["settings", "env", "yaml", "json", "options", "arguments"],

    # Design / architecture
    "design":        ["architecture", "schema", "pattern", "structure", "diagram"],
    "architecture":   ["design", "pattern", "schema", "structure", "component"],
    "pattern":       ["design", "architecture", "implementation", "best practice"],

    # Review / feedback
    "review":        ["feedback", "critique", "audit", "analysis", "assessment"],
    "feedback":      ["review", "critique", "comment", "suggestion", "improve"],

    # Wiki / docs
    "wiki":          ["documentation", "knowledge", "note", "reference", "docs"],
    "documentation": ["wiki", "note", "docs", "reference", "knowledge", "guide"],

    # Agent / swarm
    "agent":         ["worker", "task", "swarm", "orchestration", "llm", "prompt"],
    "swarm":         ["multi-agent", "coordination", "parallel", "orchestration", "agent"],
    "worker":       ["agent", "task", "swarm", "execute", "run"],
    "orchestrat":    ["swarm", "agent", "coordination", "multi-agent", "workflow"],

    # Memory / context
    "memory":        ["context", "recall", "persistence", "store", "remember", "history"],
    "context":       ["memory", "recall", "session", "history", "background"],
    "remember":      ["memory", "context", "recall", "persistence", "store"],
}

# Project-specific anchors (detected from cwd)
_PROJECT_ANCHORS = {
    "rumahlabuh":    ["boarding", "rental", "kos", "kost", "room", "booking", "tenant", "property"],
    "cekwajar":      ["salary", "pajak", "gaji", "tax", "pph", "ptkp", "bpjs", "payroll"],
    "swarm-bot":     ["agent", "telegram", "handler", "mcp", "orchestration", "telegram-bot"],
    "industreal":    ["popw", "pose", "action", "recognition", "activity", "detection"],
}


def _expand_query(query: str) -> str:
    """Expand queries using semantic anchor matching — no LLM needed.

    Strategy:
    1. Check exact phrases first (e.g. "what did we", "what happened")
    2. Check substring anchors (e.g. "buggy" → bug, "testing" → test)
    3. Apply project-specific terms if cwd matches known project
    4. For short queries (≤2 words) add generic implementation terms
    """
    q = query.lower().strip()
    if not q:
        return query

    # Sort keys by length descending so "what did we" matches before "what"
    sorted_anchors = sorted(_QUERY_EXPANSION.keys(), key=len, reverse=True)

    # 1. Exact phrase match
    for anchor in sorted_anchors:
        if q.startswith(anchor) or f" {anchor} " in f" {q} ":
            extras = _QUERY_EXPANSION[anchor]
            return f"{q} {' '.join(extras[:5])}"

    # 2. Substring anchor match (handles "buggy" → "bug", "testing" → "test")
    for anchor in sorted_anchors:
        if anchor in q:
            extras = _QUERY_EXPANSION[anchor]
            return f"{q} {' '.join(extras[:4])}"

    # 3. Project-specific expansion from cwd
    try:
        cwd = Path.cwd().name
        if project_terms := _PROJECT_ANCHORS.get(cwd):
            return f"{q} {' '.join(project_terms[:4])}"
    except Exception:
        pass

    # 4. Short generic queries get broad coverage terms
    words = q.split()
    if len(words) <= 2:
        return f"{q} project implementation code task feature"

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
    global _mcp_loop, _mcp_loop_thread, _mcp_work_queue
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    _mcp_loop = loop
    _mcp_loop_ready.set()

    async def _run_coroutine(coro, future, timeout) -> None:
        """Run one coroutine with timeout, set future result in this thread."""
        try:
            res = await asyncio.wait_for(coro, timeout=timeout)
            future.set_result(res)
        except (asyncio.TimeoutError, asyncio.CancelledError):
            future.set_result([])
        except BaseException as e:  # catches GeneratorExit, BaseExceptionGroup from anyio bug
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
        loop.create_task(_run_coroutine(coro, future, timeout))

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
            loop.create_task(_run_coroutine(coro, future, timeout))
        finally:
            # Re-schedule ourselves
            loop.call_later(0.05, poll_queue)

    poll_queue()
    loop.run_forever()
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
    try:
        return future.result(timeout=timeout + 3.0)
    except Exception:
        # GeneratorExit / BaseExceptionGroup from anyio bug in Python 3.13 — return []
        return []


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
    """Keyword overlap score 0..1. Uses bigram matching for better context."""
    if not query or not text:
        return 0.0
    q_words = set(query.lower().split())
    t_words = set(text.lower().split())
    if not q_words:
        return 0.0
    # Single word match
    direct = sum(1 for w in q_words if w in t_words) / len(q_words)
    # Bigram overlap (pairs of adjacent words in query)
    q_bigrams = {f"{a}_{b}" for a, b in zip(query.lower().split(), query.lower().split()[1:])}
    t_bigrams = {f"{a}_{b}" for a, b in zip(text.lower().split(), text.lower().split()[1:])}
    bigram_score = len(q_bigrams & t_bigrams) / len(q_bigrams) if q_bigrams else 0.0
    return 0.6 * direct + 0.4 * bigram_score


# ── Query Intent Classification ───────────────────────────────────────────────
#
# Before searching, classify WHAT KIND of memory the user wants.
# Each intent type gets a specialized search strategy, layer weighting,
# and output format — instead of generic keyword-overlap scoring.

_QUERY_INTENT_PATTERNS = {
    "session_summary": {
        "keywords": ["what did we", "what happened", "session", "history", "progress", "recent", "yesterday", "last time", "ago"],
        "primary_layers": ["checkpoints", "mem0", "observation"],
        "boost_decisions": True,
        "max_fresh_hours": 24,
    },
    "task_list": {
        "keywords": ["todo", "task", "next", "remaining", "pending", "upcoming", "will do", "plan to", "need to"],
        "primary_layers": ["symphony_tasks", "checkpoints"],
        "boost_decisions": False,
        "max_fresh_hours": 72,
    },
    "decision_recovery": {
        "keywords": ["decided", "choice", "instead of", "went with", "opted", "rejected", "why did we", "why not", "what was the decision", "agreed to"],
        "primary_layers": ["observation", "checkpoints", "graphrag"],
        "boost_decisions": True,
        "max_fresh_hours": 168,   # decisions stay relevant for a week
    },
    "code_implementation": {
        "keywords": ["code", "function", "class", "implement", "how does", "where is", "find", "search for", "file"],
        "primary_layers": ["gitnexus_mcp", "checkpoints"],
        "boost_decisions": False,
        "max_fresh_hours": 720,
    },
    "entity_facts": {
        "keywords": ["what is", "who is", "define", "explain", "tell me about", "learned", "remember about", "know about"],
        "primary_layers": ["graphrag", "obsidian_mcp", "mem0"],
        "boost_decisions": False,
        "max_fresh_hours": 720,
    },
    "bug_investigation": {
        "keywords": ["bug", "error", "crash", "fail", "broken", "issue", "problem", "not working", "wrong"],
        "primary_layers": ["observation", "checkpoints"],
        "boost_decisions": False,
        "max_fresh_hours": 72,
    },
    "architecture_design": {
        "keywords": ["architecture", "design", "pattern", "schema", "structure", "approach", "why did we choose", "tradeoff"],
        "primary_layers": ["graphrag", "gitnexus_mcp"],
        "boost_decisions": True,
        "max_fresh_hours": 720,
    },
    "wiki_docs": {
        "keywords": ["wiki", "documentation", "docs", "note", "knowledge", "reference", "readme"],
        "primary_layers": ["graphrag", "obsidian_mcp"],
        "boost_decisions": False,
        "max_fresh_hours": 720,
    },
}


def _classify_intent(query: str) -> str:
    """Classify query into one of 8 intent types, falling back to 'general'."""
    q = query.lower()
    best_type = "general"
    best_hits = 0
    for intent_type, config in _QUERY_INTENT_PATTERNS.items():
        hits = sum(1 for kw in config["keywords"] if kw in q)
        if hits > best_hits:
            best_hits = hits
            best_type = intent_type
    return best_type


# ── Temporal Decay — layer-specific half-life curves ────────────────────────────
#
# Different layers have different freshness profiles:
#   checkpoints: very short half-life (session-level, changes hourly)
#   observation: short half-life (today vs last week matters a lot)
#   graphrag: long half-life (wiki/docs don't go stale fast)
#   gitnexus: very long half-life (code structure is stable)
#
# Uses exponential decay: score *= base_rate ** (hours_since / half_life_hours)
# Half-life = hours until the base_rate decay factor reaches 0.5

_LAYER_HALF_LIFE_HOURS: dict[str, float] = {
    "checkpoints":      4.0,   # very fresh, changes hourly
    "mem0":            12.0,   # live memory, relevant for a session
    "langmem":          24.0,   # conversation-level context
    "observation":      48.0,   # observations decay after 2 days
    "graphrag":        336.0,  # wiki pages stable for 2 weeks
    "obsidian_mcp":    168.0,  # personal notes stable for 1 week
    "gitnexus_mcp":   1440.0,  # code graph extremely stable
    "ruflo_mcp":        72.0,   # learned patterns
    "symphony_tasks":   24.0,   # tasks are ephemeral
    "mem0_cloud":       24.0,   # cloud memory
}

_DECAY_BASE_RATE = 0.85  # base decay factor; lower = faster decay


def _temporal_decay(layer: str, confidence: float, text: str | None = None) -> float:
    """Apply exponential temporal decay based on layer half-life.

    The returned score = confidence * (_DECAY_BASE_RATE ** (hours / half_life)).
    If text is provided, also parse embedded ISO timestamps for more accurate decay.
    """
    import datetime
    half_life = _LAYER_HALF_LIFE_HOURS.get(layer, 120.0)
    now = datetime.datetime.now()
    effective_hours = 0.0

    if text:
        date_patterns = [
            (r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", "%Y-%m-%dT%H:%M:%S"),
            (r"\d{4}-\d{2}-\d{2}", "%Y-%m-%d"),
        ]
        for pattern, fmt in date_patterns:
            import re as _re
            for match in _re.finditer(pattern, text):
                try:
                    ts = datetime.datetime.strptime(match.group(), fmt)
                    effective_hours = max(effective_hours, (now - ts).total_seconds() / 3600)
                except Exception:
                    continue

    # If no timestamp found in text, use a small default age to apply some decay
    # on unnamed layers (they might still be stale)
    if effective_hours == 0.0:
        effective_hours = half_life * 0.5  # assume half-life by default

    decay_factor = _DECAY_BASE_RATE ** (effective_hours / half_life)
    return confidence * decay_factor


def _recency_boost(text: str, layer: str) -> float:
    """Boost recent content. Checks timestamps in content vs current time."""
    import datetime
    now = datetime.datetime.now()
    # Look for ISO timestamps in text (e.g. "2026-05-23", "2026-05-22T10:30")
    date_patterns = [
        (r"\d{4}-\d{2}-\d{2}", "%Y-%m-%d"),
        (r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", "%Y-%m-%dT%H:%M:%S"),
    ]
    for pattern, fmt in date_patterns:
        import re as _re
        for match in _re.finditer(pattern, text):
            try:
                ts = datetime.datetime.strptime(match.group(), fmt)
                age_hours = (now - ts).total_seconds() / 3600
                if age_hours < 1:
                    return 0.15   # < 1 hour old
                elif age_hours < 6:
                    return 0.10   # < 6 hours
                elif age_hours < 24:
                    return 0.05   # < 24 hours
            except Exception:
                continue
    # Layer-specific defaults (layers with fresher data get small boost)
    layer_boost = {
        "checkpoints": 0.03,   # checkpoints are always recent
        "mem0": 0.02,
        "observation": 0.01,
        "graphrag": -0.01,      # wiki is often old
        "obsidian_mcp": 0.01,
        "gitnexus_mcp": -0.01,
    }
    return layer_boost.get(layer, 0.0)


def _cross_layer_boost(results: list[MemoryResult]) -> dict[str, float]:
    """Triangulation: content appearing in multiple layers gets boosted.

    Returns a dict mapping fingerprint → boost multiplier (1.0 = no change,
    1.3 = same content found in 2 layers, 1.5 = in 3+ layers).
    """
    from collections import Counter
    fp_counts: Counter[str] = Counter()
    for r in results:
        fp_counts[r.fp] += 1
    boosts = {}
    for fp, count in fp_counts.items():
        if count >= 3:
            boosts[fp] = 1.5
        elif count == 2:
            boosts[fp] = 1.3
        else:
            boosts[fp] = 1.0
    return boosts


def _query_relevance_boost(query: str, layer: str) -> float:
    """Query-specific layer relevance boost — certain queries map to specific layers."""
    q = query.lower()
    # History / session queries → checkpoints + mem0
    if any(k in q for k in ["what did we", "what happened", "history", "session", "recent", "yesterday"]):
        if layer == "checkpoints": return 0.4
        if layer == "mem0": return 0.25
        if layer == "langmem": return 0.15
    # Bug / error queries → observation + checkpoints
    if any(k in q for k in ["bug", "error", "crash", "debug", "traceback", "issue"]):
        if layer == "observation": return 0.35
        if layer == "checkpoints": return 0.2
        if layer == "mem0": return 0.1
    # Task / todo / remaining → symphony + checkpoints
    if any(k in q for k in ["todo", "task", "next", "remaining", "pending", "plan", "upcoming"]):
        if layer == "symphony_tasks": return 0.4
        if layer == "checkpoints": return 0.15
        if layer == "mem0": return 0.1
    # Code / implementation / function → gitnexus
    if any(k in q for k in ["code", "function", "class", "implementation", "api", "module", "file"]):
        if layer == "gitnexus_mcp": return 0.4
        if layer == "checkpoints": return 0.1
    # Wiki / documentation → graphrag + obsidian
    if any(k in q for k in ["wiki", "documentation", "docs", "note", "knowledge"]):
        if layer == "graphrag": return 0.35
        if layer == "obsidian_mcp": return 0.3
    # Memory / context / remember → mem0 + langmem
    if any(k in q for k in ["memory", "context", "remember", "recall"]):
        if layer == "mem0": return 0.35
        if layer == "langmem": return 0.25
        if layer == "ruflo_mcp": return 0.2
    # Architecture / design / pattern → graphrag + gitnexus
    if any(k in q for k in ["architecture", "design", "pattern", "schema", "structure"]):
        if layer == "graphrag": return 0.3
        if layer == "gitnexus_mcp": return 0.25
    # Deploy / config / settings → checkpoints + graphrag
    if any(k in q for k in ["deploy", "config", "settings", "env", "yaml"]):
        if layer == "checkpoints": return 0.25
        if layer == "graphrag": return 0.15
    return 0.0


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


def _parse_json_array_robust(raw: str) -> list[dict]:
    """Parse a potentially truncated JSON array, returning only complete items.

    obsidian's search_notes truncates at 12000 chars via _tool_result_to_text,
    which cuts through string literals and escape sequences. This function
    finds the last complete item boundary in the array and returns everything
    up to and including that item.

    Strategy: scan from the end using a while loop (NOT for-range, since we need
    to modify the index while iterating), track nesting depth, reset when we
    find a complete top-level object.
    """
    n = len(raw)
    if n == 0:
        return []
    depth = 0
    in_string = False
    complete_boundaries: list[int] = []
    i = n - 1
    while i >= 0:
        c = raw[i]
        if in_string:
            if c == '\\':
                i -= 2  # skip escaped character, stay in string
                continue
            elif c == '"':
                in_string = False
        else:
            if c == '"':
                in_string = True
            elif c == '}':
                depth += 1
            elif c == '{':
                depth -= 1
                if depth == 0:
                    # Found a complete top-level object
                    complete_boundaries.append(i)
        i -= 1

    if not complete_boundaries:
        return []

    # Parse from the start of the first complete object to the end of the last
    first_boundary = complete_boundaries[0]
    last_boundary = complete_boundaries[-1]

    # Find the opening '[' of the array
    bracket_idx = raw.find('[', first_boundary)
    if bracket_idx < 0:
        return []

    # Parse up to the end of the last complete object
    # Use raw[bracket_idx:last_boundary+1] which is the array with complete items only
    try:
        result = json.loads(raw[bracket_idx:last_boundary + 1])
        if isinstance(result, list):
            return result
        return [result]
    except Exception:
        pass

    # Fallback: try each boundary independently
    for boundary in reversed(complete_boundaries):
        bracket_idx2 = raw.find('[', boundary)
        if bracket_idx2 < 0:
            continue
        try:
            result = json.loads(raw[bracket_idx2:boundary + 1])
            if isinstance(result, list):
                return result
            return [result]
        except Exception:
            continue

    return []


def _safe_truncate_json(raw: str, max_chars: int = 12000) -> str:
    """Truncate string at max_chars, then walk back to nearest JSON boundary.

    obsidian's search_notes returns a large JSON array that frequently gets
    truncated mid-escape-sequence (e.g. ...\'\\n...), making it unparseable.
    Walking back to the last ']' or '}' before max_chars gives valid JSON
    (even if the array is incomplete — _safe_json handles that).
    """
    if len(raw) <= max_chars:
        return raw
    # Find last complete JSON structural char within the last 200 chars
    search_start = max(0, max_chars - 200)
    for i in range(max_chars - 1, search_start, -1):
        c = raw[i]
        if c in ('}', ']') and i > 0 and raw[i - 1] not in ('\\', "'", '"', '\\n', '\\t'):
            return raw[:i + 1]
    return raw[:max_chars]


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
        # Filter obsidian's stderr injection
        cleaned = _filter_obsidian_text(str(raw))
        # Truncate at JSON boundary to avoid partial escape sequences
        truncated = _safe_truncate_json(cleaned, max_chars=12000)
        items = _safe_json(truncated)
        if not items:
            # Truncated JSON — fall back to walking backward for complete items
            items = _parse_json_array_robust(truncated)
        if not items:
            brk.record_failure()
            return []
        if not isinstance(items, list):
            items = [items]
        results = []
        for item in items[:limit]:
            if not isinstance(item, dict):
                continue
            # Obsidian returns title + preview + content. Build a safe content field.
            # Some previews may be truncated mid-escape (e.g. ...\'\\n...), causing
            # _safe_json to return a partial list with some None items — skip None.
            if item is None:
                continue
            fn = item.get("filename", "note") or "note"
            title = item.get("title", "") or ""
            preview = item.get("preview", "") or ""
            content = item.get("content", "") or preview or title
            if content:
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
    10-Layer Recall Engine with intent-driven ranking.

    Query flow:
      1. Classify intent (8 types: session_summary, task_list, decision_recovery,
         code_implementation, entity_facts, bug_investigation, architecture_design, wiki_docs)
      2. Fire all 10 layers concurrently via thread pool
      3. Score each result with:
         - base_confidence = layer_priority_weight * 0.7 + keyword_score * 0.3
         - intent_boost   = intent-driven layer weighting (per intent type)
         - recency_boost  = timestamp-parsing small boost (existing)
         - temporal_decay = exponential decay by layer half-life (hours)
      4. Cross-layer triangulation boost (content in 3+ layers → 1.5x, 2 → 1.3x)
      5. Sort by boosted_confidence descending, take top N
      6. Build 3-tier output:
         - Tier 1 (index):   compact lines — fingerprint + layer + score + 1-line summary
         - Tier 2 (context): medium blocks — first 200 chars of each result
         - Tier 3 (detail): full content for decisions + top 2 results by score

    Writes result to .session_state/recalled_context.md for /memory command.
    """
    from core.memory.memory_injector import _get_session_dir, _get_recalled_file
    session_dir = _get_session_dir(project_dir)
    recalled_file = _get_recalled_file(project_dir)

    t0 = time.monotonic()

    # ── Step 1: Intent classification ─────────────────────────────────────────
    intent_type = _classify_intent(query)
    intent_config = _QUERY_INTENT_PATTERNS.get(intent_type, {})
    intent_label = {
        "session_summary":     "📋  Session Summary",
        "task_list":           "✅  Task List",
        "decision_recovery":    "⚖️   Decision Recovery",
        "code_implementation": "💻  Code Implementation",
        "entity_facts":        "🔖  Entity Facts",
        "bug_investigation":   "🐛  Bug Investigation",
        "architecture_design": "🏗️  Architecture/Design",
        "wiki_docs":           "📚  Wiki/Docs",
        "general":             "🧠  General",
    }.get(intent_type, intent_type)

    # Expand short queries for better layer coverage
    expanded_query = _expand_query(query)

    # ── Step 2: Fire all 10 layers concurrently ─────────────────────────────────
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

    # ── Step 3: Collect results ─────────────────────────────────────────────────
    all_results: list[MemoryResult] = []
    seen_fps: set[str] = set()
    layer_timings: dict[str, float] = {}

    try:
        for name, future in futures.items():
            lt0 = time.monotonic()
            try:
                results: list[MemoryResult] = future.result(timeout=timeout)
                layer_timings[name] = time.monotonic() - lt0
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

    # ── Step 4: Score each result with multi-factor boosting ───────────────────
    #
    # boosted_confidence = base_confidence
    #                     + _query_relevance_boost(query, layer)
    #                     + _recency_boost(content, layer)
    #                     + (1.0 if decision_tagged else 0.0)   # decision recovery
    #
    # Then apply temporal_decay and cross_layer_boost:

    cross_boosts = _cross_layer_boost(all_results)  # fp → multiplier

    scored: list[tuple[MemoryResult, float]] = []
    for r in all_results:
        base_conf = r.confidence
        intent_boost_val = _query_relevance_boost(query, r.layer) if intent_config else 0.0
        recency_boost_val = _recency_boost(r.content, r.layer)

        # Decision recovery: if query is about decisions AND result has decision signals
        decision_boost = 0.0
        if intent_type == "decision_recovery":
            decision_keywords = ["decided", "choosing", "instead of", "went with", "opted", "rejected", "agreed", "decision"]
            if any(kw in r.content.lower() for kw in decision_keywords):
                decision_boost = 2.0  # big boost for decision-tagged content

        raw_score = base_conf + intent_boost_val + recency_boost_val + decision_boost

        # Apply temporal decay
        decayed_score = _temporal_decay(r.layer, raw_score, r.content)

        # Apply cross-layer triangulation boost
        triangulation_mult = cross_boosts.get(r.fp, 1.0)
        final_score = decayed_score * triangulation_mult

        scored.append((r, final_score))

    # ── Step 5: Sort and take top N ─────────────────────────────────────────────
    scored.sort(key=lambda x: x[1], reverse=True)
    top_results = [r for r, _ in scored[:top_n]]

    # ── Step 6: Build 3-tier progressive output ───────────────────────────────────
    layers_with_results = {r.layer for r in top_results}

    # Intent-aware header
    lines = [
        f"━━━ MEMORY CONTEXT ━━━  intent: {intent_label}  query: «{query}»",
        f"   layers: {len(layers_with_results)}/10  results: {len(top_results)}  time: {total_time:.2f}s ━━━",
        "",
    ]

    if not top_results:
        lines.append("(no memories found)")
        lines.append("━━━ END MEMORY CONTEXT ━━━")
        text = "\n".join(lines)
        try:
            recalled_file.write_text(text)
        except Exception:
            pass
        return text

    # ── Tier 1: Index — compact single lines for overview ──────────────────────
    lines.append("━━ INDEX ━━")
    for r, score in scored[:top_n]:
        age_label = ""
        if "2026-05" in r.content or "2025-05" in r.content:
            age_label = " [recent]"
        layer_emoji = {
            "checkpoints": "📌", "mem0": "🧠", "langmem": "🔗",
            "observation": "📝", "graphrag": "📚", "obsidian_mcp": "🏛️",
            "gitnexus_mcp": "🔍", "ruflo_mcp": "🧬", "symphony_tasks": "✅",
            "mem0_cloud": "☁️",
        }.get(r.layer, "•")
        snippet = r.content.replace("\n", " ")[:100]
        lines.append(f"  {layer_emoji} [{score:.2f}]{age_label}  {snippet}")
    lines.append("")

    # ── Tier 2: Context blocks — medium detail ──────────────────────────────────
    lines.append("━━ CONTEXT ━━")
    from collections import defaultdict
    by_layer: dict[str, list[MemoryResult]] = defaultdict(list)
    for r in top_results:
        by_layer[r.layer].append(r)

    # Build score lookup: result fp → boosted score (for label display)
    scored_fps: dict[str, float] = {r.fp: s for r, s in scored}

    layer_labels_short = {
        "checkpoints":    "📌 L1 Checkpoints",
        "mem0":           "🧠 L2 mem0",
        "langmem":        "🔗 L3 langmem",
        "observation":    "📝 L4 observation",
        "graphrag":       "📚 L5 graphrag",
        "obsidian_mcp":   "🏛️ L6 obsidian",
        "gitnexus_mcp":   "🔍 L7 gitnexus",
        "ruflo_mcp":      "🧬 L8 ruflo",
        "symphony_tasks": "✅ L9 symphony",
        "mem0_cloud":     "☁️ L10 mem0-cloud",
    }

    for layer_name, results in by_layer.items():
        label = layer_labels_short.get(layer_name, layer_name)
        first_fp = results[0].fp
        score = scored_fps.get(first_fp, results[0].confidence)
        lines.append(f"  {label}  (score={score:.2f})  [{len(results)} result{'s' if len(results)>1 else ''}]")
        for r in results:
            content_block = r.content.replace("\n", " ")[:200]
            lines.append(f"    • {content_block}")
        lines.append("")

    # ── Tier 3: Decisions + top full detail ─────────────────────────────────────
    decision_results = [r for r in top_results if any(
        kw in r.content.lower() for kw in ["decided", "choosing", "opted", "agreed", "decision"]
    )]
    if decision_results or (intent_type == "decision_recovery" and top_results):
        lines.append("━━ DECISIONS ━━")
        for r in decision_results[:5]:
            lines.append(f"  ⚖️  {r.content[:500]}")
        if not decision_results:
            lines.append("  (no explicit decisions found)")
        lines.append("")

    # Top-2 full detail for everything else
    lines.append("━━ DETAIL ━━")
    for r, score in scored[:2]:
        lines.append(f"  [{score:.2f}] {r.content[:500]}")
        lines.append("")

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
