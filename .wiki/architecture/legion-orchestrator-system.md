---
title: legion-orchestrator-system
type: architecture
status: active
tags: [architecture, orchestration, multi-agent, consolidated]
created: 2026-04-13
updated: 2026-04-13
summary: The 4 legacy orchestrators (TaskOrchestrator, LegionSwarm, Nexus, Jarvis) were consolidated into a single `core/orchestrator.py` (1324 lines) with `LegionOrchestrator` as the primary entry point.
wikilinks:
  - [[architecture/legion-module-map]]
  - [[concepts/multi-agent-orchestration]]
  - [[concepts/llm-cost-routing]]
confidence: high
source: implementation
---

# Legion Orchestrator System

## TL;DR

Legion previously had 4 competing orchestrators scattered across the codebase. These were consolidated into a single `core/orchestrator.py` (1324 lines) with `LegionOrchestrator.run(task, user_id)` as the primary entry point. Legacy versions are archived in `_archive/`.

## The 4 Legacy Orchestrators (Now Archived)

| File (Legacy) | Lines | Purpose |
|----------------|-------|---------|
| `_archive/task_orchestrator.py` | 491 | Task chaining, confirmation queue, monitors, SwarmDebateOrchestrator |
| `_archive/core/legion_swarm.py` | 321 | 3-phase parallel swarm (dynamic team from AgentRegistry) |
| `_archive/core/nexus_orchestrator.py` | 385 | 3-layer routing (keyword → semantic → LLM fallback) |
| `_archive/core/jarvis_orchestrator.py` | 207 | Context bundling (memory, Screenpipe, WhatsApp, calendar) |

The shim at `core/nexus_orchestrator.py` re-exports from `core/orchestrator.py` for backward compatibility.

## Current Consolidated System

**File**: `core/orchestrator.py` (1324 lines)

Contains 4 orchestrator classes + 1 standalone function:

### Classes (in order of creation)

#### `SwarmDebateOrchestrator` (line 277)
- Multi-round debate on topics using department agents
- Task chaining with confirmation queue
- Monitors for background task tracking
- Budget-aware LLM calls

#### `NexusOrchestrator` (line 693)
- Three-layer routing: keyword → semantic → LLM fallback
- Agent selection from `core/agent_registry.py`
- Context bundling from memory + proactive sources

#### `LegionSwarmOrchestrator` (line 972)
- Parallel 11-agent team execution
- Phase-based coordination (plan → execute → synthesize)
- Report generation with agent contributions

#### `LegionOrchestrator` (line 1192) — **PRIMARY**
```python
async def run(self, task: str, user_id: int) -> str:
    """Main entry point. All /orchestrate calls route here."""
```
- Unified handler for all orchestration modes
- Integrates with memory, budget guard, and intent routing
- Returns string response (chunked for Telegram)

### Standalone Function

#### `run_legion_swarm()` (line 1304)
- Convenience wrapper for running Legion swarm without class instantiation
- Used by `handlers/orchestrate.py`

## Budget Enforcement

All LLM call sites within orchestrators are guarded by `swarms_bot/routing/budget_guard.py`:

```python
from swarms_bot.routing.budget_guard import budget_guard

@budget_guard(task_type="orchestration")
async def run(self, task: str) -> str:
    ...
```

Budget is tracked per-task-type and checked against `MAX_PROACTIVE_PER_DAY` from `.env`.

## Handler Integration

```
handlers/orchestrate.py
└── core/orchestrator.LegionOrchestrator.run(task, user_id)
    ├── SwarmDebateOrchestrator (debate mode)
    ├── NexusOrchestrator (routing mode)
    └── LegionSwarmOrchestrator (swarm mode)
```

## Related Pages

- [[architecture/legion-module-map]] — Full module architecture
- [[concepts/multi-agent-orchestration]] — Agent coordination patterns
- [[architecture/swarms-bot-routing]] — Enterprise routing layer (swarms_bot/)
