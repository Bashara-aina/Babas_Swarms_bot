---
name: ruff-f821-fix-session-status
description: Fixed undefined name _update_state in session-status.py
type: feedback
---

# Ruff F821 Fix: undefined name `_update_state`

## Problem
```
F821 Undefined name `_update_state`
  --> .claude/skills/session-status.py:29:5
```

`set_current_task()` called `_update_state()` but the function was never defined.
Only `_read_state()` and `_write_state()` existed.

## Fix
Added the missing `_update_state()` function before `_read_state()`:

```python
def _update_state(updates: dict[str, Any]) -> None:
    """Merge updates into current state and persist."""
    state = _read_state()
    state.update(updates)
    _write_state(state)
```

**Why:** `set_current_task()` needed to merge `current_task` and `task_started_at` into state.
The function was clearly intended but never implemented.

## Verified
```
ruff check .claude/skills/session-status.py --select=F821
# All checks passed!
```

**Why:** This pattern (define → use) should never reach production. The function call existed but the definition didn't — a classic cut/paste or refactor bug.

**How to apply:** When ruff reports F821, check if the call is intentional and the function is simply missing (not renamed). If missing, add the stub.