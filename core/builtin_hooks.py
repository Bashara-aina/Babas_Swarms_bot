"""core/builtin_hooks.py — Default hooks registered at startup.

Currently provides:
  - audit_logger_hook: writes every LLM call to the audit_log table
  - opencode_session_hook: ingests OpenCode task sessions into the wiki brain
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


def register_builtin_hooks() -> None:
    """Register all built-in hooks on the global HookSystem."""
    from core.hooks import get_hooks
    from core.wiki_bridge import _ensure_opencode_dirs

    hooks = get_hooks()
    hooks.register("post_llm_call", audit_logger_hook, name="audit_logger")
    hooks.register("command_received", command_audit_hook, name="command_audit")
    hooks.register("post_llm_call", opencode_decision_hook, name="opencode_decision")

    _ensure_opencode_dirs()
    logger.info("Built-in hooks registered")
