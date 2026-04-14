---
title: Adr 002 Consolidate Agent Registries
type: decision
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- decisions
created: '2026-04-14'
updated: '2026-04-14'
summary: '- Context: Two parallel agent registries (`agents.py` with 22 agents + `core/agent_registry.py`
  with 76 YAML agents) created routing confusion, duplicate logic, and maintenance
  burden'
wikilinks: []
confidence: medium
source: research
---
# ADR-002: Consolidate Dual Agent Registries
- Date: 2026-04-10
- Status: Accepted
- Context: Two parallel agent registries (`agents.py` with 22 agents + `core/agent_registry.py` with 76 YAML agents) created routing confusion, duplicate logic, and maintenance burden
- Decision: Unify agent registries by moving all legacy agents into `config/departments.yaml` under a new `legacy` department, extracting personality/debate configs to `config/personality.yaml`, and rewriting `agents.py` as a thin backwards-compatibility wrapper
- Consequences:
  - Single source of truth for agent routing in `core/agent_registry.py`
  - `agents.py` now delegates to `core/agent_registry.py` (no duplicate `detect_agent`)
  - `PERSONALITY_WRAPPER` and `DEBATE_PERSONAS` centralized in `config/personality.yaml`
  - Circular import between `agents.py` and `core/agent_registry.py` resolved via `core/conversation_interface.py`
  - 22-23 legacy agents now organized under `legacy` department in YAML config
  - **Phase 2 (2026-04-10):** Circular import risk fully eliminated — extracted shared state (`detect_agent`, `get_fallback_chain`, conversation history dicts) into `core/conversation_interface.py` (~286 lines), updated `llm_client.py`, `agents.py`, and `swarms_bot/routing/cost_router.py` to import from centralized interface
  - **Phase 3 (2026-04-10):** Startup parallelization implemented — `_run_group_a_startup(bot)` runs 12 tasks via `asyncio.gather()` with 30s timeout; test coverage raised to 70% (67 tests across 6 new files); mypy type enforcement added
  - **Phase 4 (2026-04-10):** Intent router enhanced with LLM classification for ambiguous cases; skills/manifest.json created as single source of truth for skill discovery; skill_registry.py updated to use manifest + LLM-based routing
  - **Phase 5 (2026-04-10):** Proactive scheduler enhanced — GitHub trend watcher now calls `SelfUpgradeEngine.scan_github_trending()` for real digest; late night check uses Soul Engine emotional context for warm/casual tone
  - **Phase 6 (2026-04-10):** Web search (DuckDuckGo + SerpAPI fallback) and GeoIntelligence skills created
  - **Phase 7 (2026-04-10):** `scan_weekly_trends()` method added to self_upgrade.py; `CapabilityAudit` class created for monthly self-audit
  - **Phase 8 (2026-04-10):** `check_booking_alerts()` added to rumahlabuh_crew.py (new bookings, failed payments, overbookings); `DatabaseAgent` created (NL→SQL, SELECT-only safe)
