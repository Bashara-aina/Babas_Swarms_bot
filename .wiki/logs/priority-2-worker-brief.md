---
title: Priority 2 Worker Brief
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
summary: '**Files to create:** `core/long_term_memory.py` (new semantic search layer)'
wikilinks: []
confidence: medium
source: research
---
# PRIORITY 2: Unify Memory to 2 Tiers
**Files to create:** `core/long_term_memory.py` (new semantic search layer)
**Files to modify:** `core/memory/unified_context.py`, `core/memory/episodic_store.py` (fix data loss)
**Files to archive:** Move to `_archive/` after implementation confirmed

## Spec from Audit

### DIMENSION 2: MEMORY DEPTH (4.5/10 → 9/10)
Key problems:
1. **8 redundant memory facades** with unclear ownership
2. **No semantic vector search at inference time** — only keyword FTS
3. **Context bloat** — episodic + core + archival + profile all concatenated
4. **Silent data loss** — `episodic_store.py:120`: `self._local = self._local[-2000:]` truncates without warning
5. **Recall memory grows unbounded**

### Target Architecture: 2-Tier Memory

```
WORKING MEMORY (session, in-process)
├── Core Memory (JSON key-value, important facts)
├── Recall Memory (SQLite, last 50 turns)
└── Profile (user preferences, schedule)

LONG-TERM MEMORY (persistent, semantic)
├── Archival Memory (SQLite FTS)
├── Episodic Store (Supabase + local JSON)
└── Semantic Cache (in-memory LRU, vector embeddings)
```

**Single retrieval path:** `LongTermMemory.search(query)` → vector similarity → top-k

## What to Build

### 1. Create `core/long_term_memory.py` (NEW)
A semantic vector search layer using sentence-transformers:

```python
class LongTermMemory:
    """Single semantic retrieval entry point for long-term memory.
    
    Uses sentence-transformers (all-MiniLM-L6-v2) for embedding.
    Stores embeddings in ChromaDB (or in-memory fallback).
    Combines: archival FTS + episodic + semantic cache.
    """
    
    async def search(query: str, user_id: str, limit: int = 5) -> list[str]
    # → Returns text snippets from long-term memory, ranked by semantic similarity
```

Key features:
- **async def** — all methods async
- **try/except** on every operation — graceful degradation if ChromaDB unavailable
- **logger calls** — on entry, results, errors
- **Sentence-transformers embedding** for semantic (not keyword) search
- **ChromaDB** for vector storage (with in-memory fallback)
- **Combines archival FTS + episodic** — both layers searched and deduplicated
- **Per-user isolation** — user_id scoped

### 2. Fix `core/memory/episodic_store.py` data loss
**Line ~120:** `self._local = self._local[-2000:]` silently truncates oldest memories

**Fix:** Instead of truncation, either:
a) Consolidate old memories (summarize clusters → store summary, drop originals)
b) Warn user when approaching limit
c) Both

Implementation:
```python
# Before truncation:
if len(self._local) > 1800:  # approaching limit
    # Consolidate oldest 200 entries into summaries
    old_entries = self._local[:-200]
    summary = self._summarize_entries(old_entries)
    # Store summary separately, then truncate
    self._local = self._local[-2000:]
    # Log warning
    logger.warning("[EpisodicStore] Consolidating %d old memories to prevent data loss", len(old_entries))
```

### 3. Update `core/memory/unified_context.py`
- Import and use `LongTermMemory` for semantic search
- Add vector similarity search alongside (not replacing) FTS
- Deduplicate results from different memory tiers

## Requirements
1. **async def** — all functions async
2. **Proper imports** — type hints, logging
3. **try/except** on all async calls — never crash the bot
4. **logger calls** — log entry and exit
5. **Dependency injection** — imports inside functions for optional deps
6. **Graceful degradation** — if ChromaDB unavailable, fall back to FTS-only

## Hard Rules
- Never edit SOUL.md, CLAUDE.md, LEGION_MASTER.md
- Do NOT delete files — create new only
- Do NOT archive until verify_wiring.py passes
- Every new function: async def, try/except, logger calls, type hints