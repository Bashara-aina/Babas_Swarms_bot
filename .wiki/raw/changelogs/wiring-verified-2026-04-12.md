---
title: Wiring Verified 2026 04 12
type: reference
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- changelogs
created: '2026-04-14'
updated: '2026-04-14'
summary: '**Script**: `scripts/verify_wiring.py`'
wikilinks: []
confidence: medium
source: research
---
# Wiring Verification Report

**Date**: 2026-04-12  
**Script**: `scripts/verify_wiring.py`  
**Result**: ✅ **ALL CHECKS PASSED — Exit 0**

---

## Test Results

| Test | Module | Result |
|------|--------|--------|
| 1 | Handler Wiring | ✅ PASS — 33 handlers, all routers registered in _ROUTER_ORDER |
| 2 | Core Imports | ✅ PASS — 49 core modules all importable |
| 3 | LLM Client | ✅ PASS — llm_client imports, required functions exported |
| 4 | Tools | ✅ PASS — 9 tool modules importable |
| 5 | Bridges | ✅ PASS — 6 bridge modules importable |
| 6 | Skills | ✅ PASS — 28 skills registered, all builtin modules imported |
| 7 | Agents | ✅ PASS — agents module imported, required exports available |

---

## Details

### Test 1: Handler Wiring
- **Handlers found**: ai, admin_handlers, artifact, brain, communications, debate_handlers, legion_extras, business_handler, wiki_handler, runbook_handler, computer, ecc_compat, dev, e2e, enterprise, github_intel_handler, inline, media_tools, memory_commands, orchestrate, overnight_handler, persona_handler, pm, research, session_handler, sessions, skills, system, tasks, upgrade, voice, whatsapp_handler, wiki_router
- **Total**: 33 handlers
- **All routers** found in _ROUTER_ORDER
- **No duplicates** in _ROUTER_ORDER

### Test 2: Core Module Imports
All 49 core modules successfully imported:
core.agent, core.agent_registry, core.autonomous_router, core.capability_audit, core.circuit_breaker, core.conversation_interface, core.debate_engine, core.health, core.health_check, core.hooks, core.humanizer, core.intent_classifier, core.intent_router, core.jarvis_orchestrator, core.legion_memory_facade, core.legion_swarm, core.memory_engine, core.memory_manager, core.model_config, core.mcp_client, core.multi_user, core.natural_command_parser, core.nexus_orchestrator, core.observability, core.openai_agents_bridge, core.opencode_bridge, core.proactive_engine, core.proactive.scheduler, core.persistent_loop, core.rate_limiter, core.research_policy, core.response_filter, core.self_awareness_gate, core.self_improvement, core.self_upgrade, core.skill_registry, core.soul_engine, core.swarm, core.swarm_topologies, core.system_prompt_builder, core.task_router, core.unified_prompt_context, core.working_memory, core.wiki_auto_ingest, core.wiki_bridge, core.wiki_loader, core.wiki_manager, core.wiki_quality_gate, core.wiki_scheduler

### Test 3: LLM Client
- llm_client imports successfully
- Required functions present: chat, agent_loop, verify_api_keys, wiki_raw_completion, chunk_output

### Test 4: Tools
All 9 tools importable: web_search, browser_agent, email_client, github_intel, memory, persistence, scheduler, skill_loader, voice_engine

### Test 5: Bridges
All 6 bridges importable: discord_bridge, livekit_bridge, mastra_bridge, ruflo_bridge, screenpipe_bridge, whatsapp_bridge

### Test 6: Skills Layer
- Skill registry loaded with 28 skills
- All builtin skill modules imported: github, media, memory, personal, productivity, research, system, web

### Test 7: Agents Module
- agents module imports successfully
- Required exports available: AGENT_MODELS, FALLBACK_CHAIN, TASK_KEYWORDS, DEFAULT_AGENT, detect_agent, get_fallback_chain

---

## Actions Taken

1. **Verified script works**: `python scripts/verify_wiring.py` → exit 0
2. **Added Makefile target**: `make verify` → runs the wiring script
3. **Added CI job**: `verify-wiring` job in `.github/workflows/ci.yml`
4. **Created this report**: `WIRING_VERIFIED_2026-04-12.md`

---

*Verified by: Planner Agent | SwarmBot Audit 14*