"""
Mneme-inspired three-layer session continuity — Phase 9 (bilay314/mneme).
Tracks WHAT Legion was doing across restarts, not just what was said.
Layers: working (current task) / episodic (session summaries) / semantic (facts)
"""
from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

MNEME_DIR = Path(os.path.expanduser("~/.legion/mneme"))
MNEME_DIR.mkdir(parents=True, exist_ok=True)

WORKING_PATH = MNEME_DIR / "working_memory.json"
EPISODIC_PATH = MNEME_DIR / "episodic_memory.json"
SEMANTIC_PATH = MNEME_DIR / "semantic_memory.json"


def _read_json(path: Path, default: Any) -> Any:
    try:
        if path.exists():
            with path.open("r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.warning("mneme read %s failed: %s", path, e)
    return default


def _write_json(path: Path, data: Any) -> None:
    try:
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.warning("mneme write %s failed: %s", path, e)


# --- Working memory (current task state) ---

def set_current_task(task: str, context: dict[str, Any] | None = None) -> None:
    """Record the active task Legion is working on."""
    data = {
        "task": task,
        "context": context or {},
        "started_at": time.time(),
        "status": "in_progress",
    }
    _write_json(WORKING_PATH, data)


def complete_current_task(result_summary: str) -> None:
    """Mark current task complete and archive to episodic."""
    data = _read_json(WORKING_PATH, {})
    if data:
        data["status"] = "completed"
        data["completed_at"] = time.time()
        data["result_summary"] = result_summary
        _archive_to_episodic(data)
    _write_json(WORKING_PATH, {})


def get_current_task() -> dict[str, Any]:
    """Return the active task, or empty dict if idle."""
    return _read_json(WORKING_PATH, {})


# --- Episodic memory (session summaries) ---

def _archive_to_episodic(task_data: dict[str, Any]) -> None:
    episodes: list[dict] = _read_json(EPISODIC_PATH, [])
    episodes.append(task_data)
    if len(episodes) > 500:
        episodes = episodes[-500:]
    _write_json(EPISODIC_PATH, episodes)


def get_recent_episodes(n: int = 10) -> list[dict[str, Any]]:
    """Return the n most recent completed task episodes."""
    episodes: list[dict] = _read_json(EPISODIC_PATH, [])
    return episodes[-n:]


def build_session_resume_block() -> str:
    """Build a context block for Legion to resume after restart."""
    current = get_current_task()
    recent = get_recent_episodes(5)
    lines = ["[SESSION CONTINUITY — what Legion was doing before restart:]"]
    if current.get("task"):
        lines.append(f"⚡ Active task: {current['task']}")
        if current.get("context"):
            for k, v in current["context"].items():
                lines.append(f"   {k}: {v}")
    if recent:
        lines.append("\nRecent completed tasks:")
        for ep in reversed(recent[-3:]):
            lines.append(f"  ✓ {ep.get('task','?')} → {ep.get('result_summary','?')[:80]}")
    lines.append("[END SESSION CONTINUITY]")
    return "\n".join(lines)


# --- Semantic memory (long-lived facts) ---

def store_semantic_fact(key: str, value: Any) -> None:
    """Store a long-lived semantic fact (survives forever)."""
    facts: dict = _read_json(SEMANTIC_PATH, {})
    facts[key] = {"value": value, "stored_at": time.time()}
    _write_json(SEMANTIC_PATH, facts)


def get_semantic_fact(key: str) -> Any:
    facts: dict = _read_json(SEMANTIC_PATH, {})
    entry = facts.get(key)
    return entry["value"] if entry else None


def get_all_semantic_facts() -> dict[str, Any]:
    facts: dict = _read_json(SEMANTIC_PATH, {})
    return {k: v["value"] for k, v in facts.items()}
