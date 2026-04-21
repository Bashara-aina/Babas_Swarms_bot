"""
lib/legiona/tools/log_reader.py
Async log reading utilities with WATCHED_LOGS registry.
All functions are async, return str, have try/except guards.
"""

from __future__ import annotations

import asyncio
import re
from pathlib import Path
from typing import Optional


# ─── Log registry ──────────────────────────────────────────────────────────────

WATCHED_LOGS: dict[str, str] = {
    "auth": "/var/log/auth.log",
    "syslog": "/var/log/syslog",
    "dmesg": "/var/log/dmesg",
    "apt": "/var/log/apt/history.log",
    "apt_errors": "/var/log/apt/term.log",
    "dpkg": "/var/log/dpkg.log",
    "boot": "/var/log/boot.log",
    "kern": "/var/log/kern.log",
    "nginx_access": "/var/log/nginx/access.log",
    "nginx_error": "/var/log/nginx/error.log",
    "docker": "/var/log/docker.log",
    "systemd": "/var/log/systemd/",
    "telegram_bot": "/home/newadmin/swarm-bot/logs/legiona.log",
    "nginx_error_alt": "/var/log/nginx/error.log.1",
}

# Also watch these project logs if they exist
PROJECT_LOG_DIR = Path("/home/newadmin/swarm-bot/logs")


def _resolve_path(name_or_path: str) -> Optional[Path]:
    """Resolve a log name or path to a real file path."""
    if name_or_path in WATCHED_LOGS:
        return Path(WATCHED_LOGS[name_or_path])
    p = Path(name_or_path)
    if p.exists() and p.is_file():
        return p
    return None


async def _read_lines(
    path: Path, num_lines: int = 50, offset: int = 0
) -> str:
    """Read last N lines from a file async."""
    try:
        proc = await asyncio.create_subprocess_shell(
            f"tail -n {num_lines} {shlex_quote(str(path))}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        return stdout.decode(errors="replace")
    except Exception as exc:
        return f"ERROR reading {path}: {exc}"


def shlex_quote(s: str) -> str:
    """Simple shlex.quote for asyncio subprocess."""
    return s.replace("'", "'\"'\"'")


# ─── Core log functions ──────────────────────────────────────────────────────

async def tail_log(
    log_name: str,
    num_lines: int = 50,
    pattern: Optional[str] = None,
) -> str:
    """
    Tail the last N lines from a named log.
    Optionally filter by regex pattern.
    """
    path = _resolve_path(log_name)
    if path is None:
        return f"ERROR: log '{log_name}' not found. Known: {list(WATCHED_LOGS.keys())}"

    if not path.exists():
        return f"ERROR: {path} does not exist (may need sudo)"

    result = await _read_lines(path, num_lines)
    if pattern and not result.startswith("ERROR"):
        try:
            regex = re.compile(pattern, re.IGNORECASE)
            lines = [l for l in result.splitlines() if regex.search(l)]
            result = "\n".join(lines)
            if not result.strip():
                result = "(no lines match pattern)"
        except re.error as exc:
            return f"ERROR: invalid regex: {exc}"
    return result


async def grep_log(
    log_name: str,
    pattern: str,
    context: int = 3,
) -> str:
    """
    Grep a regex pattern in a log with N lines of context before/after.
    """
    path = _resolve_path(log_name)
    if path is None:
        return f"ERROR: log '{log_name}' not found. Known: {list(WATCHED_LOGS.keys())}"

    if not path.exists():
        return f"ERROR: {path} does not exist (may need sudo)"

    try:
        regex = re.compile(pattern, re.IGNORECASE)
    except re.error as exc:
        return f"ERROR: invalid regex: {exc}"

    cmd = (
        f"grep -B {context} -A {context} {shlex_quote(pattern)} "
        f"{shlex_quote(str(path))} 2>/dev/null || "
        f"tail -n 200 {shlex_quote(str(path))} | grep -i {shlex_quote(pattern)}"
    )
    try:
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if not stdout:
            return f"(no matches for '{pattern}' in {path.name})"
        return stdout.decode(errors="replace")
    except Exception as exc:
        return f"ERROR: {exc}"


async def count_log_entries(log_name: str, pattern: str) -> str:
    """
    Count how many lines in a log match a pattern.
    """
    path = _resolve_path(log_name)
    if path is None:
        return f"ERROR: log '{log_name}' not found. Known: {list(WATCHED_LOGS.keys())}"

    if not path.exists():
        return f"ERROR: {path} does not exist"

    try:
        re.compile(pattern)
    except re.error as exc:
        return f"ERROR: invalid regex: {exc}"

    cmd = f"grep -ci {shlex_quote(pattern)} {shlex_quote(str(path))}"
    try:
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        return f"{stdout.decode().strip()} lines match '{pattern}' in {path.name}"
    except Exception as exc:
        return f"ERROR: {exc}"


async def list_all_logs() -> str:
    """
    List all known WATCHED_LOGS and whether each file exists.
    Also includes any .log files in the project log directory.
    """
    lines = ["=== Known system logs ==="]
    for name, path_str in sorted(WATCHED_LOGS.items()):
        p = Path(path_str)
        exists = "✅" if p.exists() else "❌"
        lines.append(f"  {exists} {name}: {path_str}")

    lines.append("\n=== Project logs ===")
    if PROJECT_LOG_DIR.exists():
        for p in sorted(PROJECT_LOG_DIR.glob("*.log")):
            size_kb = p.stat().st_size // 1024
            lines.append(f"  📄 {p.name} ({size_kb} KB)")
        for p in sorted(PROJECT_LOG_DIR.glob("*.jsonl")):
            size_kb = p.stat().st_size // 1024
            lines.append(f"  📄 {p.name} ({size_kb} KB)")
    else:
        lines.append("  (log directory does not exist)")

    return "\n".join(lines)


async def watch_log_live(
    log_name: str,
    pattern: Optional[str] = None,
    duration_seconds: int = 10,
) -> str:
    """
    Stream log entries live for N seconds using tail -f.
    Returns all new lines matching the optional pattern.
    """
    path = _resolve_path(log_name)
    if path is None:
        return f"ERROR: log '{log_name}' not found. Known: {list(WATCHED_LOGS.keys())}"

    if not path.exists():
        return f"ERROR: {path} does not exist"

    grep_cmd = f"grep -i {shlex_quote(pattern)}" if pattern else "cat"
    cmd = f"tail -f -n 20 {shlex_quote(str(path))} | {grep_cmd} | head -n 50"

    try:
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            await asyncio.wait_for(proc.communicate(), timeout=duration_seconds)
        except asyncio.TimeoutError:
            proc.terminate()
            _, _ = await proc.communicate()
            return "(stream ended after timeout)"
        stdout, _ = await proc.communicate()
        return stdout.decode(errors="replace") or "(no output)"
    except Exception as exc:
        return f"ERROR: {exc}"


async def get_recent_errors(
    log_name: str,
    num_lines: int = 30,
) -> str:
    """
    Extract ERROR, WARN, CRIT, FATAL lines from a log.
    """
    path = _resolve_path(log_name)
    if path is None:
        return f"ERROR: log '{log_name}' not found. Known: {list(WATCHED_LOGS.keys())}"

    if not path.exists():
        return f"ERROR: {path} does not exist"

    pattern = r"(?i)\b(error|warn|crit|fatal|exception|fail|failed)\b"
    cmd = (
        f"grep -iE {shlex_quote(pattern)} {shlex_quote(str(path))} | "
        f"tail -n {num_lines}"
    )
    try:
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        return stdout.decode(errors="replace") or "(no error lines found)"
    except Exception as exc:
        return f"ERROR: {exc}"


async def follow_journal(
    unit: str,
    num_lines: int = 50,
) -> str:
    """
    Follow a systemd journal unit's recent logs.
    Returns stderr if journalctl fails (may need sudo or group membership).
    """
    cmd = f"journalctl -u {unit} -n {num_lines} --no-pager"
    try:
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        err = stderr.decode().strip()
        if err and proc.returncode != 0:
            return f"ERROR (may need sudo): {err}"
        return stdout.decode(errors="replace") or "(no output)"
    except Exception as exc:
        return f"ERROR: {exc}"
