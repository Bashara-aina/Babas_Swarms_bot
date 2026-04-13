---
title: chromadb
type: entity
status: active
tags: [vector, database, embeddings, rag]
created: 2026-04-13
updated: 2026-04-13
summary: ChromaDB is the vector database used for storing embeddings powering memory recall and knowledge retrieval in Legion.
wikilinks: [[vector-search]], [[memory-architecture]]
confidence: high
source: implementation
---

# ChromaDB

## TL;DR
ChromaDB is an open-source vector database for storing embeddings, used by Legion for memory persistence and semantic search.

## Legion Usage

### Memory Storage
- Collection: `legion_memory`
- Stores entity relationships and facts
- Queryable by semantic similarity

### Wiki Retrieval
- Embeds wiki content
- Enables semantic search over knowledge

## Configuration

```python
import chromadb
client = chromadb.PersistentClient(path="./data/chromadb")
collection = client.get_collection("legion_memory")
```

## Fallback Behavior

If ChromaDB unavailable:
- Bot continues without memory
- Logs warning
- All features work (degraded)

## Related Pages

- [[vector-search]] — Search implementation
- [[memory-architecture]] — Memory system
