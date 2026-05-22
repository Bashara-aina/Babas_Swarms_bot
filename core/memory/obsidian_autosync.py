"""
core/memory/obsidian_autosync.py — Automatic Obsidian vault sync for OpenCode sessions.

Every session end writes to the Obsidian vault:
  - Daily session log: Sessions/YYYY-MM-DD.md
  - Full session summary: Sessions/YYYYMMDD-HHMM-session-slug.md
  - Memory blocks for important concepts
  - Auto-index of all new memories into the wiki

Uses the Obsidian MCP via subprocess or direct file writes.
Also integrates with GitNexus for architecture decision tracking.

Writes to: .wiki/Sessions/, .wiki/bashara/, .wiki/memories/
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

WIKI_ROOT = Path.home() / "swarm-bot" / ".wiki"
SESSIONS_DIR = WIKI_ROOT / "Sessions"
DAILY_DIR = WIKI_ROOT / "daily"
MEMORIES_DIR = WIKI_ROOT / "memories"
PROJECTS_DIR = WIKI_ROOT / "bashara"
ARCHITECTURE_DIR = WIKI_ROOT / "architecture"

# ── Ensure directories exist ───────────────────────────────────────────────────


def _ensure_dirs():
    for d in [SESSIONS_DIR, DAILY_DIR, MEMORIES_DIR, PROJECTS_DIR, ARCHITECTURE_DIR]:
        d.mkdir(parents=True, exist_ok=True)


# ── Daily session log ───────────────────────────────────────────────────────────


def write_daily_session_log(
    date: str | None = None,
    session_name: str = "",
    tasks_completed: list[str] | None = None,
    key_decisions: list[str] | None = None,
    files_changed: list[str] | None = None,
    problems_encountered: list[str] | None = None,
    user_message: str = "",
    assistant_response: str = "",
    memory_layers_used: int = 0,
) -> Path:
    """
    Append to or create the daily session log.

    Writes to: .wiki/Sessions/YYYY-MM-DD.md
    """
    _ensure_dirs()
    date = date or datetime.now().strftime("%Y-%m-%d")
    log_file = SESSIONS_DIR / f"{date}.md"

    # Build frontmatter
    frontmatter = f"""---
date: {date}
type: session-log
memory_layers: {memory_layers_used}
---

# Session Log — {date}

"""
    # Check if file exists (append) or create new
    if log_file.exists():
        existing = log_file.read_text(encoding="utf-8")
        # If existing has no frontmatter yet, add it
        if not existing.startswith("---"):
            content = frontmatter + existing
        else:
            content = None
    else:
        content = frontmatter

    # Time entry
    ts = datetime.now().strftime("%H:%M")
    session_id = datetime.now().strftime("%Y%m%d-%H%M")

    entry_lines = [
        f"\n## Session {ts} — {session_name or 'OpenCode session'}\n",
    ]

    if tasks_completed:
        entry_lines.append("### Tasks Completed\n")
        for task in tasks_completed:
            entry_lines.append(f"- [x] {task}\n")
        entry_lines.append("\n")

    if key_decisions:
        entry_lines.append("### Key Decisions\n")
        for decision in key_decisions:
            entry_lines.append(f"- **{decision}**\n")
        entry_lines.append("\n")

    if files_changed:
        entry_lines.append("### Files Changed\n")
        for f in files_changed[:20]:  # cap at 20
            entry_lines.append(f"- `{f}`\n")
        entry_lines.append("\n")

    if problems_encountered:
        entry_lines.append("### Problems Encountered\n")
        for problem in problems_encountered:
            entry_lines.append(f"- ⚠️ {problem}\n")
        entry_lines.append("\n")

    if user_message:
        entry_lines.append(f"### User Message\n")
        entry_lines.append(f"> {user_message[:500]}\n\n")

    if assistant_response:
        resp_preview = assistant_response[:300].replace("\n", " ")
        entry_lines.append(f"### Assistant Response (preview)\n")
        entry_lines.append(f"> {resp_preview}...\n\n")

    entry_text = "".join(entry_lines)

    if content is None:
        # Append to existing file
        try:
            existing = log_file.read_text(encoding="utf-8")
            log_file.write_text(existing + entry_text, encoding="utf-8")
        except Exception as e:
            logger.warning("Failed to append daily log: %s", e)
    else:
        log_file.write_text(content + entry_text, encoding="utf-8")

    logger.info("[obsidian_autosync] Wrote daily log: %s", log_file)
    return log_file


# ── Full session summary ─────────────────────────────────────────────────────────


def write_session_summary(
    session_id: str,
    session_name: str,
    tasks: list[dict[str, Any]],
    decisions: list[str],
    files: list[str],
    context_blocks: str = "",
    user_query: str = "",
    model_used: str = "",
    duration_seconds: int = 0,
) -> Path:
    """
    Write a full session summary as a dedicated note.

    Writes to: .wiki/Sessions/YYYYMMDD-HHMM-session-slug.md
    """
    _ensure_dirs()

    ts = datetime.now()
    slug = session_name[:40].replace(" ", "-").replace("/", "-").replace(":", "-") or "opencode-session"
    filename = f"{ts.strftime('%Y%m%d-%H%M')}-{slug}.md"
    session_file = SESSIONS_DIR / filename

    duration_min = duration_seconds // 60 if duration_seconds else 0

    content = f"""---
date: {ts.isoformat()}
session_id: {session_id}
type: session-summary
tasks_count: {len(tasks)}
decisions_count: {len(decisions)}
files_count: {len(files)}
duration_minutes: {duration_min}
model: {model_used or 'MiniMax-M2.7'}
memory_layers: 7
---

# Session: {session_name}

**Date:** {ts.strftime('%Y-%m-%d %H:%M')} | **Duration:** {duration_min}min | **Model:** {model_used or 'MiniMax-M2.7'}

## User Query
{user_query}

## Tasks Completed

"""
    for i, task in enumerate(tasks, 1):
        task_desc = task.get("description", str(task))
        status = task.get("status", "completed")
        content += f"{i}. [{status.upper()}] {task_desc}\n"

    content += "\n## Key Decisions\n\n"
    for i, decision in enumerate(decisions, 1):
        content += f"{i}. {decision}\n"

    content += "\n## Files Changed\n\n"
    for f in files[:50]:
        content += f"- `{f}`\n"

    if context_blocks:
        content += f"\n## Memory Context (7-layer recall)\n\n{context_blocks[:2000]}\n"

    content += "\n## Metadata\n\n"
    content += f"- Session ID: `{session_id}`\n"
    content += f"- Tasks: {len(tasks)}\n"
    content += f"- Decisions: {len(decisions)}\n"
    content += f"- Files: {len(files)}\n"
    content += f"- Memory layers used: 7\n"
    content += f"- Duration: {duration_min} minutes\n"

    session_file.write_text(content, encoding="utf-8")
    logger.info("[obsidian_autosync] Wrote session summary: %s", session_file)
    return session_file


# ── Memory block writer (from mem0/ChromaDB) ──────────────────────────────────


def write_memory_block(
    content: str,
    title: str | None = None,
    tags: list[str] | None = None,
    memory_type: str = "general",
    importance: float = 0.5,
) -> Path:
    """
    Write an important memory as a dedicated note.

    Writes to: .wiki/memories/YYYYMMDD-title-slug.md
    """
    _ensure_dirs()

    ts = datetime.now()
    title = title or content[:60].replace(" ", "-").replace("/", "-")[:50]
    slug = title[:40].replace(" ", "-").replace("/", "-").lower()
    filename = f"{ts.strftime('%Y%m%d-%H%M')}-{slug}.md"
    mem_file = MEMORIES_DIR / filename

    tags_str = ", ".join(tags or [])
    content_formatted = f"""---
date: {ts.isoformat()}
type: memory-block
memory_type: {memory_type}
importance: {importance}
tags: [{tags_str}]
---

# {title}

{content}

---
*Auto-saved from OpenCode memory system (7-layer recall)*
"""

    mem_file.write_text(content_formatted, encoding="utf-8")
    logger.info("[obsidian_autosync] Wrote memory block: %s", mem_file)
    return mem_file


# ── User project auto-index ───────────────────────────────────────────────────


def index_user_project(
    project_name: str,
    project_type: str = "software",
    description: str = "",
    files: list[str] | None = None,
    decisions: list[str] | None = None,
    active: bool = True,
) -> Path:
    """
    Write or update a user project note in the wiki.

    Writes to: .wiki/bashara/projects/{project-slug}.md
    """
    _ensure_dirs()

    projects_dir = PROJECTS_DIR / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)

    slug = project_name[:40].replace(" ", "-").replace("/", "-").lower()
    project_file = projects_dir / f"{slug}.md"

    ts = datetime.now().isoformat()
    status = "🟡 Active" if active else "⚪ Completed"

    files_list = "\n".join(f"- `{f}`" for f in (files or [])[:30])
    decisions_list = "\n".join(f"- {d}" for d in (decisions or []))

    content = f"""---
date: {ts}
type: project
project_type: {project_type}
status: {status}
---

# {project_name}

**Status:** {status} | **Type:** {project_type} | **Updated:** {ts}

## Description
{description or 'No description provided.'}

## Files
{files_list or '_No files tracked._'}

## Key Decisions
{decisions_list or '_No decisions recorded._'}

## Context
Automatically managed by OpenCode memory system.
Last updated: {ts}
"""

    project_file.write_text(content, encoding="utf-8")
    logger.info("[obsidian_autosync] Indexed project: %s", project_file)
    return project_file


# ── Architecture decision writer ────────────────────────────────────────────────


def write_architecture_decision(
    title: str,
    context: str,
    decision: str,
    alternatives: list[str] | None = None,
    consequences: list[str] | None = None,
    tags: list[str] | None = None,
) -> Path:
    """
    Write an architecture decision record (ADR) to the wiki.

    Writes to: .wiki/architecture/YYYYMMDD-title-slug.md
    """
    _ensure_dirs()

    ts = datetime.now()
    slug = title[:40].replace(" ", "-").replace("/", "-").lower()
    filename = f"{ts.strftime('%Y%m%d')}-{slug}.md"
    adr_file = ARCHITECTURE_DIR / filename

    tags_str = ", ".join(tags or [])
    alternatives_str = "\n".join(f"- {a}" for a in (alternatives or []))
    consequences_str = "\n".join(f"- {c}" for c in (consequences or []))

    content = f"""---
date: {ts.isoformat()}
type: architecture-decision
status: accepted
tags: [{tags_str}]
---

# ADR: {title}

**Date:** {ts.strftime('%Y-%m-%d')} | **Status:** Accepted

## Context
{context}

## Decision
{decision}

## Alternatives Considered
{alternatives_str or '_None._'}

## Consequences
{consequences_str or '_None._'}

---
*Auto-generated by OpenCode memory system*
"""

    adr_file.write_text(content, encoding="utf-8")
    logger.info("[obsidian_autosync] Wrote ADR: %s", adr_file)
    return adr_file


# ── GitNexus integration ────────────────────────────────────────────────────────


def sync_from_gitnexus(
    query: str,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """
    Query GitNexus for relevant code context and write to wiki.
    This keeps the wiki in sync with the codebase architecture.
    """
    try:
        from core.integrations.graphrag_integration import query_wiki_graph

        results = query_wiki_graph(query, mode="global", top_n=limit)
        return results or []
    except Exception as e:
        logger.debug("GitNexus sync error: %s", e)
        return []


# ── Full session sync (call at session end) ───────────────────────────────────


def full_session_sync(
    session_id: str,
    session_name: str,
    user_query: str,
    tasks: list[dict[str, Any]],
    decisions: list[str],
    files_changed: list[str],
    context_summary: str = "",
    model: str = "",
    duration: int = 0,
) -> dict[str, Path]:
    """
    Run all sync operations at session end.

    Returns dict of operation → file written.
    """
    _ensure_dirs()

    results = {}

    # 1. Write daily session log
    try:
        tasks_strs = [t.get("description", str(t)) for t in tasks]
        results["daily_log"] = write_daily_session_log(
            session_name=session_name,
            tasks_completed=tasks_strs,
            key_decisions=decisions,
            files_changed=files_changed,
            user_message=user_query,
            memory_layers_used=7,
        )
    except Exception as e:
        logger.warning("Daily log write failed: %s", e)

    # 2. Write full session summary
    try:
        results["session_summary"] = write_session_summary(
            session_id=session_id,
            session_name=session_name,
            tasks=tasks,
            decisions=decisions,
            files=files_changed,
            context_blocks=context_summary[:2000],
            user_query=user_query,
            model_used=model,
            duration_seconds=duration,
        )
    except Exception as e:
        logger.warning("Session summary write failed: %s", e)

    # 3. Extract and write important memories
    try:
        from core.memory.store import MemoryStore

        store = MemoryStore()
        count = store.count()
        if count > 0:
            top_memories = store.recall(query=session_name, top_k=5, min_score=0.3)
            for mem in top_memories:
                if len(mem) > 50:
                    try:
                        path = write_memory_block(
                            content=mem[:500],
                            title=f"memory-{session_name[:30]}",
                            tags=["auto-saved", "important"],
                            memory_type="episodic",
                            importance=0.8,
                        )
                        results[f"memory_{mem[:30]}"] = path
                    except Exception:
                        pass
    except Exception as e:
        logger.warning("Memory block write failed: %s", e)

    # 4. Sync recent gitnexus context
    try:
        sync_results = sync_from_gitnexus(query=session_name, limit=3)
        if sync_results:
            content = f"""---
date: {datetime.now().isoformat()}
type: gitnexus-sync
query: {session_name}
---

# GitNexus Sync: {session_name}

Found {len(sync_results)} relevant code entries.

"""
            for r in sync_results[:5]:
                content += f"\n## {r.get('title', 'entry')}\n"
                content += f"{str(r.get('content', ''))[:300]}\n"

            sync_file = ARCHITECTURE_DIR / f"gitnexus-{datetime.now().strftime('%Y%m%d-%H%M')}.md"
            sync_file.write_text(content, encoding="utf-8")
            results["gitnexus_sync"] = sync_file
    except Exception as e:
        logger.warning("GitNexus sync failed: %s", e)

    logger.info(
        "[obsidian_autosync] Session sync complete — %d files written",
        len([v for v in results.values() if v]),
    )
    return results


# ── MCP-based read/search (Obsidian MCP tools) ───────────────────────────────────


def search_obsidian_notes(query: str, limit: int = 10) -> list[dict[str, str]]:
    """
    Search wiki notes using Obsidian MCP search_notes.

    Returns list of dicts with filename and snippet.
    """
    try:
        from obsidian_mcp_client import get_mcp_client
        client = get_mcp_client()
        if client is None:
            return _search_obsidian_fallback(query, limit)
        results = client.search_notes(query=query, limit=limit)
        return results if results else []
    except Exception as e:
        logger.debug("MCP search failed, using fallback: %s", e)
        return _search_obsidian_fallback(query, limit)


def _search_obsidian_fallback(query: str, limit: int = 10) -> list[dict[str, str]]:
    """Fallback: grep-based search in wiki dir."""
    import subprocess

    results = []
    try:
        proc = subprocess.run(
            ["grep", "-rn", "--include=*.md", "-l", query, str(WIKI_ROOT)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        for line in proc.stdout.strip().split("\n")[:limit]:
            if line:
                parts = line.split(":", 1)
                if len(parts) == 2:
                    results.append({"filename": parts[0], "snippet": parts[1]})
    except Exception:
        pass
    return results


def read_obsidian_note(filename: str) -> str:
    """
    Read a wiki note using Obsidian MCP read_note.

    Returns note content as string, or empty string on failure.
    """
    try:
        from obsidian_mcp_client import get_mcp_client
        client = get_mcp_client()
        if client is None:
            return _read_obsidian_note_fallback(filename)
        content = client.read_note(filename=filename)
        return content if content else ""
    except Exception as e:
        logger.debug("MCP read failed, using fallback: %s", e)
        return _read_obsidian_note_fallback(filename)


def _read_obsidian_note_fallback(filename: str) -> str:
    """Fallback: direct file read."""
    path = WIKI_ROOT / filename if not filename.startswith(str(WIKI_ROOT)) else Path(filename)
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


# ── CLI ────────────────────────────────────────────────────────────────────────


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Obsidian autosync operations")
    parser.add_argument("--daily-log", action="store_true", help="Write daily session log")
    parser.add_argument("--session-summary", action="store_true", help="Write full session summary")
    parser.add_argument("--session-id", default="cli-session", help="Session ID")
    parser.add_argument("--session-name", default="CLI session", help="Session name")
    args = parser.parse_args()

    _ensure_dirs()

    if args.daily_log:
        path = write_daily_session_log(session_name=args.session_name)
        print(f"Wrote daily log: {path}")

    if args.session_summary:
        path = write_session_summary(
            session_id=args.session_id,
            session_name=args.session_name,
            tasks=[{"description": "Example task", "status": "completed"}],
            decisions=["Example decision"],
            files=["example.py"],
        )
        print(f"Wrote session summary: {path}")