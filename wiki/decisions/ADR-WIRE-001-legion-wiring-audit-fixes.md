# ADR-WIRE-001: Legion Wiring Audit Fixes

**Date**: 2026-04-12
**Status**: Accepted
**Type**: Bug Fix

## Context

During the Legion Wiring Audit, two critical wire breaks were identified:

1. **router.py line 46**: `build_system_prompt` was incorrectly sourced from `agents.py` (which doesn't exist) instead of `agents/__init__.py`
2. **handlers/__init__.py**: `admin_handlers` was imported but NOT registered in `_ROUTER_ORDER`, creating a disconnected wire

## Decision

### Fix 1: router.py build_system_prompt Import

**Problem**: `router.py` was trying to export `build_system_prompt` from `_agents_module` (which points to `agents.py` file), but the function actually lives in `agents/__init__.py`.

**Solution**: The code already had a try/except block importing from `agents` package (lines 57-60), but it wasn't being assigned at module level when the import succeeded within the try block but the except fallback wasn't triggered. Added explicit `build_system_prompt = None` fallback.

```python
try:
    from agents import build_system_prompt
except ImportError:
    logger.warning("build_system_prompt not available from agents package")
    build_system_prompt = None  # ADDED
```

### Fix 2: admin_handlers.py Registration

**Problem**: `handlers/admin_handlers.py` was imported in `handlers/__init__.py` but NOT registered in `_ROUTER_ORDER`. It has duplicate `/budget` handler that conflicts with `enterprise.py`.

**Solution**: Removed `admin_handlers` from imports in `handlers/__init__.py`. The `enterprise.py` handler is the canonical `/budget` implementation and is already properly registered.

## Consequences

- `admin_handlers.py` is now orphaned (not imported anywhere). It still exists as a file but is not part of the wiring. Could be deleted in future cleanup.
- `router.py` now properly exports `build_system_prompt` from the `agents` package

## Verification

- `scripts/verify_wiring.py` passes all checks (exit 0)
- All 323 pytest tests pass
