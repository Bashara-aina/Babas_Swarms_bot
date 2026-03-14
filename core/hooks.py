"""core/hooks.py — Lightweight async lifecycle hook system for Legion.

Events emitted at key points in agent execution:
  pre_llm_call     — before litellm API call
  post_llm_call    — after litellm API call (with response + token counts)
  pre_tool_use     — before computer_agent tool execution
  post_tool_use    — after computer_agent tool execution
  command_received — when a Telegram command is dispatched
  response_sent    — after bot sends a reply to the user
  error_occurred   — on any caught exception in the pipeline

Hooks are async callables: async def my_hook(ctx: dict) -> dict
They receive a context dict, may modify it, and return it.
Hooks run in registration order per event.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Callable, Coroutine

logger = logging.getLogger(__name__)

HookFn = Callable[[dict[str, Any]], Coroutine[Any, Any, dict[str, Any]]]

# All recognized event names
EVENTS = frozenset({
    "pre_llm_call",
    "post_llm_call",
    "pre_tool_use",
    "post_tool_use",
    "command_received",
    "response_sent",
    "error_occurred",
})


class HookSystem:
    """Registry and executor for lifecycle hooks."""

    def __init__(self) -> None:
        self._hooks: dict[str, list[tuple[str, HookFn]]] = {e: [] for e in EVENTS}

    def register(self, event: str, fn: HookFn, name: str = "") -> None:
        """Register a hook function for an event.

        Args:
            event: One of the EVENTS constants.
            fn: Async callable receiving and returning a context dict.
            name: Optional human-readable label (defaults to fn.__name__).
        """
        if event not in EVENTS:
            logger.warning("Unknown hook event %r — registering anyway", event)
            self._hooks.setdefault(event, [])
        label = name or getattr(fn, "__name__", "anonymous")
        self._hooks[event].append((label, fn))
        logger.debug("Hook registered: %s → %s", event, label)

    async def emit(self, event: str, ctx: dict[str, Any]) -> dict[str, Any]:
        """Fire all hooks for *event* in order, threading ctx through each.

        If a hook raises, the error is logged and the next hook still runs.
        Returns the (possibly modified) context dict.
        """
        hooks = self._hooks.get(event, [])
        if not hooks:
            return ctx

        for label, fn in hooks:
            try:
                result = await asyncio.wait_for(fn(ctx), timeout=5.0)
                if isinstance(result, dict):
                    ctx = result
            except asyncio.TimeoutError:
                logger.warning("Hook %s:%s timed out (5s)", event, label)
            except Exception:
                logger.exception("Hook %s:%s raised", event, label)
        return ctx

    def clear(self, event: str | None = None) -> None:
        """Remove all hooks for *event*, or all hooks if event is None."""
        if event is None:
            for e in self._hooks:
                self._hooks[e] = []
        elif event in self._hooks:
            self._hooks[event] = []

    def list_hooks(self) -> dict[str, list[str]]:
        """Return {event: [hook_names]} for introspection."""
        return {
            event: [label for label, _ in hooks]
            for event, hooks in self._hooks.items()
            if hooks
        }


# ── Singleton ────────────────────────────────────────────────────────────────

_instance: HookSystem | None = None


def get_hooks() -> HookSystem:
    """Return the global HookSystem singleton."""
    global _instance
    if _instance is None:
        _instance = HookSystem()
    return _instance
