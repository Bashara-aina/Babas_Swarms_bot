---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/architecture/memory-system-architecture.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-05-08T01:00:00.473767"
}
---

---
title: memory-system-architecture
type: architecture
status: active
tags: [memory, architecture, chromadb, sqlite, mem0, vector]
created: 2026-04-13
updated: 2026-04-13
summary: Legion's memory system spans 8 subsystems including Core Memory (JSON), Archival Memory (SQLite FTS5), Recall Memory (conversation log), Episodic Store (Supabase/JSON), User Profile (Supabase), Temporal Knowledge Graph (aiosqlite bi-temporal), Semantic Cache (LRU), and mem0 vector embeddings — with ongoing unification efforts.
wikilinks:
  - [[concepts/memory-architecture]]
  - [[entities/chromadb]]
  - [[entities/litellm]]
  - [[architecture/legion-module-map]]
confidence: medium
source: implementation
---

# Memory System Architecture

## TL;DR
Legion's memory system is a multi-tier architecture spanning 8 subsystems: Core Memory (JSON key-value), Archival Memory (SQLite FTS5), Recall Memory (conversation log), Episodic Store (Supabase/JSON), User Profile (memobase), Temporal Knowledge Graph (graphiti bi-temporal), Semantic Cache (in-memory LRU), and mem0 vector embeddings. The system is undergoing consolidation to eliminate redundancy and add semantic vector search at inference time.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      LLM Context Window                          │
│     (last N messages, system prompt, soul, personality)          │
│                        ~4000 tokens                              │
└─────────────────────────────┬───────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────┐
│                    Working Memory                                │
│              (core/working_memory.py)                           │
│        8 open threads, 5 pending follow-ups, 300-char focus      │
└─────────────────────────────┬───────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────┐
│                    SessionTranscriptStore                        │
│                  (core/session/transcript.py)                    │
│        SQLite + aiosqlite, per-user, date-queryable              │
│        Schema: sessions(id, user_id, created_at, summary)       │
└─────────────────────────────┬───────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────┐
│                    Long-Term Memory                              │
│     ┌──────────────────┬──────────────────────────────────┐     │
│     │   ChromaDB       │  Semantic Cache (LRU)            │     │
│     │   (mem0)         │  Query result caching            │     │
│     │   Vector search  │                                  │     │
│     └──────────────────┴──────────────────────────────────┘     │
└─────────────────────────────┬───────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────┐
│                    External Stores                               │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐   │
│  │  Episodic     │ │  User        │ │  Temporal            │   │
│  │  Store        │ │  Profile     │ │  Knowledge Graph     │   │
│  │  (Supabase)   │ │  (memobase)  │ │  (graphiti)          │   │
│  └──────────────┘ └──────────────┘ └──────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Memory Subsystems

### 1. Core Memory (`core/memory/core_memory.py`)
- **Storage**: JSON file, in-memory dict
- **Purpose**: High-priority facts always in every prompt
- **Access**: Synchronous, instant
- **Example**: User name, active projects, preferences

### 2. Archival Memory (`core/memory/archive.py`)
- **Storage**: SQLite with FTS5 (full-text search)
- **Purpose**: Unlimited persistent storage
- **Access**: Keyword search via FTS5
- **Limitation**: No semantic similarity

### 3. Recall Memory (`core/memory/recall.py`)
- **Storage**: SQLite conversation log
- **Purpose**: Full conversation history
- **Access**: Last 50 turns retrieved by default
- **Growth**: Unbounded — every turn stored forever

### 4. Episodic Store (`core/memory/episodic_store.py`)
- **Storage**: Supabase PostgreSQL + local JSON backup
- **Purpose**: Session events, user corrections
- **Critical Issue**: `self._local = self._local[-2000:]` silently truncates oldest memories
- **Note**: Being fixed to summarize instead of delete

### 5. User Profile (`core/memory/user_profile.py`)
- **Storage**: Supabase JSON
- **Purpose**: Persistent user identity and preferences
- **Growth**: Automatic from interactions and explicit `/teach`

### 6. Temporal Knowledge Graph (`core/memory/temporal_graph.py`)
- **Storage**: aiosqlite bi-temporal
- **Purpose**: Facts with validity windows over time
- **Seeded**: Known facts about Bashara from day one

### 7. Semantic Cache (`core/memory/semantic_cache.py`)
- **Storage**: In-memory LRU cache
- **Purpose**: Avoid re-computing for repeated queries
- **TTL**: Configurable per query type

### 8. mem0 Vector Store (`core/memory/mem0_store.py`)
- **Storage**: ChromaDB with sentence-transformers embeddings
- **Purpose**: Semantic search over memories
- **Embedding**: all-MiniLM-L6-v2
- **Collection**: `legion_memory`

## Unification Efforts

Per the 2026-04-12 deep audit, the following unification is underway:

### Current Problems
- 8 memory subsystems + 4 facades = context bloat
- No semantic vector search at inference time
- Silent data loss in episodic store
- Redundant context injection (all layers concatenated)

### Target: 2-Tier Model
1. **Working Memory** — session-scoped, in-process, Python dict
2. **Long-Term Memory** — persistent, SQLite + vector embeddings

### Memory Manager (`core/memory/memory_manager.py`)
Primary facade being consolidated:

```python
class MemoryManager:
    async def get_context(self, user_id, query, max_tokens=400) -> str:
        # Step 1: Working memory (last 5 exchanges)
        working = self.working_memory.get_recent(user_id, last_n=5)
        
        # Step 2: Long-term semantic retrieval
        long_term = await self.long_term_memory.retrieve(user_id, query, top_k=5)
        
        # Step 3: Profile (top 10 highest importance)
        profile = await self.long_term_memory.get_profile(user_id)
        
        # Step 4: Build with token budget
        return build_with_budget([profile, long_term, working], max_tokens)
```

## Data Flow

```
User Message
    → Intent Router
    → Memory Manager.get_context(user_id, query)
        → working_memory.get_recent()
        → long_term_memory.retrieve() [semantic search]
        → user_profile.get()
    → System Prompt Builder (13 layers)
        → [Memory context injected as layer]
    → LLM
    → Response
    → Memory Manager.store(user_id, message, response)
        → episodic_store.add()
        → recall_memory.add()
        → (future: long_term_memory.embed_and_store())
```

## Nightly Consolidation

At 02:00 JST daily:
1. Deduplication (TF-IDF cosine similarity > 0.85)
2. Clustering of old memories
3. Promotion of key facts to core memory
4. Summarization of episodic batches (replacing truncation)

## Failure Handling

| Component | On Failure | Behavior |
|-----------|------------|----------|
| Working Memory | — | Cleared on restart, not persisted |
| SQLite Stores | DB corrupt | Fresh DB created, data loss |
| Supabase | Connection lost | Continue with local fallback |
| ChromaDB | Unavailable | Bot continues, no semantic search |
| Episodic Store | Full | Silent truncation (BUG — fix in progress) |

## Related Pages

- [[concepts/memory-architecture]] — Memory concepts
- [[entities/chromadb]] — Vector database
- [[architecture/legion-module-map]] — Module overview
