"""Thread memory — single source of truth, no risky circular imports.

Imported by agent_registry.py, conversation_interface.py, and agents/__init__.py.
"""

from __future__ import annotations

import logging
import threading
import time
from datetime import datetime

logger = logging.getLogger(__name__)

_THREADS_LOCK = threading.Lock()
ACTIVE_THREADS: dict[str, list[dict]] = {}


def add_to_thread(thread_id: str, agent: str, task: str, result: str) -> None:
    with _THREADS_LOCK:
        if thread_id not in ACTIVE_THREADS:
            ACTIVE_THREADS[thread_id] = []
        ACTIVE_THREADS[thread_id].append(
            {
                "agent": agent,
                "task": task,
                "result": result[:500],
                "timestamp": time.time(),
            }
        )
        if len(ACTIVE_THREADS[thread_id]) > 10:
            ACTIVE_THREADS[thread_id] = ACTIVE_THREADS[thread_id][-10:]
    logger.info("Added to thread '%s': %s agent", thread_id, agent)


def get_thread_context(thread_id: str, last_n: int = 3) -> str:
    if thread_id not in ACTIVE_THREADS or not ACTIVE_THREADS[thread_id]:
        return ""
    recent = ACTIVE_THREADS[thread_id][-last_n:]
    lines = ["<i>Previous in this thread:</i>\n"]
    for turn in recent:
        t = datetime.fromtimestamp(turn["timestamp"]).strftime("%H:%M")
        lines.append(f"[{t}] {turn['agent'].upper()}: {turn['task'][:80]}…")
        lines.append(f"\u21b3 {turn['result'][:120]}…\n")
    return "\n".join(lines)


def list_threads() -> str:
    with _THREADS_LOCK:
        if not ACTIVE_THREADS:
            return "<b>No active threads</b>\n\nUse <code>/thread &lt;name&gt;</code> to start one."
        lines = ["<b>\U0001f4cc Active Threads</b>\n"]
        for tid, turns in ACTIVE_THREADS.items():
            last = turns[-1]
            t = datetime.fromtimestamp(last["timestamp"]).strftime("%m/%d %H:%M")
            lines.append(f"  \U0001f4cc <b>{tid}</b> \u2014 {len(turns)} turns (last: {t})")
        return "\n".join(lines)


def list_threads_raw() -> list[str]:
    with _THREADS_LOCK:
        return list(ACTIVE_THREADS.keys())


def clear_thread(thread_id: str) -> bool:
    with _THREADS_LOCK:
        if thread_id in ACTIVE_THREADS:
            del ACTIVE_THREADS[thread_id]
            logger.info("Cleared thread '%s'", thread_id)
            return True
        return False


__all__ = [
    "ACTIVE_THREADS",
    "add_to_thread",
    "clear_thread",
    "get_thread_context",
    "list_threads",
    "list_threads_raw",
]
