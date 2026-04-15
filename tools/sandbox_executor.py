"""
E2B sandboxed code execution.
Replaces bare subprocess /cmd with isolated cloud sandboxes.
SECURITY: Never execute untrusted code on the host.

Usage:
  executor = get_sandbox_executor()
  result = await executor.execute("print('hello')", language="python")
"""

from __future__ import annotations

import asyncio
import os
from typing import Literal

# E2B is optional — imported lazily to avoid hard dependency
_e2b_installed: bool | None = None


def _check_e2b() -> bool:
    global _e2b_installed
    if _e2b_installed is None:
        try:
            import e2b  # noqa: F401

            _e2b_installed = True
        except ImportError:
            _e2b_installed = False
    return _e2b_installed


class SandboxExecutor:
    """Async E2B sandbox executor for untrusted code."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("E2B_API_KEY")
        self._sandbox = None
        self._enabled = os.getenv("LEGION_SANDBOX_ENABLED", "false").lower() in (
            "true",
            "1",
            "yes",
        )

    async def execute(
        self,
        code: str,
        language: Literal["python", "javascript", "bash"] = "python",
        timeout: int = 30,
    ) -> str:
        """
        Execute code inside an isolated E2B sandbox.
        Falls back to local execution if LEGION_SANDBOX_ENABLED=false.
        """
        if not self._enabled or not self.api_key:
            return await self._execute_local(code, language, timeout)

        if not _check_e2b():
            return await self._execute_local(code, language, timeout)

        return await self._execute_in_sandbox(code, language, timeout)

    async def _execute_in_sandbox(
        self,
        code: str,
        language: Literal["python", "javascript", "bash"],
        timeout: int,
    ) -> str:
        from e2b import Sandbox

        sandbox = await Sandbox.create(api_key=self.api_key)
        ext_map = {"python": "py", "javascript": "js", "bash": "sh"}
        filename = f"tmp_code.{ext_map[language]}"
        filepath = f"/tmp/{filename}"

        await sandbox.filesystem.write(filepath, code)

        cmd_map = {
            "python": f"python3 {filepath}",
            "javascript": f"node {filepath}",
            "bash": f"bash {filepath}",
        }

        proc = await sandbox.process.start(cmd_map[language])

        try:
            result = await asyncio.wait_for(proc.finish(), timeout=timeout)
        except asyncio.TimeoutError:
            await proc.kill()
            await sandbox.close()
            return f"Timed out after {timeout}s"

        stdout = await proc.stdout.read()
        stderr = await proc.stderr.read()
        combined = stdout + stderr if isinstance(stdout, bytes) else stdout + (
            stderr or b""
        )

        await sandbox.close()

        return combined.decode() if isinstance(combined, bytes) else combined

    async def _execute_local(
        self,
        code: str,
        language: Literal["python", "javascript", "bash"],
        timeout: int,
    ) -> str:
        """Fallback local execution — only for trusted code."""
        ext_map = {"python": "py", "javascript": "js", "bash": "sh"}
        filename = f"/tmp/legion_exec.{ext_map[language]}"

        with open(filename, "w") as f:
            f.write(code)

        cmd_map = {
            "python": ["python3", filename],
            "javascript": ["node", filename],
            "bash": ["bash", filename],
        }

        proc = await asyncio.create_subprocess_exec(
            *cmd_map[language],
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            await proc.kill()
            return f"Timed out after {timeout}s"
        finally:
            try:
                os.remove(filename)
            except OSError:
                pass

        combined = stdout + stderr
        return combined.decode()


_sandbox_exec: SandboxExecutor | None = None


def get_sandbox_executor() -> SandboxExecutor:
    """Singleton accessor — avoids repeated E2B session creation."""
    global _sandbox_exec
    if _sandbox_exec is None:
        _sandbox_exec = SandboxExecutor()
    return _sandbox_exec
