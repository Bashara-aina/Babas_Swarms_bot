# Legion v4 — Architecture

## Component Flow

```
Telegram User
     │
     ▼
  main.py  (entry point, ~900 lines)
     │  initialises bot/dp, calls register_all_routers()
     │  on_startup: skills registry, schedulers, heartbeat daemon,
     │             swarms_bot enterprise layer (via core/swarm.py),
     │             webhook server (core/webhooks/), MCP manager (core/mcp/)
     ▼
  handlers/  (aiogram Router per domain)
  ├── computer.py   /do /screen /click /type /key /cmd /install /upgrade
  ├── system.py     /start /stats /keys /models /git /maintenance /gpu
  ├── ai.py         /run /think (delegated to core/agent.py)
  │                  /agent /swarm /owl /predict /code_exec /ag2 /swarm_viz
  │                  /multi_execute /orchestrate /multi_plan /loop* + NL catch-all
  ├── research.py   /scrape /research /paper /ask_paper
  ├── brain.py      /remember /recall /memories /briefing
  ├── sessions.py   /save /resume /sessions /audit
  ├── tasks.py      /monitor /schedule /tasks /cancel
  ├── dev.py        /scaffold /build /vuln_scan /review
  ├── pm.py         /task_from /tasks_due /post /email
  ├── enterprise.py /budget /routing_stats /security_stats /audit_summary
  └── shared.py     auth, send_chunked, _keep_typing, _run_agent_loop
       │
       ▼
  llm_client.py
  ├── chat()         single-turn Q&A, cloud-first fallback chain
  ├── agent_loop()   multi-turn agentic loop with tool use (300s timeout)
  ├── analyze_screenshot()  vision: Ollama → Groq fallback
  └── chunk_output() Telegram-safe message splitting
       │
       ├──► router.py → agents.py
       │    ├── AGENT_MODELS     model per agent key
       │    ├── FALLBACK_CHAIN   provider priority order
       │    ├── detect_agent()   keyword-based routing
       │    └── get_fallback_chain()
       │
       └──► computer_agent.py
            ├── TOOL_DEFINITIONS  JSON schema for LLM tool calling
            ├── execute_tool()    async dispatcher
            ├── run_shell()       async subprocess
            ├── take_screenshot() scrot / Pillow
            ├── mouse_click/type/key_press
            └── open_app/open_url/read_file/write_file...
```

## Core Layer (core/)

### Agent & Swarm
- `core/agent.py` — `/run` and `/think` command implementations extracted from handlers/ai.py
- `core/swarm.py` — `init_swarm_layer()`: swarms_bot enterprise layer initialization

### Skills Registry
- `core/skills/` — 28 skills across 6 categories (system, media, personal, productivity, memory, github, research, web)
- `core/skills/registry.py` — Skill loading, keyword routing, auto-fire via intent_router
- Skills auto-fire on keyword match during natural language intent classification

### Memory
- `core/memory/` — 3-tier memory: working, episodic, semantic, user_profile, temporal_graph, consolidator
- `core/session/transcript.py` — SQLite-backed session transcript store (U1)

### Proactive Intelligence
- `core/proactive/` — Proactive scheduler, curiosity engine, proactive initiator
- `core/heartbeat/daemon.py` — Heartbeat daemon wired in main.py on_startup

### Webhooks (Phase 3)
- `core/webhooks/server.py` — aiohttp webhook server on port 8743, GitHub HMAC-SHA256 validation
- `core/webhooks/handlers/github.py` — PR merged → Telegram notification
- `core/webhooks/handlers/system.py` — GPU temp / disk usage threshold alerts

### MCP — Model Context Protocol (Phase 3)
- `core/mcp/client.py` — Async stdio subprocess MCP client
- `core/mcp/manager.py` — Start/stop all enabled MCP servers
- `core/mcp/servers/` — Brave Search, GitHub, Filesystem, Obsidian, Supabase, Browser configs

### Shell & Sandbox
- `core/shell/sandbox.py` — Safe shell command execution sandbox

### Additional Core Modules
- `core/intent_router.py` — Intent classification + skills registry auto-fire
- `core/soul_engine.py` — Personality and emotional state (v2, FOCEDED/CURIOUS/TIRED/PLAYFUL)
- `core/character/` — Character definitions, enforcer, voice
- `core/reflection/reflection_engine.py` — Multi-agent reflection
- `core/debate_engine.py` — Multi-agent debate resolution
- `core/swarm_topologies.py` — Multi-agent team execution topologies
- `core/self_upgrade.py` — GitHub trending analysis, hot-reload, rollback
- `core/cognition_pipeline.py` — Thinking/reasoning pipeline
- `core/observability/` — Metrics, logging, health checks

## Enterprise Layer (swarms_bot/)
- `ChiefOfStaff` — validate → classify → budget check → route → execute → track
- `CostAwareRouter` — complexity classification, cascade pattern
- `BudgetManager` — per-user daily/monthly spend limits
- `SecurityGuard` — prompt injection, PII redaction, credential blocking
- `AuditLogger` — SQLite-backed compliance log
- `CostMetricsCollector` — token + cost dashboard
- `SessionManager` — save/resume sessions with SQLite persistence

## Tools Layer (tools/)
- `web_browser.py` — Playwright scraping + deep research
- `persistence.py` — cache_get/set, instinct context
- `skill_loader.py` — per-agent skill injection
- `orchestrator.py` — decompose_task, execute_parallel, synthesize
- `github_intel.py` — GitHub trending intelligence engine
- `proactive_initiator.py` — Legion talks first initiator
- `deep_think.py` — Layered extended thinking with adversarial critique
- `screenpipe_bridge.py` — Screenpipe proactive monitor

## LLM Provider Priority

| Priority | Provider | Models | Strength |
|---|---|---|---|
| 1 | ZAI / GLM-4 | glm-4 | math, debug |
| 2 | Groq | llama-3.3-70b, llama-4-scout | speed, function calling |
| 3 | Cerebras | qwen-3-235b-a22b | throughput 1500 tok/s |
| 4 | Gemini | gemini-2.0-flash | 1M context |
| 5 | OpenRouter | free tier models | fallback |
| Local | Ollama | gemma3:12b | vision only (private) |

## Key Design Decisions

- **Single source of truth**: `agents.py` owns all model config; `router.py` only re-exports
- **Cloud-only for text**: Ollama is only used for vision tasks to keep latency low
- **Fail-open startup**: every enterprise module wrapped in `try/except` so partial failures never crash the bot
- **Context compaction**: messages >12 turns are summarized into a single system message to reduce token cost
- **300s hard cap**: `asyncio.wait_for()` prevents runaway agent loops from blocking the bot
- **Skills auto-fire**: Skills registered in `core/skills/registry.py` are automatically matched by keyword in intent_router
- **Webhook server**: Runs on port 8743, receives GitHub + system alert webhooks, non-fatal if port unavailable
- **MCP Manager**: Starts enabled MCP servers (Brave, GitHub, Filesystem, Obsidian, Supabase, Browser) on startup
