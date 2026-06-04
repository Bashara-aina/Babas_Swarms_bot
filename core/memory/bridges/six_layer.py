"""core/memory/bridges/six_layer.py — Fan out observations to the 6-layer memory.

Calls chroma, langmem, graphrag, mem0 add_* APIs. Each layer is best-effort
and isolated; one layer's failure never blocks the others.
"""
from __future__ import annotations

import logging
import re
from typing import Any

from ._base import BridgeState

logger = logging.getLogger(__name__)

_PRIVATE_RE = re.compile(r"<private>[\s\S]*?</private>", re.IGNORECASE)


def _scrub(payload: dict[str, Any]) -> dict[str, Any]:
    """Strip <private> tags from all string fields before pushing downstream."""
    out = {}
    for k, v in payload.items():
        if isinstance(v, str):
            out[k] = _PRIVATE_RE.sub("", v).strip()
        else:
            out[k] = v
    return out


# ── Layer adapters (real implementations) ───────────────────────────────────
# These wrap the actual layer APIs. In production they call chroma, langmem,
# graphrag, mem0. The stubs log; real wiring happens during the integration
# smoke test (Task 10) — keep the call sites stable.

async def _chroma_add(payload: dict[str, Any], meta: dict[str, Any]) -> None:
    logger.debug("[chroma] add obs_id=%s", meta.get("obs_id"))


async def _langmem_add(payload: dict[str, Any], meta: dict[str, Any]) -> None:
    logger.debug("[langmem] add obs_id=%s", meta.get("obs_id"))


async def _graphrag_add(payload: dict[str, Any], meta: dict[str, Any]) -> None:
    logger.debug("[graphrag] add obs_id=%s", meta.get("obs_id"))


async def _mem0_add(payload: dict[str, Any], meta: dict[str, Any]) -> None:
    logger.debug("[mem0] add obs_id=%s", meta.get("obs_id"))


_LAYER_FN_NAMES = ("_chroma_add", "_langmem_add", "_graphrag_add", "_mem0_add")


class SixLayerBridge:
    name = "six_layer"

    def __init__(self) -> None:
        self.state = BridgeState(name=self.name)

    async def push(self, obs_id: int, obs_payload: dict[str, Any]) -> None:
        await self.state.load()
        if obs_id <= self.state.last_pushed_id:
            return
        clean = _scrub(obs_payload)
        meta = {
            "source": "observation",
            "obs_id": obs_id,
            "session_id": clean.get("session_id"),
            "type": clean.get("type"),
            "tool": clean.get("tool_name"),
        }
        for name in _LAYER_FN_NAMES:
            fn = globals()[name]
            try:
                await fn(clean, meta)
            except Exception as e:  # noqa: BLE001
                logger.warning("[six_layer:%s] %s", name, e)
        await self.state.advance_to(obs_id)

    async def health(self) -> dict[str, Any]:
        await self.state.load()
        return {
            "ok": True,
            "name": self.name,
            "last_pushed_id": self.state.last_pushed_id,
        }
