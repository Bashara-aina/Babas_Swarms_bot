# Architecture Dependency Map

> **Purpose**: Documents the real dependencies and cross-surface bridges between OpenCode, Claude Code, and LegionBot (Legiona).
> **Generated**: 2026-04-21
> **Covers**: `core/`, `lib/legiona/`, `handlers/`, `agents/`, `tools/`

---

## 1. System Overview

The system is a **multi-agent orchestration platform** with three primary surfaces:

| Surface | Entry Point | Protocol |
|---------|-------------|----------|
| **LegionBot (Legiona)** | `main.py` + `lib/legiona/bot/handlers.py` | Telegram bot (aiogram 3.4+) |
| **OpenCode Bridge** | `core/opencode_bridge.py` | Subprocess (`/home/newadmin/.opencode/bin/opencode`) |
| **Claude Code Bridge** | `core/claude_code_bridge.py` | Subprocess (`claude` CLI) |

---

## 2. Cross-Surface Bridge Functions

### 2.1 OpenCode Bridge (`core/opencode_bridge.py`)

| Function | Signature | Purpose |
|----------|-----------|---------|
| `extract_directives` | `(text: str) -> list[tuple[str, str]]` | Parses `@legion:` and `@claude:` directives from text using `DIRECTIVES_RE` regex |
| `build_opencode_prompt` | `(telegram_msg, project, user) -> str` | Constructs full prompt with Legion pipeline instructions (STAGE 0-5) |
| `run_opencode_task` | `(prompt, project_dir, agent, model, timeout) -> str` | Executes opencode CLI subprocess, handles GitNexus context injection, writes session summary, triggers cross-system callbacks |
| `extract_report` | `(opencode_output: str) -> str` | Extracts `━━━━━━━━━━━━━━━━━━━━━━━━━━━` marker block from output |
| `handle_cross_system_callbacks` | `(text, depth, max_depth) -> dict` | Parses directives, spawns `@claude` via `spawn_claude_from_opencode()` or `@legion` via `LegionCallbackBridge` |

### 2.2 Claude Code Bridge (`core/claude_code_bridge.py`)

| Function | Signature | Purpose |
|----------|-----------|---------|
| `run_claude_task` | `(prompt, timeout, model) -> dict[str, Any]` | Runs `claude -p` subprocess, injects GitNexus context, returns `{output, error, latency_ms, success}` |
| `extract_claude_directive` | `(text: str) -> str \| None` | Extracts `@claude:` directive using `DIRECTIVE_RE` regex |
| `spawn_claude_from_opencode` | `(task_result, depth, max_depth) -> dict` | Checks OpenCode output for `@claude` directive, spawns Claude Code if found, respects max depth |

---

## 3. Core Entry Points

### 3.1 Main Telegram Bot (`main.py`)

- **Framework**: aiogram 3.4+
- **Commands**: `/do`, `/run`, `/cmd`, `/screen`, `/think`, `/open`, `/click`, `/type`, `/key`, `/install`, `/upgrade`, `/agent`, `/models`, `/keys`, `/resources`, `/stats`, `/git`, `/threads`, `/scrape`
- **Routing**: Intent detection via keyword + semantic matching → `core/orchestrator.py`

### 3.2 Legiona Bot (`lib/legiona/bot/handlers.py`)

| Command | Handler Function | Description |
|---------|-----------------|-------------|
| `/run` | `cmd_run` | Stream agent response with tools |
| `/think` | `cmd_think` | Direct M3 completion (no tools) |
| `/evolve` | `cmd_evolve` | Self-evolution from session history |
| `/rules` | `cmd_rules` | Show evolved rules |
| `/memory` | `cmd_memory` | Show global memory preview |
| `/cost` | `cmd_cost` | Today's M3 spend |
| `/budget` | `cmd_budget` | Month spend vs projection |
| `/soul` | `cmd_soul` | Display SOUL.md |
| `/debate` | `cmd_debate` | 3-agent debate |
| `/status` | `cmd_status` | System status |
| `/screen` | `cmd_screen` | Screenshot analysis |
| `/vision` | `cmd_vision` | Image analysis with prompt |
| photo | `handle_vision_photo` | Photo vision analysis |

---

## 4. Orchestration Architecture (`core/orchestrator.py`)

### 4.1 Components

| Component | Class | Purpose |
|-----------|-------|---------|
| Task Chains | `execute_chain()`, `TaskStep`, `PendingConfirmation` | Sequential steps with confirmation gates |
| Monitors | `MonitorTask`, `start_monitor()` | Background periodic tasks |
| Swarm Debate | `SwarmDebateOrchestrator` | 4-round multi-agent debate |
| Nexus Routing | `NexusOrchestrator` | 3-layer routing: keyword → semantic → LLM |
| Legion Swarm | `LegionSwarmOrchestrator` | 3-phase parallel swarm with dynamic team |
| **Main Entry** | `LegionOrchestrator` | Canonical entry point; selects single vs swarm |

### 4.2 Nexus Routing Layers

```
Layer 1 (Keyword)  → config/routing_keywords.yaml (O(1) match)
Layer 2 (Semantic)  → sentence-transformers (similarity ≥ 0.55)
Layer 3 (LLM)       → qwen3.5:35b fallback → department default
```

### 4.3 Dynamic Team Selection

`LegionOrchestrator.run()` calls `AgentRegistry.select_team()`:
- If `len(team) <= 1`: single-agent path
- If `len(team) > 1`: `LegionSwarmOrchestrator` (3-phase: propose → debate → synthesize)

---

## 5. Agent Registry (`config/departments.yaml`)

**9 Departments, 76+ Agents**:

| Department | Count | Examples |
|------------|-------|----------|
| `engineering` | 15 | `senior_python_dev`, `frontend_react_dev`, `cuda_optimizer`, `debugging_specialist` |
| `design` | 10 | `ux_designer`, `motion_artist`, `accessibility_auditor` |
| `research` | 12 | `deep_researcher`, `data_scientist`, `web_scraper_coordinator` |
| `marketing` | 12 | `copywriter`, `seo_specialist`, `growth_hacker` |
| `operations` | 7 | `project_manager`, `task_coordinator`, `scheduler` |
| `legal_compliance` | 6 | `contract_reviewer`, `gdpr_expert`, `ip_lawyer` |
| `product` | 5 | `product_manager`, `roadmap_planner`, `feedback_analyzer` |
| `extensions` | varies | `extension` area agents |
| `id` | varies | `[id]` area agents |

Each agent definition includes:
- `primary_model` — primary model reference (from `models.yaml`)
- `fallbacks` — fallback model chain
- `capabilities` — keyword list for routing
- `tools` — tool access (`interpreter`, `vscode`, `playwright`)
- `complexity_tier` — `lightweight`, `midweight`, `heavyweight`

---

## 6. Directory Structure and Dependencies

```
swarm-bot/
├── main.py                          # Telegram bot entry (aiogram)
├── core/
│   ├── opencode_bridge.py           # Telegram → OpenCode bridge
│   ├── claude_code_bridge.py        # Bidirectional Claude ↔ OpenCode
│   ├── orchestrator.py               # LegionOrchestrator, Nexus, Swarm
│   ├── agent_registry.py             # Agent registry, routing, team selection
│   ├── gitnexus_bridge.py            # GitNexus context injection
│   ├── wiki_bridge.py                # Session summary persistence
│   └── legion_callback_bridge.py     # @legion callback handler
├── lib/legiona/
│   ├── bot/
│   │   ├── handlers.py               # /run, /think, /debate, /status, etc.
│   │   └── stream_handler.py         # Telegram streaming
│   ├── minimax_client.py            # M3 API client
│   ├── self_evolve.py               # Rule evolution from sessions
│   ├── tools/
│   │   ├── registry.py               # TOOL_SCHEMAS
│   │   └── mmx_tools.py             # mmx_vision
│   ├── debate.py                     # 3-agent debate
│   └── observability/
│       ├── cost_log.py              # ¥ tracking
│       └── tracer.py                # OTEL trace IDs
├── agents/                          # 76+ specialized agents
├── tools/                            # External integrations
│   ├── screenpipe_tool.py
│   ├── github_tool.py
│   └── ...
├── config/
│   ├── departments.yaml             # Agent registry
│   ├── models.yaml                  # Model configurations
│   └── routing_keywords.yaml        # Nexus Layer 1 keywords
└── docs/
    └── architecture_dependency_map.md  # This file
```

---

## 7. Cross-System Callback Flow

```
Telegram message
    ↓
main.py (command routing)
    ↓
core/orchestrator.py (LegionOrchestrator.run)
    ↓
┌───────────────────────────────────────┐
│ Single agent or Swarm?                │
└───────────────────────────────────────┘
    ↓                           ↓
Single agent                   LegionSwarmOrchestrator
(run_single)                   (Phase 1: propose)
    ↓                           Phase 2: debate
LLM call via                    Phase 3: synthesize
llm_client.py                   ↓
                               run_opencode_task()
                                   ↓
                               ┌───────────────────────┐
                               │ GitNexus context       │
                               │ injection (if enabled) │
                               └───────────────────────┘
                                   ↓
                               opencode CLI subprocess
                                   ↓
                               extract_report()
                                   ↓
                               handle_cross_system_callbacks()
                                   ↓
                    ┌──────────────┴──────────────┐
                    ↓                              ↓
            @claude directive?            @legion directive?
                    ↓                              ↓
            spawn_claude_from_opencode()   LegionCallbackBridge
                    ↓                              ↓
            run_claude_task()             handle_legion_callback()
            (claude CLI)                         ↓
                    ↓                     [Further orchestration]
```

---

## 8. Key Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `LEGION_DEFAULT_MODEL` | `minimax-coding-plan/MiniMax-M3` | Default Ollama model |
| `LEGION_GITNEXUS_PROMPT_ENABLED` | `1` | Enable GitNexus context injection |
| `LEGION_JARVIS_MEMORY` | `1` | Enable memory layer |
| `LEGION_JARVIS_SCREENPIPE` | `1` | Enable screenpipe layer |
| `SCREENPIPE_ENABLED` | `0` | Screenpipe hardware enable |
| `TELEGRAM_BOT_TOKEN` | *(required)* | Telegram bot token |
| `ALLOWED_USER_ID` | `0` | Owner user ID |
| `OPENCODE_DISABLE_AUTOUPDATE` | `true` | Prevent opencode autoupdate |

---

## 9. GitNexus Integration

`core/gitnexus_bridge.py` provides `build_gitnexus_prompt_context()`:
- Called by both `run_opencode_task()` and `run_claude_task()`
- Adds code intelligence context (relevant symbols, execution flows)
- Max chars: 1600-1800 (configurable)
- Controlled by `LEGION_GITNEXUS_PROMPT_ENABLED`

---

## 10. Session Persistence

- **Wiki Bridge** (`core/wiki_bridge.py`): `opencode_write_session_summary()` called after `run_opencode_task()` completes
- **Legiona Memory** (`lib/legiona/self_evolve.py`): Session logs → rule evolution → `RULES_FILE` and `GLOBAL_MEMORY_FILE`
- **Cost Logging** (`lib/legiona/observability/cost_log.py`): Per-session ¥ tracking → `cost_log.jsonl`

---

## 11. Key Files Reference

| File | Key Functions |
|------|---------------|
| `core/opencode_bridge.py` | `extract_directives`, `run_opencode_task`, `extract_report`, `handle_cross_system_callbacks` |
| `core/claude_code_bridge.py` | `run_claude_task`, `extract_claude_directive`, `spawn_claude_from_opencode` |
| `core/orchestrator.py` | `LegionOrchestrator.run`, `NexusOrchestrator.route`, `LegionSwarmOrchestrator.run` |
| `core/agent_registry.py` | `AgentRegistry.select_team`, `get_agent`, `semantic_search` |
| `lib/legiona/bot/handlers.py` | `cmd_run`, `cmd_think`, `cmd_debate`, `cmd_status` |
| `lib/legiona/self_evolve.py` | `evolve`, `load_evolved_rules`, `record_session` |
| `main.py` | All Telegram command handlers, bot initialization |

---

*Last updated: 2026-04-21*
