---
title: vector-search
type: concept
status: active
tags: [vector, search, embeddings, chromadb, rag]
created: 2026-04-13
updated: 2026-04-13
summary: Vector search uses embeddings to enable semantic similarity search over documents, powering RAG and memory recall in Legion.
wikilinks: [[entities/chromadb.md], [concepts/memory-architecture.md], [concepts/rag-engineer.md]]
confidence: high
source: implementation
---

# Vector Search

## TL;DR
Vector search converts text to numerical embeddings and finds similar content based on cosine similarity in high-dimensional space.

## How It Works

1. **Index**: Documents → embeddings → stored in ChromaDB
2. **Query**: User query → embedding → similarity search
3. **Retrieve**: Top-k most similar documents returned

## Legion's Usage

### Memory Recall
```
user query → embed → ChromaDB similarity search → top memories
```

### Wiki Retrieval
```
user question → embed → search wiki knowledge → inject into context
```

## Embedding Models

| Model | Dimensions | Use Case |
|-------|------------|----------|
| text-embedding-3-small | 1536 | General |
| nomic-embed-text | 768 | Local/Ollama |

## ChromaDB Configuration

- Collection: `legion_memory`
- Metric: cosine similarity
- Top-k: 5 most similar

## Related Pages

- [[entities/chromadb.md]] — Vector database
- [[concepts/memory-architecture.md]] — Memory system
