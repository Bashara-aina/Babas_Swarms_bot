---
title: Priority 7 Orchestrator
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- logs
created: '2026-04-14'
updated: '2026-04-14'
summary: '**Status:** COMPLETED'
wikilinks: []
confidence: medium
source: research
---
# Priority 7: Consolidate 4 Orchestrators into 1

**Date:** 2026-04-12  
**Status:** COMPLETED

## Task
Consolidate 4 orchestrators into `core/orchestrator.py`:
- `task_orchestrator.py` (492 lines) — task chaining, confirmation queue, monitors, SwarmDebateOrchestrator
- `core/legion_swarm.py` (322 lines) — 3-phase parallel swarm, hardcoded 11-agent team
- `core/nexus_orchestrator.py` (385 lines) — 3-layer semantic routing
- `core/jarvis_orchestrator.py` (207 lines) — context bundle (memory, Screenpipe, WhatsApp, calendar)

## What Was Done

### 1. Created `core/orchestrator.py`
Merged unique value from all 4 orchestrators:
- `LegionOrchestrator` — single canonical entry point with `run(task, user_id)`
- `SwarmDebateOrchestrator` — 4-round debate system (from task_orchestrator.py)
- `LegionSwarmOrchestrator` — 3-phase swarm using dynamic `select_team()` (from legion_swarm.py)
- Context bundling via `gather_jarvis_bundle()` (from jarvis_orchestrator.py)
- 3-layer routing (keyword → semantic → LLM fallback) (from nexus_orchestrator.py)

### 2. Added `AgentRegistry.select_team()`
Added `select_team(task_description, max_agents)` to `core/agent_registry.py` for dynamic team selection.

### 3. Created Stubs
Created stub files that re-export from `core/orchestrator.py`:
- `task_orchestrator.py` → stub re-exporting TaskStep, PendingConfirmation, MonitorTask, SwarmDebateOrchestrator, execute_chain, queue_confirmation, confirm_action, deny_action, list_pending, start_monitor, cancel_monitor, list_monitors
- `core/legion_swarm.py` → stub re-exporting LegionSwarmOrchestrator, run_legion_swarm
- `core/nexus_orchestrator.py` → stub re-exporting NexusOrchestrator, nexus, RoutingDecision
- `core/jarvis_orchestrator.py` → stub re-exporting gather_jarvis_bundle, compose_jarvis_response

### 4. Archived Originals
Moved originals to `_archive/`:
- `_archive/task_orchestrator.py`
- `_archive/core/legion_swarm.py`
- `_archive/core/nexus_orchestrator.py`
- `_archive/core/jarvis_orchestrator.py`

### 5. Wrote ADR
ADR-016.md written to `.wiki/decisions/`

## Verification
- `python -c "from core.orchestrator import LegionOrchestrator; print('OK')"` → OK
- `python scripts/verify_wiring.py` → PASS (all 7 tests)
