"""
Voice room agent — Pipecat + LiveKit run out-of-process.

The Telegram bot only exposes status and token helpers via bridges/livekit_bridge.
"""

from __future__ import annotations

import os


def voice_stack_summary() -> str:
    if not (os.getenv("LIVEKIT_URL") or "").strip():
        return "Voice stack: disabled (no LIVEKIT_URL)."
    return (
        "Voice stack: LiveKit env detected. Run a separate Pipecat worker that "
        "uses the same LIVEKIT_* credentials; the bot does not host the audio session."
    )
