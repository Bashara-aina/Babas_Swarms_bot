"""Open Interpreter bridge (tools/oi_bridge.py)."""

from __future__ import annotations

from tools.oi_bridge import oi_execute, oi_is_available


async def run_interpreter_task(task: str, max_output_chars: int = 3000) -> str:
    return await oi_execute(task, max_output_chars=max_output_chars)


async def interpreter_available() -> bool:
    return await oi_is_available()
