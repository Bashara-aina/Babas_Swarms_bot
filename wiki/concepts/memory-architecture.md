---
title: memory-architecture
type: concept
status: active
tags: [memory, storage, chromadb, mem0, sqlite]
created: 2026-04-13
updated: 2026-04-13
summary: Legion's memory is a multi-layered system spanning short-term conversation context, medium-term session transcripts, and long-term semantic knowledge, with graceful degradation when any layer fails.
wikilinks:
  - [[intent-routing]]
  - [[vector-search]]
  - [[self-improvement-loop]]
  - [[chromadb]]
confidence: high
source: implementation
---

# Memory Architecture

## TL;DR
Legion's memory is a multi-layered system: short-term conversation context lives in LLM prompts, medium-term session transcripts persist in SQLite across bot restarts, and long-term semantic knowledge lives in ChromaDB via mem0. Each layer has independent failure modes and graceful degradation paths, so no single outage kills the entire memory system.

## Overview

Memory in Legion is not a single database — it is a tiered architecture where each tier serves a different time horizon and access pattern. The three tiers are designed to be independently replaceable: if ChromaDB goes down, SQLite-backed transcripts continue working; if SQLite corrupts, in-memory context still functions for the current session.

## Context

Legion is Bashara's permanent AI coworker accessed via Telegram. Without memory, every conversation would start from scratch with zero context about who Bashara is, what projects exist, or what preferences have been established. The memory architecture solves this by ensuring relevant context is available at inference time without requiring explicit retrieval calls from the handler layer.

## Key Properties

- **Three independent tiers** — Conversation context, session transcripts, long-term memory
- **Persistence across restarts** — SQLite transcript survives bot crashes and restarts
- **Semantic search** — ChromaDB enables recall by meaning, not just keywords
- **Auto-extraction** — UserProfile and CoreMemory automatically capture stated preferences
- **Graceful degradation** — Any tier can fail without cascading to others
- **Budget-aware** — Memory operations check BudgetManager before spending on LLM calls
- **Importance scoring** — Facts marked high-importance (≥0.85) get promoted to CoreMemory

## How It Works

### Layer 1: Conversation Context (In-Memory)
Recent message turns are kept in an in-memory list and injected into every LLM prompt. When the context window approaches capacity, oldest turns are pruned first — but SOUL.md and character definition are never trimmed. The `MemoryManager.build_context_block()` assembles this layer by calling `self.recall.get_recent(n=10)` and formatting it for the prompt.

### Layer 2: Session Transcripts (SQLite)
`core/session/transcript.py` stores full conversation history in a SQLite database keyed by session_id. On bot startup, transcripts are replayed to restore context. The schema tracks role, content, agent_used, emotion_state, and timestamp per turn. `add_conversation_turn()` auto-assigns importance: 0.7 for messages with "?", 0.9 for messages containing "remember", "important", "always", "never".

### Layer 3: Long-Term Memory (ChromaDB + mem0)
Important facts, learned patterns, and project context are embedded and stored in ChromaDB. `MemoryManager.save()` writes to ArchivalMemory with importance, tags, and source. `MemoryManager.search()` queries ChromaDB for semantically similar memories. The `core/memory/tiers.py` defines `ArchivalMemory`, `CoreMemory`, and `RecallMemory` as separate backing stores.

### Memory Auto-Extraction Pipeline
`auto_extract_and_save()` scans every user message for trigger phrases ("my name is", "i prefer", "i use", "i'm working on", "always", "never", "remember that", "my gpu", etc.). When triggered, the message is saved to ArchivalMemory and optionally promoted to CoreMemory if importance ≥ 0.85. Preference signals and known facts are also extracted and stored in UserProfile.

## Relationships

Memory architecture is the foundation that makes every other intelligence layer possible. [[intent-routing]] depends on memory to retrieve context about past user requests when classifying ambiguous messages. [[self-improvement-loop]] writes lessons learned back into memory so future reasoning can avoid repeat failures. [[vector-search]] is the retrieval mechanism ChromaDB uses — without vector search, semantic memory recall would collapse to keyword matching. The [[chromadb]] entity page details the specific configuration (collection name, embedding model, top-k) used in production.

## Current Status

**Implemented.** All three tiers are functional in production. The transcript layer was upgraded in the 2026-04-12 ClawCode session (U1). Auto-extraction fires on every user message. ChromaDB is used for long-term memory recall. Graceful degradation is confirmed working — bot continues without memory if ChromaDB is unreachable.

## See Also

- [[intent-routing]] — Intent classification uses memory context
- [[vector-search]] — ChromaDB semantic search engine
- [[self-improvement-loop]] — Learning from memory outcomes
- [[chromadb]] — Vector database backing long-term memory
