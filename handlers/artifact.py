"""Artifact preview — serves generated HTML/JS/CSS on localhost for 10 minutes."""
from __future__ import annotations

import asyncio
import logging
import os
import tempfile
import time
import uuid

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from handlers.shared import is_allowed, send_chunked

logger = logging.getLogger(__name__)
router = Router()

_ARTIFACT_PORT = int(os.getenv("ARTIFACT_PORT", "8765"))
_TTL_SECONDS = 600  # 10 minutes
_active_artifacts: dict[str, tuple[str, float]] = {}  # id -> (path, expires_at)


async def serve_artifact(html_content: str, title: str = "Legion Artifact") -> str:
    """Write HTML to a temp file and return localhost URL. Caller sends URL to user."""
    artifact_id = uuid.uuid4().hex[:8]
    tmp_dir = tempfile.mkdtemp(prefix="legion_artifact_")
    html_path = os.path.join(tmp_dir, "index.html")

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    expires_at = time.time() + _TTL_SECONDS
    _active_artifacts[artifact_id] = (tmp_dir, expires_at)

    asyncio.create_task(_expire_artifact(artifact_id))

    return f"http://localhost:{_ARTIFACT_PORT}/{artifact_id}/"


async def _expire_artifact(artifact_id: str) -> None:
    await asyncio.sleep(_TTL_SECONDS)
    if artifact_id in _active_artifacts:
        tmp_dir, _ = _active_artifacts.pop(artifact_id)
        try:
            import shutil
            shutil.rmtree(tmp_dir, ignore_errors=True)
            logger.debug("Artifact %s expired and cleaned up", artifact_id)
        except Exception:
            pass


async def start_artifact_server() -> None:
    """Start the aiohttp static file server for artifacts. Call in on_startup."""
    try:
        from aiohttp import web

        async def handler(request: web.Request) -> web.Response:
            parts = request.path.strip("/").split("/", 1)
            artifact_id = parts[0] if parts else ""
            file_path = parts[1] if len(parts) > 1 else "index.html"

            if artifact_id not in _active_artifacts:
                return web.Response(text="Artifact expired or not found", status=404)

            tmp_dir, expires_at = _active_artifacts[artifact_id]
            if time.time() > expires_at:
                return web.Response(text="Artifact expired", status=410)

            full_path = os.path.join(tmp_dir, file_path or "index.html")
            if not os.path.exists(full_path):
                full_path = os.path.join(tmp_dir, "index.html")

            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()

            content_type = "text/html"
            if file_path.endswith(".css"):
                content_type = "text/css"
            elif file_path.endswith(".js"):
                content_type = "application/javascript"

            return web.Response(text=content, content_type=content_type)

        app = web.Application()
        app.router.add_get("/{artifact_id}/{file:.*}", handler)
        app.router.add_get("/{artifact_id}", handler)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", _ARTIFACT_PORT)
        await site.start()
        logger.info("Artifact server running on http://0.0.0.0:%d", _ARTIFACT_PORT)
    except ImportError:
        logger.warning("aiohttp not installed — artifact server disabled")


@router.message(Command("preview"))
async def cmd_preview(msg: Message) -> None:
    """Usage: /preview <html content>
    Serves the HTML and returns a localhost URL valid for 10 minutes.
    """
    if not is_allowed(msg):
        return
    raw = (msg.text or "").removeprefix("/preview").strip()
    if not raw:
        await msg.answer(
            "Usage: <code>/preview &lt;html&gt;</code>\n"
            "Or let the bot auto-preview when it generates HTML code.",
            parse_mode="HTML",
        )
        return
    url = await serve_artifact(raw, title="Legion Preview")
    await msg.answer(
        f"🌐 Preview ready (10 min):\n<code>{url}</code>\n\n"
        "Open in browser on this machine.",
        parse_mode="HTML",
    )
