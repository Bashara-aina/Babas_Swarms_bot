---
title: legion-module-map
type: architecture
status: active
tags: [architecture, modules, core, overview, handlers]
created: 2026-04-13
updated: 2026-04-13
summary: Legion's module architecture spans Telegram handlers (45+ modules), core orchestration (intent routing, LLM client, memory tiers), skill system, proactive behaviors, and multi-agent swarm with 76+ agents across 9 departments.
wikilinks:
  - [[legion-bot]]
  - [[intent-routing]]
  - [[memory-architecture]]
  - [[memory-system-architecture]]
confidence: high
source: implementation
---

# Legion Module Map

## TL;DR
Legion's architecture is organized into Telegram handlers (45+ modules), core orchestration (intent routing, system prompt builder, soul engine, LLM client), multi-tier memory subsystems, skill registry, proactive engines, and multi-agent swarm with 76+ agents. The main.py entry point was refactored from 2678 lines to ~230 lines using focused handler modules.

## Entry Point

### main.py
- **Original size**: 2678 lines (monolithic)
- **Refactored size**: ~230 lines
- **Pattern**: 12 focused handler modules in `handlers/` package
- **Deployment**: systemd service (`swarm-bot.service`)

```python
# main.py structure (simplified)
dp = Dispatcher()
(dp.message | dp.callback_query)  # All updates

# Routers loaded from handlers/
dp.include_router(ai.router)      # /run, /think, /agent
dp.include_router(dev.router)     # /opencode, /cmd
dp.include_router(voice.router)  # Voice processing
dp.include_router(brain.router)  # /memory, /recall
# ... 45+ handlers total
```

## Telegram Handlers

Located in `handlers/` package:

| Handler | Commands | Purpose |
|---------|----------|---------|
| ai.py | /run, /think, /agent | Natural language processing |
| dev.py | /opencode, /cmd | OpenCode integration |
| voice.py | /vcsearch | Voice search |
| brain.py | /memory, /recall, /forget | Memory commands |
| research.py | /research, /paper | Deep research |
| system.py | /start, /help, /status | Bot info |
| admin_handlers.py | /budget, /soul | Admin functions |
| media_tools.py | /imagine, media upload | Image generation |
| computer.py | /screen, /do | Desktop control |
| sessions.py | /legion_sessions | Session management |
| tasks.py | /tasks, /schedule | Task scheduling |
| enterprise/ | /orchestrate, /swarm | Multi-agent swarm |

## Core Modules

### Intent Router (`core/intent_router.py`)
- **Lines**: 509
- **Function**: Classifies incoming messages into 23 intent types
- **Method**: Keyword matching + LLM fallback
- **Output**: Intent + confidence score

```python
class IntentRouter:
    def classify(self, text: str) -> IntentResult:
        # 23 intents: code, research, chat, websearch, etc.
```

### System Prompt Builder (`core/system_prompt_builder.py`)
- **Lines**: 377
- **Layers**: 13 injection layers in correct order
- **Layer Order**: soul → user_profile → working_memory → relevant_memory → wiki → search_results → personality → skill_context → conversation

### Soul Engine (`core/soul_engine.py`)
- **Lines**: 432
- **Function**: Reads SOUL.md at boot, builds soul_context for every prompt
- **Enforcement**: Character consistency via `core/character_enforcer.py`

### LLM Client (`core/llm_client/`)
- **Lines**: ~1809 across module
- **Function**: Unified LLM interface via litellm
- **Providers**: OpenRouter, MiniMax, Cerebras, Groq, Gemini, Ollama
- **Agents**: computer, coding, debug, vision, math, architect, analyst, general

## Memory Architecture

### Multiple Subsystems (being unified)

| Subsystem | Backend | Purpose |
|-----------|---------|---------|
| Core Memory | JSON key-value | High-priority facts |
| Archival Memory | SQLite FTS5 | Unlimited store |
| Recall Memory | SQLite | Full conversation log |
| Episodic Store | Supabase/JSON | Session events |
| User Profile | Supabase/JSON | Persistent user data |
| Temporal Knowledge Graph | aiosqlite bi-temporal | Time-based facts |
| Semantic Cache | In-memory LRU | Query caching |
| mem0 | Vector embeddings | Semantic search |

### Working Memory (`core/working_memory.py`)
- 8 open threads per session
- 5 pending follow-ups
- 300-character focus

## Multi-Agent System

### Agent Registry (`core/agent_registry.py`)
- **Lines**: 798
- **Agents**: 76 defined in `config/departments.yaml`
- **Departments**: 9 (Engineering, Research, Product, Marketing, Design, Operations, Creative, Legal, Strategy)

### Orchestrators (4 competing)

| Orchestrator | File | Purpose |
|--------------|------|---------|
| Task Orchestrator | task_orchestrator.py (492 lines) | Task chaining + debate |
| Legion Swarm | core/legion_swarm.py (322 lines) | 11-agent team |
| Nexus | core/nexus_orchestrator.py | 3-layer routing |
| Jarvis | core/jarvis_orchestrator.py | Context bundling |

## Skill System

### Skill Registry (`core/skills/registry.py`)
- **Lines**: 43
- **Pattern**: In-memory dict with keyword matching
- **Loader**: Filesystem scan of `.md` skill files

### Executable Skills (core/skills/)
- weather, translate, timer, web_search, arxiv, summarize_url, hacker_news, github_pr, github_commits, code_review

### Reference Skills (skills/)
- 28 markdown files injected into system prompts

## Proactive Engine

### Curiosity Engine (`core/proactive/curiosity_engine.py`)
- Check-in messages (pool of 9 variants)
- 4-hour cooldown between check-ins
- Triggered by 8+ hours of silence

### Daily Briefing (`core/proactive/daily_briefing.py`)
- Morning summary at configured time
- Budget status, pending tasks, reminders

## Shell Sandbox (`core/shell/sandbox.py`)
- Blacklist guard for security
- Allowed paths configuration
- Replaces raw subprocess calls

## Module Dependency Graph

```
main.py
├── handlers/
│   ├── ai.py → llm_client → system_prompt_builder → soul_engine
│   ├── dev.py → opencode_bridge → sandbox
│   └── brain.py → memory_manager → memory subsystems
├── core/
│   ├── intent_router.py → handler selection
│   ├── system_prompt_builder.py → 13 layers
│   ├── soul_engine.py → SOUL.md
│   ├── llm_client/ → litellm
│   ├── agent_registry.py → orchestrators
│   └── proactive/
│       ├── curiosity_engine.py
│       └── daily_briefing.py
└── tools/
    ├── browser_agent.py
    ├── deep_research.py
    └── documents.py
```

## Related Pages

- [[legion-bot]] — Project overview
- [[intent-routing]] — Intent classification
- [[memory-architecture]] — Memory concepts
- [[memory-system-architecture]] — Memory implementation
