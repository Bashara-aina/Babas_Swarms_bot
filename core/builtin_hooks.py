"""core/builtin_hooks.py — Default hooks registered at startup.

Currently provides:
  - audit_logger_hook: writes every LLM call to the audit_log table
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


def register_builtin_hooks() -> None:
    """Register all built-in hooks on the global HookSystem."""
    from core.hooks import get_hooks
    hooks = get_hooks()
    hooks.register("post_llm_call", audit_logger_hook, name="audit_logger")
    hooks.register("command_received", command_audit_hook, name="command_audit")
    logger.info("Built-in hooks registered")
