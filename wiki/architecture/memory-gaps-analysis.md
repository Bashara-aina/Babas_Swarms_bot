---
title: memory-architecture
type: concept
status: active
tags: [memory, architecture, concepts]
created: 2026-04-13
updated: 2026-04-13
summary: Memory architecture defines how Legion stores, retrieves, and manages information across sessions using multiple storage tiers.
wikilinks: [[concepts/intent-routing.md]], [[concepts/reasoning-loop.md]], [[architecture/memory-system-architecture.md]]
confidence: high
source: audit
---

# Memory Architecture

## TL;DR
Legion's memory system spans 8+ subsystems creating context but lacking semantic retrieval — ranked as 4.5/10 with primary issues being redundant facades, no vector search, and silent data loss.

## Current State

### What's Implemented
- **Core Memory**: JSON key-value store for high-priority facts
- **Archival Memory**: SQLite FTS5 for unlimited persistent storage  
- **Recall Memory**: Full conversation history in SQLite
- **Episodic Store**: JSON-based session memory with 2000 entry cap
- **User Profile**: Supabase-backed persistent user data
- **Temporal Graph**: aiosqlite bi-temporal knowledge tracking
- **Semantic Cache**: In-memory LRU for fast retrieval
- **mem0 Integration**: Vector embeddings for memory

### Critical Problems

**1. Silent Data Loss**
`core/memory/episodic_store.py` truncates at 2000 entries:
```python
self._local = self._local[-2000:]  # Oldest data deleted without warning
```

**2. Redundant Facades**
4+ memory facades with overlapping functionality:
- `core/memory/memory_manager.py`
- `core/memory/unified_context.py`
- `core/legion_memory_facade.py`
- `core/memory_engine.py`

**3. No Semantic Retrieval**
All retrieval uses keyword FTS, not embeddings. Natural language queries fail:
```
Query: "What's my main project?"
Expected: "I'm building a rental website"
Actual: No match (only keyword FTS)
```

**4. Per-User Isolation Partial**
Core memory, archival memory, and temporal graph are NOT user-scoped.

## Target Architecture (2-Tier)

**Tier 1 — Working Memory** (session, in-process)
- Python dict keyed by user_id
- 50 exchanges max per session
- Fast, ephemeral

**Tier 2 — Long-Term Memory** (persistent, semantic)
- SQLite + sentence-transformers embeddings
- Cosine similarity retrieval
- Per-user isolated

## Related Pages

- [[architecture/memory-system-architecture.md]] — Technical implementation details
- [[concepts/reasoning-loop.md]] — How reasoning uses memory
- [[concepts/intent-routing.md]] — How routing interacts with memory