---
title: legion-module-map
type: architecture
status: active
tags: [architecture, modules, core, overview]
created: 2026-04-13
updated: 2026-04-13
summary: Legion's core modules handle intent routing, memory, LLM calls, skills, and agent orchestration.
wikilinks: [[projects/legion-bot.md], [concepts/intent-routing.md], [concepts/memory-architecture.md]]
confidence: high
source: implementation
---

# Legion Module Map

## TL;DR
Core modules handle routing, memory, LLM orchestration, skills, and multi-agent coordination.

## Module Overview

```
main.py
└── handlers/          # 45+ handlers for commands
    ├── ai.py          # NL message handling
    ├── dev.py         # /opencode integration
    ├── voice.py       # Voice processing
    └── ...
    
core/
├── intent_router.py   # Message classification
├── task_router.py    # Task routing
├── soul_engine.py    # Character enforcement
├── system_prompt_builder.py  # Prompt construction
├── memory_engine.py  # Memory management
├── memory_manager.py # mem0 + ChromaDB
├── session/transcript.py  # SQLite transcripts
├── proactive/
│   └── curiosity_engine.py  # Check-ins
├── shell/sandbox.py  # Sandboxed execution
└── observability.py  # Metrics
```

## Data Flow

```
[Telegram Message]
    → [intent_router.classify()]
    → [appropriate handler]
    → [llm_client.chat()]
    → [Response]
```

## Key Files

| File | Responsibility |
|------|----------------|
| intent_router.py | Message → intent classification |
| llm_client.py | Unified LLM interface |
| memory_manager.py | Memory read/write |
| soul_engine.py | Character consistency |

## Related Pages

- [[projects/legion-bot.md]] — Project overview
- [[concepts/intent-routing.md]] — Routing logic
- [[concepts/memory-architecture.md]] — Memory system
