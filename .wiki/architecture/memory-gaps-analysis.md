---
title: Memory Gaps Analysis
type: architecture
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- architecture
created: '2026-04-14'
updated: '2026-04-14'
summary: Legion's memory system spans 8+ subsystems creating context but lacking semantic
  retrieval — ranked as 4.5/10 with primary issues being redundant facades, no vector
  search, and silent data loss.
wikilinks: []
confidence: medium
source: research
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

- [[architecture/memory-system-architecture]] — Technical implementation details
- [[concepts/memory-architecture]] — Memory concepts
- [[projects/legion-bot]] — Project using this architecture

## Audit Findings Summary

| Issue | Severity | Affected Subsystem | Impact |
|-------|----------|-------------------|--------|
| Silent truncation at 2000 entries | Critical | Episodic Store | Data loss invisible to user |
| 4+ redundant memory facades | High | memory_manager, unified_context, legion_memory_facade | Maintenance burden, inconsistent API |
| No vector search for NL queries | High | Semantic Cache | Natural language memory queries fail |
| Per-user isolation incomplete | Medium | Core/Archival/Temporal Graph | Cross-user data leakage risk |
| mem0 integration untested | Medium | mem0 | Vector search may not work in prod |