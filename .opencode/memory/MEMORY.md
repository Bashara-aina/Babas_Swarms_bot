---
name: swarm-bot
description: "OpenCode persistent memory index. Project overview, critical files, patterns, and conventions."
---

# OpenCode Memory — swarm-bot

Project context index. Updated after each session. Human + AI readable.

## Machine & Project
- **Machine**: RTX 3060, 32GB RAM, Ubuntu 22.04
- **Owner**: Bashara
- **Repo**: swarm-bot (Python Telegram bot)
- **Canonical paths**: `/home/newadmin/swarm-bot/`, `cekwajar.id/` (symlinked)

## Project Overview
- **Type**: Python Telegram bot with multi-agent orchestration
- **Framework**: aiogram 3.x (async Telegram), litellm 1.57+ (LLM routing)
- **Memory**: mem0ai (episodic + semantic), NOT OpenCode memory
- **Deployment**: systemd on Ubuntu (not Docker)
- **Parse mode**: HTML with `html.escape()`

## Directory Structure
```
swarm-bot/
├── handlers/         # 45+ aiogram router files (one per feature)
├── core/             # Agent orchestration, intent routing, memory, soul engine
├── swarms_bot/       # Enterprise orchestration layer
├── agents/           # 76+ specialized agents across 9 departments
├── tools/            # Browser, scraper, GitHub, n8n integrations
├── config/           # YAML configs for models, departments, routing
├── tests/            # pytest-asyncio test suite
├── .wiki/            # Knowledge base (architecture, decisions, logs)
├── llm_client.py     # LLM calls via litellm — NEVER call litellm directly
└── main.py           # Bot startup
```

## Critical Files
| File | Purpose | Risk if broken |
|------|---------|----------------|
| llm_client.py | All LLM calls, fallback chain | ALL AI features |
| core/intent_router.py | Message → agent routing | ALL message handling |
| core/memory/memory_manager.py | mem0ai memory (separate from OpenCode) | Memory recall |
| agents.py | Agent registry, TASK_KEYWORDS | Agent dispatch |
| handlers/loader.py | Handler registration | Bot handlers |
| core/system_prompt_builder.py | Agent prompt construction | Agent quality |

## Swarm-Bot-Specific Conventions

### NEVER
- Call litellm directly — use llm_client.py
- Use `time.sleep()` — use `asyncio.sleep()`
- Hardcode secrets — use `os.getenv()`
- Use bare `except:` — catch specific exceptions
- Use `.format()` — use f-strings

### ALWAYS
- `async def` + `await` for all I/O
- Type hints on all functions
- html.escape() for Telegram HTML output
- Docstrings on public methods
- Run tests: `pytest tests/ -x --asyncio-mode=auto -q`

## Two Memory Systems (DO NOT CONFUSE)

### 1. Swarm-Bot Memory (mem0ai)
- Location: `core/memory/memory_manager.py`
- Type: episodic + semantic memory for the bot's agents
- API: `memory_manager.save()`, `memory_manager.recall()`, `memory_manager.search()`
- Separate from OpenCode's .opencode/memory/

### 2. OpenCode Memory (this file)
- Location: `.opencode/memory/MEMORY.md`
- Type: session index, project context
- Updated by OpenCode after each session

## cekwajar.id Reference
- Canonical: `/media/newadmin/dataset/home_newadmin/cekwajar.id/` (OLD HARD DISK — destroyed; no longer exists)
- Symlinked at: `swarm-bot/cekwajar.id`
- Research data, OCR pipeline, ML models

## LLM Fallback Chain
groq → cerebras → claude-3-5-sonnet

## Agent Departments
| Department | Count | Examples |
|-----------|-------|----------|
| coding | ~20 | coder, reviewer, tester |
| research | ~15 | researcher, analyst, data |
| creative | ~10 | writer, designer |
| ops | ~8 | deployer, monitor |
