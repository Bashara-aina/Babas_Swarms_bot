from __future__ import annotations

import os
from typing import Any

import aiohttp


async def run_ruflo_workflow(task: str, agents: list[str], model: str = "openrouter/anthropic/claude-3.5-sonnet") -> str:
    if not (os.getenv("OPENROUTER_API_KEY") or os.getenv("ANTHROPIC_API_KEY")):
        return "ruflo disabled: OPENROUTER_API_KEY or ANTHROPIC_API_KEY not set"

    payload: dict[str, Any] = {"task": task, "agents": agents, "model": model}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post("http://127.0.0.1:7834/run", json=payload, timeout=60) as resp:
                data = await resp.json()
                if data.get("success"):
                    return str(data.get("output", ""))
                return f"ruflo error: {data.get('error', 'unknown error')}"
    except Exception as exc:
        return f"ruflo bridge unavailable: {exc}"
