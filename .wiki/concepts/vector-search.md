---
title: vector-search
type: concept
status: active
tags: [vector, search, embeddings, chromadb, rag, semantic]
created: 2026-04-13
updated: 2026-04-13
summary: Vector search converts text into numerical embeddings and finds similar content using cosine similarity in high-dimensional space, powering semantic memory recall and wiki retrieval in Legion.
wikilinks:
  - [[./entities/chromadb]]
  - [[./concepts/memory-architecture]]
  - [[./concepts/karpathy-kb-pattern]]
  - [[./concepts/context-window-budget]]
confidence: high
source: implementation
---

# Vector Search

## TL;DR
Vector search enables semantic similarity retrieval: text is converted to a high-dimensional embedding vector, and queries find the closest vectors by cosine similarity. In Legion, this powers memory recall (finding past conversations by meaning, not keywords) and wiki retrieval (injecting relevant knowledge into context). The underlying engine is ChromaDB.

## Overview

Traditional search matches keywords. "what did i say about my gpu" returns nothing if you wrote "my graphics card has been overheating" because there are no keyword overlaps. Vector search solves this by converting both the stored text and the query into embedding vectors — numeric representations of semantic meaning — and finding stored items whose vectors are closest to the query vector.

## Context

Legion needs to recall past context without Bashara explicitly retrieving it. When Bashara says "training gimana" (how's the training), Legion needs to find GPU status information from previous conversations even though the phrasing is different. Vector search makes this possible by indexing conversation embeddings and retrieving semantically similar ones regardless of keyword overlap.

## Key Properties

- **Semantic, not lexical**: Finds meaning matches even when vocabulary differs
- **ChromaDB backend**: `legion_memory` collection, cosine similarity metric, top-k=5 results
- **Embedding models**: text-embedding-3-small (1536 dimensions, OpenAI-compatible) for general use; nomic-embed-text (768 dimensions, Ollama-local) for local GPU inference
- **High-dimensional space**: 768–1536 dimensions depending on model; similarity computed by cosine similarity
- **Memory integration**: ChromaDB stores vector embeddings; MemoryManager.search() queries them
- **RAG pipeline**: User query → embed → ChromaDB similarity search → top-k memories → inject into LLM context
- **Wiki retrieval**: Same pipeline used to inject relevant wiki content into context when processing queries
- **Graceful degradation**: If ChromaDB is unavailable, search returns empty list and bot continues without memory

## How It Works

### Indexing Phase
1. A document (memory, wiki excerpt) is taken
2. An embedding model converts it to a vector (list of floats)
3. The vector is stored in ChromaDB with the original text as metadata

### Query Phase
1. User query arrives: "training gimana gpu"
2. Same embedding model converts query to a vector
3. ChromaDB computes cosine similarity between query vector and all stored vectors
4. Top-k most similar results are returned with their text metadata
5. Results are injected into the LLM prompt as context

### ChromaDB Configuration
```
Collection: legion_memory
Embedding function: text-embedding-3-small (or nomic-embed-text for local)
Metric: cosine similarity
Top-k: 5 most similar results
```

### In-Memory Recall Pipeline
```
MemoryManager.search(query="gpu training status")
  → embed query with ChromaDB
  → cosine similarity search
  → top-5 results
  → format as context block
  → inject into system prompt
```

## Relationships

Vector search is the retrieval mechanism for [[./concepts/memory-architecture]]'s Layer 3 (long-term memory). Without it, semantic recall would collapse to keyword matching, making memory practically useless for queries with different phrasing. The [[./entities/chromadb]] entity page details the specific configuration (collection name, embedding model, top-k) and operational considerations. Embedding computation is token-intensive and factors into [[./concepts/context-window-budget]] — each memory search consumes tokens from the embedding model's context window. The [[./concepts/karpathy-kb-pattern]] wiki structure makes wiki retrieval viable: structured, synthesized pages with clear summaries can be efficiently embedded and retrieved.

## Current Status

**Implemented.** ChromaDB is running with the `legion_memory` collection. Embedding models are configured (text-embedding-3-small for cloud, nomic-embed-text for local Ollama). Memory search is functional. Wiki retrieval via the same pipeline is in use via `wiki_loader.py`. Graceful degradation when ChromaDB is unavailable is confirmed working.

## See Also

- [[./entities/chromadb]] — Vector database configuration and operational details
- [[./concepts/memory-architecture]] — Memory layers where vector search is Layer 3
- [[./concepts/context-window-budget]] — Token costs of embedding computation
- [[./concepts/karpathy-kb-pattern]] — Wiki pattern that makes wiki retrieval effective
