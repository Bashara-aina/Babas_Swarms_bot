"""Lightweight HTTP health endpoint for external uptime monitors.

Exposes GET /health → 200 {"status": "ok", "bot": "@LegionBot"}

Usage in main.py on_startup:
    from core.health import start_health_server
    asyncio.create_task(start_health_server(port=8080))
"""
import asyncio
import json
import logging
from aiohttp import web

logger = logging.getLogger(__name__)

_BOT_USERNAME = "LegionBot"


async def _health_handler(request: web.Request) -> web.Response:
    return web.Response(
        text=json.dumps({"status": "ok", "bot": f"@{_BOT_USERNAME}"}),
        content_type="application/json",
        status=200,
    )


async def start_health_server(port: int = 8080, bot_username: str = "LegionBot") -> None:
    """Start the health HTTP server on the given port."""
    global _BOT_USERNAME
    _BOT_USERNAME = bot_username

    app = web.Application()
    app.router.add_get("/health", _health_handler)
    app.router.add_get("/", _health_handler)  # root alias

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info("Health endpoint running on http://0.0.0.0:%d/health", port)
    # Keep running indefinitely
    while True:
        await asyncio.sleep(3600)
