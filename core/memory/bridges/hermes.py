"""core/memory/bridges/hermes.py — stub; filled in Task 5."""
from __future__ import annotations
from typing import Any
from ._base import BridgeState

class HermesBridge:
    name = "hermes"
    def __init__(self) -> None:
        self.state = BridgeState(name=self.name)
    async def push(self, obs_id: int, obs_payload: dict[str, Any]) -> None:
        raise NotImplementedError
    async def health(self) -> dict[str, Any]:
        return {"ok": False, "reason": "not implemented"}
