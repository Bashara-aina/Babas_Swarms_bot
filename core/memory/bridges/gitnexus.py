"""core/memory/bridges/gitnexus.py — Fan out code-modifying observations to GitNexus.

Only fires for code-modifying tools (Edit/Write/MultiEdit/NotebookEdit).
Skips noise paths (.obsidian, .wiki, data/, __pycache__).
Maps `files_modified` → graph nodes via `mcp__gitnexus__cypher` MERGE.
"""
from __future__ import annotations

import logging
from typing import Any

from ._base import BridgeState

logger = logging.getLogger(__name__)

_CODE_TOOLS = frozenset({"Edit", "Write", "MultiEdit", "NotebookEdit"})

_NOISE_PATH_FRAGMENTS = (".obsidian/", ".wiki/", "data/", "__pycache__/", ".git/")


def _is_noise_path(path: str) -> bool:
    return any(frag in path for frag in _NOISE_PATH_FRAGMENTS)


async def _cypher(query: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Real impl: calls mcp__gitnexus__cypher. Stub here; wire in Task 10."""
    raise NotImplementedError("wire to mcp__gitnexus__cypher in Task 10")


class GitNexusBridge:
    name = "gitnexus"

    def __init__(self) -> None:
        self.state = BridgeState(name=self.name)

    async def push(self, obs_id: int, obs_payload: dict[str, Any]) -> None:
        await self.state.load()
        if obs_id <= self.state.last_pushed_id:
            return
        tool = obs_payload.get("tool_name", "")
        if tool not in _CODE_TOOLS:
            return
        files = [f for f in (obs_payload.get("files_modified") or []) if not _is_noise_path(f)]
        if not files:
            return
        try:
            for f in files:
                await _cypher(
                    """
                    MERGE (o:Observation {obs_id: $obs_id})
                    MERGE (file:File {path: $path})
                    MERGE (o)-[:MODIFIES]->(file)
                    """,
                    {"obs_id": obs_id, "path": f},
                )
        except Exception as e:  # noqa: BLE001
            logger.warning("[gitnexus] cypher MERGE failed: %s", e)
            return
        await self.state.advance_to(obs_id)

    async def health(self) -> dict[str, Any]:
        await self.state.load()
        return {
            "ok": True,
            "name": self.name,
            "last_pushed_id": self.state.last_pushed_id,
        }
