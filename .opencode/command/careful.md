---
allowed-tools: Read,Bash,Glob,Grep
argument-hint: [module-or-function-name]
description: "Work carefully and methodically. Audit first, change minimal code, verify each step. Use before /ship."
---

# /careful — Careful mode

Execute tasks with extra verification at each step. Use for risky or large changes.

## When to Use
- Large refactors
- Changes to core systems (llm_client, intent_router, memory)
- Multiple interdependent files
- Security-sensitive changes

## Workflow (extra verification at each step)
```
1. Audit — understand the full scope
2. Plan — break into smallest safe steps
3. Implement step by step
4. Verify after each step
5. Final verification before reporting
```

## Extra Checks
- Run relevant tests after each change
- Check git diff before moving to next step
- Verify no broken imports
- Confirm affected handlers still register

## Verification Command
```bash
pytest tests/ -x --asyncio-mode=auto -q
```

## Swarm-Bot Critical Areas (always use /careful)
- llm_client.py — all AI calls
- core/intent_router.py — message routing
- core/memory/memory_manager.py — memory writes
- handlers/loader.py — handler registration
