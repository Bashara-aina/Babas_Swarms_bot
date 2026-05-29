"""core/builtin_hooks.py — Default hooks registered at startup.

Currently provides:
  - audit_logger_hook: writes every LLM call to the audit_log table
  - opencode_session_hook: ingests OpenCode task sessions into the wiki brain
  - claude_code_session_hook: ingests Claude Code sessions into the wiki brain
"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

# Module-level store for CC session data since hook ctx is not preserved
# between emit() calls. Populated by claude_code_session_start_hook and
# consumed by claude_code_session_end_hook on session_end.
_cc_session_store: dict[str, Any] = {}


async def audit_logger_hook(ctx: dict[str, Any]) -> dict[str, Any]:
    """Log post_llm_call events to the SQLite audit_log table."""
    try:
        from tools.persistence import log_audit

        await log_audit(
            action="llm_call",
            detail=f"{ctx.get('agent', '?')}",
            model=ctx.get("model", ""),
            tokens_in=ctx.get("tokens_in", 0),
            tokens_out=ctx.get("tokens_out", 0),
            duration_ms=ctx.get("duration_ms", 0),
            success=ctx.get("success", True),
        )
    except Exception:
        logger.debug("audit_logger_hook: DB not ready, skipping")
    return ctx


async def command_audit_hook(ctx: dict[str, Any]) -> dict[str, Any]:
    """Log command_received events to the audit_log table."""
    try:
        from tools.persistence import log_audit

        await log_audit(
            action="command",
            detail=ctx.get("command", "?"),
        )
    except Exception:
        logger.debug("command_audit_hook: DB not ready, skipping")
    return ctx


async def opencode_session_start_hook(ctx: dict[str, Any]) -> dict[str, Any]:
    """Record task start metadata for later wiki ingest on task completion."""
    ctx["_opencode_session_started"] = True
    ctx["_opencode_session_task"] = ctx.get("task", "unknown")
    return ctx


async def opencode_session_end_hook(ctx: dict[str, Any]) -> dict[str, Any]:
    """Ingest completed OpenCode task sessions into the wiki brain."""
    if not ctx.get("_opencode_session_started"):
        return ctx
    try:
        import uuid

        from core.wiki_bridge import opencode_write_session_summary

        session_id = ctx.get("sessionId") or f"task-{uuid.uuid4().hex[:8]}"
        await opencode_write_session_summary(
            session_id=session_id,
            task_description=ctx.get("task", "unknown"),
            actions_taken=ctx.get("actions_taken", ""),
            outcome=ctx.get("outcome", "unknown"),
            files_modified=ctx.get("files_modified"),
            decisions=ctx.get("decisions"),
        )
    except Exception:
        logger.debug("opencode_session_end_hook: wiki bridge unavailable, skipping")
    return ctx


async def opencode_decision_hook(ctx: dict[str, Any]) -> dict[str, Any]:
    """Write an ADR when OpenCode makes a significant architectural decision."""
    if not ctx.get("_opencode_decision"):
        return ctx
    try:
        import uuid

        from core.wiki_bridge import opencode_write_decision

        decision_id = ctx.get("decision_id") or uuid.uuid4().hex[:8]
        await opencode_write_decision(
            decision_id=decision_id,
            title=ctx.get("_opencode_decision_title", "Untitled Decision"),
            context=ctx.get("_opencode_decision_context", ""),
            rationale=ctx.get("_opencode_decision", ""),
            alternatives_considered=ctx.get("_opencode_decision_alternatives"),
        )
    except Exception:
        logger.debug("opencode_decision_hook: wiki bridge unavailable, skipping")
    return ctx


# ── Claude Code session hooks ──────────────────────────────────────────────────


async def claude_code_session_start_hook(ctx: dict[str, Any]) -> dict[str, Any]:
    """Record Claude Code session start metadata for wiki ingest on completion."""
    import uuid
    session_id = ctx.get("session_id") or f"cc-{uuid.uuid4().hex[:8]}"
    prompt = ctx.get("prompt", "")[:500]
    ctx["_cc_session_started"] = True
    ctx["_cc_session_id"] = session_id
    ctx["_cc_session_prompt"] = prompt
    # Also persist to module store so session_end hook can access it
    _cc_session_store["session_id"] = session_id
    _cc_session_store["prompt"] = prompt
    _cc_session_store["started"] = True
    return ctx


async def claude_code_session_end_hook(ctx: dict[str, Any]) -> dict[str, Any]:
    """Ingest completed Claude Code sessions into the wiki brain.

    Fires on session_end. Reads session data from module-level _cc_session_store
    since ctx is not preserved between emit() calls.
    """
    # Check module store (set by claude_code_session_start_hook on pre_llm_call)
    if not _cc_session_store.get("started"):
        return ctx
    try:
        from core.wiki_bridge import claude_code_write_session

        session_id = ctx.get("_cc_session_id") or _cc_session_store.get("session_id", "unknown")
        prompt = ctx.get("_cc_session_prompt") or _cc_session_store.get("prompt", "")
        report = ctx.get("report", ctx.get("outcome", ""))
        await claude_code_write_session(
            session_md=(
                f"# Claude Code Session\n\n"
                f"**ID**: {session_id}\n\n"
                f"## Prompt\n\n{prompt}\n\n"
                f"## Result\n\n{report[:2000]}"
            ),
            summary=f"CC session: {report[:100] if report else 'no output'}",
        )
        # Clear store after writing
        _cc_session_store.clear()
    except Exception:
        logger.debug("claude_code_session_end_hook: wiki bridge unavailable, skipping")
    return ctx


async def _post_compact_reset_hook(ctx: dict[str, Any]) -> dict[str, Any]:
    """GAP-08: Clear incremental summary after compaction to start fresh."""
    try:
        from core.incremental_summary import reset as reset_incremental_summary
        reset_incremental_summary()
    except Exception:
        pass
    return ctx


async def _compaction_event_hook(ctx: dict[str, Any]) -> dict[str, Any]:
    """GAP-15: Log compaction events to event-store-lite for session replay."""
    try:
        from core.session_snapshots import append_compaction_event

        event_type = ctx.get("event", "unknown")
        session_id = ctx.get("user_id", "default")
        append_compaction_event(
            event_type=event_type,
            session_id=session_id,
            details={
                "message_count": len(ctx.get("messages", [])),
                "compaction_reason": ctx.get("reason", ""),
            }
        )
    except Exception:
        pass
    return ctx


async def _recalled_context_refresh_hook(ctx: dict[str, Any]) -> dict[str, Any]:
    """GAP-28: Rebuild remembered_context.md immediately after compaction.

    This ensures OpenCode receives fresh memory context without waiting
    for the session_watcher periodic 60s refresh cycle.
    Writes to the swarm-bot project session_state (not cwd).
    """
    try:
        import sys as _sys
        from pathlib import Path as _Path

        _sys.path.insert(0, str(_Path(__file__).parent.parent.parent))
        from core.memory.memory_injector import build_memory_context

        # Use the swarm-bot project dir explicitly (not cwd, which may differ
        # when OpenCode runs with --dangerously-skip-permissions in a different cwd)
        project_dir = ctx.get("project_dir") or "/home/newadmin/swarm-bot"
        session_dir = _Path(project_dir) / ".session_state"

        # Use the task_desc if available (set by the task dispatcher), otherwise
        # fall back to a broad project-specific query that covers all memory layers.
        # The task_desc is more targeted and ensures the recall is relevant to the
        # current task, not generic.
        task_desc = ctx.get("task_desc", "")
        query = task_desc if task_desc else "swarm-bot project opencode memory compaction MCP tools agents recent work"
        ctx_text = build_memory_context(query=query, user_id="bashara", project_dir=project_dir)
        if ctx_text:
            session_dir.mkdir(parents=True, exist_ok=True)
            recalled_file = session_dir / "remembered_context.md"
            with open(recalled_file, "w") as f:
                f.write(ctx_text)
            logger.info("remembered_context.md refreshed after compaction (%d chars)", len(ctx_text))
        else:
            logger.warning("remembered_context.md: build_memory_context returned empty, skipping write")
    except Exception as e:
        logger.error("_recalled_context_refresh_hook: failed to refresh remembered_context.md: %s", e)
    return ctx


# ── Symphony session lifecycle hooks ─────────────────────────────────────────
# Symphony MCP: multi-agent chat rooms, task boards, persistent memory.
# Automatically: create tasks on post_task, store memories on session_end.


async def _get_mcp_pool():
    """Lazily get the MCPClientPool singleton."""
    try:
        from core.mcp_client import MCPClientPool
        return MCPClientPool()
    except Exception:
        return None


async def symphony_session_start_hook(ctx: dict[str, Any]) -> dict[str, Any]:
    """On session_start: join the swarm-bot room so this session is visible to teammates."""
    try:
        pool = await _get_mcp_pool()
        if not pool:
            return ctx
        # Join the default swarm-bot coordination room
        await pool.call_tool("symphony", "room_join", {"room_id": "swarm-bot"})
        ctx["_symphony_room_joined"] = True
        logger.debug("Symphony: joined swarm-bot room")
    except Exception:
        pass
    return ctx


async def symphony_post_task_hook(ctx: dict[str, Any]) -> dict[str, Any]:
    """On post_task: create a Symphony task for the completed task."""
    try:
        pool = await _get_mcp_pool()
        if not pool:
            return ctx
        task_desc = ctx.get("task", "")
        if not task_desc:
            return ctx
        outcome = ctx.get("outcome", "")[:200]
        task_id = await pool.call_tool(
            "symphony", "create_task",
            {
                "title": task_desc[:100],
                "description": outcome or "completed",
                "status": "done",
                "priority": "medium",
            },
        )
        if task_id and "Error" not in str(task_id)[:50]:
            ctx["_symphony_task_created"] = str(task_id)[:100]
            logger.debug("Symphony: created task %s", task_id)
    except Exception:
        pass
    return ctx


async def symphony_session_end_hook(ctx: dict[str, Any]) -> dict[str, Any]:
    """On session_end: store session summary to Symphony persistent memory."""
    try:
        pool = await _get_mcp_pool()
        if not pool:
            return ctx

        # Build session summary from ctx
        session_id = ctx.get("session_id", "legion-session")
        source = ctx.get("source", "unknown")

        # Store session metadata in symphony memory
        await pool.call_tool(
            "symphony", "memory_store",
            {
                "key": f"session-{session_id}",
                "value": f"Legion session ended | source={source} | ts={datetime.now().isoformat()}",
            },
        )

        # Update any in-progress tasks created by symphony_post_task_hook as done
        if ctx.get("_symphony_task_created"):
            try:
                created = ctx["_symphony_task_created"]
                # Try to extract task_id from the result text
                id_match = re.search(r"id['\"]?\s*:\s*['\"]?([\w-]+)", created)
                if id_match:
                    task_id = id_match.group(1)
                    await pool.call_tool(
                        "symphony", "update_task",
                        {"task_id": task_id, "status": "done"},
                    )
            except Exception:
                pass

        logger.debug("Symphony: session_end memory stored")
    except Exception:
        pass
    return ctx


async def gitnexus_detect_changes_hook(ctx: dict[str, Any]) -> dict[str, Any]:
    """Run gitnexus_detect_changes before git commit and attach diff summary to ctx."""
    try:
        import subprocess

        result = subprocess.run(
            ["npx", "gitnexus", "detect-changes", "--scope", "staged"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd="/home/newadmin/swarm-bot",
        )
        if result.returncode == 0 and result.stdout.strip():
            ctx["_gitnexus_changes"] = result.stdout.strip()[:500]
            ctx["_gitnexus_safe"] = True
        else:
            ctx["_gitnexus_warning"] = result.stderr.strip()[:200] or "gitnexus check returned non-zero"
            ctx["_gitnexus_safe"] = False
    except Exception as e:
        ctx["_gitnexus_warning"] = str(e)[:200]
        ctx["_gitnexus_safe"] = True  # don't block on gitnexus failure
    return ctx


def register_builtin_hooks() -> None:
    """Register all built-in hooks on the global HookSystem."""
    from core.hooks import get_hooks
    from core.wiki_bridge import _ensure_opencode_dirs

    hooks = get_hooks()
    hooks.register("post_llm_call", audit_logger_hook, name="audit_logger")
    hooks.register("command_received", command_audit_hook, name="command_audit")
    hooks.register("post_llm_call", opencode_decision_hook, name="opencode_decision")
    hooks.register("pre_llm_call", claude_code_session_start_hook, name="cc_session_start")
    hooks.register("session_end", claude_code_session_end_hook, name="cc_session_end")

    # OpenCode session lifecycle hooks — map ruflo's task lifecycle to session hooks
    # ruflo sends "task_complete" and "task_success" → map to post_task for wiki ingest
    hooks.register("post_task", opencode_session_start_hook, name="opencode_session_start")
    hooks.register("post_task", opencode_session_end_hook, name="opencode_session_end")
    hooks.register("task_success", opencode_session_end_hook, name="opencode_session_end_success")

    # Symphony session lifecycle — auto-task-creation and memory persistence
    hooks.register("session_start", symphony_session_start_hook, name="symphony_session_start")
    hooks.register("post_task", symphony_post_task_hook, name="symphony_post_task")
    hooks.register("session_end", symphony_session_end_hook, name="symphony_session_end")

    # GitNexus integration — run gitnexus_detect_changes before git commit
    hooks.register("pre_git_commit", gitnexus_detect_changes_hook, name="gitnexus_pre_commit")

    from core.incremental_summary import incremental_summary_pre_compact_hook

    hooks.register("pre_compact", incremental_summary_pre_compact_hook, name="incremental_summary_pre_compact")
    hooks.register("post_compact", _post_compact_reset_hook, name="incremental_summary_reset")
    hooks.register("pre_compact", _compaction_event_hook, name="compaction_event_pre")
    hooks.register("post_compact", _compaction_event_hook, name="compaction_event_post")

    # GAP-28: refresh remembered_context.md immediately after any compaction
    hooks.register("post_compact", _recalled_context_refresh_hook, name="recalled_context_refresh")

    _ensure_opencode_dirs()
    logger.info("Built-in hooks registered")
