---
title: Ruflo Memory Routing
type: concept
status: active
tags: [/]
created: 2026-05-03
updated: 2026-05-03
---

# Ruflo Memory Routing Guide

## The 4 Memory Systems — When to Use Each

### 1. ruflo memory_store (Session-Scoped)
**Use for**: Agent swarm context, task state, coordination data between agents
- **Namespace format**: `project/task-name`
- **Retrieval**: memory_search at task start
- **Lifetime**: Session only — lost after session ends
- **Example**: Storing "implementing PPh21 TER, phase 2 of 4" during a swarm task

### 2. mem0ai (Cross-Session Semantic)
**Use for**: Facts, patterns, user preferences, domain knowledge
- **Storage**: `~/.legion/mem0_history.db` + ChromaDB vectors
- **API**: `mem0_add(user_id, content, metadata)` / `mem0_search(query)`
- **Lifetime**: Permanent until explicitly deleted
- **Example**: "User prefers Indonesian responses", "PPh21 TER uses cumulative method"

### 3. obsidian .wiki/ (Permanent Human-Readable)
**Use for**: Decisions, architecture notes, research findings, retrospectives
- **Location**: `/home/newadmin/swarm-bot/.wiki/`
- **Retrieval**: graphrag query_wiki_graph for research
- **Lifetime**: Permanent — version controlled with git
- **Example**: Architecture decisions, meeting notes, research summaries

### 4. ruflo sessions (Full Snapshots)
**Use for**: Continuing exactly where you left off
- **Save**: session_save at end of every session
- **Restore**: session_restore at start of next session
- **Includes**: Agent state, conversation history, tool call results
- **Example**: Restore a multi-hour refactoring session mid-task

## Memory Routing Rule (Mnemonic)

| Need | System |
|------|--------|
| "Next 5 minutes" | ruflo memory_store |
| "Next week" | mem0ai + obsidian |
| "Search past decisions" | graphrag query_wiki_graph |
| "Continue where I left off" | ruflo session_restore |

## Stacking Example

For a PPh21 TER implementation task:
1. **Start**: `session_restore` → `memory_search` (ruflo) + `mem0_search` (mem0) + `query_wiki_graph` (graphrag)
2. **During**: `memory_store` (ruflo) after each phase completes
3. **End**: `session_save` + `mem0_add` (mem0) + write `.wiki/pph21-ter-decisions.md` (obsidian)