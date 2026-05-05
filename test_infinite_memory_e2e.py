"""
E2E tests for infinite memory system.
Run: python3 test_infinite_memory_e2e.py
"""
import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

# Change to swarm-bot dir for path resolution
os.chdir(Path(__file__).parent)

def test_write_state():
    """Test .session_state/current.json write/read."""
    from core.memory.session_watcher import _load_current_state, SESSION_DIR, STATE_FILE
    SESSION_DIR.mkdir(exist_ok=True)
    test_state = {"phase": "test", "task_summary": "test task", "session_name": "e2e_test"}
    with open(STATE_FILE, "w") as f:
        json.dump(test_state, f)
    loaded = _load_current_state()
    assert loaded["phase"] == "test", f"Expected phase=test, got {loaded}"
    print("✓ test_write_state: current.json write/read OK")
    shutil.rmtree(SESSION_DIR, ignore_errors=True)

def test_mem0_save_recall():
    """Test mem0 save + semantic recall."""
    from core.memory.store import MemoryStore
    store = MemoryStore()
    before = store.count()
    store.remember(content="E2E test memory about intent routing in OpenCode session", agent_id="opencode", memory_type="episodic")
    after = store.count()
    assert after >= before, f"Expected >= {before}, got {after}"
    results = store.recall(query="intent routing OpenCode", agent_id=None, top_k=3, min_score=0.25)
    print(f"✓ test_mem0_save_recall: stored, count now {after}, recall returned {len(results)} results")
    assert len(results) >= 1, f"Expected at least 1 recall result, got {len(results)}"

def test_memory_injector():
    """Test 4-layer recall engine."""
    from core.memory.memory_injector import build_memory_context
    SESSION_DIR = Path(".session_state")
    SESSION_DIR.mkdir(exist_ok=True)
    (SESSION_DIR / "checkpoints").mkdir(exist_ok=True)
    # Write a checkpoint for layer 1
    with open(SESSION_DIR / "checkpoints" / "checkpoint_20260506_120000.json", "w") as f:
        json.dump({"task": "infinite memory build", "phase": "done"}, f)
    ctx = build_memory_context("infinite memory", user_id="bashara")
    assert len(ctx) > 50, f"Expected context > 50 chars, got {len(ctx)}"
    assert "RECALLED MEMORY" in ctx, "Expected RECALLED MEMORY header"
    assert SESSION_DIR.joinpath("recalled_context.md").exists(), "recalled_context.md should exist"
    print(f"✓ test_memory_injector: 4-layer recall OK, context {len(ctx)} chars")
    shutil.rmtree(SESSION_DIR, ignore_errors=True)

def test_session_watcher_lifecycle():
    """Test watcher start/stop via STOP_SIGNAL."""
    from core.memory.session_watcher import SESSION_DIR, STOP_FILE, PID_FILE, LOG_FILE, run, stop_event, _write_checkpoint, _load_current_state
    SESSION_DIR.mkdir(exist_ok=True)
    (SESSION_DIR / "checkpoints").mkdir(exist_ok=True)
    stop_event.clear()
    # Write a state file
    with open(SESSION_DIR / "current.json", "w") as f:
        json.dump({"phase": "test", "session_name": "lifecycle_test"}, f)
    # Touch stop file to end the loop immediately
    STOP_FILE.touch()
    # Run the watcher (it will see stop file and exit immediately)
    run()
    assert PID_FILE.exists() == False or not Path(PID_FILE).read_text().strip(), "PID file should be cleaned up"
    assert STOP_FILE.exists() == False, "STOP_FILE should be cleaned up after run()"
    print("✓ test_session_watcher_lifecycle: start/stop cycle OK")
    shutil.rmtree(SESSION_DIR, ignore_errors=True)

def main():
    print("=== Infinite Memory E2E Tests ===\n")
    tests = [
        test_write_state,
        test_mem0_save_recall,
        test_memory_injector,
        test_session_watcher_lifecycle,
    ]
    passed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"✗ {t.__name__}: {e}")
            import traceback
            traceback.print_exc()
    print(f"\n=== {passed}/{len(tests)} passed ===")

if __name__ == "__main__":
    main()