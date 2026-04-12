# ADR-??? — LEGION AUDIT 12: Nihongo Mode User Isolation Fix
> Architecture Decision Record

**Date:** 2026-04-12  
**Status:** Proposed  
**Deciders:** @planner, @worker, @reviewer  

---

## Context

LEGION AUDIT 12 identified a potential issue: nihongo mode may leak between users. The concern is that if the nihongo active flag is stored globally (rather than per-user), one user's activation could affect another user's experience.

### Current Implementation Analysis

**Storage (`skills/nihongo/mode_manager.py`):**
```python
class NihongoModeManager:
    _sessions: dict[int, NihongoSession] = {}  # Line 48

    @classmethod
    def is_active(cls, user_id: int) -> bool:
        session = cls._sessions.get(user_id)
        return session.active if session else False
```

**Activation (`handlers/nihongo_handler.py:51-52`):**
```python
if text == "/nihonko" or text.startswith("/nihonko chat"):
    session = NihongoModeManager.activate(user_id, NihongoSubMode.CHAT)
```

**Intercept check (`handlers/ai.py:755-757`):**
```python
if NihongoModeManager.is_active(user_id):
    await handle_nihongo_message(msg, ContextTypes.DEFAULT_TYPE)
    return
```

### Initial Assessment

The code **appears correct** — `_sessions` is keyed by `user_id` (int), and all operations pass `user_id` explicitly. However:

1. **Missing test coverage**: `tests/test_multi_user_isolation.py:10-24` only checks `user_a != user_b` — it does NOT actually test that nihongo mode is isolated
2. **Potential confusion**: The command is `/stopp` and `/stop`, but documentation mentions `/nihongo_off`
3. **No dedicated isolation test**: `tests/test_nihongo_isolation.py` does not exist

---

## Decision

### Primary Fix: Create Dedicated Isolation Test

Create `tests/test_nihongo_isolation.py` with concrete per-user tests that verify:
1. User A activates nihongo → User B remains unaffected
2. Concurrent users with different states
3. Deactivation only affects the target user

### Secondary Fix: Add `/nihongo_off` Alias

Add `/nihongo_off` as an alias to `/stopp` for discoverability, matching user expectations from documentation.

### Verification: Run Full Test Suite

Ensure all existing nihongo tests pass, especially:
- `tests/test_nihongo_mode.py:17-45` — sensei prompt isolation
- `tests/test_soul_persistence.py:46` — soul preservation

---

## Consequences

**Positive:**
- Definitively proves per-user isolation works
- Adds regression protection
- Clarifies command interface

**Negative:**
- None — this is a test addition and alias only

**Risks:**
- If `NihongoModeManager._sessions` were ever changed to a global flag, isolation would break
- In-memory dict means session data lost on restart (acceptable for current design)

---

## References

- `skills/nihongo/mode_manager.py` — NihongoModeManager class
- `handlers/nihongo_handler.py` — Command handlers
- `handlers/ai.py:743-760` — NIHONGO MODE INTERCEPT
- `LEGION_WIRING_AUDIT_PROMPT.md:168-177` — Entry point documentation
