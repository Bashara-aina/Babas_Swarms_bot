"""
core/memory/autoinject.py — Persistent memory auto-inject for OpenCode sessions.

Builds a rich, always-on memory context block from all 6 layers and injects it
into the OpenCode system prompt at session start. Uses the full 62GB RAM
available to keep the context warm and extensive.

Layers:
  L1: CoreMemory (always-on key-value, 200KB cap)
  L2: RecallMemory (recent 500 conversation turns)
  L3: ArchivalMemory (FTS5 search over all saved memories)
  L4: MemoryStore (ChromaDB semantic recall, top_k=50)
  L5: Session checkpoints (latest session state)
  L6: User profile + emotion state

Usage:
  from core.memory.autoinject import build_persistent_context, inject_into_opencode
  ctx = build_persistent_context(user_id="bashara")
  inject_into_opencode(ctx)
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Paths — use project_dir when provided, fallback to cwd for backward compat
def _session_dir(project_dir: str | None = None) -> Path:
    if project_dir:
        return Path(project_dir) / ".session_state"
    return Path.cwd() / ".session_state"


def _wiki_dir(project_dir: str | None = None) -> Path:
    if project_dir:
        return Path(project_dir) / ".wiki"
    return Path.cwd() / ".wiki"


SESSION_DIR = Path.cwd() / ".session_state"
MEMORY_CONTEXT_FILE = SESSION_DIR / "persistent_memory_context.md"
OPENCODE_INJECT_FILE = SESSION_DIR / "memory_inject.md"

WIKI_VAULT_PATH = Path.home() / "swarm-bot" / ".wiki"

# ── Layer 1: CoreMemory (always-on key-value) ─────────────────────────────────


def _load_core_memory() -> str:
    """Load core memory as a prompt block."""
    try:
        from core.memory.tiers import CoreMemory

        core = CoreMemory()
        return core.to_prompt_block()
    except Exception as e:
        logger.debug("CoreMemory load error: %s", e)
        return ""


# ── Layer 2: RecallMemory (recent turns) ───────────────────────────────────────


def _load_recent_turns(n: int = 50) -> str:
    """Load recent conversation turns."""
    try:
        from core.memory.tiers import RecallMemory

        async def _get():
            r = RecallMemory()
            await r._ensure_connection()
            await r._init_db()
            return await r.get_recent(n=n)

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _get())
                turns = future.result(timeout=10)
        else:
            turns = asyncio.run(_get())

        if not turns:
            return ""

        lines = ["[RECENT CONVERSATION TURNS]"]
        for turn in turns[-30:]:
            ts = str(turn.get("timestamp", ""))[:16]
            role = str(turn.get("role", "?"))
            content = str(turn.get("content", ""))[:300]
            lines.append(f"  [{ts}] {role}: {content}")
        return "\n".join(lines)
    except Exception as e:
        logger.debug("RecallMemory load error: %s", e)
        return ""


# ── Layer 3: ArchivalMemory (FTS5 search) ──────────────────────────────────────


def _load_archival(query: str = "", limit: int = 20) -> str:
    """Load from ArchivalMemory (FTS5 searchable)."""
    try:
        from core.memory.tiers import ArchivalMemory

        async def _search():
            a = ArchivalMemory()
            await a._ensure_connection()
            await a._init_db()
            q = query or "project code AI agent memory"
            return await a.search(q, limit=limit)

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _search())
                results = future.result(timeout=10)
        else:
            results = asyncio.run(_search())

        if not results:
            return ""

        lines = ["[ARCHIVAL MEMORIES (important saved facts)]"]
        for r in results:
            content = str(r.get("content", ""))[:400]
            importance = r.get("importance", 0.5)
            # tags = r.get("tags", [])  # reserved for future tagging use
            created = str(r.get("created_at", ""))[:10]
            lines.append(f"  [{created}] [imp={importance:.1f}] {content}")
        return "\n".join(lines)
    except Exception as e:
        logger.debug("ArchivalMemory load error: %s", e)
        return ""


# ── Layer 4: MemoryStore (ChromaDB semantic) ───────────────────────────────────


def _load_mem0_context(query: str = "project work coding agent AI", top_k: int = 30) -> str:
    """Load from ChromaDB via MemoryStore with maxed-out retrieval."""
    try:
        from core.memory.store import MemoryStore, _get_collection

        # Get collection directly via module-level singleton
        col = _get_collection()
        total = col.count()
        if total == 0:
            logger.info("MemoryStore/ChromaDB: empty collection — Layer 4 returns empty")
            return ""

        store = MemoryStore()
        memories = store.recall(query=query, agent_id=None, top_k=top_k, min_score=0.15)
        if not memories:
            logger.debug("MemoryStore recall returned 0 results")
            return ""

        lines = [f"[LONG-TERM MEMORY (ChromaDB semantic recall, top {top_k})]"]
        for i, mem in enumerate(memories, 1):
            lines.append(f"  {i}. {mem}")
        return "\n".join(lines)
    except Exception as e:
        logger.warning("MemoryStore recall error: %s", e)
        return ""


# ── Layer 5: Session checkpoints ────────────────────────────────────────────────


def _load_session_checkpoint() -> str:
    """Load the most recent session checkpoint."""
    try:
        checkpoint_dir = SESSION_DIR / "checkpoints"
        if not checkpoint_dir.exists():
            return ""
        checkpoints = sorted(checkpoint_dir.glob("checkpoint_*.json"), reverse=True)
        if not checkpoints:
            return ""

        with open(checkpoints[0]) as f:
            data = json.load(f)

        lines = ["[LAST SESSION CHECKPOINT]"]
        for key in ["session_name", "phase", "task_summary", "last_query", "files_changed", "decisions"]:
            if data.get(key):
                val = data[key]
                if isinstance(val, list):
                    val = "; ".join(str(v) for v in val[:5])
                elif isinstance(val, dict):
                    val = json.dumps(val, default=str)[:200]
                lines.append(f"  {key}: {val}")
        return "\n".join(lines)
    except Exception as e:
        logger.debug("Checkpoint load error: %s", e)
        return ""


# ── Layer 6: User profile + patterns ───────────────────────────────────────────


def _load_user_profile() -> str:
    """Load user profile, preferences, and known facts."""
    try:
        from core.memory.user_profile import UserProfile

        p = UserProfile()
        return p.to_prompt_block()
    except Exception as e:
        logger.debug("UserProfile load error: %s", e)
        return ""


# ── Layer 7: Obsidian recent notes ─────────────────────────────────────────────


def _load_obsidian_recent(limit: int = 5) -> str:
    """Load most recently modified Obsidian notes."""
    try:
        vault = WIKI_VAULT_PATH
        if not vault.exists():
            return ""

        md_files = []
        for f in vault.rglob("*.md"):
            if f.is_file():
                md_files.append((f.stat().st_mtime, f))

        md_files.sort(reverse=True)
        lines = ["[RECENT OBSIDIAN NOTES]"]
        count = 0
        for mtime, f in md_files:
            if count >= limit:
                break
            try:
                content = f.read_text(encoding="utf-8")
                # Get first heading or first line
                first_line = content.split("\n")[0][:80]
                rel = f.relative_to(vault)
                date = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
                lines.append(f"  [{date}] {rel.name}: {first_line}")
                count += 1
            except Exception:
                continue
        return "\n".join(lines)
    except Exception as e:
        logger.debug("Obsidian load error: %s", e)
        return ""


# ── Unified build ─────────────────────────────────────────────────────────────


def build_persistent_context(
    query: str = "general work project coding AI",
    user_id: str = "bashara",
    include_layers: list[int] | None = None,
) -> str:
    """
    Build the full persistent memory context from all available layers.
    Writes to .session_state/persistent_memory_context.md and
    .session_state/memory_inject.md for OpenCode to pick up.

    Args:
        query: Semantic search query to anchor ChromaDB recall
        user_id: User identifier for profile lookup
        include_layers: Which layers to include (default all 1-7)

    Returns:
        Formatted memory context string
    """
    if include_layers is None:
        include_layers = list(range(1, 8))

    lines = [
        "╔════════════════════════════════════════════════════════════════╗",
        "║           PERSISTENT MEMORY — auto-injected at session start   ║",
        "║  All items below are confirmed prior context. Use as reliable. ║",
        "╚════════════════════════════════════════════════════════════════╝",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Query anchor: {query}",
        "",
    ]

    layer_names = {  # noqa: F841 — reserved for future layer visualization/debugging
        1: "CoreMemory (always-on key-value, 200KB cap)",
        2: "RecallMemory (recent 500 turns)",
        3: "ArchivalMemory (FTS5 full-text search)",
        4: "MemoryStore/ChromaDB (semantic, top_k=50, min_score=0.15)",
        5: "Session checkpoint (last session state)",
        6: "UserProfile (preferences, patterns, known facts)",
        7: "Obsidian vault (recent notes from .wiki/)",
    }

    layer_outputs = {}

    if 1 in include_layers:
        l1 = _load_core_memory()
        if l1:
            lines.append("━━━ LAYER 1: CoreMemory ━━━")
            lines.append(l1)
            lines.append("")
            layer_outputs[1] = True

    if 2 in include_layers:
        l2 = _load_recent_turns(50)
        if l2:
            lines.append("━━━ LAYER 2: RecallMemory (recent 50 turns) ━━━")
            lines.append(l2)
            lines.append("")
            layer_outputs[2] = True

    if 3 in include_layers:
        l3 = _load_archival(query=query, limit=20)
        if l3:
            lines.append("━━━ LAYER 3: ArchivalMemory (FTS5) ━━━")
            lines.append(l3)
            lines.append("")
            layer_outputs[3] = True

    if 4 in include_layers:
        l4 = _load_mem0_context(query=query, top_k=30)
        if l4:
            lines.append("━━━ LAYER 4: MemoryStore/ChromaDB (semantic recall) ━━━")
            lines.append(l4)
            lines.append("")
            layer_outputs[4] = True

    if 5 in include_layers:
        l5 = _load_session_checkpoint()
        if l5:
            lines.append("━━━ LAYER 5: Session Checkpoint ━━━")
            lines.append(l5)
            lines.append("")
            layer_outputs[5] = True

    if 6 in include_layers:
        l6 = _load_user_profile()
        if l6:
            lines.append("━━━ LAYER 6: UserProfile ━━━")
            lines.append(l6)
            lines.append("")
            layer_outputs[6] = True

    if 7 in include_layers:
        l7 = _load_obsidian_recent(limit=5)
        if l7:
            lines.append("━━━ LAYER 7: Obsidian vault (recent notes) ━━━")
            lines.append(l7)
            lines.append("")
            layer_outputs[7] = True

    active = len(layer_outputs)
    lines.append(f"━━━ Memory context ready — {active}/7 layers loaded ━━━")

    # ── MCP TOOL REMINDER ─────────────────────────────────────────────────────
    # This reminder is BAKED INTO memory_inject.md so it survives OpenCode's
    # own internal compaction (which runs at ~38k chars, 50% of 76800 max).
    # OpenCode injects memory_inject.md via -f flags, so the reminder is always
    # present in the prompt even after OpenCode compacts its own context.
    lines.append("")
    lines.append("━━━ MCP TOOL REMINDER ━━━")
    lines.append("MCP tools are always active — gitnexus, obsidian, ruflo_memory,")
    lines.append("filesystem, exa, hermes, crawl4ai, browser_use, symphony, and more.")
    lines.append("")
    lines.append("MANDATORY per-task checks BEFORE reading files or making changes:")
    lines.append("  1. @ruflo_memory_search — query 6-layer memory for prior context")
    lines.append("  2. @mcp_gitnexus — get code context, callers, impact BEFORE editing")
    lines.append("  3. @mcp_obsidian — check .wiki for prior decisions and patterns")
    lines.append("  4. @mcp_symphony — check task state before starting new work")
    lines.append("")
    lines.append("These tools provide critical context. ALWAYS use them.")

    final_text = "\n".join(lines)

    # Write SHORT inject version for OpenCode system prompt (summary only)
    # Write FULL version as persistent memory archive
    try:
        SESSION_DIR.mkdir(parents=True, exist_ok=True)
        # Filter turn-data lines from final_text before writing
        final_lines = final_text.split('\n')
        inject_lines = [
            line_item for line_item in final_lines
            if not (line_item.startswith("  [") and "] " in line_item and ": " in line_item.split("] ", 1)[-1])
        ]
        inject_text = "\n".join(inject_lines)
        print(f"[DEBUG] write: final_lines={len(final_lines)} inject_lines={len(inject_lines)}")
        # Write both files inside try block
        MEMORY_CONTEXT_FILE.write_text(final_text, encoding="utf-8")
        OPENCODE_INJECT_FILE.write_text(inject_text, encoding="utf-8")
        inj = OPENCODE_INJECT_FILE.read_text(encoding="utf-8")
        ctx = MEMORY_CONTEXT_FILE.read_text(encoding="utf-8")
        if inj != ctx:
            logger.warning("[autoinject] INJECT != CONTEXT — filter may not be working! inj=%d ctx=%d", len(inj), len(ctx))
        else:
            logger.info("[autoinject] Wrote persistent context: %d chars, %d layers", len(final_text), active)
    except Exception as e:
        logger.warning("[autoinject] Could not write context file: %s", e)

    return final_text


def read_persistent_context() -> str:
    """Read the last built persistent context."""
    try:
        if MEMORY_CONTEXT_FILE.exists():
            return MEMORY_CONTEXT_FILE.read_text(encoding="utf-8")
    except Exception:
        pass
    return ""


def build_minimal_context() -> str:
    """Build a lightweight context for quick sessions (skips heavy layers)."""
    return build_persistent_context(include_layers=[1, 5, 6])


# ── CLI ────────────────────────────────────────────────────────────────────────


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build persistent memory context")
    parser.add_argument("--query", default="general work coding AI project", help="Search query")
    parser.add_argument("--user", default="bashara", help="User ID")
    parser.add_argument("--minimal", action="store_true", help="Skip heavy layers")
    args = parser.parse_args()

    if args.minimal:
        ctx = build_minimal_context()
    else:
        ctx = build_persistent_context(query=args.query, user_id=args.user)

    print(ctx)
    print(f"\n[Written to {MEMORY_CONTEXT_FILE}]")