---
allowed-tools: Read,Bash,Grep,Glob
argument-hint: [query]
description: "Search OpenCode session memory. Without args: show recent context. With query: semantic search across session history."
---

# /memory — Query OpenCode session memory

Search and manage the OpenCode persistent memory index.

## Usage
```
/memory
/memory recent decisions about intent routing
/memory LLM model configurations
```

## Memory Architecture

### OpenCode Memory (.opencode/memory/MEMORY.md)
- Project context index
- Updated after each session
- Human + AI readable
- Key files and patterns

### Swarm-Bot Memory (separate system)
- core/memory/memory_manager.py (mem0ai)
- Episodic + semantic memory for the bot itself
- NOT the same as OpenCode memory

## What /memory does
1. Searches .opencode/memory/MEMORY.md
2. Returns relevant entries
3. Shows recency and context

## Swarm-Bot Key Memory Entries
- Project overview (aiogram 3.x, litellm)
- Directory structure
- Critical files (llm_client.py, intent_router.py)
- Agent keywords
- Tools and capabilities

## Output Format
```
## MEMORY_ENTRIES
<matching entries with context>

## LAST_UPDATED
<timestamp>

## SOURCES
<files that contributed to these entries>
```
