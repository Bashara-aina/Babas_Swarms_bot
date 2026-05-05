---
allowed-tools: Read,Bash,Grep,Glob,Task
argument-hint: [query]
description: "Recall prior session context from 4-layer memory before starting work. Query is optional — without args shows recent context."
---

# /memory — Infinite Memory Recall (4-Layer Engine)

Before starting any task, run `/memory <brief query>` to pull in prior context.

## Usage
```
/memory                          # show recent context
/memory intent routing decisions  # semantic recall across all layers
/memory LLM model configurations   # recall model configs from prior sessions
/memory what did we do on infinite memory  # recall the full infinite memory build
```

## How It Works

`/memory` queries 4 layers in priority order:

| Layer | Source | Trigger |
|-------|--------|---------|
| 1 | `.session_state/checkpoints/` | Session state snapshots (auto-created by session_watcher) |
| 2 | mem0 (ChromaDB + Ollama) | Vector search — `MemoryStore().recall()` |
| 3 | langmem | `SwarmBotMemoryManager.search_memories()` |
| 4 | graphrag | `query_wiki_graph()` — wiki knowledge base |

## Session Lifecycle

```
.start_session_watcher.sh  →  work  →  /memory  →  work  →  .stop_session_watcher.sh
```

- **Start of session**: `./scripts/start_session_watcher.sh` — starts the background daemon
- **During work**: daemon polls `.session_state/` every 30s, saves to mem0+langmem every 2 min
- **Before task**: `/memory <query>` — runs 4-layer recall, result cached to `.session_state/recalled_context.md`
- **End of session**: `./scripts/stop_session_watcher.sh` — final checkpoint + graceful stop

## Memory Files

| File | Purpose |
|------|---------|
| `.session_state/current.json` | Active session state (last LLM call, phase, query) |
| `.session_state/checkpoints/` | Timestamp-named snapshots of full session state |
| `.session_state/recalled_context.md` | Output from last /memory call |
| `.session_state/watcher.pid` | PID of running watcher daemon |
| `.session_state/watcher.log` | Daemon log file |
| `.session_state/llm_events.log` | Append-only log of all LLM calls |

## /memory Implementation

```python
from core.memory.memory_injector import build_memory_context

ctx = build_memory_context(query, user_id="bashara")
# Returns formatted context block + writes .session_state/recalled_context.md
```

## Example Output

```
━━━ RECALLED MEMORY (4-layer search) ━━━
Query: intent routing decisions
Layers with results: 3/4

━━━ LAYER 1: Session Checkpoints ━━━
  • [2026-05-06 14:32] {"phase": "llm_call_complete", "last_query": "intent routing...", ...}

━━━ LAYER 2: mem0 (ChromaDB) ━━━
  1. Implemented 23-intent classifier in intent_router.py with cosine similarity routing
  2. Intent keywords updated with "swarm", "agent" for multi-agent coordination
  3. Default fallback routes to "general" intent with low confidence

━━━ LAYER 3: langmem ━━━
  • Intent routing refactored to use cosine similarity instead of keyword matching

━━━ END RECALL — treat as prior context ━━━
```

## Notes

- Memory is **additive only** — nothing is ever deleted or compacted
- Checkpoints accumulate in `.session_state/checkpoints/` — these are your session history
- The daemon (session_watcher) saves incrementally so you never lose work if OpenCode crashes
- For explicit checkpoint during a session: write to `.session_state/current.json` directly