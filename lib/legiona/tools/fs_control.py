"""
lib/legiona/tools/fs_control.py
Async filesystem control tools — read, write, list, search, grep, disk.
All functions are async, return str, have try/except guards.
SECURITY: File reads are restricted to the project directory tree.
Destructive writes require explicit confirmation.
"""

from __future__ import annotations

import asyncio
import shlex
from pathlib import Path
from typing import Optional


PROJECT_ROOT = Path("/home/newadmin/swarm-bot").resolve()
SHELL_TIMEOUT = 30


def _safe_path(path: str) -> Optional[Path]:
    """Resolve and validate path stays within project directory."""
    try:
        p = Path(path).resolve()
        if not str(p).startswith(str(PROJECT_ROOT)):
            return None  # Outside project tree
        return p
    except Exception:
        return None


# ─── Read ───────────────────────────────────────────────────────────────────

async def read_file(path: str, offset: int = 0, limit: int = 500) -> str:
    """
    Read a file's contents (offset + limit for large files).
    SECURITY: Restricted to project directory.
    """
    p = _safe_path(path)
    if p is None:
        return f"ERROR: Access denied. '{path}' is outside the project directory."
    if not p.exists():
        return f"ERROR: File '{path}' does not exist."
    if not p.is_file():
        return f"ERROR: '{path}' is not a regular file."
    try:
        text = p.read_text(errors="replace")
        lines = text.splitlines()
        total = len(lines)
        start = min(offset, total)
        end = min(offset + limit, total)
        chunk = "\n".join(lines[start:end])
        tail_note = "" if end < total else " (EOF)"
        return f"--- {path} [{start+1}-{end} of {total} lines]{tail_note} ---\n{chunk}"
    except PermissionError:
        return f"ERROR: Permission denied reading '{path}'."
    except Exception as exc:
        return f"ERROR reading '{path}': {exc}"


async def write_file(path: str, content: str, confirm: bool = False) -> str:
    """
    Write content to a file. Set confirm=True to actually write; otherwise returns
    a preview of what WOULD be written.
    SECURITY: Restricted to project directory.
    DESTRUCTIVE: Requires confirm=True to write.
    """
    p = _safe_path(path)
    if p is None:
        return f"ERROR: Access denied. '{path}' is outside the project directory."
    if not confirm:
        preview = content[:500] + ("..." if len(content) > 500 else "")
        return (
            f"PREVIEW (confirm=False — no write occurred) for '{path}':\n"
            f"--- first 500 chars ---\n{preview}"
        )
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, errors="replace")
        return f"OK: Wrote {len(content)} bytes to '{path}'."
    except PermissionError:
        return f"ERROR: Permission denied writing '{path}'."
    except Exception as exc:
        return f"ERROR writing '{path}': {exc}"


# ─── Directory listing ─────────────────────────────────────────────────────────

async def list_dir(path: str = ".", depth: int = 1) -> str:
    """
    List a directory's contents (files and subdirs).
    SECURITY: Restricted to project directory.
    """
    p = _safe_path(path)
    if p is None:
        return f"ERROR: Access denied. '{path}' is outside the project directory."
    if not p.exists():
        return f"ERROR: Directory '{path}' does not exist."
    if not p.is_dir():
        return f"ERROR: '{path}' is not a directory."
    try:
        parts = [f"=== {p.resolve()} (depth={depth}) ==="]
        if depth <= 0:
            return "ERROR: depth must be >= 1"
        for entry in sorted(p.iterdir()):
            rel = entry.relative_to(p)
            if entry.is_dir():
                parts.append(f"  [DIR]  {rel}/")
            else:
                size = entry.stat().st_size
                size_str = _format_size(size)
                parts.append(f"  [FILE] {rel} ({size_str})")
        if not parts[1:]:
            parts.append("  (empty)")
        return "\n".join(parts)
    except PermissionError:
        return f"ERROR: Permission denied listing '{path}'."
    except Exception as exc:
        return f"ERROR listing '{path}': {exc}"


def _format_size(size: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}TB"


# ─── Search ───────────────────────────────────────────────────────────────────

async def search_files(pattern: str, path: str = ".", filetype: str = "f") -> str:
    """
    Find files matching a name pattern using find.
    SECURITY: Restricted to project directory.
    Args:
        pattern: Filename pattern (passed to find -name)
        path: Directory to search within
        filetype: 'f' = regular files, 'd' = dirs, '' = all
    """
    p = _safe_path(path)
    if p is None:
        return f"ERROR: Access denied. '{path}' is outside the project directory."
    if not p.exists():
        return f"ERROR: Directory '{path}' does not exist."
    type_arg = f"-{filetype}" if filetype else ""
    cmd = f"find {shlex.quote(str(p))} {type_arg} -name {shlex.quote(pattern)} -not -path '*/.git/*' -not -path '*/__pycache__/*' -not -path '*/node_modules/*' -not -path '*/.venv/*' -not -path '*/.pytest_cache/*' 2>/dev/null | head -50"
    try:
        proc = await asyncio.wait_for(
            asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            ),
            timeout=SHELL_TIMEOUT,
        )
        stdout, stderr = await proc.communicate()
        out = stdout.decode(errors="replace").strip()
        if not out:
            return f"(no files matching '{pattern}' in '{path}')"
        return out
    except asyncio.TimeoutError:
        return f"ERROR: search timed out after {SHELL_TIMEOUT}s"
    except Exception as exc:
        return f"ERROR: {exc}"


async def grep_files(pattern: str, path: str = ".", context: int = 2) -> str:
    """
    Grep for a regex pattern in files within the project directory.
    SECURITY: Restricted to project directory.
    """
    p = _safe_path(path)
    if p is None:
        return f"ERROR: Access denied. '{path}' is outside the project directory."
    if not p.exists():
        return f"ERROR: Directory '{path}' does not exist."
    try:
        re.compile(pattern)
    except re.error as exc:
        return f"ERROR: invalid regex: {exc}"
    import re as re_mod
    cmd = (
        f"grep -r -n -B {context} -A {context} "
        f"--include='*.py' --include='*.ts' --include='*.js' "
        f"--include='*.md' --include='*.yaml' --include='*.yml' "
        f"--include='*.json' --include='*.txt' "
        f"{shlex.quote(pattern)} {shlex.quote(str(p))} "
        f"--exclude-dir=.git --exclude-dir=__pycache__ "
        f"--exclude-dir=node_modules --exclude-dir=.venv "
        f"2>/dev/null | head -100"
    )
    try:
        proc = await asyncio.wait_for(
            asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            ),
            timeout=SHELL_TIMEOUT,
        )
        stdout, stderr = await proc.communicate()
        out = stdout.decode(errors="replace").strip()
        if not out:
            return f"(no matches for '{pattern}' in '{path}')"
        return out
    except asyncio.TimeoutError:
        return f"ERROR: grep timed out after {SHELL_TIMEOUT}s"
    except Exception as exc:
        return f"ERROR: {exc}"


# ─── Disk usage ───────────────────────────────────────────────────────────────

async def disk_usage(path: str = "/") -> str:
    """
    Report disk usage for the given path using df + du.
    """
    try:
        # df -h shows filesystem-level usage
        df_proc = await asyncio.wait_for(
            asyncio.create_subprocess_shell(
                f"df -h {shlex.quote(path)} 2>/dev/null",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            ),
            timeout=10,
        )
        df_out, _ = await df_proc.communicate()

        # du -sh shows total for path
        du_proc = await asyncio.wait_for(
            asyncio.create_subprocess_shell(
                f"du -sh {shlex.quote(path)} 2>/dev/null || echo 'du unavailable'",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            ),
            timeout=30,
        )
        du_out, _ = await du_proc.communicate()

        lines = ["=== Disk Usage ===", df_out.decode().strip()]
        du_line = du_out.decode().strip()
        if du_line and not du_line.startswith("du:"):
            lines.append(f"\n=== Directory Size ===\n{du_line}")
        return "\n".join(lines)
    except asyncio.TimeoutError:
        return f"ERROR: disk usage timed out"
    except Exception as exc:
        return f"ERROR: {exc}"
