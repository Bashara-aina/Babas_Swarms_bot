# Legion Bot — Runtime Entry Points

> Every way to start, trigger, or invoke Legion at runtime.

---

## Primary Entry Point: main.py

**File:** `main.py`

```bash
python main.py                    # Direct execution
make run                          # Same via Makefile
```

`main.py` is a standard aiogram 3 bot. The execution flow:

```
if __name__ == "__main__":
    asyncio.run(main())

main()
  → on_startup(bot)               # Full initialization
  → dp.start_polling(bot, ...)    # Begin receiving Telegram updates
```

### Key exports from main.py

| Symbol | Type | Used by |
|--------|------|---------|
| `bot` | `aiogram.Bot` | Handlers, tools, schedulers |
| `dp` | `aiogram.Dispatcher` | Router registration |
| `BOT_TOKEN` | `str` | Internally by aiogram |
| `ALLOWED_USER_ID` | `int` | `handlers.shared`, all handlers |
| `_shared` | `handlers.shared` module | Cross-module state |
| `_harvester_scheduler` | `DailyHarvesterScheduler` | Internal |
| `_wiki_scheduler` | `WikiQualityScheduler` | Internal |
| `run_legion_boot_health(bot)` | `async fn` | Health reporting |
| `print_legion_boot_report(results)` | `fn` | Console output |
| `print_health_report()` | `fn` | `/stats` command |

### Watchdog wrapper (zero-downtime)

```bash
scripts/start_with_watchdog.sh    # Starts bot under watchdog
```

This runs `core/watchdog.py` which spawns `main.py` as a child process
and restarts it on crash or upgrade signal. Telegram gap < 3 seconds.

---

## Handler Entry Points

**Location:** `handlers/`

All handlers are aiogram Routers. They are registered in `handlers/__init__.py`
in a specific order (more specific → general, `ai.router` LAST as NL catch-all).

### Complete router list (38 routers)

| Router | File | Primary Commands |
|--------|------|-----------------|
| `legiona_tools.router` | `handlers/legiona_tools.py` | `/logs /ps /kill /sys /ls /find /grep /read /write /disk /window /screen /clipboard /type /key /service /tree` |
| `computer.router` | `handlers/computer.py` | `/do /screen /click /type /key /cmd /install` |
| `plandex_commands.router` | `handlers/plandex_commands.py` | `/code /diff /apply /abort` |
| `swe_commands.router` | `handlers/swe_commands.py` | `/fix /fix_dry` |
| `communications.router` | `handlers/communications.py` | `/emails /inbox /calendar` |
| `runbook_handler.router` | `handlers/runbook_handler.py` | `/runbook` |
| `business_handler.router` | `handlers/business_handler.py` | `/db /site_health /bookings /db_schema` |
| `github_intel_handler.router` | `handlers/github_intel_handler.py` | `/github_intel /eval_repo /upgrade_from` |
| `whatsapp_handler.router` | `handlers/whatsapp_handler.py` | `/wa /wa_reply /wa_qr /wa_status` |
| `system.router` | `handlers/system.py` | `/start /stats /keys /models /git /maintenance /gpu` |
| `hermes.router` | `handlers/hermes.py` | `/hermes /hermes-search /hermes-delegate /hermes-tools /hermes-smoke` |
| `research.router` | `handlers/research.py` | `/scrape /research /paper /ask_paper /workernet_papers` |
| `draft.router` | `handlers/draft.py` | `/draft` |
| `memory_commands.router` | `handlers/memory_commands.py` | `/memory /remember /recall /emotion /opinions /forget /profile /teach` |
| `wiki_handler.router` | `handlers/wiki_handler.py` | `/wiki /wiki_ingest /wiki_lint` |
| `brain.router` | `handlers/brain.py` | `/memories /briefing /learn /instincts` |
| `session_handler.router` | `handlers/session_handler.py` | `/task /task_done /task_sessions /semantic_set /semantic_get` |
| `sessions.router` | `handlers/sessions.py` | `/save /resume /sessions /audit` |
| `tasks.router` | `handlers/tasks.py` | `/monitor /schedule /tasks /cancel` |
| `threads_mode.router` | `handlers/threads_mode.py` | `/threads_mode on\|off\|toggle\|status` |
| `dev.router` | `handlers/dev.py` | `/scaffold /build /vuln_scan /review` |
| `pm.router` | `handlers/pm.py` | `/task_from /tasks_due /post /email` |
| `enterprise.router` | `handlers/enterprise.py` | `/budget /routing_stats /security_stats /audit_summary` |
| `artifact.router` | `handlers/artifact.py` | `/preview` |
| `upgrade.router` | `handlers/upgrade.py` | `/upgrade /upgrade_status /upgrade_history` |
| `debate_handlers.router` | `handlers/debate_handlers.py` | `/debate /opinion` |
| `overnight_handler.router` | `handlers/overnight_handler.py` | `/overnight /dashboard /overnight_*` |
| `voice.router` | `handlers/voice.py` | `/voice_on /voice_off /voice_status /voice_toggle` + F.voice |
| `media_tools.router` | `handlers/media_tools.py` | `/imagine /search /speak` + F.photo |
| `inline.router` | `handlers/inline.py` | inline_query |
| `skills.router` | `handlers/skills.py` | `/skills /skill /skill_reload` |
| `gstack.router` | `handlers/gstack.py` | `/review /ship /officehours /codex /investigate /qa /careful /planreview` |
| `persona_handler.router` | `handlers/persona_handler.py` | `/persona /mood /persona_reset /persona_note` |
| `ecc_compat.router` | `handlers/ecc_compat.py` | `/harness_audit /model_route /quality_gate /verify /plan /checkpoint` |
| `e2e.router` | `handlers/e2e.py` | `/e2etest /e2eplan /dbquery /dbhealth /dbtables` |
| `orchestrate.router` | `handlers/orchestrate.py` | `/orchestrate /orchestrate_cancel` |
| `legion_extras.router` | `handlers/legion_extras.py` | `/simulate /screenpipe_status /mcp_status /voice_room /websearch /quickscrape` |
| `wiki_router` | `handlers/wiki/__init__.py` | `/wiki_audit /wiki_flush /wiki_restore /wiki_scan /wiki_stats` |
| `harvest_review.router` | `handlers/harvest_review.py` | `/harvest_review` |
| `admin_handlers.router` | `handlers/admin_handlers.py` | `/budget /soul` (owner-only) |
| `ai.router` | `handlers/ai.py` | `/run /think /agent /swarm` + NL catch-all (LAST) |

### Handler registration

```python
# handlers/__init__.py
def register_all_routers(dp: Dispatcher) -> None:
    for r in _ROUTER_ORDER:
        dp.include_router(r)
```

Called from `main.py`:
```python
from handlers import register_all_routers
register_all_routers(dp)
```

---

## Agent Entry Points

**Location:** `agents/`, `core/agent_registry.py`

### Agent Registry (76 agents, 9 departments)

Config: `config/departments.yaml`

```python
# agents.py (backwards-compat shim)
from core.agent_registry import (
    AGENT_REGISTRY,      # dict of all agents
    TASK_KEYWORDS,       # keyword → agent mapping
    DEFAULT_AGENT,
    FALLBACK_CHAIN,
    detect_agent(task),
    get_model(agent_name),
)
```

### Key agent entry points

| Function | File | Purpose |
|----------|------|---------|
| `detect_agent(task)` | `core/agent_registry.py` | Auto-select agent from NL task |
| `get_model(agent_name)` | `core/agent_registry.py` | Get LLM model for agent |
| `get_fallback_chain(agent_name)` | `core/agent_registry.py` | Get fallback models |
| `list_agents()` | `core/agent_registry.py` | List all 76 agents |
| `build_system_prompt(role)` | `agents.py` | Build agent system prompt with personality |

### 9 Departments

Agents are organized into departments. See `config/departments.yaml` for full list.

### Agent execution flow

```
User message (NL)
  → ai.router (ai.py)
    → detect_agent(task)        # pick agent from TASK_KEYWORDS
      → get_model(agent_name)  # resolve LLM model
        → llm_client.py         # make LLM call
          → response
```

---

## Tool Entry Points

**Location:** `tools/`

Tools are invoked by handlers or agents. Not all tools are accessible via
Telegram commands — some are called internally by other tools or agents.

### Tools with Telegram command wrappers

| Tool | Handler | Telegram Commands |
|------|---------|------------------|
| `plandex_agent.py` | `plandex_commands.py` | `/code /diff /apply /abort` |
| `swe_agent_bridge.py` | `swe_commands.py` | `/fix /fix_dry` |
| `scheduler.py` | `tasks.py` | `/schedule /tasks /cancel` |
| `github_intel.py` | `github_intel_handler.py` | `/github_intel /eval_repo` |
| `brain.py` (tools) | `brain.py` (handler) | `/memories /briefing` |
| `letta_personality.py` | `memory_commands.py` | `/emotion /profile /teach` |
| `persistence.py` | `e2e.py` | `/e2etest /dbquery` |
| `scaffolder.py` | `dev.py` | `/scaffold /build` |
| `web_search.py` | `research.py` | `/scrape /research` |
| `arxiv.py` | `research.py` | `/paper /ask_paper` |

### Standalone tool invocation

```python
from tools.scheduler import TaskScheduler
scheduler = TaskScheduler(bot, ALLOWED_USER_ID)
await scheduler.start()
```

### Tools used internally by main.py startup

| Tool | Called by | Purpose |
|------|-----------|---------|
| `llm_client.py` | main.py, handlers | LLM calls via litellm/minimax |
| `persistence.py` | on_startup | SQLite init |
| `scheduler.py` | on_startup | Task scheduler |
| `memory.py` | on_startup | Memory DB |
| `n8n_bridge.py` | on_startup | Webhook listener |
| `proactive_monitors.py` | on_startup | GPU/site monitoring |
| `voice_engine.py` | on_startup | Voice pre-warm |
| `supabase_client.py` | on_startup | Supabase skill bootstrap |
| `screenpipe_tool.py` | on_startup | Desktop monitoring |
| `briefing.py` | on_startup | Daily briefing |
| `capability_nightly.py` | on_startup | Nightly capability report |
| `github_intel.py` | on_startup | Daily GitHub trending |
| `proactive_initiator.py` | on_startup | Legion initiates contact |
| `runbook_engine.py` | on_startup | Runbook execution |

### Tool categories

**Browser/Desktop:**
- `browser_tool.py`, `nanobrowser_agent.py`, `computer_use_agent.py`
- `screenpipe_tool.py`, `openclaw_bridge.py`
- `interpreter_tool.py`, `oi_bridge.py`

**Code/Research:**
- `scaffolder.py`, `code_reviewer.py`, `swe_agent_bridge.py`
- `deep_research.py`, `arxiv.py`, `scraper_tool.py`
- `codebase_reader.py`, `rag_tool.py`

**Memory:**
- `memory.py`, `open_memory.py`, `memoryos_client.py`
- `letta_personality.py`, `mem0_client.py`

**Communication:**
- `email_client.py`, `n8n_bridge.py`, `whatsapp_handler.py`
- `telegram_formatter.py`

**Orchestration:**
- `orchestrate_engine.py`, `swarm_wire.py`, `plandex_agent.py`
- `agent_s_tool.py`, `supervision_tool.py`

**Monitoring:**
- `resource_monitor.py`, `system_maintenance.py`
- `proactive_monitors.py`, `proactive_initiator.py`

---

## lib/legiona/ Entry Points

**Location:** `lib/legiona/`

Legiona is the autonomous self-improvement subsystem.

### Core modules

| File | Purpose |
|------|---------|
| `__init__.py` | Package init |
| `scheduler.py` | `start_scheduler()` → Legiona autonomous maintenance |
| `self_evolve.py` | `evolve(last_n=5)` → one M2.7 self-evolution cycle |
| `minimax_client.py` | Structured LLM calls via MiniMax |
| `rag_indexer.py` | Build RAG index from .wiki/ |
| `rag_retriever.py` | Retrieve relevant context from RAG |
| `debate.py` | `debate_sync(question)` → 3-agent debate |

### Bot handler

| File | Purpose |
|------|---------|
| `bot/handlers.py` | /legiona command handler |
| `bot/stream_handler.py` | Streaming response handler |
| `bot/__init__.py` | Router registration |

```python
# legiona_tools.py handler delegates to:
from lib.legiona.bot import router as legiona_router
```

### Tools

| File | Purpose |
|------|---------|
| `tools/registry.py` | Tool registration |
| `tools/system_monitor.py` | System health monitoring |
| `tools/fs_control.py` | Filesystem control tools |
| `tools/log_reader.py` | Log reading tools |
| `tools/desktop_control.py` | Desktop control tools |
| `tools/mmx_tools.py` | MiniMax-specific tools |

### Observability

| File | Purpose |
|------|---------|
| `observability/cost_log.py` | LLM cost tracking |
| `observability/tracer.py` | Distributed tracing |
| `observability/__init__.py` | Package init |

### Evaluation

| File | Purpose |
|------|---------|
| `eval/hallucination_eval.py` | RAGAS hallucination eval harness |
| `eval/__init__.py` | Package init |

```bash
# Run evaluation
make legiona-eval
python lib/legiona/eval/hallucination_eval.py

# Run self-evolution
make legiona-evolve
python -c "from lib.legiona.self_evolve import evolve; evolve(last_n=5)"

# Run 3-agent debate
make legiona-debate
```

---

## Other Runtime Entry Points

### Proactive Engine (Legion initiates contact)

```python
# core/proactive_engine.py
run_proactive_loop()    # Continuous monitoring loop
register_sender(fn)     # Register bot.send_message wrapper

# core/proactive/scheduler.py
ProactiveScheduler.start()  # Daily briefing at 8AM, business checks
```

Triggered by: `/monitor` command, proactive_initiator, scheduled tasks.

### Cron/Scheduled Entry Points (internal asyncio loops)

| Schedule | Entry Point | Purpose |
|----------|-------------|---------|
| Daily 02:00 | `_run_memory_consolidation_nightly()` | Consolidate memory tiers |
| Daily 03:40 | `schedule_nightly_capability_report()` | Capability regression check |
| Monday 03:00 | `_run_memory_consistency_weekly()` | Memory consistency validation |
| Daily 09:00 | `_run_github_intel_daily()` | GitHub trending scan |
| 7:30 AM (planned) | `schedule_daily_briefing()` | Morning briefing |

### Sidecar Processes

| Sidecar | Command | Port |
|---------|---------|------|
| ruflo | `node tools/ruflo/server.js` | 7834 (health probe) |
| opencode | `opencode serve --port 4096` | 4096 |
| webhook server | `WEBHOOK_SERVER.start()` | dynamic |
| MCP servers | `MCP_MANAGER.start_all()` | dynamic |
| health server | `start_health_server(port=8080)` | 8080 |

### Systemd Service Entry Point

```bash
sudo systemctl start legion.service   # Start
sudo systemctl stop legion.service    # Stop
sudo systemctl restart legion.service # Restart
sudo journalctl -u legion.service -f  # View logs
```

---

## Environment-driven Conditional Entry Points

These are gated by environment variables:

| Env Variable | Effect |
|--------------|--------|
| `OPENROUTER_API_KEY` or `ANTHROPIC_API_KEY` | Starts ruflo sidecar |
| `SCREENPIPE_ENABLED=1` | Starts Screenpipe monitor loop |
| `SCREENPIPE_PROACTIVE_ENABLED=1` (default) | Screenpipe proactive monitoring |
| `LEGION_GITNEXUS_AUTO_ANALYZE=1` | Runs GitNexus auto-analyze |
| `TELEGRAM_BOT_TOKEN` | Required for Telegram polling |
| `ALLOWED_USER_ID` | Required for bot to accept commands |

---

## Entry Point Summary Table

| Entry Point | Type | How to Trigger |
|-------------|------|----------------|
| `python main.py` | Process | Systemd, watchdog, direct |
| `dp.start_polling()` | Polling loop | Started by main.py |
| `/do <task>` | Command | Telegram message → computer router |
| `/run <prompt>` | Command | Telegram message → ai router (NL) |
| `/code <task>` | Command | Telegram message → plandex router |
| `/fix <issue>` | Command | Telegram message → swe_commands router |
| Legiona self-evolve | CLI | `make legiona-evolve` |
| Legiona debate | CLI | `make legiona-debate` |
| Legiona eval | CLI | `make legiona-eval` |
| Proactive contact | Background | Scheduled, triggers on conditions |
| Webhook server | HTTP | GitHub/system events → port |
| MCP tools | MCP protocol | External MCP clients |
| Health check | HTTP | `GET http://host:8080/health` |