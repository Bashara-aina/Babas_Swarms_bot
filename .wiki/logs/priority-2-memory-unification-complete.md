---
title: Priority 2 Memory Unification Complete
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- logs
created: '2026-04-14'
updated: '2026-04-14'
summary: '**Completed:** 2026-04-12'
wikilinks: []
confidence: medium
source: research
---
# PRIORITY 2: Unify Memory to 2 Tiers — COMPLETE

**Completed:** 2026-04-12
**Files created:** `core/long_term_memory.py`
**Files modified:** `core/memory/unified_context.py`, `core/memory/episodic_store.py`
**Verification:** `python scripts/verify_wiring.py` → PASS

## What Was Done

### 1. Created `core/long_term_memory.py`
New semantic vector search layer:

- `LongTermMemory` class with `search()` and `store()` methods
- Uses `sentence-transformers/all-MiniLM-L6-v2` for embedding
- ChromaDB for vector storage (with graceful degradation if unavailable)
- `search_long_term_memory(query, user_id, limit)` → returns `list[MemoryHit]`
- `store_long_term_memory(text, user_id, source)` → for future retrieval
- Strategy: semantic first → FTS fallback → episodic tertiary
- All async, all wrapped in try/except, all logged

### 2. Fixed `core/memory/episodic_store.py` data loss
**The bug:** Line 120-121: `self._local = self._local[-2000:]` silently truncated oldest memories

**The fix:**
- Added `_consolidate_entries()` method: summarizes old entries before truncation
- Modified `store()` to check for `len(self._local) > 1900` BEFORE truncation
- When approaching limit: oldest 300 entries consolidated into a summary entry
- Summary stored as special `episode_type="consolidated_summary"` entry
- Warning logged with entry count: `"Consolidating 300 old memories into summary to prevent data loss"`
- Now preserves historical data instead of losing it

### 3. Updated `core/memory/unified_context.py`
- **Primary retrieval:** `LongTermMemory.search()` (semantic, vector-based)
- **Fallback:** MemoryManager FTS (keyword-based)
- **Working memory:** Core + Profile + Recall always included
- **Deduplication:** avoids showing the same memory from multiple tiers
- Single clear retrieval path replacing the old multi-backend concatenation

## 2-Tier Memory Architecture

```
WORKING MEMORY (session, in-process)
├── Core Memory (JSON key-value, important facts)
├── Recall Memory (SQLite, last 50 turns)
└── Profile (user preferences)

LONG-TERM MEMORY (persistent, semantic) ← NEW
├── Semantic search (vector embeddings) ← PRIMARY
├── Archival FTS (keyword fallback)
└── Episodic store (events, facts)
```

## Key Decisions

### ADR-011: 2-Tier Memory Architecture
**Decision:** Create `core/long_term_memory.py` as the single semantic retrieval entry point
**Rationale:** Eliminates the 8-redundant-memory-facade problem. Single clear path: semantic → FTS → episodic.
**Consequences:** ChromaDB required for full functionality (graceful degradation if unavailable)

### ADR-012: Episodic Memory Consolidation Over Truncation
**Decision:** Instead of `self._local[-2000:]` silent truncation, consolidate old entries into summary before dropping
**Rationale:** Data loss was a trust-breaker per audit. Summary preserves historical information.
**Consequences:** Slight memory overhead when approaching limit; better data preservation

## Next
Priority 3 — Wire Self-Improvement Loop