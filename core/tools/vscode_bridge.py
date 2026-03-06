# /home/newadmin/swarm-bot/vscode_bridge.py
"""VSCode integration via filesystem + terminal subprocess commands.

Two layers:
1. Direct filesystem access — read/write files in the workspace (fast, always works)
2. MCP client (optional) — when VSCode MCP server is running, enables richer context

Primary workspace: /home/newadmin (configurable via VSCODE_WORKSPACE env var)
"""

from __future__ import annotations

import asyncio
import logging
import os
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

WORKSPACE_ROOT = Path(os.getenv("VSCODE_WORKSPACE", "/home/newadmin"))
MAX_FILE_READ_BYTES = 50_000  # 50KB cap to stay within context limits


# ── Direct Filesystem Layer ────────────────────────────────────────────────────

def _read_file_sync(path: str) -> str:
    """Read a file from the workspace (sync).

    Args:
        path: Absolute path or path relative to WORKSPACE_ROOT.

    Returns:
        File contents as string (capped at MAX_FILE_READ_BYTES).

    Raises:
        FileNotFoundError: If the file does not exist.
        PermissionError: If the file is not readable.
    """
    p = Path(path)
    if not p.is_absolute():
        p = WORKSPACE_ROOT / p

    if not p.exists():
        raise FileNotFoundError(f"File not found: {p}")

    raw = p.read_bytes()
    if len(raw) > MAX_FILE_READ_BYTES:
        logger.warning("File %s is large (%d bytes), truncating", p, len(raw))
        raw = raw[:MAX_FILE_READ_BYTES]

    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("latin-1", errors="replace")


def _write_file_sync(path: str, content: str) -> str:
    """Write content to a file in the workspace (sync).

    Args:
        path: Absolute or workspace-relative path.
        content: Text content to write.

    Returns:
        Confirmation string with path and byte count.
    """
    p = Path(path)
    if not p.is_absolute():
        p = WORKSPACE_ROOT / p

    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    logger.info("Wrote %d bytes to %s", len(content), p)
    return f"Written: {p} ({len(content)} bytes)"


def _list_files_sync(directory: str = ".", pattern: str = "**/*") -> str:
    """List files in a workspace directory (sync).

    Args:
        directory: Directory path (absolute or relative to WORKSPACE_ROOT).
        pattern: Glob pattern (default: all files recursively).

    Returns:
        Newline-separated list of file paths (relative to WORKSPACE_ROOT).
    """
    base = Path(directory)
    if not base.is_absolute():
        base = WORKSPACE_ROOT / base

    files = sorted(
        p for p in base.glob(pattern)
        if p.is_file()
        and ".git" not in p.parts
        and "__pycache__" not in p.parts
        and ".venv" not in str(p)
    )

    if not files:
        return f"No files found in {base} matching '{pattern}'"

    def _rel(p: Path) -> str:
        try:
            return str(p.relative_to(WORKSPACE_ROOT))
        except ValueError:
            return str(p)

    lines = [_rel(f) for f in files[:200]]
    result = "\n".join(lines)
    if len(files) > 200:
        result += f"\n... and {len(files) - 200} more files"
    return result


def _run_command_sync(cmd: str, cwd: Optional[str] = None, timeout: int = 30) -> str:
    """Run a shell command and return combined stdout+stderr (sync).

    Args:
        cmd: Shell command string to execute.
        cwd: Working directory (default: WORKSPACE_ROOT).
        timeout: Seconds before timeout (default 30).

    Returns:
        Combined stdout + stderr output string.
    """
    work_dir = Path(cwd) if cwd else WORKSPACE_ROOT
    logger.info("Running command in %s: %s", work_dir, cmd)

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(work_dir),
            env={**os.environ, "DISPLAY": ":0"},
        )
        output = result.stdout + result.stderr
        logger.info("Command exit code %d, output length %d", result.returncode, len(output))
        if result.returncode != 0:
            return f"[exit {result.returncode}]\n{output}"
        return output or "(no output)"
    except subprocess.TimeoutExpired:
        return f"Command timed out after {timeout}s: {cmd}"
    except Exception as exc:
        logger.exception("Command failed: %s", exc)
        return f"Command error: {exc}"


def _git_status_sync() -> str:
    """Get git status of the workspace (sync).

    Returns:
        Git status + recent log output.
    """
    status = _run_command_sync("git status --short", cwd=str(WORKSPACE_ROOT))
    log = _run_command_sync(
        "git log --oneline -10", cwd=str(WORKSPACE_ROOT)
    )
    return f"=== Git Status ===\n{status}\n\n=== Recent Commits ===\n{log}"


def _get_terminal_output_sync() -> str:
    """Read recent output from the system journal (VSCode terminal fallback).

    Returns:
        Recent terminal/journal output.
    """
    # Try to get recent shell history or journalctl output
    try:
        result = subprocess.run(
            ["journalctl", "--user", "-n", "50", "--no-pager", "-o", "short"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.stdout or "(no journal output)"
    except Exception:
        pass

    # Fallback: read .bash_history
    history = Path.home() / ".bash_history"
    if history.exists():
        lines = history.read_text(errors="replace").strip().splitlines()
        return "Recent commands:\n" + "\n".join(lines[-20:])

    return "(terminal output not available)"


# ── Async Public API ───────────────────────────────────────────────────────────

async def read_file(path: str) -> str:
    """Async: read a file from the workspace.

    Args:
        path: Absolute or workspace-relative file path.

    Returns:
        File contents string.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _read_file_sync, path)


async def write_file(path: str, content: str) -> str:
    """Async: write content to a file.

    Args:
        path: Absolute or workspace-relative file path.
        content: Text to write.

    Returns:
        Confirmation string.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _write_file_sync, path, content)


async def list_files(directory: str = ".", pattern: str = "**/*") -> str:
    """Async: list files in a workspace directory.

    Args:
        directory: Directory path.
        pattern: Glob pattern.

    Returns:
        Newline-separated file paths.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _list_files_sync, directory, pattern)


async def run_command(cmd: str, cwd: Optional[str] = None, timeout: int = 30) -> str:
    """Async: run a shell command in the workspace.

    Args:
        cmd: Shell command to execute.
        cwd: Working directory.
        timeout: Seconds before timeout.

    Returns:
        Command output string.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _run_command_sync, cmd, cwd, timeout)


async def git_status() -> str:
    """Async: get workspace git status.

    Returns:
        Formatted git status + log.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _git_status_sync)


async def get_terminal_output() -> str:
    """Async: get recent terminal/journal output.

    Returns:
        Recent terminal output string.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _get_terminal_output_sync)


# ── MCP Config Generator ───────────────────────────────────────────────────────

def generate_mcp_config(workspace_path: str = str(WORKSPACE_ROOT)) -> dict:
    """Generate .vscode/mcp.json content for MCP server setup.

    Args:
        workspace_path: Absolute path to the workspace directory.

    Returns:
        Dict representing mcp.json content.
    """
    return {
        "mcpServers": {
            "filesystem": {
                "command": "npx",
                "args": [
                    "-y",
                    "@modelcontextprotocol/server-filesystem",
                    workspace_path,
                ],
            },
            "git": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-git", "--repository", workspace_path],
            },
        }
    }
