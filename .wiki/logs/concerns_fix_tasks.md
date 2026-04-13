---

---
# Fix 7 Critical Concerns — Subtask Plan
**Date**: 2026-04-12
**Planner**: @planner
**Status**: Draft — requires @worker execution

## Concern 1: Dual llm_client — llm_client.py (root) AND llm_client/ (dir)

### Current State
- `/home/newadmin/swarm-bot/llm_client.py` — 33-line backwards-compatibility shim that re-exports from `llm_client/` package
- `/home/newadmin/swarm-bot/llm_client/` — package directory with `__init__.py` (1809 lines actual implementation)

### Root Cause
The shim at root exists for backwards compatibility but creates confusion about which one is the "real" client.

### Fix Strategy
Keep the package (`llm_client/`), remove the root shim (`llm_client.py`), and update all importers to use the package directly.

### Subtask 1.1: Audit all imports of llm_client
```bash
grep -r "from llm_client import\|import llm_client" --include="*.py" /home/newadmin/swarm-bot | grep -v "__pycache__"
```
**Expected**: List of files that import from llm_client

### Subtask 1.2: Update router.py (line 7)
- File: `/home/newadmin/swarm-bot/router.py`
- Change: `from llm_client import ...` → `from llm_client import ...` (already correct, just verify)

### Subtask 1.3: Update main.py (line 62)
- File: `/home/newadmin/swarm-bot/main.py`
- Current: `from llm_client import verify_api_keys, init_humanization_layer`
- This already imports from the package — verify it works with `python -c "from llm_client import verify_api_keys; print('OK')"`

### Subtask 1.4: Delete root shim
- File: `/home/newadmin/swarm-bot/llm_client.py`
- Action: Delete this file after verifying all imports work via package

### Subtask 1.5: Verify no broken imports
```bash
cd /home/newadmin/swarm-bot && python -c "from llm_client import chat, call_llm, verify_api_keys; print('All exports OK')"
```

### Verification
- `python -c "import llm_client; print('Package import OK')"` should work
- `ls llm_client/` should show `__init__.py` and no root shim

---

## Concern 2: Dual agents — agents.py (root) AND agents/ (dir)

### Current State
- `/home/newadmin/swarm-bot/agents.py` — 133-line backwards-compatibility shim re-exporting from `core.agent_registry` and `core.conversation_interface`
- `/home/newadmin/swarm-bot/agents/` — directory with `__init__.py` (1852 lines) plus sub-agents (creative/, design/, engineering/, etc.)

### Root Cause
Two separate agent systems exist: the shim at root pointing to `core.agent_registry`, and the `agents/` directory with its own agent implementations.

### Fix Strategy
Consolidate by keeping `agents/` as the single source of truth for agent implementations. The root `agents.py` shim can stay (for backwards compat with `router.py`), but ensure `agents/` is properly structured.

### Subtask 2.1: Audit agents/ directory structure
```bash
ls -la /home/newadmin/swarm-bot/agents/
```
**Expected**: `__init__.py`, plus subdirectories for each agent type

### Subtask 2.2: Audit what agents.py exports vs agents/__init__.py
```bash
head -60 /home/newadmin/swarm-bot/agents.py
grep "^from\|^import" /home/newadmin/swarm-bot/agents/__init__.py | head -40
```

### Subtask 2.3: Verify router.py imports
- File: `/home/newadmin/swarm-bot/router.py` (line 21-28)
- Currently dynamically imports `agents.py` from root
- Should verify this pattern still works or update to import from `agents` package

### Subtask 2.4: Check handlers/ for agent imports
```bash
grep -r "from agents import\|from agents." --include="*.py" /home/newadmin/swarm-bot/handlers | head -20
```

### Verification
- `python -c "import agents; print(dir(agents))"` should show expected exports
- `python -c "from agents import detect_agent, get_fallback_chain; print('OK')"` should work

---

## Concern 3: Swarm handler is a stub — handlers/swarm_handler.py is 906 bytes

### Current State
- `/home/newadmin/swarm-bot/handlers/swarm_handler.py` — Only contains `SwarmCommandArgs` dataclass and `parse_swarm_args()` function (34 lines)
- `/home/newadmin/swarm-bot/handlers/ai.py` (line 88-145) — Has `cmd_swarm()` that calls `parse_swarm_args` from swarm_handler
- `/home/newadmin/swarm-bot/task_orchestrator.py` — Has `SwarmDebateOrchestrator` class with 4-round debate logic

### Root Cause
`handlers/swarm_handler.py` is not a handler at all — it's just an argument parser. The actual swarm logic is in `ai.py` and `task_orchestrator.py`.

### Fix Strategy
Either:
A) Rename `swarm_handler.py` to `swarm_args.py` (or move to `core/swarm_args.py`) to clarify it's not a handler
B) Integrate the `SwarmDebateOrchestrator` from `task_orchestrator.py` into a proper swarm handler

### Subtask 3.1: Check if swarm_handler.py has a router
```bash
grep -n "router\|Router" /home/newadmin/swarm-bot/handlers/swarm_handler.py
```
**Expected**: No router found — it's not a handler

### Subtask 3.2: Determine correct location for parse_swarm_args
- If it's only used by `handlers/ai.py`, consider moving to `core/swarm_args.py`

### Subtask 3.3: Move parse_swarm_args if appropriate
- Create `core/swarm_args.py` with the dataclass and parser
- Update `handlers/ai.py` line 101 to import from `core.swarm_args`
- Delete `handlers/swarm_handler.py`

### Verification
- `/swarm` command should still work via `handlers/ai.py`
- `python -c "from core.swarm_args import parse_swarm_args; print(parse_swarm_args('--sdk test'))"` should work

---

## Concern 4: Search result injection bug — search triggered but results NOT injected into LLM context

### Current State
- `/home/newadmin/swarm-bot/handlers/media_tools.py` (line 189-202) — `/search` command calls `web_search()` and returns results directly to user
- `/home/newadmin/swarm-bot/tools/web_search.py` — `search_web()` returns formatted results
- `/home/newadmin/swarm-bot/llm_client/__init__.py` (line 1352-1406) — Self-awareness gate DOES inject search results into LLM context, but only after initial LLM call fails

### Root Cause
The `/search` command returns results directly to user without passing them through the LLM for synthesis. The self-awareness gate in `llm_client/__init__.py` only triggers when the LLM says "I don't know".

### Subtask 4.1: Understand the two search paths
1. `/search` command in media_tools.py — returns raw results to user
2. Self-awareness gate in llm_client — triggers search on "I don't know" and reinjects

### Subtask 4.2: Determine desired behavior
- Option A: `/search` should inject results into LLM for synthesis before returning
- Option B: Keep as-is (raw results to user) since self-awareness gate handles it

### Subtask 4.3: If fix needed — modify media_tools.py cmd_search
- File: `/home/newadmin/swarm-bot/handlers/media_tools.py` (line 189-202)
- After getting `result = await web_search(query=text)`, instead of returning directly:
- Build a prompt: `Sintesiskan hasil pencarian berikut untuk pengguna: {result}`
- Call LLM to synthesize and return that instead

### Verification
- Send `/search latest AI news`
- Response should be synthesized (not raw search results dump)

---

## Concern 5: Daily harvester not scheduled — daily_harvester.py exists but not wired to scheduler

### Current State
- `/home/newadmin/swarm-bot/daily_harvester.py` — CLI entry point (65 lines)
- `/home/newadmin/swarm-bot/core/daily_harvester/scheduler.py` — `DailyHarvesterScheduler` class (103 lines)
- `/home/newadmin/swarm-bot/main.py` (line 584-595) — `_start_daily_harvester()` creates and starts scheduler

### Root Cause
Need to verify the scheduler is actually being called on startup.

### Subtask 5.1: Verify main.py wiring
- File: `/home/newadmin/swarm-bot/main.py` (line 584-595)
- `_start_daily_harvester()` is called in `_run_group_a_startup()` (line 633)
- This creates `DailyHarvesterScheduler` and calls `.start()`

### Subtask 5.2: Check DailyHarvesterScheduler.start()
- File: `/home/newadmin/swarm-bot/core/daily_harvester/scheduler.py` (line 41-48)
- Creates `asyncio.create_task(self._run_loop())` — runs continuously

### Subtask 5.3: Verify HarvestPipeline exists
```bash
python -c "from core.daily_harvester.harvest_pipeline import HarvestPipeline; print('OK')"
```

### Verification
- Check logs on bot startup for "DailyHarvesterScheduler started"
- `python daily_harvester.py --dry-run` should complete without error

---

## Concern 6: Growth without verification — no CI/pre-commit guards

### Current State
- `/home/newadmin/swarm-bot/.github/workflows/ci.yml` — CI pipeline exists (lint, test, verify-wiring)
- No pre-commit configuration at repo root

### Root Cause
No pre-commit hooks to catch issues before commit.

### Subtask 6.1: Create pre-commit configuration
- File: `/home/newadmin/swarm-bot/.pre-commit-config.yaml`
- Include:
  - `ruff` for Python linting
  - `mypy` for type checking (if installed)
  - Trailing whitespace fixer
  - End-of-file fixer
  - JSON/YAML validator

### Subtask 6.2: Add pre-commit to requirements.txt or as dev dependency
```bash
grep "pre-commit" /home/newadmin/swarm-bot/requirements.txt || echo "pre-commit not in requirements"
```

### Subtask 6.3: Document pre-commit setup in CONTRIBUTING.md
- File: `/home/newadmin/swarm-bot/CONTRIBUTING.md`
- Add section: "Pre-commit hooks: pip install pre-commit && pre-commit install"

### Verification
- `pre-commit run --all-files` should complete without error
- `git commit` should trigger pre-commit hooks

---

## Concern 7: Soul integrity — risk that some code paths bypass soul injection

### Current State
- `/home/newadmin/swarm-bot/llm_client/__init__.py`:
  - `chat()` function (line 966) — INJECTS soul via `build_soul_context()` (line 1027-1029)
  - `call_llm()` function (line 352) — DOES NOT inject soul, takes raw messages
- `/home/newadmin/swarm-bot/task_orchestrator.py`:
  - `SwarmDebateOrchestrator._call_agent()` (line 277) — calls `self.llm_call()` which is `call_llm`
  - This BYPASSES soul injection

### Root Cause
`call_llm()` is a low-level function that takes pre-built messages. Only `chat()` adds soul context. Any caller using `call_llm()` directly bypasses soul.

### Subtask 7.1: Audit all call_llm usages
```bash
grep -r "call_llm\|from llm_client import call_llm" --include="*.py" /home/newadmin/swarm-bot | grep -v "__pycache__" | grep -v "test"
```

### Subtask 7.2: Identify callers that bypass soul
- `task_orchestrator.py` line 294, 299 — `SwarmDebateOrchestrator` uses `call_llm`
- Any others found in audit

### Subtask 7.3: Fix SwarmDebateOrchestrator
- Option A: Use `chat()` instead of `call_llm()` (but `chat()` adds conversation history which may not be wanted)
- Option B: Add `build_soul_context()` to messages before calling `call_llm`
- Option C: Create `call_llm_with_soul()` wrapper

### Subtask 7.4: Implement fix
If fixing task_orchestrator.py:
- File: `/home/newadmin/swarm-bot/task_orchestrator.py`
- In `_call_agent()` method (line 277), prepend soul context to messages

### Verification
```python
# Test that SwarmDebateOrchestrator includes soul
from task_orchestrator import SwarmDebateOrchestrator
import asyncio

async def test():
    orch = SwarmDebateOrchestrator(lambda m, s, u: "test")
    # Inject a mock that captures messages
    captured = []
    async def capture_llm(model, system, user):
        captured.append(system)
        return "test response"
    orch.llm_call = capture_llm
    await orch._call_agent("strategist", "test task")
    assert "Legion" in captured[0] or "SOUL" in captured[0].upper(), "Soul not injected!"

asyncio.run(test())
```

---

## Execution Order

| Order | Concern | Priority | Est. Complexity |
|-------|---------|----------|-----------------|
| 1 | Dual llm_client | Medium | Low (cleanup) |
| 2 | Dual agents | Medium | Medium (audit) |
| 3 | Swarm handler stub | Low | Low (rename) |
| 4 | Search injection bug | High | Medium (behavior change) |
| 5 | Daily harvester | Low | Verify only |
| 6 | Pre-commit guards | Medium | Low (add config) |
| 7 | Soul integrity | High | High (audit + fix) |

---

## Notes

- **Do NOT modify**: `SOUL.md`, `CLAUDE.md`, `LEGION_MASTER.md`, `LEGION_NIHONGO_MODE.md`
- **Constraints**: Fix concerns in order (1-7), verify each fix before moving to next
- **Testing**: Run `pytest tests/ -x --asyncio-mode=auto -q` after each fix
