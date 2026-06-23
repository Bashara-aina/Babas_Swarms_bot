#!/usr/bin/env python3
"""
Run this at the start of every OpenCode session.
Prints a rich memory context block to paste into your first message.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.memory.store import MemoryStore

store = MemoryStore()
status = store.status()

print("\n" + "═" * 60)
print("🧠 BABAS SWARMS — SESSION MEMORY CONTEXT")
print("═" * 60)
print(f"Total memories: {status['total_memories']}")
print(f"Storage: {status['storage_path']}")
print(f"Embedder: {status['embedder']}")
print("═" * 60)

topics = [
    "project architecture and structure",
    "recent tasks and decisions",
    "cekwajar implementation status",
    "legion agent configuration",
    "active bugs or issues",
]

if len(sys.argv) > 1:
    topics = [" ".join(sys.argv[1:]), *topics[:2]]

print("\n📚 RECALLED CONTEXT FOR THIS SESSION:\n")
seen = set()
all_memories = []

for topic in topics:
    memories = store.recall(topic, top_k=5, min_score=0.3)
    for m in memories:
        key = m[:80]
        if key not in seen:
            seen.add(key)
            all_memories.append(m)

if all_memories:
    for i, m in enumerate(all_memories[:15], 1):
        print(f"{i}. {m[:300]}{'...' if len(m) > 300 else ''}")
        print()
else:
    print("  (No memories yet — this may be your first session)")

print("═" * 60)
print("💡 TIP: Run with a topic: python scripts/opencode_session_start.py 'legion bug'")
print("═" * 60 + "\n")
