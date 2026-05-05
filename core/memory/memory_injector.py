"""
4-layer recall engine for infinite memory without compaction.

Layer 1 (highest priority): .session_state/checkpoints/
Layer 2: mem0 (ChromaDB + Ollama embedder)
Layer 3: langmem (SwarmBotMemoryManager)
Layer 4: graphrag (query_wiki_graph)

Usage:
    from core.memory.memory_injector import build_memory_context
    ctx = build_memory_context("what did we do with intent routing", user_id="bashara")
    # ctx is a string ready to inject into the system prompt
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ── Paths ───────────────────────────────────────────────────────────────────
SESSION_DIR = Path.cwd() / ".session_state"
CHECKPOINT_DIR = SESSION_DIR / "checkpoints"
RECALLED_CONTEXT_FILE = SESSION_DIR / "recalled_context.md"

# ── Layer 1: Checkpoints ─────────────────────────────────────────────────────

def _recall_from_checkpoints(query: str, top_k: int = 5) -> list[str]:
    """Search checkpoint files for query-relevant entries."""
    if not CHECKPOINT_DIR.exists():
        return []
    try:
        checkpoints = sorted(CHECKPOINT_DIR.glob("checkpoint_*.json"), reverse=True)
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

# ── Layer 3: langmem ──────────────────────────────────────────────────────────

def _recall_from_langmem(query: str, limit: int = 5) -> list[str]:
    """Search langmem (SwarmBotMemoryManager)."""
    try:
        from core.integrations.langmem_integration import SwarmBotMemoryManager
        mgr = SwarmBotMemoryManager()
        results = mgr.search_memories(query, limit=limit)
        if isinstance(results, list):
            return [str(r) for r in results if len(str(r)) > 20]
        return []
    except Exception as e:
        logger.debug("langmem recall error: %s", e)
        return []

# ── Layer 4: graphrag ────────────────────────────────────────────────────────

def _recall_from_graphrag(query: str, limit: int = 3) -> list[str]:
    """Query wiki graph for structured knowledge."""
    try:
        from core.integrations.graphrag_integration import query_wiki_graph
        result = query_wiki_graph(query, mode="global", limit=limit)
        if result:
            if isinstance(result, list):
                return [str(r) for r in result if len(str(r)) > 20]
            return [str(result)]
        return []
    except Exception as e:
        logger.debug("graphrag recall error: %s", e)
        return []

# ── Public API ────────────────────────────────────────────────────────────────

def build_memory_context(query: str, user_id: str = "bashara") -> str:
    """
    Query all 4 layers and return a formatted context block.
    Writes result to .session_state/recalled_context.md for OpenCode to pick up.
    """
    l1 = _recall_from_checkpoints(query)
    l2 = _recall_from_mem0(query)
    l3 = _recall_from_langmem(query)
    l4 = _recall_from_graphrag(query)

    layers_used = sum(1 for l in [l1, l2, l3, l4] if l)

    lines = [
        "━━━ RECALLED MEMORY (4-layer search) ━━━",
        f"Query: {query}",
        f"Layers with results: {layers_used}/4",
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
        lines.append("━━━ LAYER 4: graphrag (wiki) ━━━")
        for mem in l4:
            lines.append(f"  • {mem}")
        lines.append("")

    if not any([l1, l2, l3, l4]):
        lines.append("(no memories found)")

    lines.append("━━━ END RECALL — treat as prior context ━━━")
    text = "\n".join(lines)

    # Write to .session_state/recalled_context.md for /memory command
    try:
        SESSION_DIR.mkdir(parents=True, exist_ok=True)
        with open(RECALLED_CONTEXT_FILE, "w") as f:
            f.write(text)
        logger.debug("Wrote recalled context to %s", RECALLED_CONTEXT_FILE)
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