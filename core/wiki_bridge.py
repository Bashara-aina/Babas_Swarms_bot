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
from pathlib import Path

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
    files_modified: list[str] | None = None,
    decisions: list[str] | None = None,
    auto_ingest: bool = True,
) -> str:
    """
    Write a session summary to `.wiki/opencode/sessions/<session_id>.md`.

    OpenCode calls this after each task (via a hook or post-task callback).
    Optionally triggers wiki ingest so the content propagates to related pages.
    """

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


async def claude_code_write_session(session_md: str, summary: str = "") -> str:
    """
    Write a Claude Code session to `.wiki/claude-code/sessions/<slug>.md`.

    Called by Claude Code session hooks after each task.
    Also writes to joint-brain cross-refs via joint_memory.
    """
    import aiofiles

    if not _wiki_enabled():
        return ""

    import hashlib
    slug = hashlib.md5(session_md[:80].encode()).hexdigest()[:12]
    session_dir = WIKI_DIR / "claude-code" / "sessions"
    session_dir.mkdir(parents=True, exist_ok=True)

    content = f"""---
tags: [claude-code-session, session]
created: {_now_jst()}
---

# Claude Code Session

## Summary
{summary or session_md[:200]}

## Session Log

{session_md}
"""
    session_file = session_dir / f"{slug}.md"
    try:
        async with aiofiles.open(session_file, "w", encoding="utf-8") as f:
            await f.write(content)
        logger.info("Claude Code session written: %s", session_file)

        # Also write via joint_memory for cross-system search
        try:
            from core.joint_memory import joint_save
            await joint_save(session_md, "claude-code", tags=["claude-code", "session"], summary=summary)
        except Exception as e:
            logger.debug("joint_memory write failed (non-fatal): %s", e)
    except Exception as exc:
        logger.warning("Failed to write Claude Code session: %s", exc)

    return str(session_file)


async def opencode_write_decision(
    decision_id: str,
    title: str,
    context: str,
    rationale: str,
    alternatives_considered: list[str] | None = None,
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
            async with aiofiles.open(sf, encoding="utf-8") as f:
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
            async with aiofiles.open(sf, encoding="utf-8") as f:
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
            async with aiofiles.open(adrf, encoding="utf-8") as f:
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
            async with aiofiles.open(adrf, encoding="utf-8") as f:
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


# ── GAP-13: wiki-based cross-session compaction cache ──────────────────────────────────


def write_note(filename: str, content: str, folder: str | None = None) -> bool:
    """Write a note to the wiki.

    Args:
        filename: Name of the note (e.g. 'my-key' or 'sessions/snap-abc123')
        content: Markdown content to write
        folder: Optional subfolder under WIKI_DIR (e.g. 'compaction-cache', 'session-snapshots')
                If None, writes directly to WIKI_DIR
    Returns:
        True if written successfully, False otherwise.
    """
    if not _wiki_enabled():
        return False
    try:
        dir_path = WIKI_DIR / folder if folder else WIKI_DIR
        dir_path.mkdir(parents=True, exist_ok=True)
        # Always add .md extension
        if not filename.endswith(".md"):
            filename += ".md"
        file_path = dir_path / filename
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.debug("write_note: wrote %s", file_path)
        return True
    except Exception as exc:
        logger.warning("write_note failed for %s: %s", filename, exc)
        return False


def read_note(filename: str, folder: str | None = None) -> str:
    """Read a note from the wiki.

    Args:
        filename: Name of the note (e.g. 'compaction-cache/my-key' or 'sessions/snap-abc123')
        folder: Optional subfolder under WIKI_DIR
    Returns:
        Content of the note, or empty string if not found.
    """
    if not _wiki_enabled():
        return ""
    try:
        dir_path = WIKI_DIR / folder if folder else WIKI_DIR
        if not filename.endswith(".md"):
            filename += ".md"
        file_path = dir_path / filename
        with open(file_path, encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


def list_notes(folder: str | None = None) -> list[dict[str, str]]:
    """List all notes in a wiki folder.

    Args:
        folder: Optional subfolder under WIKI_DIR (e.g. 'compaction-cache', 'session-snapshots')
                If None, lists WIKI_DIR root.
    Returns:
        List of dicts with 'filename' and 'modified' keys.
    """
    if not _wiki_enabled():
        return []
    try:
        dir_path = WIKI_DIR / folder if folder else WIKI_DIR
        if not dir_path.is_dir():
            return []
        notes = []
        for f in dir_path.iterdir():
            if f.is_file() and f.suffix == ".md":
                stat = f.stat()
                notes.append({
                    "filename": f"{folder}/{f.name}" if folder else f.name,
                    "modified": str(stat.st_mtime),
                })
        return notes
    except Exception as exc:
        logger.warning("list_notes failed for folder %s: %s", folder, exc)
        return []
