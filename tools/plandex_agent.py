"""
Plandex agent wrapper for swarm-bot.
Wraps plandex CLI as an async subprocess tool.
Plandex handles multi-file AI editing with plan/diff/apply workflow.

Usage:
  /code <task>  → create plan
  /diff         → review proposed changes
  /apply        → apply approved plan
  /abort        → cancel pending plan
"""

from __future__ import annotations

import asyncio
import os
import shutil
from collections.abc import AsyncGenerator
from pathlib import Path

PLANDEX_CLI = shutil.which("plandex") or os.getenv("PLANDEX_PATH", "plandex")
PLANDEX_PROJECT_DIR = os.getenv(
    "PLANDEX_PROJECT_DIR", "/home/newadmin/projects"
)


class PlandexAgent:
    """Async wrapper for plandex CLI — streams plan output to Telegram."""

    def __init__(self, project_dir: str = PLANDEX_PROJECT_DIR):
        self.project_dir = project_dir

    async def plan(
        self, prompt: str, *, project_path: str | None = None
    ) -> AsyncGenerator[str]:
        """
        Create a plan for the given prompt. Streams output lines.
        Yields decoded stdout lines from plandex.
        """
        proj = project_path or self.project_dir
        cmd = [
            PLANDEX_CLI,
            "plan",
            "--no-stream",
            "--project-dir",
            proj,
            "--description",
            prompt,
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=proj,
        )
        for line in proc.stdout:
            yield line.decode().strip()

    async def apply(
        self, plan_id: str, *, project_path: str | None = None
    ) -> str:
        """Apply an approved plan by ID."""
        proj = project_path or self.project_dir
        cmd = [
            PLANDEX_CLI,
            "apply",
            plan_id,
            "--project-dir",
            proj,
            "--yes",
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=proj,
        )
        stdout, stderr = await proc.communicate()
        return (stdout + stderr).decode()

    async def diff(
        self, plan_id: str, *, project_path: str | None = None
    ) -> str:
        """Get the diff of proposed changes for review."""
        proj = project_path or self.project_dir
        cmd = [PLANDEX_CLI, "diff", plan_id, "--project-dir", proj]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=proj,
        )
        stdout, _ = await proc.communicate()
        return stdout.decode()

    async def abort(
        self, plan_id: str, *, project_path: str | None = None
    ) -> None:
        """Abort a running or pending plan."""
        proj = project_path or self.project_dir
        cmd = [PLANDEX_CLI, "abort", plan_id, "--project-dir", proj]
        await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.DEVNULL, stderr=asyncio.DEVNULL
        )

    async def list_plans(
        self, *, project_path: str | None = None
    ) -> list[dict]:
        """List recent plans for the project."""
        proj = project_path or self.project_dir
        cmd = [PLANDEX_CLI, "ls", "--project-dir", proj, "--json"]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=proj,
        )
        stdout, _ = await proc.communicate()
        try:
            import json

            return json.loads(stdout.decode())
        except Exception:
            return []

    @staticmethod
    def extract_plan_id(lines: list[str]) -> str | None:
        """Extract plan ID from plandex output lines."""
        for line in lines:
            if "plan-" in line:
                parts = line.split("plan-", 1)
                if len(parts) > 1:
                    return parts[1].split()[0]
        return None
