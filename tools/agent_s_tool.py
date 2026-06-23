"""
Agent-S style GUI control — optional ``agent_s`` package, else OpenHands webhook, else safe message.

Install on Ubuntu when available: ``pip install agent-s`` (project-specific; verify upstream).
"""

from __future__ import annotations

import asyncio
import logging
import os

import httpx

logger = logging.getLogger(__name__)

_DANGEROUS = ("rm ", "delete", "drop table", "format", "sudo rm", "mkfs", "dd if=")


class AgentSTool:
    def __init__(self) -> None:
        self.engine_type = os.getenv("AGENT_S_ENGINE", "anthropic")
        self.model = os.getenv("AGENT_S_MODEL", "claude-sonnet-4-20250514")

    def _blocked(self, task: str) -> str | None:
        low = task.lower()
        if any(k in low for k in _DANGEROUS):
            return (
                "BLOCKED: task mentions a potentially destructive operation. "
                "Confirm explicitly in Telegram before running GUI automation."
            )
        return None

    async def execute_task(self, task: str, context: str | None = None) -> str:
        b = self._blocked(task)
        if b:
            return b
        full = f"Context: {context}\n\nTask: {task}" if context else task

        try:
            from agent_s.api import AgentSAPI  # type: ignore

            def _run() -> str:
                agent = AgentSAPI(
                    engine_params={"engine_type": self.engine_type, "model": self.model}
                )
                return str(agent.run(full))

            return await asyncio.to_thread(_run)
        except Exception as exc:
            logger.info("Agent-S package not available or failed (%s); trying webhook", exc)

        url = (os.getenv("AGENT_S_WEBHOOK_URL") or "").strip()
        if url:
            try:
                async with httpx.AsyncClient(timeout=180.0) as client:
                    r = await client.post(
                        url,
                        json={"task": full, "source": "legion-agent-s-tool"},
                    )
                    r.raise_for_status()
                    data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
                    if isinstance(data, dict) and data.get("result"):
                        return str(data["result"])
                    return r.text[:4000] or "Webhook returned empty body."
            except Exception as exc2:
                logger.warning("agent_s webhook failed: %s", exc2)
                return f"Agent-S webhook error: {exc2}"

        return (
            "Agent-S not installed and AGENT_S_WEBHOOK_URL unset. "
            "Use /do, computer tools, or set OpenHands/Agent-S HTTP endpoint."
        )

    async def take_screenshot(self) -> str:
        import subprocess
        import time

        path = f"/tmp/legion_screenshot_{int(time.time())}.png"
        try:
            subprocess.run(["scrot", path], check=True, timeout=30)
            return path
        except Exception as exc:
            logger.warning("scrot failed: %s", exc)
            return f"Screenshot error: {exc}"


async def agent_s_delegate(task: str, timeout_sec: float = 120.0) -> str:
    """Thin delegate for legacy imports — prefers :class:`AgentSTool`."""
    tool = AgentSTool()
    out = await tool.execute_task(task)
    if out.startswith("Agent-S not installed") and (os.getenv("AGENT_S_WEBHOOK_URL") or "").strip():
        async with httpx.AsyncClient(timeout=timeout_sec) as client:
            r = await client.post(
                os.getenv("AGENT_S_WEBHOOK_URL", "").strip(),
                json={"task": task, "source": "legion-telegram"},
            )
            r.raise_for_status()
            return r.text[:4000]
    return out
