---
title: legion-bot
type: project
status: active
tags: [telegram, bot, ai, multi-agent, swarm]
created: 2026-04-13
updated: 2026-04-13
summary: Legion is Bashara's permanent AI coworker — a Telegram bot with 76+ specialized agents across 9 departments, multi-tier memory, autonomous coding via OpenCode, and full media processing capabilities deployed as a systemd service on Ubuntu with RTX 3060.
wikilinks:
  - [[opencode]]
  - [[openrouter]]
  - [[minimax-m2-7]]
  - [[multi-agent-orchestration]]
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
| Specialist Agents | 72 | 9 departments × 8 agents |
| Department Leads | 9 | One per department |
| Debate Personas | 6 | Structured debate participants |
| Total per /swarm | ~87 | Full research swarm |
| LLM Calls | ~96 | 4-round debate mode |

### Departments
1. Engineering — Software development
2. Research — Academic and market research
3. Product — Feature planning and roadmapping
4. Marketing — Content and growth
5. Design — UI/UX considerations
6. Operations — Process automation
7. Creative — Content generation
8. Legal — Compliance and contracts
9. Strategy — Long-term planning

## Memory System

Three-tier memory architecture:

1. **Core Memory** — High-priority facts always in prompt
2. **Archival Memory** — Unlimited SQLite FTS5 store
3. **Recall Memory** — Full conversation history

Plus:
- Temporal Knowledge Graph (graphiti)
- User Profile (memobase)
- Reflection Engine (Reflexion)

## Directory Structure

```
/home/newadmin/swarm-bot/
├── main.py                    # Bot entry point (refactored to ~230 lines)
├── core/                      # Core orchestration
│   ├── intent_router.py       # Message classification (509 lines)
│   ├── system_prompt_builder.py  # 13-layer prompt injection
│   ├── soul_engine.py         # Character enforcement (432 lines)
│   ├── llm_client/            # LLM routing (1809 lines)
│   ├── memory/                # Memory subsystems
│   ├── skills/                # Skill registry
│   └── proactive/            # Curiosity engine, check-ins
├── handlers/                  # 45+ handler modules
├── agents/                    # 76+ agent definitions
├── tools/                     # External integrations
├── config/                    # YAML configurations
└── data/                      # Persistent storage
```

## Related Pages

- [[legion-module-map]] — Core module organization
- [[memory-system-architecture]] — Memory tiers
- [[multi-agent-orchestration]] — Agent coordination
- [[opencode]] — OpenCode integration
- [[openrouter]] — LLM routing provider
- [[minimax-m2-7]] — Primary model
- [[architecture/audit-2026-04-11-fixes]] — 2026-04-11 critical fixes applied
- [[architecture/code_reviews]] — Legion's code review patterns
- [[architecture/opencode-integration-2026-04-11]] — OpenCode integration log
- [[architecture/refactoring-2026-04-11]] — April refactoring changes
- [[architecture/orchestrator-comparison]] — Four competing orchestrators analysis
- [[architecture/memory-gaps-analysis]] — Memory system gaps identified
- [[entities/markitdown]] — Document conversion pipeline
- [[entities/obsidian]] — Wiki platform configuration
- [[people/andrej-karpathy]] — Pattern inspiration for knowledge base
- [[logs/reviewer-approved-2026-04-13-wiki-restructure]] — Latest wiki restructure log
