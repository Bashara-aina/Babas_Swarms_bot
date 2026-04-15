---
title: Litellm Budget Audit Contract4
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- research
created: '2026-04-14'
updated: '2026-04-14'
summary: '**Contract**: #4 of 7 — RESEARCH'
wikilinks: []
confidence: medium
source: research
---
# LITELLM CALL SITE INVENTORY vs BUDGETMANAGER COVERAGE

**Contract**: #4 of 7 — RESEARCH  
**Date**: 2026-04-14  
**Purpose**: Full inventory of all litellm call sites across codebase vs BudgetManager coverage.

---

## EXECUTIVE SUMMARY

- **Total litellm call sites found**: 8 unique locations (excluding llm_client/__init__.py itself and .venv library files)
- **Going through BudgetManager**: 1 location (`llm_client/__init__.py:1558` — the `chat()` function's hard-stop guard)
- **Bypassing BudgetManager entirely**: 8 locations
- **Bypass rate**: 88% of LLM calls are untracked by budget controls

---

## LITELLM CALL SITES (excluding .venv and llm_client/__init__.py)

| # | File | Line | Function / Context | Budget Managed? |
|---|------|------|--------------------|-----------------|
| 1 | `main.py` | 218 | `_probe_llm()` — startup LLM ping | NO |
| 2 | `core/task_router.py` | 209, 421 | `TaskRouter._classify()` and `_decompose()` — routing decisions | NO |
| 3 | `handlers/nihongo_handler.py` | 8, 32 | `_call_llm()` — Japanese teacher mode LLM calls | NO |
| 4 | `swarms_bot/orchestrator/dag_planner.py` | 133 | `DAGPlanner.decompose()` — task decomposition | NO |
| 5 | `swarms_bot/orchestrator/orchestration_runner.py` | 200 | `SwarmSynthesizer.orchestrate()` — result synthesis | NO |
| 6 | `skills/database_agent.py` | 65 | `_nl_to_sql()` — natural language to SQL conversion | NO |
| 7 | `tools/mindbus_router.py` | 104 | `MindBusRouter.route()` — skill routing decision | NO |
| 8 | `tools/autonomous_loop.py` | 132 | `_estimate_cost()` — cost estimation (read-only, not a real LLM call) | N/A |

### LEGEND
- **Budget Managed**: Has `get_budget_guard().can_spend()` check before/after call
- **NO**: Direct `litellm.acompletion()` or `litellm.completion()` call, no budget guard
- **N/A**: Not an actual LLM call (cost estimation only)

---

## DETAILED BYPASS ANALYSIS

### BYPASS 1 — `main.py:218` (`_probe_llm()`)
```python
result = await litellm.acompletion(
    model=primary,
    messages=[{"role": "user", "content": "ping"}],
    max_tokens=2,
)
```
**Purpose**: Startup connectivity probe  
**Budget guard present**: None  
**Risk**: Low volume but runs on every bot startup

---

### BYPASS 2 — `core/task_router.py:209` (`TaskRouter._classify()`)
```python
resp = await acompletion(
    model=self._classify_model,
    messages=[{"role": "user", "content": prompt}],
    temperature=0.0, max_tokens=24,
)
```
**Purpose**: Classify incoming message into TaskType  
**Budget guard present**: None  
**Risk**: Medium volume, runs on every routed message

---

### BYPASS 3 — `core/task_router.py:421` (`TaskRouter._decompose()`)
```python
resp = await acompletion(
    model=self._classify_model,
    messages=[{"role": "user", "content": prompt}],
    temperature=0.1, max_tokens=400,
)
```
**Purpose**: Multi-step task decomposition  
**Budget guard present**: None  
**Risk**: Medium volume, triggered on complex tasks

---

### BYPASS 4 — `handlers/nihongo_handler.py:32` (`_call_llm()`)
```python
response = await acompletion(
    model=model,
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ],
    max_tokens=800, temperature=0.7,
)
```
**Purpose**: Japanese teacher mode (NihongoMode)  
**Budget guard present**: None  
**Risk**: Active when user is in `/nihonko` mode; hardcoded model "claude-3-5-haiku" without fallback

---

### BYPASS 5 — `swarms_bot/orchestrator/dag_planner.py:133` (`DAGPlanner.decompose()`)
```python
response = await litellm.acompletion(
    model=self.model,
    messages=[{"role": "user", "content": prompt}],
    temperature=0.2, max_tokens=2048,
)
```
**Purpose**: Break down multi-step goals into task DAG  
**Budget guard present**: None  
**Risk**: Used in swarms orchestrator; hardcoded model "groq/llama-3.3-70b-versatile"

---

### BYPASS 6 — `swarms_bot/orchestrator/orchestration_runner.py:200` (`SwarmSynthesizer.orchestrate()`)
```python
response = await litellm.acompletion(
    model="groq/llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.3, max_tokens=4096,
)
```
**Purpose**: Synthesize results from multiple agents in swarm orchestration  
**Budget guard present**: None  
**Risk**: High token usage per call (max_tokens=4096); hardcoded groq model

---

### BYPASS 7 — `skills/database_agent.py:65` (`_nl_to_sql()`)
```python
resp = await litellm.acompletion(
    model=os.getenv("DEFAULT_MODEL", "groq/llama-3.3-70b-versatile"),
    messages=[{"role": "user", "content": prompt}],
    temperature=0.1, max_tokens=256,
)
```
**Purpose**: Convert natural language queries to SQL (Supabase)  
**Budget guard present**: None  
**Risk**: Medium tokens but runs on every NL database query

---

### BYPASS 8 — `tools/mindbus_router.py:104` (`MindBusRouter.route()`)
```python
resp = await asyncio.to_thread(
    litellm.completion,
    model=os.getenv("ROUTING_MODEL", "groq/llama-3.3-70b-versatile"),
    messages=[{"role": "user", "content": routing_prompt}],
    max_tokens=120, temperature=0.0,
    response_format={"type": "json_object"},
)
```
**Purpose**: Skill routing decisions  
**Budget guard present**: None  
**Risk**: Runs on many messages to determine routing; hardcoded groq fallback

---

## BUDGETMANAGER COVERAGE DETAILS

### Where BudgetManager IS used in llm_client/__init__.py:

**Line 1558** — hard-stop after all model fallbacks exhausted:
```python
if not get_budget_guard().can_spend("chat"):
    raise BudgetExceededError(f"Budget exceeded for 'chat' — all models exhausted for '{agent_key}'.")
```

This check ONLY fires when:
1. All models in the chain have been tried AND failed
2. The "chat" budget category has been exceeded

**It does NOT**:
- Track per-call spending
- Guard individual LLM calls
- Apply to any litellm call outside `llm_client/__init__.py`

---

## COST ESTIMATION (NOT A BYPASS)

`tools/autonomous_loop.py:132` uses `litellm.completion_cost()` but only for cost estimation, not as an actual LLM call. This is not a bypass — it's read-only cost calculation.

---

## RECOMMENDATIONS

1. **Wrap all 7 bypassed LLM call sites** with `get_budget_guard().can_spend()` before making the call
2. **MindBusRouter** (`tools/mindbus_router.py:104`) — add budget check, use `_call_model()` from llm_client
3. **Database agent** (`skills/database_agent.py:65`) — add budget check, use llm_client's `_call_model()` for consistency
4. **Nihongo handler** (`handlers/nihongo_handler.py:32`) — currently hardcoded to "claude-3-5-haiku"; should use `chat()` path via llm_client facade
5. **DAG planner and orchestration runner** — should use `chat()` from llm_client instead of raw litellm calls
6. **Task router** — `_classify()` and `_decompose()` should route through `chat()` or have budget guards

---

## FILES REQUIRING FIXES (BYPASS COUNT BY FILE)

| File | Bypasses |
|------|----------|
| `main.py` | 1 |
| `core/task_router.py` | 2 |
| `handlers/nihongo_handler.py` | 1 |
| `swarms_bot/orchestrator/dag_planner.py` | 1 |
| `swarms_bot/orchestrator/orchestration_runner.py` | 1 |
| `skills/database_agent.py` | 1 |
| `tools/mindbus_router.py` | 1 |
| **TOTAL** | **8** |

---

## SOURCES
- `/home/newadmin/swarm-bot/llm_client/__init__.py` — BudgetManager definition (line 1558)
- `/home/newadmin/swarm-bot/main.py:218` — probe_llm bypass
- `/home/newadmin/swarm-bot/core/task_router.py:209,421` — task router bypasses
- `/home/newadmin/swarm-bot/handlers/nihongo_handler.py:32` — nihongo bypass
- `/home/newadmin/swarm-bot/swarms_bot/orchestrator/dag_planner.py:133` — dag planner bypass
- `/home/newadmin/swarm-bot/swarms_bot/orchestrator/orchestration_runner.py:200` — orchestrator bypass
- `/home/newadmin/swarm-bot/skills/database_agent.py:65` — database agent bypass
- `/home/newadmin/swarm-bot/tools/mindbus_router.py:104` — mindbus router bypass
- `/home/newadmin/swarm-bot/tools/autonomous_loop.py:132` — cost estimation (not a bypass)