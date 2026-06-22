"""Alerting engine — 5 severity levels, 4 channels."""

from __future__ import annotations
from datetime import datetime
from pathlib import Path
from typing import Callable
from .config import SWARM_LOG


# ── Severity levels ────────────────────────────────────────────────────────
SEVERITY_DEBUG = 0
SEVERITY_INFO = 1
SEVERITY_WARN = 2
SEVERITY_ERROR = 3
SEVERITY_CRITICAL = 4

SEVERITY_LABELS = {
    SEVERITY_DEBUG: "DEBUG",
    SEVERITY_INFO: "INFO",
    SEVERITY_WARN: "WARN",
    SEVERITY_ERROR: "ERROR",
    SEVERITY_CRITICAL: "CRITICAL",
}

AlertCallback = Callable[[int, str, str], None]  # (severity, title, message)


def _severity_str(sev: int) -> str:
    return SEVERITY_LABELS.get(sev, f"LVL{sev}")


def _timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class AlertingEngine:
    """Multi-channel alert dispatcher."""

    def __init__(self, log_path: Path = SWARM_LOG):
        self.log_path = log_path
        self._callbacks: list[AlertCallback] = []
        self._setup_defaults()

    def _setup_defaults(self):
        """Register built-in channels."""
        self._callbacks.append(_console_alert)
        self._callbacks.append(lambda sev, title, msg: _file_alert(sev, title, msg, self.log_path))

    def add_channel(self, cb: AlertCallback):
        """Register a custom alert channel (e.g. webhook, Slack)."""
        self._callbacks.append(cb)

    def alert(self, severity: int, title: str, message: str = ""):
        """Dispatch an alert to all registered channels."""
        for cb in self._callbacks:
            try:
                cb(severity, title, message)
            except Exception:
                pass  # don't let one channel failure break others

    def warn(self, title: str, message: str = ""):
        self.alert(SEVERITY_WARN, title, message)

    def error(self, title: str, message: str = ""):
        self.alert(SEVERITY_ERROR, title, message)

    def critical(self, title: str, message: str = ""):
        self.alert(SEVERITY_CRITICAL, title, message)

    def info(self, title: str, message: str = ""):
        self.alert(SEVERITY_INFO, title, message)


# ── Built-in channels ──────────────────────────────────────────────────────

def _console_alert(severity: int, title: str, message: str):
    ts = _timestamp()
    sev = _severity_str(severity)
    print(f"[{ts}] [{sev}] {title}")
    if message:
        for line in message.strip().splitlines():
            print(f"         {line}")


def _file_alert(severity: int, title: str, message: str, log_path: Path):
    ts = _timestamp()
    sev = _severity_str(severity)
    line = f"[{ts}] [{sev}] {title}"
    if message:
        line += f"\n  {message.strip().replace(chr(10), chr(10) + '  ')}"
    with open(log_path, "a") as f:
        f.write(line + "\n")
