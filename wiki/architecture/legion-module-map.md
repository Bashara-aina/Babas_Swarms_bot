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
- **Lines**: 696
- **Layer Order** (highest to lowest priority, soul is ALWAYS first):
  1. `soul` — ALWAYS included, never compressed
  2. `user_profile` — ALWAYS included (top 5 facts only)
  3. `working_memory` — Last 5 exchanges, compressed if tight
  4. `relevant_memory` — Top-3 semantic results, dropped if very tight
  5. `wiki_context` — Only if query directly relevant to wiki content
  6. `search_results` — Only if search was triggered
  7. `personality` — Compressed to key traits if context tight
  8. `skill_context` — Only if skill was triggered

Async cross-cutting layers (wiki, Screenpipe, JST calendar, MCP calendar, RAG, skills, KG) are gathered in parallel by `core.unified_prompt_context` and appended within `llm_client.chat`.

### Soul Engine (`core/soul_engine.py`)
- **Lines**: 452
- **Function**: Reads SOUL.md at boot, builds soul_context for every prompt
- **Enforcement**: Character consistency via `core/character_enforcer.py`
- **Identity contract**: SOUL.md is Legion's living identity — updated when Legion learns new facts about Bashara or forms new opinions

### LLM Client (`core/llm_client/`)
- **Function**: Unified LLM interface via litellm
- **Providers**: OpenRouter, MiniMax M2.7, Cerebras Qwen3-235B, Groq (Llama3.3-70B, Kimi-K2), Gemini, Ollama (Gemma4, Llama3.3-70B for local/vision)
- **Primary models**: MiniMax M2.7 (coding/reasoning), Cerebras Qwen3-235B-A22B (fast long-context)
- **Fallback chains**: Per-agent configured in `config/models.yaml` and `config/departments.yaml`
- **Key functions**: `chat()`, `agent_loop()`, `get_fallback_chain()`

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
- **Lines**: 897
- **Agents**: 84 active + 23 legacy = 107 total defined in `config/departments.yaml`
- **Departments**: 9 active (Engineering 15, Design 10, Research 12, Marketing 12, Operations 7, Legal Compliance 6, Product 8, Creative 8, Vision/Multimodal 6)
- **Legacy**: 23 archived agents in `legacy/` department

### Orchestrator System — CONSOLIDATED

The 4 legacy orchestrators were merged into a single unified entry point:

| Legacy File | Status | Current Location |
|------------|--------|-----------------|
| `task_orchestrator.py` (491L) | Archived | `_archive/task_orchestrator.py` |
| `core/legion_swarm.py` (321L) | Archived | `_archive/core/legion_swarm.py` |
| `core/nexus_orchestrator.py` (385L) | Shim (re-exports) | `_archive/core/nexus_orchestrator.py` |
| `core/jarvis_orchestrator.py` (207L) | Archived | `_archive/core/jarvis_orchestrator.py` |

**Current consolidated orchestrator:** `core/orchestrator.py` (1324 lines)

Contains 4 orchestrator classes:
- `SwarmDebateOrchestrator` (line 277) — task chaining + debate
- `NexusOrchestrator` (line 693) — 3-layer routing (keyword → semantic → LLM)
- `LegionSwarmOrchestrator` (line 972) — 11-agent parallel swarm team
- `LegionOrchestrator` (line 1192) — **primary entry point** for `LegionOrchestrator.run(task, user_id)`

Plus `run_legion_swarm()` (line 1304) — standalone swarm runner.

### Structured Orchestration Layer (`swarms_bot/`)

Separate from `agents/` (root-level agent scripts). `swarms_bot/` is the enterprise-grade orchestration package:

```
swarms_bot/
├── routing/
│   ├── budget_guard.py       # Budget enforcement for LLM calls
│   ├── budget_manager.py     # Daily/monthly spend tracking
│   └── cost_router.py       # Cost-optimized model selection
├── orchestrator/
│   ├── agent_base.py         # Base class for swarms agents
│   ├── agent_messaging.py     # Inter-agent messaging
│   ├── chief_of_staff.py     # Top-level coordination
│   ├── dag_executor.py       # DAG-based task execution
│   ├── dag_planner.py        # DAG planning from natural language
│   ├── human_in_loop.py      # Approval gates for destructive actions
│   ├── model_router.py       # Per-task model routing
│   ├── nested_agents.py      # Sub-agent creation
│   ├── orchestration_runner.py# Main orchestration loop
│   └── registry.py           # Agent registry for orchestration layer
└── observability/            # Metrics and monitoring
```

### External Integrations

#### Everything Claude Code (`ext/everything-claude-code/`)
- **Source**: https://github.com/affaan-m/everything-claude-code (MIT, 140K+ stars)
- **Integration**: `ext/everything_claude_code/__init__.py` Python facade
- **Agents**: 13 specialized coding agents (planner, code-reviewer, security-reviewer, tdd-guide, build-error-resolver, refactor-cleaner, e2e-runner, loop-operator, performance-optimizer, harness-optimizer, architect, silent-failure-hunter, type-design-analyzer)
- **Skills**: 6 high-value skills (agentic-engineering, autonomous-loops, continuous-learning, tdd-workflow, security-review, security-scan)
- **Hooks**: 17 hooks reference for quality enforcement (pre-commit lint, tmux reminder, secrets detection)
- **Rules**: Language-specific linting rules (python/, typescript/, common/)
- **Wiki ADR**: [[decisions/adr-2026-04-13-ecc-integration]]

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

## Daily Harvester (`core/daily_harvester/`)

Autonomous research and synthesis system — runs daily to keep Legion's knowledge current:

```
core/daily_harvester/
├── swarm_debate.py       # Daily debate on sourced topics (LLM calls guarded by budget)
├── harvest_pipeline.py   # Multi-source content gathering pipeline
├── morning_report.py     # Formatted morning digest
├── scheduler.py          # Cron scheduling logic
├── scorer.py             # Topic relevance scoring
├── source_strategy.py    # Source selection logic
├── topic_budget.py       # Daily topic allocation
├── topic_evolution.py    # Topic depth evolution
├── types.py             # Typed data classes
├── wiki_indexer.py      # Wiki content indexing
└── wiki_storage.py     # Wiki write-back logic
```

Primary entry: `daily_harvester.py` (root) → imports `core/daily_harvester/`

## Module Dependency Graph

```
main.py
├── handlers/                           # 40 handler modules
│   ├── ai.py → llm_client → system_prompt_builder → soul_engine
│   ├── brain.py → memory_manager → memory subsystems
│   └── orchestrate.py → core/orchestrator.py (LegionOrchestrator)
├── core/
│   ├── orchestrator.py                 # CONSOLIDATED (1324L) — 4 legacy merged
│   ├── intent_router.py                # 23-intent classifier (509L)
│   ├── autonomous_router.py            # Autonomous mode router (585L)
│   ├── task_router.py                  # Task-level routing (446L)
│   ├── system_prompt_builder.py       # 8 priority layers (696L)
│   ├── soul_engine.py                  # SOUL.md → context (452L)
│   ├── debate_engine.py                # Belief-based debate (181L)
│   ├── agent_registry.py              # 107 agents, 9 departments (897L)
│   ├── llm_client/                    # LiteLLM unified client
│   ├── memory/                        # MemoryManager + subsystems
│   ├── personality/                   # Personality + emotion engine
│   ├── proactive/                      # Curiosity + daily briefing
│   ├── daily_harvester/               # Autonomous research (11 modules)
│   └── ...
├── swarms_bot/                        # Enterprise orchestration layer
│   ├── routing/budget_manager.py       # Cost tracking
│   └── orchestrator/                  # DAG-based execution
└── tools/                             # 70+ external integrations
```

## Related Pages

- [[legion-bot]] — Project overview
- [[intent-routing]] — Intent classification
- [[memory-architecture]] — Memory concepts
- [[memory-system-architecture]] — Memory implementation
