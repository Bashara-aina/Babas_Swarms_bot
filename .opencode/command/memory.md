---
allowed-tools: Read,Bash,Grep,Glob,Task
argument-hint: [query]
description: "Recall prior session context from 4-layer memory. Auto-starts session_watcher if not running. Without args: show recent context."
---

# /memory — Infinite Memory Recall

Fully automatic — starts the session_watcher daemon if needed, then queries all 4 layers.

## Usage
```
/memory                          # show recent context
/memory intent routing decisions  # semantic recall across all layers
/memory LLM model configurations   # recall model configs from prior sessions
/memory what did we do on infinite memory  # recall the full infinite memory build
```

## How It Works

`/memory` queries 4 layers in priority order, auto-starting the watcher if needed:

| Layer | Source | Trigger |
|-------|--------|---------|
| 1 | `.session_state/checkpoints/` | Session state snapshots (auto-created by session_watcher) |
| 2 | mem0 (ChromaDB + Ollama) | Vector search — `MemoryStore().recall()` |
| 3 | langmem | `SwarmBotMemoryManager.search_memories()` |
| 4 | graphrag | `query_wiki_graph()` — wiki knowledge base |

## Session Lifecycle (fully automatic now)

```
.opencode-start.sh          →  work  →  /memory  →  work  →  opencode-stop.sh
```

Or just:
```bash
# Start everything (daemon + recall) — one command
./scripts/opencode-start.sh

# End session + final save — one command
./scripts/opencode-stop.sh
```

## What opencode-start.sh does

1. **Starts session_watcher daemon** (if not already running)
2. **Queries 4-layer memory** for the given query
3. **Writes recalled context** to `.session_state/recalled_context.md`
4. **Echoes the context** so you paste it as OpenCode's first message

## What opencode-stop.sh does

1. **Graceful stop** of session_watcher (final checkpoint + save to mem0/langmem)
2. **Session summary** (checkpoints created, files changed, LLM calls logged)
3. **Confirmation** that memory is durable

## Manual state updates (optional)

During work, you can enrich checkpoints by writing state:
```python
from core.memory.session_watcher import write_state
write_state({
    "current_task": "Building Rumahlabuh search page",
    "files_changed": ["app/search/page.tsx"],
    "decisions": ["Server-side pagination over client-side"],
    "progress_notes": ["API done, UI 60% complete"],
    "status": "in_progress"
})
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

## Key Files

| File | Purpose |
|------|---------|
| `.session_state/current.json` | Active session state (last LLM call, phase, query) |
| `.session_state/checkpoints/` | Timestamp-named snapshots of full session state |
| `.session_state/recalled_context.md` | Output from last /memory call |
| `.session_state/watcher.pid` | PID of running watcher daemon |
| `.session_state/watcher.log` | Daemon log file |
| `.session_state/llm_events.log` | Append-only log of all LLM calls |

## Notes

- Memory is **additive only** — nothing is ever deleted or compacted
- Checkpoints accumulate in `.session_state/checkpoints/` — these are your session history
- The daemon (session_watcher) saves incrementally so you never lose work if OpenCode crashes
- For explicit checkpoint during a session: write to `.session_state/current.json` directly