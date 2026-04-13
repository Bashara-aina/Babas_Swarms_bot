---
title: ADR — Budget Guard Fix: can_spend() Added to BudgetManager
type: decision
status: active
tags: [legion, budget, daily-harvester, swarm-debate, background-tasks]
created: 2026-04-13
updated: 2026-04-13
summary: "BUG: BudgetManager.can_spend() was called throughout the codebase but never implemented. Also, swarm_debate (daily harvester) and curiosity_engine made LLM calls without budget guards. Added can_spend() to BudgetManager + budget guards to swarm_debate.py."
wikilinks:
  - [[architecture/legion-module-map]]
  - [[entities/litellm]]
confidence: high
source: loop-6-audit
project: legion
---

## Decision

1. Added `can_spend(task_type: str = "chat") -> bool` to `BudgetManager` in `swarms_bot/routing/budget_manager.py`
2. Added budget guards to all 4 LLM call sites in `core/daily_harvester/swarm_debate.py`

## Problem

`BudgetManager.can_spend()` was called in `llm_client/__init__.py:1554` as the final fallback before raising `BudgetExceededError`, but the method did not exist on the class. Additionally, two background tasks made LLM calls without any budget guard:

- **swarm_debate.py**: 4-agent debate (Prosecutor, Defender, FactChecker, Judge) — each agent calls `llm_client.chat()`
- **curiosity_engine.py**: `get_pending_followups()` reads data/beliefs.json (sync, no LLM), `check_site_health()` uses browser_agent (no LLM), sleep pattern check is pure time math — **no LLM calls found, no fix needed**

The `can_spend()` method was referenced in CLAUDE.md Section 8 (budget enforcement) and multiple wiki articles but had never been implemented.

## Implementation

### BudgetManager.can_spend()

Added at line 121 of `swarms_bot/routing/budget_manager.py`:

```python
def can_spend(self, task_type: str = "chat") -> bool:
    """Return True if budget allows spending for the given task type.

    Args:
        task_type: Type of task (e.g., 'chat', 'debate', 'research').
                   Currently unused but reserved for per-task limits.

    Returns:
        True if daily and monthly limits are not exceeded.
    """
    return self.check_budget()["allowed"]
```

### swarm_debate.py Budget Guards

Added `_budget_guard_check(task_type) -> bool` helper function and wrapped all 4 LLM call sites:

| Agent | Task Type | Guard Action |
|-------|-----------|--------------|
| Prosecutor | `debate` | Skip with warning, return `[f"Budget exceeded — candidate skipped"]` |
| Defender | `debate` | Skip with warning, return `[f"Budget exceeded — candidate skipped"]` |
| FactChecker | `research` | Skip with warning, return `{"result": "UNABLE_TO_VERIFY", ...}` |
| Judge | `analyst` | Skip with warning, return `SwarmVerdict(verdict=NEEDS_MORE_RESEARCH, reasoning="Budget exceeded")` |

If the budget guard singleton is unavailable (import fails), calls are allowed through (fail-open for robustness).

## Consequences

- `BudgetManager.can_spend()` now exists and returns `bool`
- swarm_debate LLM calls now check budget before firing
- curiosity_engine makes no LLM calls (confirmed — follows up from beliefs.json data only)
- `llm_client/__init__.py:1554` will now find `can_spend()` on the BudgetManager instance

## Files Changed

- `swarms_bot/routing/budget_manager.py` — +11 lines: `can_spend()` method added
- `core/daily_harvester/swarm_debate.py` — +28 lines: `_budget_guard_check()` + 4 guard blocks

## Notes

- The budget guard in `swarm_debate.py` uses `fail-open` semantics: if `get_budget_guard()` or `can_spend()` throws, the call proceeds. This prevents a budget guard bug from blocking the entire harvest pipeline.
- The daily harvester's `run_debate_batch()` does not have a top-level budget guard — each agent individually checks. This means budget-exhausted candidates still enter the pipeline but get SKIP verdicts rather than crashing the batch.
- curiosity_engine does NOT call LLM directly — `_check_pending_followups()` reads beliefs.json (no LLM), `_check_site_health()` uses browser_agent (no LLM), `_check_sleep_pattern()` is pure time math. No budget guard needed there.