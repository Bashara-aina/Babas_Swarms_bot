from __future__ import annotations

import os
from typing import Any

import aiohttp


async def run_ruflo_workflow(task: str, agents: list[str], model: str = "minimax-coding-plan/MiniMax-M2.7") -> str:
    if not os.getenv("MINIMAX_API_KEY"):
        return "ruflo disabled: MINIMAX_API_KEY not set"

    payload: dict[str, Any] = {"task": task, "agents": agents, "model": model}
    try:
        async with aiohttp.ClientSession() as session, session.post(
            "http://127.0.0.1:7834/run", json=payload, timeout=aiohttp.ClientTimeout(total=60)
        ) as resp:
            data = await resp.json()
            if data.get("success"):
                return str(data.get("output", ""))
            return f"ruflo error: {data.get('error', 'unknown error')}"
    except Exception as exc:
        return f"ruflo bridge unavailable: {exc}"