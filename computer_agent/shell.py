"""computer_agent/shell.py — Subprocess execution, app launchers, system maintenance."""

from __future__ import annotations

import asyncio
import logging
import os
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def _resolve_tool_bin(name: str) -> str | None:
    """Resolve a desktop tool binary even when systemd PATH is minimal."""
    path = shutil.which(name)
    if path:
        return path
    for candidate in (f"/usr/bin/{name}", f"/bin/{name}", f"/usr/local/bin/{name}"):
        if Path(candidate).exists():
            return candidate
    return None


async def run_shell(cmd: str, timeout: int = 30, capture_stderr: bool = True) -> str:
    """Run a shell command asynchronously with sandbox protection. Returns stdout+stderr as string."""
    # Sandbox pre-flight check (U2)
    try:
        from core.shell.sandbox import DEFAULT_SANDBOX, SandboxExecutor

        sandbox = SandboxExecutor(DEFAULT_SANDBOX)
        result = await sandbox.execute(cmd)
        if not result.ok:
            return f"⛔ {result.stderr}"
        out = result.stdout
        err = result.stderr
        if result.exit_code == 0:
            return out or "(done, no output)"
        return f"exit {result.exit_code}\nstdout: {out}\nstderr: {err}".strip()
    except ImportError:
        pass  # Fall through to direct subprocess if sandbox unavailable

    try:
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE if capture_stderr else asyncio.subprocess.DEVNULL,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        out = stdout.decode("utf-8", errors="replace").strip()
        err = stderr.decode("utf-8", errors="replace").strip() if stderr else ""
        if proc.returncode == 0:
            return out or "(done, no output)"
        return f"exit {proc.returncode}\nstdout: {out}\nstderr: {err}".strip()
    except TimeoutError:
        try:
            proc.kill()  # type: ignore[name-defined]
            await proc.communicate()  # type: ignore[name-defined]
        except Exception:
            pass
        return f"⏱ timed out after {timeout}s"
    except Exception as e:
        return f"run_shell error: {e}"


APP_MAP: dict[str, str] = {
    "whatsapp": "google-chrome --app=https://web.whatsapp.com --new-window",
    "whatsapp web": "google-chrome --app=https://web.whatsapp.com --new-window",
    "telegram": "telegram-desktop",
    "vscode": "code",
    "vs code": "code",
    "code": "code",
    "terminal": "gnome-terminal",
    "konsole": "konsole",
    "files": "nautilus .",
    "file manager": "nautilus .",
    "nautilus": "nautilus .",
    "firefox": "firefox",
    "email": "google-chrome --app=https://mail.google.com --new-window",
    "gmail": "google-chrome --app=https://mail.google.com --new-window",
    "supabase": "google-chrome --app=https://app.supabase.com --new-window",
    "github": "google-chrome https://github.com",
    "slack": "slack",
    "spotify": "spotify",
    "discord": "discord",
    "notion": "google-chrome --app=https://notion.so --new-window",
    "youtube": "google-chrome https://youtube.com",
    "calculator": "gnome-calculator",
    "settings": "gnome-control-center",
    "system monitor": "gnome-system-monitor",
    "htop": "gnome-terminal -- htop",
    "nvidia-smi": "gnome-terminal -- watch -n1 nvidia-smi",
    "jupyter": "jupyter lab",
    "pycharm": "pycharm",
    "obsidian": "obsidian",
}

BROWSER_APPS: dict[str, str] = {
    "whatsapp": "https://web.whatsapp.com",
    "gmail": "https://mail.google.com",
    "supabase": "https://app.supabase.com",
    "notion": "https://notion.so",
    "github": "https://github.com",
    "youtube": "https://youtube.com",
}


async def open_url(url: str) -> str:
    """Open a URL in the default browser."""
    from computer_agent.display import detect_display as _detect_display

    display = await _detect_display()
    import re

    if not re.match(r"^https?://", url):
        url = f"https://{url}"
    await run_shell(f"DISPLAY={display} xdg-open '{url}' &", timeout=5)
    await asyncio.sleep(1)
    return f"opened: {url}"


async def open_app(app_name: str) -> str:
    """Open an application by name. Checks APP_MAP first, then tries directly."""
    from computer_agent.display import detect_display as _detect_display

    display = await _detect_display()
    import re

    key = app_name.lower().strip()
    if key in APP_MAP:
        cmd = f"DISPLAY={display} {APP_MAP[key]} &"
    else:
        cmd = f"DISPLAY={display} xdg-open '{key}' 2>/dev/null || DISPLAY={display} {key} &"
    await run_shell(cmd, timeout=5)
    await asyncio.sleep(1.5)
    return f"opening {app_name}..."


async def list_processes(filter_str: str = "") -> str:
    """List running processes."""
    cmd = f"ps aux | grep -i '{filter_str}' | grep -v grep | head -20"
    return await run_shell(cmd, timeout=5)


async def kill_process(process_name: str) -> str:
    """Kill a process by name."""
    return await run_shell(f"pkill -f '{process_name}'; echo 'killed'", timeout=5)


async def install_packages(packages: list[str]) -> str:
    """Install pip packages. Returns install output."""
    pkg_str = " ".join(f"'{p}'" for p in packages)
    logger.info("Installing packages: %s", pkg_str)
    result = await run_shell(
        f"{sys.executable} -m pip install {pkg_str} 2>&1",
        timeout=180,
    )
    logger.info("Install result: %s", result[-200:])
    return result


async def upgrade_from_git(repo_dir: str = "") -> str:
    """git pull latest from remote.

    Args:
        repo_dir: Path to repository. Defaults to the swarm-bot directory
                  resolved from this file's location (not hardcoded).
    """
    if not repo_dir:
        repo_dir = str(Path(__file__).resolve().parent.parent)
    expanded = str(Path(repo_dir).expanduser())
    return await run_shell(
        f"cd {shlex.quote(expanded)} && git pull origin main 2>&1",
        timeout=30,
    )


def restart_bot(delay_seconds: float = 1.0) -> None:
    """Restart the bot process. Call AFTER sending Telegram notification.

    Uses os.execv to replace the current process, which means:
    - Same PID group
    - Fresh Python interpreter
    - Reloads all modules (picks up new pip packages)
    - Bot reconnects to Telegram automatically

    Note: time.sleep() is acceptable here because os.execv() replaces the process
    and never returns — there is no async context to block. The delay is minimal (1s).
    """
    logger.info("Bot restarting via os.execv...")
    time.sleep(delay_seconds)
    os.execv(sys.executable, [sys.executable, *sys.argv])
