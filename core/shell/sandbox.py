"""Sandboxed shell executor — blocks dangerous commands, enforces allowed paths.

Wraps asyncio.create_subprocess_shell with:
- Blocklist of dangerous shell patterns (rm -rf /, chained pipes, network downloads, etc.)
- Allowed directory enforcement (cwd must be in allowed list)
- Output size cap (1MB default)
- Timeout enforcement (30s default)

Usage:
    from core.shell.sandbox import SandboxExecutor, DEFAULT_SANDBOX
    result = await SandboxExecutor(DEFAULT_SANDBOX).execute("echo hello")
"""

from __future__ import annotations

import asyncio
import logging
import re
import shutil
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class SandboxConfig:
    """Configuration for sandboxed shell execution."""

    allowed_dirs: list[str] = field(
        default_factory=lambda: [
            "/home/newadmin",
            "/tmp",
            "/var/log",
            "/home/newadmin/swarm-bot",
        ]
    )
    blocked_cmds: list[str] = field(
        default_factory=lambda: [
            r"rm\s+-rf\s+/\s*",
            r"rm\s+-rf\s+/",
            r"dd\s+if=",
            r"mkfs",
            r":\(\)\s*:\s*\|",
            r"curl.*-o.*http",
            r"curl.*--output.*http",
            r"wget.*-O.*http",
            r"wget.*--output-document.*http",
            r"nc\s+-e",
            r"bash\s+-i",
            r"python.*-c.*http",
            r"perl.*-e.*http",
            r"ruby.*-e.*http",
            r"nc\s+-\s+[lnp",
            r"/dev/tcp/",
            r"/dev/udp/",
            r"chmod\s+777\s+/",
            r"chmod\s+4755",
            r">\s*/etc/passwd",
            r">\s*/etc/shadow",
            r"fork\s+bomb",
            r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;",
            r"nohup\s+.*\s+&",
        ]
    )
    max_output_bytes: int = 1024 * 1024  # 1MB
    timeout_secs: int = 30


DEFAULT_SANDBOX = SandboxConfig()


@dataclass
class ShellResult:
    """Result of a sandboxed shell execution."""

    stdout: str
    stderr: str
    exit_code: int
    ok: bool


class SandboxExecutor:
    """Executes shell commands in a sandboxed environment."""

    def __init__(self, config: SandboxConfig) -> None:
        self.config = config
        self._blocked_patterns = [re.compile(p, re.IGNORECASE) for p in config.blocked_cmds]

    def _is_blocked(self, cmd: str) -> Optional[str]:
        """Check if command matches any blocked pattern. Returns reason if blocked, None if ok."""
        for pattern in self._blocked_patterns:
            if pattern.search(cmd):
                return f"blocked pattern: {pattern.pattern}"
        return None

    def _validate_cwd(self, cwd: Optional[str]) -> Optional[str]:
        """Validate cwd is in allowed list. Returns resolved path or None."""
        import os

        if cwd is None:
            return None
        resolved = os.path.realpath(os.path.expanduser(cwd))
        for allowed in self.config.allowed_dirs:
            allowed_resolved = os.path.realpath(os.path.expanduser(allowed))
            if resolved.startswith(allowed_resolved + "/") or resolved == allowed_resolved:
                return resolved
        return None

    async def execute(self, cmd: str, cwd: Optional[str] = None) -> ShellResult:
        """Execute a shell command in the sandbox.

        Args:
            cmd: The shell command to run.
            cwd: Working directory (must be in allowed_dirs).

        Returns:
            ShellResult with stdout, stderr, exit_code, and ok flag.
        """
        # Pre-flight: blocklist check
        blocked_reason = self._is_blocked(cmd)
        if blocked_reason:
            logger.warning("[sandbox] blocked command: %s (%s)", cmd[:80], blocked_reason)
            return ShellResult(
                stdout="",
                stderr=f"[sandbox] Command blocked: {blocked_reason}",
                exit_code=1,
                ok=False,
            )

        # Pre-flight: cwd validation
        resolved_cwd = self._validate_cwd(cwd)
        if cwd is not None and resolved_cwd is None:
            logger.warning("[sandbox] rejected cwd outside allowed dirs: %s", cwd)
            return ShellResult(
                stdout="",
                stderr=f"[sandbox] Working directory '{cwd}' is not in allowed list.",
                exit_code=1,
                ok=False,
            )

        # Validate binary exists using resolved_cwd parent if needed
        if resolved_cwd:
            cmd_with_path = shutil.which(cmd.strip().split()[0]) if cmd.strip() else None
            if cmd_with_path:
                cmd_bin_dir = os.path.dirname(os.path.realpath(cmd_with_path))
                bin_allowed = any(
                    cmd_bin_dir.startswith(os.path.realpath(os.path.expanduser(a))) for a in self.config.allowed_dirs
                )
                if not bin_allowed:
                    logger.warning(
                        "[sandbox] binary outside allowed dirs: %s (from %s)",
                        cmd_with_path,
                        cmd_bin_dir,
                    )
                    return ShellResult(
                        stdout="",
                        stderr=f"[sandbox] Binary path '{cmd_bin_dir}' is not in allowed directories.",
                        exit_code=1,
                        ok=False,
                    )

        # Execute
        try:
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=resolved_cwd,
            )
            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    proc.communicate(), timeout=self.config.timeout_secs
                )
            except asyncio.TimeoutError:
                try:
                    proc.kill()
                    await proc.communicate()
                except Exception:
                    pass
                return ShellResult(
                    stdout="",
                    stderr=f"[sandbox] Command timed out after {self.config.timeout_secs}s",
                    exit_code=124,
                    ok=False,
                )

            stdout = stdout_bytes.decode("utf-8", errors="replace")
            stderr = stderr_bytes.decode("utf-8", errors="replace")

            # Cap output
            if len(stdout) > self.config.max_output_bytes:
                stdout = stdout[: self.config.max_output_bytes] + "\n[output truncated]"
            if len(stderr) > self.config.max_output_bytes // 4:
                stderr = stderr[: self.config.max_output_bytes // 4] + "\n[stderr truncated]"

            logger.info(
                "[sandbox] executed: %s (exit=%d, stdout_len=%d)",
                cmd[:60],
                proc.returncode,
                len(stdout),
            )

            return ShellResult(
                stdout=stdout.strip(),
                stderr=stderr.strip(),
                exit_code=proc.returncode or 0,
                ok=proc.returncode == 0,
            )

        except Exception as e:
            logger.warning("[sandbox] execution error: %s", e)
            return ShellResult(stdout="", stderr=f"[sandbox] error: {e}", exit_code=1, ok=False)
