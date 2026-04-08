"""LiveKit room helpers — Pipecat worker runs separately."""

from __future__ import annotations

import os
import urllib.parse


def build_room_token(identity: str, room: str, ttl_sec: int = 3600) -> str:
    """Return access token for client join when livekit-api + env are available."""
    key = (os.getenv("LIVEKIT_API_KEY") or "").strip()
    secret = (os.getenv("LIVEKIT_API_SECRET") or "").strip()
    url = (os.getenv("LIVEKIT_URL") or "").strip()
    if not key or not secret or not url:
        return ""
    try:
        from datetime import timedelta

        from livekit.api import AccessToken, VideoGrants  # type: ignore

        grant = VideoGrants(room_join=True, room=room)
        at = (
            AccessToken(key, secret)
            .with_identity(identity)
            .with_ttl(timedelta(seconds=ttl_sec))
            .with_grants(grant)
        )
        return at.to_jwt()
    except Exception:
        return ""


def livekit_status_message() -> str:
    url = (os.getenv("LIVEKIT_URL") or "").strip()
    if not url:
        return "LiveKit not configured (LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET)."
    return f"LiveKit URL set: {url}\nPipecat/voice worker is not started by the bot process."


def meet_join_url(token: str, *, room: str = "legion") -> str:
    """Browser join link for LiveKit Meet (client still needs a running Pipecat worker in the room)."""
    lk = (os.getenv("LIVEKIT_URL") or "").strip()
    if not lk or not (token or "").strip():
        return ""
    q_url = urllib.parse.quote(lk, safe="")
    q_tok = urllib.parse.quote(token.strip(), safe="")
    return (
        f"https://meet.livekit.io/custom?liveKitUrl={q_url}&token={q_tok}"
        f"&room={urllib.parse.quote(room, safe='')}"
    )
