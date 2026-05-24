"""Open Interpreter bridge for computer-control fallback."""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

_OI_AVAILABLE = False
try:
    import interpreter as oi  # type: ignore
    _OI_AVAILABLE = True
except Exception:
    oi = None  # type: ignore[assignment]
    logger.warning("open-interpreter not installed — pip install open-interpreter")


def _configure_oi() -> None:
    """Configure Open Interpreter with Legion defaults."""
    if not _OI_AVAILABLE or oi is None:
        return
    oi.llm.model = os.getenv("OI_MODEL", "minimax-coding-plan/MiniMax-Text-01")
    oi.llm.api_key = os.getenv("MINIMAX_API_KEY", "")
    oi.auto_run = True
    oi.safe_mode = "off"
    oi.verbose = False
    oi.system_message = (
        "You are Legion, Bashara's autonomous AI coworker on Ubuntu Linux. "
        "Execute tasks directly. Verify results."
    )


async def oi_execute(task: str, max_output_chars: int = 3000) -> str:
    """Execute a task via Open Interpreter."""
    if not _OI_AVAILABLE or oi is None:
        return "❌ Open Interpreter not installed — pip install open-interpreter"

    def _run() -> str:
        _configure_oi()
        output_parts: list[str] = []
        try:
            for chunk in oi.chat(task, display=False, stream=True):
                if isinstance(chunk, dict):
                    content = chunk.get("content", "")
                    role = chunk.get("role", "")
                    ctype = chunk.get("type", "")
                    if role == "computer" and ctype == "console":
                        output_parts.append(f"$ {content}")
                    elif role == "assistant" and ctype == "message":
                        output_parts.append(content)
            result = "\n".join(output_parts)
            return result[:max_output_chars] if result else "Task completed (no output)"
        except Exception as exc:
            return f"Open Interpreter error: {exc}"

    return await asyncio.to_thread(_run)


async def oi_is_available() -> bool:
    """Return whether Open Interpreter can be used."""
    return _OI_AVAILABLE
