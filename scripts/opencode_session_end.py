#!/usr/bin/env python3
"""
Run this at the END of every OpenCode session.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.memory.store import MemoryStore

store = MemoryStore()

print("📝 Enter session summary (what was accomplished, decisions made, bugs found, code written).")
print("   Press Ctrl+D when done:\n")

try:
    content = sys.stdin.read().strip()
except KeyboardInterrupt:
    print("\nCancelled.")
    sys.exit(0)

if not content or len(content) < 20:
    print("Summary too short, not stored.")
    sys.exit(0)

n = store.remember(
    content=content,
    agent_id="opencode",
    memory_type="episodic",
    importance=1.5,
)

print(f"\n✅ Stored {n} memory chunks from this session.")
print(f"   Total memories: {store.count()}")
print("   These will be recalled automatically in future sessions.")