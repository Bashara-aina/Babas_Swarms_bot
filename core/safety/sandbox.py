"""core/safety/sandbox.py — Docker/gVisor shell sandboxing for GAP-21.

Provides sandboxed bash execution when LEGION_SANDBOX_ENABLED=true.
Falls back to direct execution when sandbox is disabled or unavailable.
"""
import asyncio
import logging
import os
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)

SANDBOX_IMAGE = os.getenv("LEGION_SANDBOX_IMAGE", "ubuntu:22.04")
SANDBOX_ENABLED = os.getenv("LEGION_SANDBOX_ENABLED", "false").lower() in ("1", "true", "yes")


def is_sandbox_available() -> bool:
    """Check if Docker is available on the system."""
    return shutil.which("docker") is not None


async def run_sandboxed_bash(
    command: str,
    timeout: int = 30,
    cwd: str | None = None,
    readonly_root: bool = True,
) -> tuple[int, str, str]:
    """Run a bash command inside a Docker sandbox.

    Args:
        command: Bash command string to execute
        timeout: Timeout in seconds (default 30)
        cwd: Working directory to mount into the container
        readonly_root: Mount root filesystem as read-only (default True)

    Returns:
        (returncode, stdout, stderr) tuple
    """
    if not SANDBOX_ENABLED or not is_sandbox_available():
        return await _run_direct_bash(command, timeout, cwd)

    mount_options = []
    if cwd:
        host_cwd = Path(cwd).resolve()
        if host_cwd.exists():
            mount_options.extend([
                "-v", f"{host_cwd}:/workdir:ro",
            ])
            workdir = "/workdir"
        else:
            workdir = "/tmp"
    else:
        workdir = "/tmp"

    read_only_flag = "--read-only" if readonly_root else ""
    network_flag = "--network=none"

    cmd = [
        "docker", "run",
        "--rm",
        "--user=1000:1000",
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges",
        network_flag,
        read_only_flag,
        "--memory=512m",
        "--memory-swap=512m",
        "--pids-limit=64",
        "--cpus=1",
        "-i",
        SANDBOX_IMAGE,
        "/bin/bash", "-c", command,
    ]

    for opt in mount_options:
        cmd.insert(7, opt)

    if workdir != "/tmp":
        cmd.extend(["--workdir", workdir])

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    try:
        stdout_b, stderr_b = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return proc.returncode, stdout_b.decode(), stderr_b.decode()
    except TimeoutError:
        proc.kill()
        await proc.wait()
        return -1, "", f"Command timed out after {timeout}s"
    except Exception as exc:
        proc.kill()
        await proc.wait()
        logger.warning("Sandbox run failed, falling back to direct: %s", exc)
        return await _run_direct_bash(command, timeout, cwd)


async def _run_direct_bash(
    command: str,
    timeout: int = 30,
    cwd: str | None = None,
) -> tuple[int, str, str]:
    """Direct bash execution (no sandbox)."""
    cmd = ["/bin/bash", "-c", command]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd,
    )
    try:
        stdout_b, stderr_b = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return proc.returncode, stdout_b.decode(), stderr_b.decode()
    except TimeoutError:
        proc.kill()
        await proc.wait()
        return -1, "", f"Command timed out after {timeout}s"
