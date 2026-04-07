"""Voice engine wrapper for pre-warm and configuration."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

VOICE_ROOT = Path.home() / ".legion" / "voice"
VOICE_ROOT.mkdir(parents=True, exist_ok=True)


def prewarm_voice_engine() -> None:
    """Touch voice dependencies so the first message is faster."""
    try:
        from core.utils.multimodal_processor import TTS_VOICE
        logger.info("Voice engine prewarmed with voice %s", TTS_VOICE)
    except Exception as exc:
        logger.debug("Voice engine prewarm skipped: %s", exc)


async def run_prewarm() -> None:
    """Async wrapper for startup hooks."""
    await asyncio.to_thread(prewarm_voice_engine)
