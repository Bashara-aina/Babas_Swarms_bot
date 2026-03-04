# /home/newadmin/swarm-bot/interpreter_bridge.py
"""Open Interpreter ↔ Ollama bridge.

Runs interpreter in a thread-pool executor to stay non-blocking.
Output is chunked to 4000 chars for Telegram's hard message limit.
"""

from __future__ import annotations

import asyncio
import logging
import subprocess
from typing import AsyncIterator

from interpreter import interpreter

logger = logging.getLogger(__name__)

TELEGRAM_CHUNK_SIZE = 4000


def _configure_interpreter(model: str) -> None:
    """Apply required interpreter settings for local Ollama use.

    Args:
        model: Full Ollama model string, e.g. "ollama_chat/phi4".
    """
    interpreter.llm.model = model
    interpreter.llm.api_base = "http://localhost:11434"
    interpreter.offline = True
    interpreter.auto_run = True
    interpreter.safe_mode = False


def _prewarm_model(model: str) -> None:
    """Ensure Ollama has the model loaded before interpreter starts.

    Runs `ollama run <bare_model> ""` synchronously.

    Args:
        model: Full model string like "ollama_chat/phi4".
    """
    bare = model.removeprefix("ollama_chat/")
    logger.debug("Pre-warming Ollama model: %s", bare)
    try:
        subprocess.run(
            ["ollama", "run", bare, ""],
            timeout=60,
            capture_output=True,
            check=False,
        )
    except subprocess.TimeoutExpired:
        logger.warning("Pre-warm timed out for %s — continuing anyway", bare)
    except FileNotFoundError:
        logger.error("ollama binary not found — skipping pre-warm")


def _run_interpreter_sync(model: str, task: str) -> str:
    """Blocking interpreter call — run this in an executor.

    Args:
        model: Full Ollama model string.
        task: Task text to execute.

    Returns:
        Concatenated text output from interpreter.
    """
    _configure_interpreter(model)
    _prewarm_model(model)

    try:
        messages = interpreter.chat(task, display=False, stream=False)
    except Exception as exc:
        logger.exception("Interpreter error: %s", exc)
        return f"Interpreter error: {exc}"

    # Collect all text-type message content
    parts: list[str] = []
    for msg in messages:
        if isinstance(msg, dict):
            content = msg.get("content") or ""
            if isinstance(content, str) and content.strip():
                parts.append(content.strip())
        elif isinstance(msg, str) and msg.strip():
            parts.append(msg.strip())

    return "\n\n".join(parts) if parts else "No output returned."


async def run_task(model: str, task: str) -> str:
    """Run an interpreter task asynchronously.

    Args:
        model: Full Ollama model string, e.g. "ollama_chat/coding".
        task: Task description / code to execute.

    Returns:
        Full output string (may be multiple kilobytes).
    """
    loop = asyncio.get_event_loop()
    result: str = await loop.run_in_executor(
        None, _run_interpreter_sync, model, task
    )
    return result


def chunk_output(text: str, size: int = TELEGRAM_CHUNK_SIZE) -> list[str]:
    """Split text into Telegram-safe chunks.

    Args:
        text: Full output string.
        size: Max chars per chunk (default 4000).

    Returns:
        List of string chunks, each ≤ size chars.
    """
    if not text:
        return ["(empty output)"]
    return [text[i : i + size] for i in range(0, len(text), size)]


async def stream_chunks(model: str, task: str) -> AsyncIterator[str]:
    """Async generator yielding output chunks as they become available.

    Runs the full interpreter task then yields chunks sequentially.

    Args:
        model: Full Ollama model string.
        task: Task to execute.

    Yields:
        String chunks ≤ TELEGRAM_CHUNK_SIZE chars.
    """
    full_output = await run_task(model, task)
    for chunk in chunk_output(full_output):
        yield chunk
