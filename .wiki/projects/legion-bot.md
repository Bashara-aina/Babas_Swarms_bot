---
title: legion-bot
type: project
status: active
tags: [telegram, bot, ai, multi-agent, swarm]
created: 2026-04-13
updated: 2026-04-13
summary: Legion is Bashara's permanent AI coworker — a Telegram bot with 76+ specialized agents across 9 departments, multi-tier memory, autonomous coding via OpenCode, and full media processing capabilities deployed as a systemd service on Ubuntu with RTX 3060.
wikilinks:
  - [[./entities/opencode]]
  - [[./entities/openrouter]]
  - [[./entities/minimax-m2-7]]
  - [[./concepts/multi-agent-orchestration]]
  - [[legion-module-map]]
  - [[memory-system-architecture]]
confidence: high
source: implementation
---

# Legion Bot

## TL;DR
Legion is Bashara's permanent AI coworker — not a chatbot, not an assistant. It's a production Telegram bot running on Ubuntu with RTX 3060, featuring 76+ specialized agents across 9 departments, multi-tier memory architecture, autonomous OpenCode integration for coding tasks, and full media processing (vision, voice, video). Deployed as a systemd service, it provides persistent context across sessions with personality enforcement and character consistency.

## Project Identity

**Owner**: Bashara (Data Science Master's student, Shibaura Institute of Technology, Tokyo)  
**Machine**: Ubuntu Linux, NVIDIA RTX 3060 12GB VRAM, 64GB RAM, 5TB storage  
**Interface**: Telegram (iPhone) ONLY — no web UI, no other interfaces  
**Framework**: aiogram 3.4+ (fully async)  
**LLM Routing**: litellm 1.57+ via OpenRouter + direct provider fallbacks  
**Deployment**: systemd service (`swarm-bot.service`)

## Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Interface | Telegram (aiogram 3.4+) | User messaging |
| LLM Routing | LiteLLM 1.57+ | Unified model access |
| Primary Model | MiniMax M2.7 | Coding, reasoning, general |
| Fallback Providers | OpenRouter, Cerebras, Groq, Gemini | Redundancy |
| Local Models | Ollama (Gemma4, Llama3.3:70b) | Privacy, offline |
| Memory | ChromaDB + mem0 + SQLite | Multi-tier persistence |
| Code Agent | OpenCode CLI | Autonomous coding |
| Vision | MiniMax multimodal + Ollama | Image understanding |
| Voice | faster-whisper + Kokoro-ONNX | Transcription, TTS |
| Deployment | systemd | Service management |

## Active Commands

### System Commands
- `/start`, `/help`, `/status` — Bot info and health
- `/budget` — Cost tracking and limits
- `/soul` — Soul engine status

### Intelligence Commands
- `/run`, `/think`, `/agent` — AI message processing
- `/research <topic>` — Deep multi-source research
- `/paper <arxiv_url>` — Academic paper analysis
- `/scrape <url>` — Web page content extraction

### Coding Commands
- `/opencode <task>` — Autonomous coding via OpenCode
- `/cmd <shell>` — Sandboxed shell execution
- `/screen` — Screenshot capture and analysis

### Memory Commands
- `/remember <fact>` — Store permanent fact
- `/recall <query>` — Search archival memory
- `/forget <key>` — Remove stored fact
- `/memories`, `/briefing` — Memory status
- `/learn <topic>` — Topic teaching

### Project Commands
- `/legion_sessions` — Session management
- `/vcsearch` — Voice search

## Multi-Agent Architecture

Legion's swarm system comprises:

| Layer | Count | Description |
|-------|-------|-------------|
| Specialist Agents | 84 | 9 departments (see below) |
| Legacy Agents | 23 | Archived, unused |
| Department Leads | 9 | One per active department |
| Debate Personas | 6 | Structured debate participants |
| Total per /swarm | ~99 | Full research swarm |

### Departments (config/departments.yaml)

| Department | Agents | Description |
|-----------|--------|-------------|
| Engineering | 15 | Python, React, FastAPI, systems, security |
| Research | 12 | Academic, market, data analysis |
| Product | 8 | Feature planning, roadmapping |
| Marketing | 12 | Content, social, growth |
| Design | 10 | UI/UX considerations |
| Operations | 7 | Process automation |
| Creative | 8 | Content generation |
| Legal/Compliance | 6 | Contracts, regulatory (BPJS, tax, labor) |
| Vision/Multimodal | 6 | Image, video, voice processing |
| **Legacy** | **23** | **Archived — do not use** |

## Memory System

Five-tier memory architecture with a unified facade:

| Tier | Technology | Purpose |
|------|-----------|---------|
| Working | `core/working_memory.py` | Per-session: 8 open threads, 5 pending follow-ups |
| Episodic | `core/memory/episodic_store.py` (SQLite) | Session events, 30-day retention |
| Semantic | mem0ai (vector) | Semantic search across all conversations |
| Core Facts | `data/user_profile.json` | Persistent key facts about Bashara |
| Graph | TemporalKnowledgeGraph (aiosqlite) | Time-based relationship graph |

**Facade**: `core/legion_memory_facade.py` — RAG compositor combining mem0 + wiki + Screenpipe for tool context.  
**Manager**: `core/memory/memory_manager.py` — unified write/read interface (never write directly to individual stores).

## Directory Structure

```
/home/newadmin/swarm-bot/
├── main.py                     # Bot entry point (1227 lines)
├── agents.py                   # Legacy agent routing (→ core/agent_registry.py)
├── router.py                  # Legacy router shim
├── task_orchestrator.py        # LEGACY — use _archive/ instead
│
├── core/                       # Core orchestration (60+ modules)
│   ├── orchestrator.py         # CONSOLIDATED orchestrator (1324L)
│   ├── agent_registry.py        # 107 agents, 9 departments (897L)
│   ├── intent_router.py         # 23-intent classifier (509L)
│   ├── autonomous_router.py    # Autonomous mode routing (585L)
│   ├── task_router.py          # Task-level routing (446L)
│   ├── system_prompt_builder.py # 8-layer prompt assembly (696L)
│   ├── soul_engine.py          # SOUL.md → context (452L)
│   ├── debate_engine.py        # Belief-based debate (181L)
│   ├── llm_client/             # Unified LiteLLM client
│   ├── memory/                 # MemoryManager + subsystems
│   ├── personality/             # Personality + emotion engine
│   ├── proactive/               # Curiosity engine + daily briefing
│   ├── daily_harvester/        # Autonomous research (11 modules)
│   └── ...
│
├── handlers/                   # 40 Telegram handler modules
├── tools/                     # 70+ external integrations
├── swarms_bot/                # Enterprise orchestration layer
│   ├── routing/               # budget_guard, budget_manager, cost_router
│   └── orchestrator/          # DAG executor, chief of staff, human-in-loop
├── agents/                    # Standalone agent scripts
├── config/                    # departments.yaml (107 agents), models.yaml, routing_keywords.yaml
├── _archive/                  # Archived legacy orchestrators
├── data/                      # Persistent storage (user_profile.json)
├── SOUL.md                    # Legion's living identity
└── wiki/                      # Obsidian knowledge base (142 articles)
```

## Related Pages

- [[legion-module-map]] — Core module organization (updated 2026-04-13)
- [[memory-system-architecture]] — Memory tiers and facade
- [[./concepts/multi-agent-orchestration]] — Agent coordination and swarm patterns
- [[intent-routing]] — 23-intent classification system
- [[./entities/opencode]] — OpenCode CLI integration
- [[./entities/openrouter]] — LLM routing provider
- [[./entities/minimax-m2-7]] — Primary coding/reasoning model
- [[entities/litellm]] — LiteLLM unified client
- [[entities/obsidian]] — Wiki platform (Karpathy KB pattern)
- [[people/andrej-karpathy]] — Pattern inspiration for knowledge base
