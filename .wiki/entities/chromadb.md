---
title: ChromaDB
type: entity
status: active
tags: [vector, database, embeddings, rag]
created: 2026-04-13
updated: 2026-04-13
summary: ChromaDB is an open-source vector database used by Legion for storing embeddings that power semantic memory recall. Collection `legion_memory` stores facts and entity relationships queried by cosine similarity.
wikilinks:
  - [[vector-search]]
  - [[memory-architecture]]
  - [[litellm]]
confidence: high
source: implementation
project: legion
---

# ChromaDB

## TL;DR
ChromaDB is Legion's semantic memory store — an open-source vector database that persists embeddings for the `legion_memory` collection at `data/chromadb/`. When Legion needs to recall facts about Bashara or prior conversations, it queries ChromaDB by cosine similarity. If ChromaDB is unavailable, the bot degrades gracefully and continues without memory.

## Storage Configuration
```python
import chromadb
client = chromadb.PersistentClient(path="./data/chromadb")
collection = client.get_collection("legion_memory")
```
- Storage path: `data/chromadb/` (relative to swarm-bot root)
- Collection name: `legion_memory`
- Persisted to disk — survives restarts

## Embedding Generation
Embeddings are generated via LiteLLM's embedding endpoint using `text-embedding-3-small` (OpenAI) or equivalent model. The embedding model is selected automatically based on availability.

## Query Pattern
```python
results = collection.query(
    query_texts=["Bashara's preferences"],
    n_results=5
)
# Returns (ids, distances, documents, metadatas)
```

## Failure Modes
- **ChromaDB unavailable**: `chromadb.errors.NotFoundError` → logged as warning, bot continues without memory
- **Collection missing**: Auto-created on first write
- **Embedding API down**: Fallback to in-memory dict lookup (degraded mode)

## Relationship to Other Memory Tiers
ChromaDB is Tier 3 (Semantic) in Legion's 6-tier memory system:
1. Working memory (in-process dict) — current session
2. Episodic (SQLite) — recent conversations
3. **Semantic (ChromaDB)** — vector search over facts/entities ← this tier
4. Core facts (memory_manager facade)
5. Graph (graphiti-core) — relationship knowledge
6. Long-term (Letta) — hierarchical

## See Also
[[vector-search]] — How semantic search is implemented
[[memory-architecture]] — Full 6-tier memory system
[[litellm]] — Embedding generation via litellm
