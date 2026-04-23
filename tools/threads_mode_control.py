"""Shared Threads campaign mode control (bot + CLI)."""

from __future__ import annotations

from tools.persistence import kv_get, kv_set

THREADS_MODE_KEY = "threads_campaign_mode_enabled"
THREADS_WORKSPACE_URL = "https://www.threads.com/@rumahlabuh"


async def is_enabled() -> bool:
    """Return whether Threads campaign mode is active."""
    value = await kv_get(THREADS_MODE_KEY)
    if value is None:
        return False
    return value.lower() in {"1", "true", "yes", "on"}


async def set_enabled(enabled: bool) -> None:
    """Persist Threads campaign mode state."""
    await kv_set(THREADS_MODE_KEY, "true" if enabled else "false")


async def toggle() -> bool:
    """Flip mode state and return the new state."""
    new_state = not await is_enabled()
    await set_enabled(new_state)
    return new_state


async def open_workspace() -> str:
    """Open the Rumahlabuh Threads workspace in Chrome/desktop browser."""
    from computer_agent import open_url

    return await open_url(THREADS_WORKSPACE_URL)
