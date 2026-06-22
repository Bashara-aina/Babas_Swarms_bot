"""Atomic file reloaders — log tail, state.json, metrics.jsonl, config."""

from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Any


def load_log(log_path: Path, tail_n: int = 200_000, head_n: int = 5000) -> tuple[list[str], str, str]:
    """Return (lines, text, head_text) from subprocess.log.

    - lines, text: tail of the log (last ~tail_n lines)
    - head_text: first ~head_n lines (captures startup config that scrolls out of tail)
    """
    head_text = ""
    if not log_path.exists():
        return [], "", ""
    try:
        text = _tail_file(log_path, tail_n)
        lines = text.splitlines()
        # Read head for startup config that scrolls out of tail
        head_text = _head_file(log_path, head_n)
        return lines, text, head_text
    except Exception:
        return [], "", ""


def _tail_file(path: Path, n: int) -> str:
    """Read last ~n lines efficiently."""
    chunk_size = 8192
    data = bytearray()
    total_size = path.stat().st_size
    with open(path, "rb") as f:
        if total_size < chunk_size * 100:
            return f.read().decode("utf-8", errors="replace")
        # seek near the end
        f.seek(max(0, total_size - chunk_size * (n // 10 + 1)))
        data = f.read()
    # trim to approximately n lines
    text = data.decode("utf-8", errors="replace")
    lines = text.splitlines()
    if len(lines) > n:
        lines = lines[-n:]
        text = "\n".join(lines)
    return text


def _head_file(path: Path, n: int) -> str:
    """Read first ~n lines of a file."""
    try:
        with open(path, "rb") as f:
            data = f.read(8192 * (n // 10 + 1))
        text = data.decode("utf-8", errors="replace")
        lines = text.splitlines()
        if len(lines) > n:
            lines = lines[:n]
            text = "\n".join(lines)
        return text
    except Exception:
        return ""


def load_state(state_path: Path) -> dict[str, Any]:
    """Parse rf_stage_state.json, return empty dict on failure."""
    if not state_path.exists():
        return {}
    try:
        return json.loads(state_path.read_text())
    except Exception:
        return {}


def load_metrics(metrics_path: Path) -> list[dict[str, Any]]:
    """Parse metrics.jsonl (one JSON object per line), return list."""
    if not metrics_path.exists():
        return []
    records: list[dict[str, Any]] = []
    try:
        for line in metrics_path.read_text().splitlines():
            line = line.strip()
            if line:
                records.append(json.loads(line))
    except Exception:
        pass
    return records


def load_config(config_path: Path) -> dict[str, Any]:
    """Parse training config.py by extracting top-level assignments.

    Returns a flat dict of name → value for UPPERCASE names and simple types.
    """
    if not config_path.exists():
        return {}
    cfg: dict[str, Any] = {}
    try:
        text = config_path.read_text()
        for m in re.finditer(r'^([A-Z][A-Z0-9_]+)\s*=\s*(.+?)$', text, re.MULTILINE):
            name, raw = m.group(1), m.group(2).strip().rstrip(",")
            # safe eval for literals only
            try:
                cfg[name] = eval(raw, {"__builtins__": {}}, {})
            except Exception:
                cfg[name] = raw
    except Exception:
        pass
    return cfg


def reload_all(
    log_path: Path,
    state_path: Path,
    metrics_path: Path,
    config_path: Path,
    tail_n: int = 200_000,
    head_n: int = 5000,
) -> dict[str, Any]:
    """Atomic reload of all data sources — returns a single ctx dict."""
    log_lines, log_text, log_head_text = load_log(log_path, tail_n, head_n)
    return {
        "log_lines": log_lines,
        "log_text": log_text,
        "log_head_text": log_head_text,
        "state": load_state(state_path),
        "metrics": load_metrics(metrics_path),
        "config": load_config(config_path),
    }
