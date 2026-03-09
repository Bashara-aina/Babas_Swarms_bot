"""git_tools.py — Structured git operations for Legion.

Wraps git commands as async functions with safety checks.
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


async def _git(cmd: str, repo_path: str = "~/swarm-bot") -> str:
    """Run a git command in the given repo directory."""
    from computer_agent import run_shell
    expanded = str(Path(repo_path).expanduser())
    return await run_shell(f"cd '{expanded}' && git {cmd}", timeout=30)


async def git_status(repo_path: str = "~/swarm-bot") -> str:
    """Show git status (working tree, staged changes)."""
    return await _git("status --short", repo_path)


async def git_diff(repo_path: str = "~/swarm-bot", staged: bool = False) -> str:
    """Show git diff. Set staged=True for staged changes."""
    flag = "--staged" if staged else ""
    result = await _git(f"diff {flag}", repo_path)
    if len(result) > 6000:
        result = result[:6000] + "\n\n[...truncated]"
    return result


async def git_log(repo_path: str = "~/swarm-bot", n: int = 10) -> str:
    """Show recent git commits."""
    return await _git(
        f"log --oneline --graph -n {n}",
        repo_path,
    )


async def git_commit(
    repo_path: str = "~/swarm-bot",
    message: str = "",
    files: list[str] | None = None,
) -> str:
    """Stage files and commit. If files is None, stages all changes."""
    if not message:
        return "commit message required"

    if files:
        file_list = " ".join(f"'{f}'" for f in files)
        stage = await _git(f"add {file_list}", repo_path)
    else:
        stage = await _git("add -A", repo_path)

    # Escape single quotes in message
    safe_msg = message.replace("'", "'\\''")
    result = await _git(f"commit -m '{safe_msg}'", repo_path)
    return f"stage: {stage}\ncommit: {result}"


async def git_branch(
    repo_path: str = "~/swarm-bot",
    name: str = "",
    checkout: bool = False,
) -> str:
    """List branches, create, or checkout a branch."""
    if not name:
        return await _git("branch -a", repo_path)
    if checkout:
        return await _git(f"checkout -b '{name}' 2>/dev/null || git checkout '{name}'", repo_path)
    return await _git(f"branch '{name}'", repo_path)


async def git_pull(repo_path: str = "~/swarm-bot") -> str:
    """Pull latest from remote."""
    return await _git("pull origin main", repo_path)


async def git_push(repo_path: str = "~/swarm-bot") -> str:
    """Push to remote."""
    return await _git("push", repo_path)


async def git_stash(
    repo_path: str = "~/swarm-bot",
    action: str = "save",
) -> str:
    """Git stash operations. action: save, pop, list, drop."""
    valid = {"save": "stash", "pop": "stash pop", "list": "stash list", "drop": "stash drop"}
    cmd = valid.get(action, "stash")
    return await _git(cmd, repo_path)
