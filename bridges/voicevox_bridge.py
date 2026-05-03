"""VoiceVox TTS bridge — neural voice synthesis with gTTS fallback.

VoiceVox API runs on http://localhost:50021 by default.
If VoiceVox is unavailable (ConnectionRefusedError), falls back to gTTS.

Usage:
    bridge = VoiceVoxBridge()
    audio_bytes = await bridge.synthesize("こんにちは", speed=0.75)
    # Returns mp3 bytes, using VoiceVox if available, gTTS otherwise.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)

_VOICEVOX_HOST = "http://localhost:50021"
_DEFAULT_SPEAKER = 3  # VOICEVOX speaker_id (3 = ずんだもん)


class VoiceVoxBridge:
    """Async TTS bridge with VoiceVox + gTTS fallback."""

    def __init__(self, speaker: int = _DEFAULT_SPEAKER) -> None:
        self.speaker = speaker
        self._voicevox_available: bool | None = None

    # ── VoiceVox query ─────────────────────────────────────────────────────────

    async def _query_voicevox(self, text: str, speed: float = 1.0) -> dict[str, Any]:
        """Call VoiceVox /audio_query then /synthesis. Returns audio bytes."""
        async with aiohttp.ClientSession() as session:
            # Step 1: audio_query
            params = {"text": text, "speaker": self.speaker}
            async with session.post(
                f"{_VOICEVOX_HOST}/audio_query",
                params=params,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                resp.raise_for_status()
                query: dict[str, Any] = await resp.json()

            # Override speed (1.0 = normal)
            if speed != 1.0:
                query["speedScale"] = speed

            # Step 2: synthesis
            async with session.post(
                f"{_VOICEVOX_HOST}/synthesis",
                params={"speaker": self.speaker},
                json=query,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                resp.raise_for_status()
                return await resp.read()

    # ── Public synthesize ───────────────────────────────────────────────────────

    async def synthesize(self, text: str, speed: float = 1.0) -> bytes:
        """Synthesize text to MP3 audio bytes.

        Tries VoiceVox first; falls back to gTTS if VoiceVox is not running.
        Raises exception only if both fail.
        """
        # Check availability lazily (cached)
        if self._voicevox_available is None:
            self._voicevox_available = await self._check_voicevox()

        if self._voicevox_available:
            try:
                return await self._query_voicevox(text, speed=speed)
            except (aiohttp.ClientError, ConnectionRefusedError) as exc:
                logger.warning("[VoiceVox] unavailable, falling back to gTTS: %s", exc)
                self._voicevox_available = False

        # gTTS fallback
        return await self._gtts_fallback(text, speed=speed)

    async def _check_voicevox(self) -> bool:
        """Ping VoiceVox speakers endpoint to check availability."""
        try:
            async with aiohttp.ClientSession() as session, session.get(
                f"{_VOICEVOX_HOST}/speakers",
                timeout=aiohttp.ClientTimeout(total=3),
            ) as resp:
                return resp.status == 200
        except (aiohttp.ClientError, ConnectionRefusedError):
            return False

    @staticmethod
    async def _gtts_fallback(text: str, speed: float = 1.0) -> bytes:
        """Block-only gTTS fallback (no speed control)."""
        # gTTS is synchronous — run in thread pool to avoid blocking event loop
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            _gtts_sync,
            text,
            speed,
        )


def _gtts_sync(text: str, speed: float = 1.0) -> bytes:
    """Synchronous gTTS call (must run in thread pool)."""
    from gtts import gTTS

    # gTTS doesn't support speed; lang 'ja' for Japanese TTS
    tts = gTTS(text=text, lang="ja", slow=(speed < 0.8))
    import io

    buf = io.BytesIO()
    tts.write_to_fp(buf)
    buf.seek(0)
    return buf.read()
