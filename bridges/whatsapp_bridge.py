"""WhatsApp bridge — Python wrapper around the wa_sidecar Node.js process.

Architecture: Same pattern as ruflo sidecar (see bridges/ruflo_bridge.py).
The sidecar (bridges/wa_sidecar/index.js) runs whatsapp-web.js in Puppeteer,
exposes a local HTTP API on port 3002 (WA_SIDECAR_PORT), and this class talks to it.

Usage:
    bridge = WhatsAppBridge()
    await bridge.start_sidecar()     # Launch Node.js process
    qr_bytes = await bridge.get_qr_code()   # PNG QR to scan
    unread = await bridge.get_unread()
    ok = await bridge.send_message("1234567890@c.us", "Hello!")

⚠️ Ban risk note (see plan): whatsapp-web.js uses unofficial reverse-engineering
of WhatsApp Web. Keep usage human-like (rate limiter in sidecar: 1 msg/10s).
If banned, migrate to WhatsApp Business API (1000 free conv/month since 2024).
"""

from __future__ import annotations

import asyncio
import logging
import os
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_SIDECAR_DIR = Path(__file__).parent / "wa_sidecar"
_PORT = int(os.getenv("WA_SIDECAR_PORT", "3002"))
_BASE_URL = f"http://127.0.0.1:{_PORT}"
_sidecar_process: subprocess.Popen | None = None


class WhatsAppBridge:
    """Async interface to the wa_sidecar Node.js process."""

    def __init__(self) -> None:
        self._base = _BASE_URL

    # ── Sidecar lifecycle ─────────────────────────────────────────────────────

    async def start_sidecar(self) -> bool:
        """Launch the Node.js sidecar. Returns True if started/already running."""
        global _sidecar_process

        if await self._is_healthy():
            return True

        # Check that dependencies are installed
        if not (_SIDECAR_DIR / "node_modules").exists():
            logger.info("[WA Bridge] Installing wa_sidecar npm dependencies...")
            proc = await asyncio.create_subprocess_exec(
                "npm", "install", "--prefix", str(_SIDECAR_DIR),
                "--quiet", "--no-fund", "--no-audit",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.wait()

        _sidecar_process = subprocess.Popen(
            ["node", "index.js"],
            cwd=str(_SIDECAR_DIR),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env={**os.environ, "WA_SIDECAR_PORT": str(_PORT)},
        )
        logger.info("[WA Bridge] Sidecar launched (PID %d)", _sidecar_process.pid)

        # Wait for it to become healthy (up to 30s)
        for _ in range(30):
            await asyncio.sleep(1)
            if await self._is_healthy():
                return True
        logger.warning("[WA Bridge] Sidecar did not become healthy within 30s")
        return False

    async def stop_sidecar(self) -> None:
        """Stop the sidecar process."""
        global _sidecar_process
        if _sidecar_process is not None:
            _sidecar_process.terminate()
            _sidecar_process = None

    async def _is_healthy(self) -> bool:
        """Return True if the sidecar HTTP API is responding."""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session, session.get(
                f"{self._base}/health",
                timeout=aiohttp.ClientTimeout(total=3),
            ) as resp:
                return resp.status == 200
        except Exception:
            return False

    async def get_status(self) -> dict[str, Any]:
        """Return {status: ready|qr_pending|initialising, message_count: N}."""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session, session.get(
                f"{self._base}/health",
                timeout=aiohttp.ClientTimeout(total=5),
            ) as resp:
                return await resp.json()
        except Exception as exc:
            return {"status": "offline", "error": str(exc)}

    # ── QR code ───────────────────────────────────────────────────────────────

    async def get_qr_code(self) -> bytes | None:
        """Return PNG QR code bytes, or None if already authenticated."""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session, session.get(
                f"{self._base}/qr",
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 200 and resp.content_type == "image/png":
                    return await resp.read()
                return None
        except Exception as exc:
            logger.warning("[WA Bridge] get_qr_code failed: %s", exc)
            return None

    # ── Messages ──────────────────────────────────────────────────────────────

    async def get_unread(self, limit: int = 20) -> list[dict[str, Any]]:
        """Return up to `limit` unread messages from the ring buffer."""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session, session.get(
                f"{self._base}/messages",
                params={"limit": limit},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                return []
        except Exception as exc:
            logger.warning("[WA Bridge] get_unread failed: %s", exc)
            return []

    async def send_message(self, chat_id: str, body: str) -> bool:
        """Send a WhatsApp message. Returns True on success."""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session, session.post(
                f"{self._base}/send",
                json={"chatId": chat_id, "body": body},
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                data = await resp.json()
                if not data.get("ok"):
                    logger.warning("[WA Bridge] send failed: %s", data.get("error"))
                return bool(data.get("ok"))
        except Exception as exc:
            logger.warning("[WA Bridge] send_message failed: %s", exc)
            return False
