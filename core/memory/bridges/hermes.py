"""core/memory/bridges/hermes.py — Fan out observations to hermes MCP memory.

Maps each observation to a hermes memory_save call with key `obs:{obs_id}`.
Session summaries also call memory_share_write so swarm agents see them.
Hermes being offline is non-fatal — the observation lives in SQLite and can
be backfilled later.
"""
from __future__ import annotations

import logging
import re
from typing import Any

from ._base import BridgeState

logger = logging.getLogger(__name__)

_PRIVATE_RE = re.compile(r"<private>[\s\S]*?</private>", re.IGNORECASE)


def _scrub(payload: dict[str, Any]) -> dict[str, Any]:
    out = {}
    for k, v in payload.items():
        if isinstance(v, str):
            out[k] = _PRIVATE_RE.sub("", v).strip()
        else:
            out[k] = v
    return out


async def _memory_save(key: str, value: dict[str, Any], decay_rate: float = 0.1) -> None:
    """Real impl: calls mcp__hermes__memory_save. Stub here; real wiring in Task 10."""
    raise NotImplementedError("wire to mcp__hermes__memory_save in Task 10")


async def _memory_share_write(key: str, value: dict[str, Any]) -> None:
    """Real impl: calls mcp__hermes__memory_share_write. Stub for now."""
    raise NotImplementedError("wire to mcp__hermes__memory_share_write in Task 10")


class HermesBridge:
    name = "hermes"

    def __init__(self) -> None:
        self.state = BridgeState(name=self.name)

    async def push(self, obs_id: int, obs_payload: dict[str, Any]) -> None:
        await self.state.load()
        if obs_id <= self.state.last_pushed_id:
            return
        clean = _scrub(obs_payload)
        key = f"obs:{obs_id}"
        try:
            await _memory_save(key, clean)
        except Exception as e:  # noqa: BLE001
            logger.warning("[hermes] memory_save failed for %s: %s", key, e)
            return
        if clean.get("type") == "session_summary":
            try:
                await _memory_share_write(key, clean)
            except Exception as e:  # noqa: BLE001
                logger.warning("[hermes] memory_share_write failed for %s: %s", key, e)
        await self.state.advance_to(obs_id)

    async def health(self) -> dict[str, Any]:
        await self.state.load()
        return {
            "ok": True,
            "name": self.name,
            "last_pushed_id": self.state.last_pushed_id,
        }
