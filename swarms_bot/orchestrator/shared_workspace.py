"""Shared Workspace — agents read/write files to a common coordination space.

Mirrors OpenClaw's coordinator file system:
  goal.md       — the original goal (read-only after creation)
  plan.md       — the decomposed task plan
  status.md     — live execution status per node
  log.md        — append-only execution log
  artifacts/    — outputs from each agent (code, reports, etc.)

All reads/writes are async and thread-safe.
"""
from __future__ import annotations

import asyncio
import logging
import time
from pathlib import Path
from typing import Dict, Optional

import aiofiles

logger = logging.getLogger(__name__)

WORKSPACE_ROOT = Path("data/workspaces")


class SharedWorkspace:
    """Per-run shared filesystem workspace for agent coordination."""

    def __init__(self, run_id: str, root: Optional[Path] = None):
        self.run_id = run_id
        self.root = (root or WORKSPACE_ROOT) / run_id
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "artifacts").mkdir(exist_ok=True)

    # ── Core files ──────────────────────────────────────────────────────────

    async def set_goal(self, goal: str) -> None:
        await self._write("goal.md", f"# Goal\n\n{goal}\n")

    async def get_goal(self) -> str:
        return await self._read("goal.md")

    async def set_plan(self, plan_text: str) -> None:
        await self._write("plan.md", plan_text)

    async def get_plan(self) -> str:
        return await self._read("plan.md")

    async def update_status(self, node_id: str, status: str, detail: str = "") -> None:
        """Update status.md with current node state."""
        existing = await self._read("status.md")
        lines = existing.splitlines()
        # Replace or append
        updated = [l for l in lines if not l.startswith(f"- {node_id}:")]
        icon = {"pending": "⏳", "running": "🔄", "done": "✅", "failed": "❌", "skipped": "⏭"}.get(status, "❓")
        updated.append(f"- {node_id}: {icon} {status} — {detail[:120]}")
        await self._write("status.md", "\n".join(updated) + "\n")

    async def append_log(self, entry: str) -> None:
        """Append to the execution log."""
        ts = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        current = await self._read("log.md")
        await self._write("log.md", current + f"\n[{ts}] {entry}")

    # ── Artifacts ───────────────────────────────────────────────────────────

    async def write_artifact(self, node_id: str, filename: str, content: str) -> Path:
        """Write an artifact file produced by an agent."""
        artifact_dir = self.root / "artifacts" / node_id
        artifact_dir.mkdir(parents=True, exist_ok=True)
        path = artifact_dir / filename
        async with aiofiles.open(path, "w", encoding="utf-8") as f:
            await f.write(content)
        await self.append_log(f"{node_id} wrote artifact: {filename}")
        logger.debug("Artifact written: %s", path)
        return path

    async def read_artifact(self, node_id: str, filename: str) -> str:
        """Read an artifact file from the workspace."""
        path = self.root / "artifacts" / node_id / filename
        if not path.exists():
            return ""
        async with aiofiles.open(path, "r", encoding="utf-8") as f:
            return await f.read()

    async def list_artifacts(self) -> Dict[str, list]:
        """List all artifacts by node."""
        artifacts: Dict[str, list] = {}
        artifact_root = self.root / "artifacts"
        if artifact_root.exists():
            for node_dir in artifact_root.iterdir():
                if node_dir.is_dir():
                    artifacts[node_dir.name] = [f.name for f in node_dir.iterdir()]
        return artifacts

    async def get_all_results(self) -> str:
        """Concatenate all artifact contents for final synthesis."""
        parts = []
        artifact_root = self.root / "artifacts"
        if artifact_root.exists():
            for node_dir in sorted(artifact_root.iterdir()):
                for fpath in sorted(node_dir.iterdir()):
                    content = await self.read_artifact(node_dir.name, fpath.name)
                    if content:
                        parts.append(f"## {node_dir.name} / {fpath.name}\n{content}")
        return "\n\n".join(parts)

    def workspace_path(self) -> Path:
        return self.root

    # ── Internals ──────────────────────────────────────────────────────────

    async def _write(self, filename: str, content: str) -> None:
        path = self.root / filename
        async with aiofiles.open(path, "w", encoding="utf-8") as f:
            await f.write(content)

    async def _read(self, filename: str) -> str:
        path = self.root / filename
        if not path.exists():
            return ""
        async with aiofiles.open(path, "r", encoding="utf-8") as f:
            return await f.read()
