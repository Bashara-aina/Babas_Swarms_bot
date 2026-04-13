---
title: memory-system-architecture
type: architecture
status: active
tags: [memory, architecture, chromadb, sqlite]
created: 2026-04-13
updated: 2026-04-13
summary: Legion's memory system uses three layers: in-context conversation, SQLite session transcripts, and ChromaDB vector storage.
wikilinks: [[concepts/memory-architecture.md], [entities/chromadb.md]]
confidence: high
source: implementation
---

# Memory System Architecture

## TL;DR
Three-tier memory: fast in-context, persistent SQLite transcripts, and searchable ChromaDB vector storage.

## Architecture Diagram

```
┌─────────────────────────────────────────┐
│           LLM Context                   │
│  (last N messages, system prompt)        │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│        SessionTranscriptStore           │
│            (SQLite)                     │
│     Per-user, date-queryable            │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│         ChromaDB (mem0)                 │
│     Vector embeddings, semantic         │
│           search                         │
└─────────────────────────────────────────┘
```

## Components

### SessionTranscriptStore
- **Location**: `core/session/transcript.py`
- **Storage**: SQLite with aiosqlite
- **Schema**: sessions(id, user_id, created_at, summary)
- **Operations**: init, add_turn, get_session, search

### ChromaDB Collection
- **Collection name**: `legion_memory`
- **Embedding**: text-embedding-3-small
- **Ops**: add, query, get, delete

## Failure Handling

| Component | On Failure | Behavior |
|-----------|------------|----------|
| LLM Context | — | Trims oldest messages |
| SQLite | DB corrupt | Fresh DB created |
| ChromaDB | Unavailable | Bot continues, no memory |

## Related Pages

- [[concepts/memory-architecture.md]] — Concept overview
- [[entities/chromadb.md]] — Vector DB
