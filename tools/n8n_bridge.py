"""Lightweight n8n bridge and status helpers."""

from __future__ import annotations

import asyncio
import logging
import os
import subprocess
from pathlib import Path
from typing import Any

import aiohttp
from aiohttp import web

logger = logging.getLogger(__name__)

N8N_PORT = int(os.getenv("N8N_WEBHOOK_PORT", "7835"))
N8N_BASE_URL = os.getenv("N8N_BASE_URL", f"http://127.0.0.1:{N8N_PORT}")
N8N_DATA_DIR = Path(os.path.expanduser("~/.legion/n8n"))
N8N_DATA_DIR.mkdir(parents=True, exist_ok=True)

_server_task: asyncio.Task | None = None


async def n8n_status() -> dict[str, Any]:
    """Check whether n8n is reachable."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{N8N_BASE_URL}/healthz", timeout=aiohttp.ClientTimeout(total=3)) as resp:
                return {"healthy": resp.status == 200, "status": resp.status, "base_url": N8N_BASE_URL}
    except Exception as exc:
        return {"healthy": False, "error": str(exc), "base_url": N8N_BASE_URL}


async def _run_listener() -> None:
    async def handle_webhook(request: web.Request) -> web.Response:
        payload = await request.json() if request.can_read_body else {}
        logger.info("n8n webhook received: %s", payload)
        return web.json_response({"ok": True})

    app = web.Application()
    app.router.add_post("/webhook", handle_webhook)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=N8N_PORT)
    await site.start()
    logger.info("n8n webhook listener running on :%s", N8N_PORT)
    while True:
        await asyncio.sleep(3600)


def start_n8n_webhook_listener() -> asyncio.Task | None:
    """Start the webhook listener if enabled."""
    global _server_task
    if os.getenv("ENABLE_N8N_LISTENER", "true").lower() not in {"1", "true", "yes", "on"}:
        return None
    if _server_task and not _server_task.done():
        return _server_task
    _server_task = asyncio.create_task(_run_listener())
    return _server_task


async def ensure_n8n_running() -> dict[str, Any]:
    """Try to start a local n8n instance via docker compose if available."""
    if os.getenv("ENABLE_N8N_AUTO_START", "false").lower() not in {"1", "true", "yes", "on"}:
        return {"started": False, "reason": "auto-start disabled"}
    try:
        proc = await asyncio.to_thread(
            subprocess.run,
            ["docker", "compose", "up", "-d", "n8n"],
            check=False,
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).resolve().parent.parent),
        )
        return {"started": proc.returncode == 0, "returncode": proc.returncode, "stdout": proc.stdout[-1200:], "stderr": proc.stderr[-1200:]}
    except Exception as exc:
        return {"started": False, "error": str(exc)}
