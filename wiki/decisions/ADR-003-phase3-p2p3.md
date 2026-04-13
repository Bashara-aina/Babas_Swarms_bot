---
title: Adr 003 Phase3 P2P3
type: decision
status: stub
tags: [decisions, general]
created: 2026-04-13
updated: 2026-04-13
summary: Stub — needs enrichment. Auto-added frontmatter during QC restructure.
wikilinks: []
confidence: low
source: migration
project: general
---

# ADR-003: Phase 3 Legion Upgrades + P2/P3 CLAUDE.md Tasks

**Date:** 2026-04-13  
**Phase:** Phase 3 (Webhooks + MCP Backbone) + P2/P3 remaining CLAUDE.md tasks  
**Status:** Planned  
**Deciders:** Bashara, Planner Agent

---

## Context

Phase 2 (Skills Registry, Heartbeat Daemon, Prompt Injection Protection) completed 2026-04-12.  
Phase 3 adds the final integration layer: event-driven webhooks and MCP-backed external tools.  
Additionally, several P2/P3 tasks from CLAUDE.md remain: swarm logic migration, /run /think migration, documentation.

---

## Phase 3 — Webhooks + MCP Backbone (~5h)

### U8: Webhook Listener (`core/webhooks/`) — 2h

**From:** LEGION_MASTER.md Part 6 + LEGION_CLAWCODE_UPGRADE.md UPGRADE 4

**Files to create:**
1. `core/webhooks/__init__.py` — exports WEBHOOK_SERVER singleton
2. `core/webhooks/server.py` — aiohttp-based webhook receiver with HMAC validation

**Endpoints:**
- `POST /webhook/github` — GitHub PR merged → trigger morning briefing summary
- `POST /webhook/rumahlabuh` — new booking/inquiry → immediate notify Bashara
- `POST /webhook/generic` — catch-all for any other webhook source
- `POST /webhook/system` — disk > 90%, GPU temp > 85°C → alert

**Wire into `main.py` on_startup():**
```python
from core.webhooks import WEBHOOK_SERVER
asyncio.create_task(WEBHOOK_SERVER.start())
```

**GitHub HMAC verification:**
- Validate `X-Hub-Signature-256` header using `WEBHOOK_SECRET_GITHUB` env var
- Reject with 401 if signature mismatch

**Handler modules:**
- `core/webhooks/handlers/github.py` — PR merged → brief summary message to Bashara
- `core/webhooks/handlers/rumahlabuh.py` — new inquiry → immediate notification
- `core/webhooks/handlers/system.py` — health alerts

**Add to `.env`:**
```
WEBHOOK_PORT=8743
WEBHOOK_SECRET_GITHUB=your_github_webhook_secret
```

**Budget gate:** All webhook handlers that call LLM must check `BudgetManager.can_spend()` first.

---

### U9: MCP Backbone (`core/mcp/`) — 3h

**From:** LEGION_MCP_SKILLS_MASTER.md Part 3

**Files to create:**
1. `core/mcp/__init__.py` — exports MCP_MANAGER singleton
2. `core/mcp/client.py` — MCPClient wrapper (JSON-RPC 2.0 over stdin/stdout)
3. `core/mcp/manager.py` — MCPManager: auto-starts enabled servers, registers tools as Skills
4. `core/mcp/servers/brave.py` — Brave Search MCP config
5. `core/mcp/servers/github.py` — GitHub MCP config
6. `core/mcp/servers/filesystem.py` — Filesystem MCP config
7. `core/mcp/servers/obsidian.py` — Obsidian MCP config
8. `core/mcp/servers/supabase.py` — Supabase MCP config
9. `core/mcp/servers/browser.py` — Playwright/Crawl4AI MCP config

**Graceful fallback:** If `MCP_*_ENABLED=false` or key not set, skip that server silently. Legion works without any MCP.

**Wire into `main.py` on_startup():**
```python
from core.mcp import MCP_MANAGER
await MCP_MANAGER.start_all()
```

**Server priorities (implement in order):**
1. Brave Search (`MCP_BRAVE_ENABLED`) — powers `web_search` skill
2. GitHub MCP (`MCP_GITHUB_ENABLED`) — powers `github_pr_status`, `github_commit_log`
3. Filesystem MCP (`MCP_FILESYSTEM_ENABLED`) — powers `run_shell`
4. Obsidian MCP (`MCP_OBSIDIAN_ENABLED`) — powers `obsidian_write`
5. Supabase MCP (`MCP_SUPABASE_ENABLED`) — powers `rumahlabuh_status`, `cekwajar_status`
6. Playwright/Crawl4AI (`MCP_BROWSER_ENABLED`) — powers `web_audit`, `web_scrape`

**Add to `.env`:**
```
MCP_BRAVE_ENABLED=true
MCP_GITHUB_ENABLED=true
MCP_FILESYSTEM_ENABLED=true
MCP_OBSIDIAN_ENABLED=false
MCP_SUPABASE_ENABLED=false
MCP_BROWSER_ENABLED=false
MCP_FILESYSTEM_ALLOWED_DIRS=/home/bashara/legion_workspace,/tmp/legion
OBSIDIAN_VAULT_PATH=/home/bashara/Documents/ObsidianVault
```

---

## P2/P3 CLAUDE.md Remaining Tasks (~2h)

### P2-1: Migrate swarm logic main.py → `core/swarm.py` — 30min

**Goal:** Clean up main.py by extracting swarm initialization block.

**What to move (lines ~681-713 in main.py):**
- All `swarms_bot` imports
- `_shared._cost_router`, `_shared._budget_manager`, etc. initialization
- `_shared._chief_of_staff` initialization
- `configure_structured_logging()` call

**Create:** `core/swarm.py` — function `init_swarm_layer()` that returns the initialized components.

**Update:** `main.py` — replace the entire block with:
```python
from core.swarm import init_swarm_layer
init_swarm_layer()
```

---

### P2-2: Move /run /think ai.py → `core/agent.py` — 30min

**Goal:** Reduce handlers/ai.py complexity by extracting AI-specific command handlers.

**handlers/ai.py contains:**
- `cmd_think()` (lines 36-123) — deep reasoning with QwQ
- `cmd_run()` (lines 126-139) — LLM chat only
- `cmd_agent()` (lines 142-159) — force specific agent
- Plus: /swarm, /multi_execute, /orchestrate, /multi_plan, /loop*

**What to move to `core/agent.py`:**
- `cmd_think()` and its helper `_llm_call` / `_progress` (lines 36-123)
- `cmd_run()` (lines 126-139)
- Keep `/swarm`, `/multi_execute`, `/orchestrate`, `/multi_plan`, `/loop*` in handlers/ai.py (they're larger)
- Keep `cmd_agent()` in handlers/ai.py (already fine)

**Wire:** `core/agent.py` exports the functions; `handlers/ai.py` imports and registers them.

---

### P3-3: ARCHITECTURE.md update — 20min

**Goal:** Document Phase 1, 2, 3 architecture changes.

**File:** `docs/architecture.md` (already exists — update it)

**Changes to document:**
- Phase 1 additions: `core/session/transcript.py`, `core/shell/sandbox.py`
- Phase 2 additions: `core/skills/` (28 skills), `core/heartbeat/daemon.py`, injection protection
- Phase 3 additions: `core/webhooks/`, `core/mcp/`
- New file list: `core/session/`, `core/shell/`, `core/skills/`, `core/heartbeat/`, `core/webhooks/`, `core/mcp/`
- Skills registry auto-fire via `SKILL_REGISTRY.find_by_example()` in `intent_router.py`
- Heartbeat daemon wired in `main.py` on_startup
- Webhook server wired in `main.py` on_startup
- MCP Manager wired in `main.py` on_startup

---

### P3-4: docs/MIGRATION.md — 20min

**Goal:** Document migration steps from old architecture to new.

**Create:** `docs/MIGRATION.md`

**Sections:**
1. Dependency changes (new packages: aiohttp, crawl4ai, yt-dlp, python-pptx, ebooklib)
2. Config changes (new env vars for webhooks, MCP feature flags)
3. New environment variables table
4. What changed in `main.py` (swarm layer extracted, webhook+MCP initialized)
5. What changed in `handlers/ai.py` (/run /think migrated)
6. New skills available (list all 28 skills)

---

### P3-5/6: Inline comments in main.py and agent.py — 10min

**main.py:** Add docstrings to public functions:
- `on_startup()` — what gets initialized and in what order
- `on_shutdown()` — cleanup order
- `_trim_log_text()` — purpose and limit convention

**core/agent.py:** Add module-level docstring + docstrings on:
- `cmd_think()` — what it does, what the depth/branches flags mean
- `cmd_run()` — difference from /do

---

## Atomic Subtask List

| # | Task | File(s) | What to do |
|---|------|---------|------------|
| 1 | U8-1: Webhook server core | `core/webhooks/server.py`, `core/webhooks/__init__.py` | Create aiohttp webhook server with HMAC validation, X-Hub-Signature-256 check, register() for handlers, start() on port 8743 |
| 2 | U8-2: GitHub webhook handler | `core/webhooks/handlers/github.py` | Create `handle_github_pr_merged(payload)` — extract PR info, send brief summary to Bashara via bot |
| 3 | U8-3: System webhook handler | `core/webhooks/handlers/system.py` | Create `handle_system_alert(payload)` — check disk/GPU thresholds, alert if exceeded |
| 4 | U8-4: Wire webhook into main.py | `main.py` on_startup | Import WEBHOOK_SERVER, add `asyncio.create_task(WEBHOOK_SERVER.start())`, register handlers |
| 5 | U9-1: MCP client wrapper | `core/mcp/client.py`, `core/mcp/__init__.py` | Create `MCPClient` class with `start()`, `call()`, `list_tools()`; JSON-RPC 2.0 over subprocess stdin/stdout |
| 6 | U9-2: MCP manager | `core/mcp/manager.py` | Create `MCPManager` with `_is_enabled()`, `start_all()`, `stop_all()`; auto-register tools as Skills |
| 7 | U9-3: MCP server configs | `core/mcp/servers/` (brave, github, filesystem, obsidian, supabase, browser) | Create one file per server with server command + env var check; graceful fallback if key not set |
| 8 | U9-4: Wire MCP into main.py | `main.py` on_startup | Import MCP_MANAGER, call `await MCP_MANAGER.start_all()` after skills import |
| 9 | P2-1: Migrate swarm to core/swarm.py | `core/swarm.py`, `main.py` | Extract swarms_bot init block (lines ~681-713) into `core/swarm.py` `init_swarm_layer()`; update main.py to call it |
| 10 | P2-2: Migrate /run /think to core/agent.py | `core/agent.py`, `handlers/ai.py` | Move `cmd_think()`, `cmd_run()` + helpers to `core/agent.py`; handlers/ai.py imports and registers them |
| 11 | P3-3: Update ARCHITECTURE.md | `docs/architecture.md` | Update with Phase 1/2/3 changes: new files, skills registry, heartbeat, webhooks, MCP backbone |
| 12 | P3-4: Create docs/MIGRATION.md | `docs/MIGRATION.md` | Document: new deps, new env vars, migration steps, new skills list |
| 13 | P3-5: Docstrings main.py | `main.py` | Add docstrings to `on_startup()`, `on_shutdown()`, `_trim_log_text()` |
| 14 | P3-6: Docstrings core/agent.py | `core/agent.py` | Add module docstring + docstrings on `cmd_think()`, `cmd_run()` |

---

## Review Task

**Review:** All 14 subtasks → assign to @reviewer

Review checklist:
- [ ] Webhook HMAC validation is correct (HMAC-SHA256, constant-time comparison)
- [ ] MCP client uses asyncio subprocess correctly (no blocking reads)
- [ ] All webhook/MCP handlers call `BudgetManager.can_spend()` before LLM calls
- [ ] `core/swarm.py` import is non-blocking (swarms_bot errors are non-fatal)
- [ ] No new hardcoded API keys or secrets
- [ ] All new files have correct import ordering (stdlib → third-party → local)
- [ ] Tests pass: `pytest tests/ -x --asyncio-mode=auto -q`

---

## References

- LEGION_MASTER.md Part 6 — Webhook listener spec
- LEGION_CLAWCODE_UPGRADE.md UPGRADE 4 — Webhook server code
- LEGION_CLAWCODE_UPGRADE.md UPGRADE 7 — MCP client wrapper spec
- LEGION_MCP_SKILLS_MASTER.md Part 3 — MCP Manager + server configs
- CLAUDE.md P2-1, P2-2, P3-3 through P3-6 — remaining task specs
- ADR-002-phase2.md — Phase 2 decisions (already completed)
