"""Legion Anti-Slop Integration — Drop-in wrapper for llm_client.

LegionQualityGateway wraps llm_client.chat() with the 4-guard pipeline.
Can be enabled/disabled per-session. Follows the existing gateway wrapper pattern.

Usage:
    gateway = LegionQualityGateway()
    response, quality_result = await gateway.chat_with_quality(
        text="your question",
        task="optional task hint",
        agent_key="coding",
    )

    # Or use the decorator
    @anti_slop
    async def my_llm_call(text: str) -> str:
        ...
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import TypeVar

from legion.anti_slop.core import (
    QualityResult,
    get_slop_stats,
    quarantine_response,
    run_quality_gate,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")

# ── LegionQualityGateway ────────────────────────────────────────────────────────


@dataclass
class LegionQualityGateway:
    """Drop-in wrapper for llm_client with 4-guard anti-slop pipeline.

    Attributes:
        enabled: If False, bypasses quality gate (passthrough to llm_client).
        quarantine_on_reject: If True, quarantines rejected content.

    Example:
        gateway = LegionQualityGateway()
        text, result = await gateway.chat_with_quality(
            text="how do I fix the memory leak?",
            task="debug",
            agent_key="debug",
        )
        if result.verdict == "REJECT":
            text = "Sorry, I can't provide that response."
    """

    enabled: bool = True
    quarantine_on_reject: bool = True

    async def chat_with_quality(
        self,
        text: str,
        task: str | None = None,
        agent_key: str | None = None,
        **kwargs,
    ) -> tuple[str, QualityResult]:
        """Call llm_client.chat() and run quality gate on the response.

        Args:
            text: The user's message/prompt.
            task: Optional task hint for the LLM.
            agent_key: Optional agent key override.
            **kwargs: Additional arguments passed to llm_client.chat().

        Returns:
            Tuple of (response_text, QualityResult).
            If quality gate rejects, response_text will be the quarantine path.
        """
        if not self.enabled:
            # Passthrough mode — just call the LLM
            response, model = await self._call_llm(text, task, agent_key, **kwargs)
            result = QualityResult(
                verdict="PASS",
                score=1.0,
                reason="quality_gate_disabled",
                guard_triggered=None,
                latency_ms=0.0,
            )
            return response, result

        # Call LLM
        response, model = await self._call_llm(text, task, agent_key, **kwargs)

        # Run quality gate (internally updates stats via _update_stats)
        quality_result = await run_quality_gate(content=response, query=text)

        # Handle rejection
        if quality_result.verdict == "REJECT" and self.quarantine_on_reject:
            q_path = await quarantine_response(response, text, quality_result)
            quality_result.quarantined = True
            quality_result.quarantine_path = str(q_path)
            logger.warning(
                "Anti-slop rejected response for query '%s...': %s",
                text[:50],
                quality_result.reason,
            )

        return response, quality_result

    async def _call_llm(
        self,
        text: str,
        task: str | None,
        agent_key: str | None,
        **kwargs,
    ) -> tuple[str, str]:
        """Call the underlying LLM client."""
        from llm_client import chat

        return await chat(
            task=text,
            agent_key=agent_key,
            **kwargs,
        )


# ── anti_slop decorator ────────────────────────────────────────────────────────


def anti_slop(
    func: Callable[..., Coroutine[None, None, str]] | None = None,
    *,
    quarantine_on_reject: bool = True,
) -> Callable[[Callable[..., Coroutine[None, None, str]]], Callable[..., Coroutine[None, None, str]]]:
    """Decorator to wrap an async LLM call function with anti-slop quality gate.

    Usage:
        @anti_slop
        async def get_response(text: str) -> str:
            response, _ = await llm_client.chat(task=text, agent_key="general")
            return response

        # Or with options:
        @anti_slop(quarantine_on_reject=False)
        async def get_response_no_quarantine(text: str) -> str:
            ...

    Returns the raw response text. If you need QualityResult, use LegionQualityGateway directly.
    """

    def decorator(fn: Callable[..., Coroutine[None, None, str]]) -> Callable[..., Coroutine[None, None, str]]:
        async def wrapper(*args, **kwargs) -> str:
            gateway = LegionQualityGateway(quarantine_on_reject=quarantine_on_reject)
            # Assume first string arg is the text to evaluate
            text_arg = args[0] if args else kwargs.get("text", "")
            if not isinstance(text_arg, str):
                text_arg = str(text_arg)
            response, result = await gateway.chat_with_quality(
                text=text_arg,
                task=kwargs.get("task"),
                agent_key=kwargs.get("agent_key"),
            )
            if result.verdict == "REJECT":
                return f"[Content rejected by quality gate: {result.reason}]"
            return response

        return wrapper

    if func is None:
        # Called with options: @anti_slop(quarantine_on_reject=False)
        return decorator
    else:
        # Called without options: @anti_slop
        return decorator(func)


# ── anti_slop_call — functional interface ──────────────────────────────────────


async def anti_slop_call(
    text: str,
    task: str | None = None,
    agent_key: str | None = None,
    quarantine: bool = True,
) -> tuple[str, QualityResult]:
    """Functional interface to run a single LLM call through anti-slop.

    Args:
        text: The user's message.
        task: Optional task hint.
        agent_key: Optional agent key.
        quarantine: Whether to quarantine rejected content.

    Returns:
        Tuple of (response_text, QualityResult).

    Example:
        response, result = await anti_slop_call(
            "how do I fix the bug?",
            agent_key="debug",
        )
        if result.verdict == "PASS":
            print(response)
    """
    gateway = LegionQualityGateway(quarantine_on_reject=quarantine)
    return await gateway.chat_with_quality(
        text=text,
        task=task,
        agent_key=agent_key,
    )


# ── Convenience helpers ────────────────────────────────────────────────────────


def get_stats() -> dict:
    """Get current anti-slop statistics as a dict."""
    return get_slop_stats().to_dict()


def is_enabled() -> bool:
    """Check if anti-slop is globally enabled."""
    # This could be tied to a config flag in the future
    return True
