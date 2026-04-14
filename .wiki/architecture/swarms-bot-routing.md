---
title: swarms-bot-routing
type: architecture
status: active
tags: [architecture, routing, budget, cost, orchestration]
created: 2026-04-13
updated: 2026-04-13
summary: swarms_bot/ is Legion's enterprise-grade orchestration layer with structured routing (budget_guard, budget_manager, cost_router) and DAG-based task execution (orchestrator/).
wikilinks:
  - [[architecture/legion-module-map]]
  - [[./concepts/llm-cost-routing]]
  - [[architecture/legion-orchestrator-system]]
confidence: high
source: implementation
---

# swarms_bot — Enterprise Orchestration Layer

## TL;DR

`swarms_bot/` is a separate package from the root-level `agents/` and `core/` directories. It provides enterprise-grade orchestration with structured routing (budget management, cost-optimized model selection) and DAG-based task execution. Located at `/home/newadmin/swarm-bot/swarms_bot/`.

## Directory Structure

```
swarms_bot/
├── routing/                        # Cost and budget management
│   ├── budget_guard.py           # Decorator: guards LLM calls with budget check
│   ├── budget_manager.py          # Daily/monthly spend tracking (can_spend())
│   └── cost_router.py             # Cost-optimized model selection per task
├── orchestrator/                  # DAG-based execution
│   ├── agent_base.py              # Base class for swarms agents
│   ├── agent_messaging.py          # Inter-agent message passing
│   ├── chief_of_staff.py           # Top-level coordination
│   ├── dag_executor.py             # Executes DAG of tasks
│   ├── dag_planner.py              # Converts natural language → DAG
│   ├── human_in_loop.py            # Approval gates for destructive actions
│   ├── model_router.py             # Per-task model selection
│   ├── nested_agents.py           # Sub-agent creation/management
│   ├── orchestration_runner.py     # Main orchestration loop
│   └── registry.py                # Agent registry for this layer
├── observability/                  # Metrics collection
├── sessions/                       # Session state management
├── audit/                          # Audit logging
└── evaluation/                     # Performance evaluation
```

## Budget System

### BudgetManager (`swarms_bot/routing/budget_manager.py`)

Tracks spend per task type across all LLM providers:

```python
class BudgetManager:
    async def can_spend(self, task_type: str = "chat") -> bool:
        """Check if budget available for task_type today."""

    async def record_spend(self, task_type: str, cost: float) -> None:
        """Record USD spend for a task_type."""
```

Environment variables:
- `MAX_PROACTIVE_PER_DAY` — max budget for background tasks (default: 3 USD)
- `BUDGET_DAILY_LIMIT_USD` — hard cap across all tasks (default: 2.00 USD)

### budget_guard (`swarms_bot/routing/budget_guard.py`)

Decorator that wraps LLM call sites:

```python
@budget_guard(task_type="orchestration")
async def run_swarm(task: str) -> str:
    ...
```

If `can_spend()` returns False, the call is skipped and a warning is logged.

### cost_router (`swarms_bot/routing/cost_router.py`)

Selects the cheapest model that meets quality threshold for a task:

```python
def select_model(task_type: str, quality_required: float) -> str:
    """Return model ID for task_type that meets quality at minimum cost."""
```

## DAG Orchestration

### DAG Planner (`orchestrator/dag_planner.py`)

Converts natural language task descriptions into directed acyclic graphs:

```
"Deploy the API to staging and run smoke tests"
  → DAG:
    [build_image] → [deploy_staging] → [run_smoke_tests]
                                      ↓
                                 [rollback_if_failed]
```

### DAG Executor (`orchestrator/dag_executor.py`)

Executes DAG with:
- Parallel execution of independent nodes
- Dependency resolution
- Failure handling with retry limits
- Human-in-loop approval for destructive nodes

### Chief of Staff (`orchestrator/chief_of_staff.py`)

Top-level coordinator that:
- Receives task from `LegionOrchestrator`
- Plans DAG via `dag_planner`
- Assigns agents via `model_router`
- Monitors execution via `dag_executor`
- Reports results back to `LegionOrchestrator`

## Agent Messaging

`agent_messaging.py` provides structured inter-agent communication:

```python
class AgentMessage:
    from_agent: str
    to_agent: str
    content: str
    metadata: dict  # task_id, deadline, quality_requirements

async def send(message: AgentMessage) -> None: ...
async def receive(agent_id: str) -> AgentMessage: ...
```

## Relationship to core/orchestrator.py

```
handlers/orchestrate.py
└── core/orchestrator.LegionOrchestrator.run()
    ├── (for simple tasks) → direct execution
    └── (for complex DAG tasks) → swarms_bot.orchestrator.chief_of_staff.run()
                                      ├── dag_planner.build()
                                      ├── model_router.select()
                                      └── dag_executor.execute()
```

`swarms_bot/` is invoked when `LegionOrchestrator` needs structured multi-step execution with budget tracking and human-in-loop gates.

## Related Pages

- [[architecture/legion-module-map]] — Full module map
- [[./concepts/llm-cost-routing]] — Cost routing strategy
- [[architecture/legion-orchestrator-system]] — How it connects to LegionOrchestrator
