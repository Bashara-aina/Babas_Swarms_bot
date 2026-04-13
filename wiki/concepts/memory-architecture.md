---
title: memory-architecture
type: concept
status: active
tags: [memory, storage, chromadb, mem0]
created: 2026-04-13
updated: 2026-04-13
summary: Legion's memory system uses a layered architecture combining ChromaDB for vector storage, mem0 for managed memory, and SQLite for transcript persistence.
wikilinks: [[concepts/intent-routing.md]], [[concepts/vector-search.md]], [[entities/chromadb.md]]
confidence: high
source: implementation
---

# Memory Architecture

## TL;DR
Legion's memory is a multi-layered system: short-term conversation context in LLM context, medium-term session transcripts in SQLite, and long-term knowledge in ChromaDB via mem0.

## Layers

### Layer 1: Conversation Context
- In-memory list of recent messages
- Included in every LLM prompt
- Pruned when context window nears capacity

### Layer 2: Session Transcripts (SQLite)
- `core/session/transcript.py` stores conversation history
- Survives bot restarts
- Queryable by date/user

### Layer 3: Long-term Memory (ChromaDB + mem0)
- Vector embeddings of important facts
- Semantic search via `memory_manager`
- Relationship tracking between entities

## Failure Modes

- **ChromaDB down**: Bot continues without memory, logs warning
- **SQLite corrupt**: Fresh transcript store created
- **mem0 unavailable**: Graceful degradation to stateless mode

## Related Pages

- [[entities/chromadb.md]] — Vector database
- [[concepts/vector-search.md]] — Semantic search implementation
