from __future__ import annotations

import os
from typing import Any

import aiohttp


async def run_mastra_workflow(task: str, agents: list[str], endpoint: str = "http://127.0.0.1:7835/run") -> str:
    """Optional TypeScript Mastra sidecar bridge.

    Feature is disabled unless `MASTRA_SIDECAR_URL` is configured or default sidecar is running.
    """
    target = os.getenv("MASTRA_SIDECAR_URL", endpoint)
    payload: dict[str, Any] = {"task": task, "agents": agents}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(target, json=payload, timeout=45) as resp:
                data = await resp.json()
                if data.get("success"):
                    return str(data.get("output", ""))
                return f"mastra error: {data.get('error', 'unknown error')}"
    except Exception as exc:
        return f"mastra bridge unavailable: {exc}"
