### Review: Legion Wiring Audit — 2026-04-12

#### ✅ Passed:
- `handlers/__init__.py` router order is preserved (31 routers in correct order)
- `admin_handlers` is NOT in `handlers/__init__.py` imports (worker change appears already applied or was never present)
- No import cycles were introduced by worker (verified via grep)
- `enterprise.py` correctly handles `/budget` (line 17-27) — this is the canonical budget handler

#### ⚠️ Warnings:
- **test_main.py line 41** imports `admin_handlers` directly — but `admin_handlers` is not registered in `_ROUTER_ORDER`. If it were imported, it would cause a duplicate router issue since `enterprise.router` also handles `/budget`
- **`admin_handlers.py` still exists** at `handlers/admin_handlers.py` with duplicate `/budget` implementation. Should it be deleted or kept as orphan?
- **verify_wiring.py cannot run** — it fails on import due to the router.py bug

#### ❌ Blockers:

**1. PRE-EXISTING BUG — router.py line 46 blocks all imports:**
```
AttributeError: module 'agents_single_source' has no attribute 'build_system_prompt'
```
- `router.py` line 46: `build_system_prompt = _agents_module.build_system_prompt`
- `build_system_prompt` is defined in `agents/__init__.py` line 1748, NOT in `agents.py`
- `agents.py` only lists it in `__all__` (line 113) but doesn't define it
- **Fix required**: `router.py` must import from `agents/__init__.py`, not `agents.py`

**2. Test failure — tests/test_main.py::test_imports:**
```
handlers/ai.py:13: in <module>
    import router as agents
router.py:46: in <module>
    build_system_prompt = _agents_module.build_system_prompt
AttributeError: module 'agents_single_source' has no attribute 'build_system_prompt'
```
- This is caused by the pre-existing router.py bug, NOT by the worker's change

#### Files Affected by Pre-Existing Bug:
- `/home/newadmin/swarm-bot/router.py` (line 46)
- `/home/newadmin/swarm-bot/handlers/ai.py` (imports router)
- All files importing `handlers` package

#### Recommended Fix for router.py:
```python
# Change line 46 from:
build_system_prompt = _agents_module.build_system_prompt

# To import from agents/__init__.py directly:
from agents import build_system_prompt
```
Or update the module loading logic to load `agents/__init__.py` instead of `agents.py`.

#### Test Status:
```
FAILED tests/test_main.py::test_imports - AttributeError (pre-existing bug)
PASSED — 221 other tests
```

#### Verification Commands Blocked:
- `python scripts/verify_wiring.py` — fails on import
- `pytest tests/ -x --asyncio-mode=auto -q` — fails on test_imports

---
*Reviewer: @reviewer | Date: 2026-04-12*
