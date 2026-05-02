"""core/builtin_hooks.py — Default hooks registered at startup.

Currently provides:
  - audit_logger_hook: writes every LLM call to the audit_log table
  - opencode_session_hook: ingests OpenCode task sessions into the wiki brain
  - claude_code_session_hook: ingests Claude Code sessions into the wiki brain
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


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

        session_id = ctx.get("session_id") or f"task-{uuid.uuid4().hex[:8]}"
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
    ctx["_cc_session_started"] = True
    ctx["_cc_session_id"] = ctx.get("session_id") or f"cc-{uuid.uuid4().hex[:8]}"
    ctx["_cc_session_prompt"] = ctx.get("prompt", "")[:500]
    return ctx


async def claude_code_session_end_hook(ctx: dict[str, Any]) -> dict[str, Any]:
    """Ingest completed Claude Code sessions into the wiki brain."""
    if not ctx.get("_cc_session_started"):
        return ctx
    try:
        import uuid

        from core.wiki_bridge import claude_code_write_session

        session_id = ctx.get("_cc_session_id") or f"cc-{uuid.uuid4().hex[:8]}"
        report = ctx.get("report", "")
        await claude_code_write_session(
            session_md=(
                f"# Claude Code Session\n\n"
                f"**ID**: {session_id}\n\n"
                f"## Prompt\n\n{ctx.get('_cc_session_prompt', '')}\n\n"
                f"## Result\n\n{report[:2000]}"
            ),
            summary=f"CC session: {report[:100]}",
        )
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


def register_builtin_hooks() -> None:
    """Register all built-in hooks on the global HookSystem."""
    from core.hooks import get_hooks
    from core.wiki_bridge import _ensure_opencode_dirs

    hooks = get_hooks()
    hooks.register("post_llm_call", audit_logger_hook, name="audit_logger")
    hooks.register("command_received", command_audit_hook, name="command_audit")
    hooks.register("post_llm_call", opencode_decision_hook, name="opencode_decision")
    hooks.register("pre_llm_call", claude_code_session_start_hook, name="cc_session_start")
    hooks.register("post_llm_call", claude_code_session_end_hook, name="cc_session_end")

    from core.incremental_summary import incremental_summary_pre_compact_hook

    hooks.register("pre_compact", incremental_summary_pre_compact_hook, name="incremental_summary_pre_compact")
    hooks.register("post_compact", _post_compact_reset_hook, name="incremental_summary_reset")
    hooks.register("pre_compact", _compaction_event_hook, name="compaction_event_pre")
    hooks.register("post_compact", _compaction_event_hook, name="compaction_event_post")

    _ensure_opencode_dirs()
    logger.info("Built-in hooks registered")
