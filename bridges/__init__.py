"""Bridges layer — all bridge modules wrapped with graceful fallback.

Each bridge import is wrapped in try/except so the bot can start
even if optional sidecar services are not running.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

__all__ = [
    "WhatsAppBridge",
    "ScreenpipeBridge",
    "start_discord_bridge",
    "run_mastra_workflow",
    "run_ruflo_workflow",
    "VoiceVoxBridge",
    "GitHubBridge",
    "GitHubIntelEngine",
    "TrendingRepo",
    "RepoEvaluation",
    "meet_join_url",
    "build_room_token",
    "livekit_status_message",
]

# ── WhatsApp bridge ────────────────────────────────────────────────────────────
try:
    from bridges.whatsapp_bridge import WhatsAppBridge
except Exception as exc:  # noqa: BLE001
    logger.warning("[bridges] whatsapp_bridge unavailable: %s", exc)
    WhatsAppBridge = None  # type: ignore[assignment, misc]

# ── Discord bridge ────────────────────────────────────────────────────────────
try:
    from bridges.discord_bridge import start_discord_bridge
except Exception as exc:  # noqa: BLE001
    logger.warning("[bridges] discord_bridge unavailable: %s", exc)
    start_discord_bridge = None  # type: ignore[assignment, misc]

# ── Mastra bridge ─────────────────────────────────────────────────────────────
try:
    from bridges.mastra_bridge import run_mastra_workflow
except Exception as exc:  # noqa: BLE001
    logger.warning("[bridges] mastra_bridge unavailable: %s", exc)
    run_mastra_workflow = None  # type: ignore[assignment, misc]

# ── RUFLO bridge ──────────────────────────────────────────────────────────────
try:
    from bridges.ruflo_bridge import run_ruflo_workflow
except Exception as exc:  # noqa: BLE001
    logger.warning("[bridges] ruflo_bridge unavailable: %s", exc)
    run_ruflo_workflow = None  # type: ignore[assignment, misc]

# ── Screenpipe bridge ─────────────────────────────────────────────────────────
try:
    from bridges.screenpipe_bridge import ScreenpipeBridge
except Exception as exc:  # noqa: BLE001
    logger.warning("[bridges] screenpipe_bridge unavailable: %s", exc)
    ScreenpipeBridge = None  # type: ignore[assignment, misc]

# ── VoiceVox bridge ───────────────────────────────────────────────────────────
try:
    from bridges.voicevox_bridge import VoiceVoxBridge
except Exception as exc:  # noqa: BLE001
    logger.warning("[bridges] voicevox_bridge unavailable: %s", exc)
    VoiceVoxBridge = None  # type: ignore[assignment, misc]

# ── LiveKit bridge ────────────────────────────────────────────────────────────
try:
    from bridges.livekit_bridge import build_room_token, livekit_status_message, meet_join_url
except Exception as exc:  # noqa: BLE001
    logger.warning("[bridges] livekit_bridge unavailable: %s", exc)
    meet_join_url = None  # type: ignore[assignment, misc]
    build_room_token = None  # type: ignore[assignment, misc]
    livekit_status_message = None  # type: ignore[assignment, misc]

# ── GitHub bridge ─────────────────────────────────────────────────────────────
try:
    from bridges.github_bridge import GitHubBridge, GitHubIntelEngine, RepoEvaluation, TrendingRepo
except Exception as exc:  # noqa: BLE001
    logger.warning("[bridges] github_bridge unavailable: %s", exc)
    GitHubBridge = None  # type: ignore[assignment, misc]
    GitHubIntelEngine = None  # type: ignore[assignment, misc]
    TrendingRepo = None  # type: ignore[assignment, misc]
    RepoEvaluation = None  # type: ignore[assignment, misc]
