"""Recursive bridge: LegionBot → OpenCode with depth tracking."""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Any

LEGION_DIRECTIVE_RE = re.compile(r"@legion[:\s]+(.+?)(?:\n|$)", re.IGNORECASE)

@dataclass
class SpawnTracker:
    """Tracks recursive spawn depth to prevent infinite loops."""
    max_depth: int = 3
    spawns: list[dict] = field(default_factory=list)

    def can_spawn(self, depth: int = 0) -> bool:
        return depth < self.max_depth

    def record_spawn(self, task_id: str, depth: int) -> None:
        self.spawns.append({"task_id": task_id, "depth": depth, "ts": time.time()})

    def get_active_spawns(self, max_age: int = 300) -> list[dict]:
        now = time.time()
        return [s for s in self.spawns if now - s["ts"] < max_age]

class LegionCallbackBridge:
    """Bridge for LegionBot to spawn OpenCode sub-tasks without Telegram round-trip."""

    def __init__(self):
        self._tracker = SpawnTracker()

    def parse_callback_directive(self, text: str) -> str | None:
        """Extract @legion directive from text."""
        m = LEGION_DIRECTIVE_RE.search(text)
        return m.group(1).strip() if m else None

    async def spawn_opencode_from_legion(
        self,
        task_prompt: str,
        depth: int = 0,
        timeout: int = 120,
    ) -> dict[str, Any]:
        """Spawn OpenCode from LegionBot task without Telegram round-trip."""
        if not self._tracker.can_spawn(depth):
            return {"spawned": False, "reason": f"max depth {self._tracker.max_depth} reached"}

        self._tracker.record_spawn(task_prompt[:50], depth)

        try:
            from core.opencode_bridge import run_opencode_task
            result = await run_opencode_task(
                prompt=task_prompt,
                project_dir="/home/newadmin/swarm-bot",
                agent="general",
                timeout=timeout,
            )
            return {
                "spawned": True,
                "result": result,
                "depth": depth,
            }
        except Exception as exc:
            return {"spawned": False, "reason": str(exc)}

    async def handle_legion_callback(self, text: str, depth: int = 0) -> dict[str, Any]:
        """Parse @legion directive and handle callback."""
        directive = self.parse_callback_directive(text)
        if not directive:
            return {"handled": False, "reason": "no @legion directive"}
        return await self.spawn_opencode_from_legion(directive, depth=depth)
