"""openclaw_bridge.py — Delegate tasks to OpenClaw for 50+ integrations.

OpenClaw runs alongside Legion on the same machine.
Legion delegates smart home, Apple Notes, Obsidian, Spotify, etc. to OpenClaw.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

import aiohttp

logger = logging.getLogger(__name__)

OPENCLAW_PORT = int(os.getenv("OPENCLAW_PORT", "3456"))
OPENCLAW_BASE_URL = f"http://localhost:{OPENCLAW_PORT}"

# Keywords that should be delegated to OpenClaw
OPENCLAW_KEYWORDS = [
    "apple notes", "obsidian", "things3", "philips hue", "smart home",
    "spotify", "apple music", "trello", "linear", "notion",
    "homekit", "smart lights", "smart plug", "iot",
]


async def is_openclaw_running() -> bool:
    """Check if OpenClaw is running via health endpoint."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{OPENCLAW_BASE_URL}/health",
                timeout=aiohttp.ClientTimeout(total=5),
            ) as resp:
                return resp.status == 200
    except Exception:
        return False


async def delegate_to_openclaw(task: str, context: Optional[str] = None) -> str:
    """Send task to OpenClaw's API, return result."""
    payload = {"task": task}
    if context:
        payload["context"] = context

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{OPENCLAW_BASE_URL}/api/task",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("result", data.get("response", str(data)))
                return f"OpenClaw returned HTTP {resp.status}"
    except aiohttp.ClientConnectorError:
        return (
            "OpenClaw is not running.\n"
            "Start it: cd ~/openclaw && npm start\n"
            f"Expected at: {OPENCLAW_BASE_URL}"
        )
    except Exception as e:
        return f"OpenClaw error: {e}"


async def openclaw_integrations() -> str:
    """List all installed OpenClaw skills/integrations."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{OPENCLAW_BASE_URL}/api/skills",
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    skills = data if isinstance(data, list) else data.get("skills", [])
                    lines = ["<b>OpenClaw Integrations</b>\n"]
                    for skill in skills:
                        if isinstance(skill, dict):
                            name = skill.get("name", "?")
                            desc = skill.get("description", "")[:50]
                            lines.append(f"  - {name}: {desc}")
                        else:
                            lines.append(f"  - {skill}")
                    return "\n".join(lines)
                return f"Failed to list skills: HTTP {resp.status}"
    except Exception as e:
        return f"OpenClaw unavailable: {e}"


def should_delegate_to_openclaw(task: str) -> bool:
    """Check if a task matches OpenClaw-specific integrations."""
    task_lower = task.lower()
    return any(kw in task_lower for kw in OPENCLAW_KEYWORDS)
