"""GitNexus bridge helpers for Claude Code, OpenCode, Copilot, and Legion."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

_ERROR_MARKERS = (
    "disabled in config",
    "not in config",
    "mcp error",
    "no command configured",
    "not installed",
    "error:",
)


def _repo_root() -> str:
    return str(Path(__file__).resolve().parent.parent)


def _looks_valid_mcp_payload(text: str) -> bool:
    normalized = (text or "").strip().lower()
    if not normalized:
        return False
    return not any(marker in normalized for marker in _ERROR_MARKERS)


async def run_gitnexus_analyze(
    repo_path: str | None = None,
    *,
    with_skills: bool = True,
    force: bool = False,
    timeout: int = 1800,
) -> str:
    """Run gitnexus analyze for this repository."""
    target = repo_path or _repo_root()
    cmd = [
        "pnpm",
        "dlx",
        "--allow-build=kuzu",
        "--allow-build=tree-sitter-kotlin",
        "gitnexus@1.4.0",
        "analyze",
        target,
    ]
    if with_skills:
        cmd.append("--skills")
    if force:
        cmd.append("--force")

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=target,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env={
            **os.environ,
            # Prevent node-gyp from accidentally using ~/.local/bin/cc launcher script.
            "CC": os.getenv("CC", "/usr/bin/gcc"),
            "CXX": os.getenv("CXX", "/usr/bin/g++"),
        },
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except TimeoutError:
        proc.kill()
        await proc.wait()
        return f"GitNexus analyze timed out after {timeout}s"

    out = (stdout or b"").decode().strip()
    err = (stderr or b"").decode().strip()
    if proc.returncode != 0:
        return f"GitNexus analyze failed: {err[:2000] or out[:2000]}"
    return out[:4000] if out else "GitNexus analyze completed"


async def query_gitnexus(
    query: str,
    *,
    repo: str | None = None,
    max_chars: int = 2500,
) -> str:
    """Query GitNexus MCP server and return a compact response."""
    try:
        from core.mcp_client import MCPClient
    except Exception:
        return ""

    args: dict[str, str] = {"query": query}
    if repo:
        args["repo"] = repo
    raw = await MCPClient().call_tool("gitnexus", "query", args)
    if not _looks_valid_mcp_payload(raw):
        return ""
    return raw.strip()[:max_chars]


async def build_gitnexus_prompt_context(
    query: str,
    *,
    repo: str | None = None,
    max_chars: int = 2500,
) -> str:
    """Return a prompt-ready GitNexus context block."""
    ctx = await query_gitnexus(query, repo=repo, max_chars=max_chars)
    if not ctx:
        return ""
    return f"## GITNEXUS GRAPH CONTEXT\n{ctx}"
