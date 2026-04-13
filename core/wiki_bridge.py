"""
core/wiki_bridge.py — Bidirectional OpenCode ↔ Legion wiki bridge.

Makes OpenCode and Legion share the same `.wiki/` vault as their joint brain:
  • OpenCode writes session summaries + decisions into `.wiki/` after each task
  • OpenCode queries `.wiki/` for context before and during task execution
  • Legion's WikiManager reads from the same vault; both systems stay in sync
  • OpenCode session events (task_start, task_end, decision) are ingested as wiki pages

Wiki auto-ingest is controlled by `LEGION_WIKI_AUTO_INGEST=1` (default on).
To disable for a specific operation pass `auto_ingest=False`.
"""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent
WIKI_DIR = REPO_ROOT / ".wiki"
OPENCODE_SESSION_DIR = WIKI_DIR / "opencode" / "sessions"
OPENCODE_DECISIONS_DIR = WIKI_DIR / "decisions"


def _now_jst() -> str:
    from datetime import datetime
    from zoneinfo import ZoneInfo

    return datetime.now(ZoneInfo("Asia/Tokyo")).strftime("%Y-%m-%d %H:%M JST")


async def opencode_write_session_summary(
    session_id: str,
    task_description: str,
    actions_taken: str,
    outcome: str,
    files_modified: Optional[list[str]] = None,
    decisions: Optional[list[str]] = None,
    auto_ingest: bool = True,
) -> str:
    """
    Write a session summary to `.wiki/opencode/sessions/<session_id>.md`.

    OpenCode calls this after each task (via a hook or post-task callback).
    Optionally triggers wiki ingest so the content propagates to related pages.
    """
    import asyncio

    import aiofiles

    if not _wiki_enabled():
        return ""

    session_dir = OPENCODE_SESSION_DIR
    session_dir.mkdir(parents=True, exist_ok=True)

    files_block = ""
    if files_modified:
        files_block = "\n".join(f"- `{f}`" for f in files_modified)

    decisions_block = ""
    if decisions:
        decisions_block = "\n## Decisions Made\n" + "\n".join(f"- {d}" for d in decisions)

    content = f"""---
tags: [opencode-session, session-summary]
created: {_now_jst()}
---

# OpenCode Session: {session_id}

## Task
{task_description}

## Actions Taken
{actions_taken}

## Outcome
{outcome}

{files_block if files_block else ""}
{decisions_block if decisions_block else ""}

---
_Last updated: {_now_jst()} by OpenCode_
"""
    session_file = session_dir / f"{session_id}.md"
    try:
        async with aiofiles.open(session_file, "w", encoding="utf-8") as f:
            await f.write(content)
        logger.info("OpenCode session summary written: %s", session_file)

        if auto_ingest and _auto_ingest_enabled():
            await _ingest_opencode_session(
                session_id=session_id,
                task=task_description,
                outcome=outcome,
            )
    except Exception as exc:
        logger.warning("Failed to write OpenCode session summary: %s", exc)

    return str(session_file)


async def opencode_write_decision(
    decision_id: str,
    title: str,
    context: str,
    rationale: str,
    alternatives_considered: Optional[list[str]] = None,
    auto_ingest: bool = True,
) -> str:
    """
    Write an ADR-style decision record to `.wiki/decisions/ADR-{decision_id}.md`.

    OpenCode calls this when it makes a significant architectural or design choice.
    """
    import aiofiles

    if not _wiki_enabled():
        return ""

    decisions_dir = OPENCODE_DECISIONS_DIR
    decisions_dir.mkdir(parents=True, exist_ok=True)

    alts_block = ""
    if alternatives_considered:
        alts_block = "\n## Alternatives Considered\n" + "\n".join(f"- {a}" for a in alternatives_considered)

    content = f"""---
tags: [decision, adr, opencode]
created: {_now_jst()}
status: accepted
---

# ADR-{decision_id}: {title}

## Context
{context}

## Decision
{rationale}

{alts_block if alts_block else ""}

---
_Last updated: {_now_jst()} by OpenCode_
"""
    adr_file = decisions_dir / f"ADR-{decision_id}.md"
    try:
        async with aiofiles.open(adr_file, "w", encoding="utf-8") as f:
            await f.write(content)
        logger.info("OpenCode ADR written: %s", adr_file)

        if auto_ingest and _auto_ingest_enabled():
            await _ingest_opencode_decision(
                decision_id=decision_id,
                title=title,
                rationale=rationale,
            )
    except Exception as exc:
        logger.warning("Failed to write OpenCode ADR: %s", exc)

    return str(adr_file)


async def opencode_query_wiki(
    query: str,
    top_k: int = 3,
    include_sessions: bool = True,
    include_decisions: bool = True,
    include_legion: bool = True,
) -> str:
    """
    Query the shared wiki from OpenCode's perspective.

    Returns a markdown block with relevant content from:
      - OpenCode session summaries
      - OpenCode ADR decisions
      - Legion knowledge pages

    This is what OpenCode calls before/during task execution to get
    context from both agents' shared brain.
    """
    if not _wiki_enabled():
        return ""

    try:
        from core.wiki_manager import get_wiki_manager

        wm = get_wiki_manager()
    except Exception as exc:
        logger.debug("opencode_query_wiki: wiki_manager unavailable: %s", exc)
        return ""

    parts: list[str] = []

    if include_sessions:
        sessions = await _query_sessions(query, top_k=min(top_k, 2))
        if sessions:
            parts.append(sessions)

    if include_decisions:
        decisions = await _query_decisions(query, top_k=min(top_k, 2))
        if decisions:
            parts.append(decisions)

    if include_legion:
        legion_block = await wm.query(query, top_k=min(top_k, 2))
        if legion_block:
            parts.append(legion_block)

    return "\n\n---\n\n".join(parts) if parts else ""


async def _query_sessions(query: str, top_k: int = 2) -> str:
    """Return relevant OpenCode session summaries."""
    import re

    import aiofiles

    if not OPENCODE_SESSION_DIR.exists():
        return ""

    try:
        session_files = sorted(
            OPENCODE_SESSION_DIR.glob("*.md"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
    except OSError:
        return ""

    q_lower = query.lower()
    scored: list[tuple[float, Path]] = []
    for sf in session_files[:50]:
        try:
            async with aiofiles.open(sf, encoding="utf-8", mode="r") as f:
                text = await f.read()
            score = sum(1 for kw in q_lower.split() if kw in text.lower())
            if score > 0:
                scored.append((score, sf))
        except OSError:
            continue

    scored.sort(reverse=True)
    selected = scored[:top_k]

    blocks: list[str] = []
    for _, sf in selected:
        try:
            async with aiofiles.open(sf, encoding="utf-8", mode="r") as f:
                content = await f.read()
            preview = content[:800]
            blocks.append(f"### From {sf.name}:\n{preview}")
        except OSError:
            continue

    return "\n\n".join(blocks) if blocks else ""


async def _query_decisions(query: str, top_k: int = 2) -> str:
    """Return relevant OpenCode ADR decisions."""
    import aiofiles

    if not OPENCODE_DECISIONS_DIR.exists():
        return ""

    try:
        adr_files = sorted(
            OPENCODE_DECISIONS_DIR.glob("ADR-*.md"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
    except OSError:
        return ""

    q_lower = query.lower()
    scored: list[tuple[float, Path]] = []
    for adrf in adr_files[:30]:
        try:
            async with aiofiles.open(adrf, encoding="utf-8", mode="r") as f:
                text = await f.read()
            score = sum(1 for kw in q_lower.split() if kw in text.lower())
            if score > 0:
                scored.append((score, adrf))
        except OSError:
            continue

    scored.sort(reverse=True)
    selected = scored[:top_k]

    blocks: list[str] = []
    for _, adrf in selected:
        try:
            async with aiofiles.open(adrf, encoding="utf-8", mode="r") as f:
                content = await f.read()
            preview = content[:600]
            blocks.append(f"### From {adrf.name}:\n{preview}")
        except OSError:
            continue

    return "\n\n".join(blocks) if blocks else ""


async def _ingest_opencode_session(
    session_id: str,
    task: str,
    outcome: str,
) -> None:
    """Trigger wiki ingest for an OpenCode session summary."""
    try:
        from core.wiki_manager import get_wiki_manager

        wm = get_wiki_manager()
        await wm.ingest(
            source=f"OpenCode session {session_id}\nTask: {task}\nOutcome: {outcome}",
            source_type="opencode_session",
            context=f"session_id={session_id}",
        )
    except Exception as exc:
        logger.debug("Ingest of OpenCode session %s failed: %s", session_id, exc)


async def _ingest_opencode_decision(
    decision_id: str,
    title: str,
    rationale: str,
) -> None:
    """Trigger wiki ingest for an OpenCode ADR."""
    try:
        from core.wiki_manager import get_wiki_manager

        wm = get_wiki_manager()
        await wm.ingest(
            source=f"OpenCode ADR-{decision_id}: {title}\nDecision: {rationale}",
            source_type="opencode_decision",
            context=f"decision_id={decision_id}",
        )
    except Exception as exc:
        logger.debug("Ingest of OpenCode ADR %s failed: %s", decision_id, exc)


def _wiki_enabled() -> bool:
    return os.getenv("LEGION_WIKI_ENABLED", "1").strip().lower() not in ("0", "false", "no", "off")


def _auto_ingest_enabled() -> bool:
    return os.getenv("LEGION_WIKI_AUTO_INGEST", "1").strip().lower() not in ("0", "false", "no", "off")


def _ensure_opencode_dirs() -> None:
    """Ensure OpenCode wiki subdirs exist. Call once at startup."""
    OPENCODE_SESSION_DIR.mkdir(parents=True, exist_ok=True)
    OPENCODE_DECISIONS_DIR.mkdir(parents=True, exist_ok=True)
