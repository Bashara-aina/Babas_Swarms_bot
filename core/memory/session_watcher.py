"""
Background daemon that incrementally saves session state to long-term memory.

Run: ./scripts/start_session_watcher.sh
Stop: ./scripts/stop_session_watcher.sh

Saves every 2 min to:
  - mem0 (ChromaDB + Ollama all-MiniLM-L6-v2)
  - langmem (SwarmBotMemoryManager)

Checkpoint on every .session_state/current.json change (tracked via mtime).

Safe: all ops wrapped in try/except. SIGTERM graceful shutdown.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import signal
import tempfile
import time
from pathlib import Path
from threading import Event

logger = logging.getLogger(__name__)

# ── Config ──────────────────────────────────────────────────────────────────
SWARM_DIR = Path(__file__).parent.parent.parent  # .../swarm-bot
SESSION_DIR = SWARM_DIR / ".session_state"
CHECKPOINT_DIR = SESSION_DIR / "checkpoints"
POLL_INTERVAL = 30        # seconds between state checks
SAVE_INTERVAL = 120       # seconds between mem0/langmem saves
STOP_FILE = SESSION_DIR / "STOP_WATCHER"
PID_FILE = SESSION_DIR / "watcher.pid"
LOG_FILE = SESSION_DIR / "watcher.log"
STATE_FILE = SESSION_DIR / "current.json"

# ── Memory clients ────────────────────────────────────────────────────────────
_mem0_store = None
_langmem_mgr = None

def _get_mem0_store():
    global _mem0_store
    if _mem0_store is None:
        from core.memory.store import MemoryStore
        _mem0_store = MemoryStore()
    return _mem0_store

def _get_langmem():
    global _langmem_mgr
    if _langmem_mgr is None:
        from core.integrations.langmem_integration import SwarmBotMemoryManager
        _langmem_mgr = SwarmBotMemoryManager()
    return _langmem_mgr

# ── Signal handling ──────────────────────────────────────────────────────────
stop_event = Event()

def _handle_sigterm(signum, frame):
    logger.info("SIGTERM received — stopping gracefully")
    stop_event.set()

signal.signal(signal.SIGTERM, _handle_sigterm)

# ── Checkpoint helpers ───────────────────────────────────────────────────────

def _write_checkpoint(state: dict) -> Path:
    """Write a timestamped checkpoint snapshot."""
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    path = CHECKPOINT_DIR / f"checkpoint_{ts}.json"
    tmp = tempfile.NamedTemporaryFile(mode="w", dir=SESSION_DIR, delete=False, suffix=".tmp")
    json.dump(state, tmp, indent=2, default=str)
    tmp.close()
    os.rename(tmp.name, str(path))
    logger.debug("Checkpoint written: %s", path.name)
    return path

def _load_latest_checkpoint() -> dict | None:
    """Load most recent checkpoint."""
    if not CHECKPOINT_DIR.exists():
        return None
    checkpoints = sorted(CHECKPOINT_DIR.glob("checkpoint_*.json"), reverse=True)
    if not checkpoints:
        return None
    try:
        with open(checkpoints[0]) as f:
            return json.load(f)
    except Exception:
        return None

def _load_current_state() -> dict:
    """Load current.json safely."""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def _save_to_memories(state: dict) -> None:
    """Save current session state to mem0 + langmem. All ops non-crashing."""
    try:
        store = _get_mem0_store()
    except Exception as e:
        logger.warning("Could not get mem0 store: %s", e)
        store = None

    try:
        langmem = _get_langmem()
    except Exception as e:
        logger.warning("Could not get langmem: %s", e)
        langmem = None

    # Build text summary from state
    summary_parts = []
    if state.get("session_name"):
        summary_parts.append(f"Session: {state['session_name']}")
    if state.get("last_query"):
        summary_parts.append(f"Last query: {state['last_query']}")
    if state.get("phase"):
        summary_parts.append(f"Phase: {state['phase']}")
    if state.get("task_summary"):
        summary_parts.append(f"Task: {state['task_summary']}")
    if state.get("files_changed"):
        files = state["files_changed"]
        if isinstance(files, list):
            summary_parts.append(f"Files: {', '.join(files[:10])}")
    if state.get("decisions"):
        decisions = state["decisions"]
        if isinstance(decisions, list):
            summary_parts.append(f"Decisions: {'; '.join(decisions[:5])}")

    text = "\n".join(summary_parts) or "OpenCode session state checkpoint"
    if len(text) < 20:
        text = json.dumps(state, default=str)[:500]

    if store:
        try:
            store.remember(content=text, agent_id="opencode", memory_type="episodic")
            logger.debug("Saved to mem0: %s", text[:80])
        except Exception as e:
            logger.debug("mem0 save failed: %s", e)

    if langmem:
        try:
            # langmem.extract_memories takes messages=[{"role": "...", "content": "..."}]
            messages = [{"role": "user", "content": text[:500]}]
            asyncio.run(langmem.extract_memories(messages))
            logger.debug("Saved to langmem")
        except Exception as e:
            logger.debug("langmem save failed: %s", e)

def _write_pid():
    """Write our PID to .session_state/watcher.pid."""
    try:
        with open(PID_FILE, "w") as f:
            f.write(str(os.getpid()))
    except Exception:
        pass

def _log(msg: str) -> None:
    """Write to log file."""
    try:
        SESSION_DIR.mkdir(parents=True, exist_ok=True)
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, "a") as f:
            f.write(f"{ts} {msg}\n")
    except Exception:
        pass

# ── Main loop ────────────────────────────────────────────────────────────────

def run() -> None:
    _log(f"session_watcher started (PID {os.getpid()})")
    _write_pid()
    logger.info("session_watcher started — poll=%ds save=%ds", POLL_INTERVAL, SAVE_INTERVAL)

    _last_save_time = time.time()
    prev_state_str = ""

    while not stop_event.wait(POLL_INTERVAL):
        try:
            # Check stop signal
            if STOP_FILE.exists():
                _log("stop signal detected")
                break

            state = _load_current_state()

            # Checkpoint on state change
            state_str = json.dumps(state, sort_keys=True, default=str)
            if state_str != prev_state_str and state:
                _write_checkpoint(state)
                prev_state_str = state_str
                _last_save_time = time.time()  # reset save timer on new checkpoint
                _log(f"checkpoint created (phase={state.get('phase', '?')})")

            # Periodic save to mem0/langmem
            if time.time() - _last_save_time >= SAVE_INTERVAL:
                _save_to_memories(state)
                _last_save_time = time.time()
                _log("periodic save done")

        except Exception as e:
            logger.debug("Poll error: %s", e)
            _log(f"poll error: {e}")

    # Graceful shutdown: final checkpoint + save
    _log("shutting down — final save")
    final_state = _load_current_state()
    if final_state:
        _write_checkpoint(final_state)
    _save_to_memories(final_state)
    _log("session_watcher stopped")

    # Cleanup
    try:
        if PID_FILE.exists():
            os.remove(PID_FILE)
    except Exception:
        pass
    try:
        if STOP_FILE.exists():
            os.remove(STOP_FILE)
    except Exception:
        pass


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(message)s")
    run()
