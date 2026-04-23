---
name: orchestrator
description: "Skill for the Orchestrator area of swarm-bot. 47 symbols across 15 files."
---

# Orchestrator

47 symbols | 15 files | Cohesion: 88%

## When to Use

- Working with code in `swarms_bot/`
- Understanding how send_fn, set_goal, get_goal work
- Modifying orchestrator-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `swarms_bot/orchestrator/shared_workspace.py` | set_goal, get_goal, set_plan, get_plan, update_status (+6) |
| `swarms_bot/orchestrator/chief_of_staff.py` | select_agent_key, route_task, _execute_with_retry, _log_routing, get_stats (+3) |
| `swarms_bot/orchestrator/orchestration_runner.py` | run, _notify, _approval_cb, _synthesize |
| `tests/test_enterprise_layer.py` | test_select_agent_key, test_select_agent_override, test_stats, test_integration_setters |
| `swarms_bot/orchestrator/registry.py` | LLMAgent, AgenticLoopAgent, CodeReviewAgent |
| `swarms_bot/orchestrator/human_in_loop.py` | request_plan_approval, request_clarification |
| `tests/test_dag_planner.py` | test_is_complete, test_to_text_plan |
| `swarms_bot/orchestrator/dag_planner.py` | is_complete, to_text_plan |
| `swarms_bot/orchestrator/dag_executor.py` | execute, _run_node |
| `swarms_bot/orchestrator/nested_agents.py` | execute, _spawn_one |

## Entry Points

Start here when exploring this area:

- **`send_fn`** (Function) — `handlers/orchestrate.py:79`
- **`set_goal`** (Function) — `swarms_bot/orchestrator/shared_workspace.py:37`
- **`get_goal`** (Function) — `swarms_bot/orchestrator/shared_workspace.py:40`
- **`set_plan`** (Function) — `swarms_bot/orchestrator/shared_workspace.py:43`
- **`get_plan`** (Function) — `swarms_bot/orchestrator/shared_workspace.py:46`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `LLMAgent` | Class | `swarms_bot/orchestrator/registry.py` | 17 |
| `AgenticLoopAgent` | Class | `swarms_bot/orchestrator/registry.py` | 58 |
| `CodeReviewAgent` | Class | `swarms_bot/orchestrator/registry.py` | 95 |
| `Agent` | Class | `swarms_bot/orchestrator/agent_base.py` | 30 |
| `send_fn` | Function | `handlers/orchestrate.py` | 79 |
| `set_goal` | Function | `swarms_bot/orchestrator/shared_workspace.py` | 37 |
| `get_goal` | Function | `swarms_bot/orchestrator/shared_workspace.py` | 40 |
| `set_plan` | Function | `swarms_bot/orchestrator/shared_workspace.py` | 43 |
| `get_plan` | Function | `swarms_bot/orchestrator/shared_workspace.py` | 46 |
| `update_status` | Function | `swarms_bot/orchestrator/shared_workspace.py` | 49 |
| `append_log` | Function | `swarms_bot/orchestrator/shared_workspace.py` | 59 |
| `write_artifact` | Function | `swarms_bot/orchestrator/shared_workspace.py` | 67 |
| `read_artifact` | Function | `swarms_bot/orchestrator/shared_workspace.py` | 78 |
| `get_all_results` | Function | `swarms_bot/orchestrator/shared_workspace.py` | 96 |
| `run` | Function | `swarms_bot/orchestrator/orchestration_runner.py` | 57 |
| `request_plan_approval` | Function | `swarms_bot/orchestrator/human_in_loop.py` | 41 |
| `request_clarification` | Function | `swarms_bot/orchestrator/human_in_loop.py` | 89 |
| `test_select_agent_key` | Function | `tests/test_enterprise_layer.py` | 85 |
| `test_select_agent_override` | Function | `tests/test_enterprise_layer.py` | 99 |
| `track_task` | Function | `swarms_bot/sessions/session_manager.py` | 143 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Run → _write` | intra_community | 3 |
| `Run → _read` | intra_community | 3 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Tests | 8 calls |
| Handlers | 3 calls |
| Routing | 1 calls |

## How to Explore

1. `gitnexus_context({name: "send_fn"})` — see callers and callees
2. `gitnexus_query({query: "orchestrator"})` — find related execution flows
3. Read key files listed above for implementation details
