"""Webhook server for receiving external events (GitHub, system alerts, etc.)."""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
import os
from typing import Any, Awaitable, Callable

from aiohttp import web

logger = logging.getLogger(__name__)


class WebhookServer:
    """Async webhook server using aiohttp to receive and dispatch external events."""

    def __init__(self, port: int = 8743) -> None:
        self.port = port
        self._handlers: dict[str, Callable[[dict[str, Any]], Awaitable[None]]] = {}
        self._app = web.Application()
        self._app.router.add_post("/webhook/{source}", self._handle)
        self._runner: web.AppRunner | None = None

    def register(self, source: str, handler: Callable[[dict[str, Any]], Awaitable[None]]) -> None:
        """Register a handler for a given webhook source."""
        self._handlers[source] = handler

    def _validate_github(self, payload: bytes, signature: str | None, secret: str) -> bool:
        """Validate GitHub webhook signature using HMAC-SHA256."""
        if not signature:
            return False
        expected = "sha256=" + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)

    async def _handle(self, request: web.Request) -> web.Response:
        """Handle incoming webhook POST requests."""
        source = request.match_info["source"]
        payload = await request.read()
        signature = request.headers.get("X-Hub-Signature-256")

        secret_key = f"WEBHOOK_SECRET_{source.upper()}"
        secret = os.getenv(secret_key, "")

        if source == "github" and secret:
            if not self._validate_github(payload, signature, secret):
                return web.Response(status=401, text="Invalid signature")

        try:
            data = json.loads(payload) if payload else {}
        except Exception:
            data = {}

        handler = self._handlers.get(source)
        if handler:
            try:
                await handler(data)
            except Exception as e:
                logger.error(f"Webhook handler error for {source}: {e}")

        return web.Response(status=200, text="OK")

    async def start(self) -> None:
        """Start the webhook server on the configured port."""
        self._runner = web.AppRunner(self._app)
        await self._runner.setup()
        site = web.TCPSite(self._runner, "0.0.0.0", self.port)
        await site.start()
        logger.info(f"Webhook server listening on port {self.port}")


WEBHOOK_SERVER = WebhookServer()
