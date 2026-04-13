---
title: "ADR-054: Core Module Export Policy"
audit: "AUDIT 05"
date: "2026-04-13"
option_a_(selected): "Explicit Re-Export Policy"
option_b: "Document the Direct Import Pattern"
option_c: "Lazy Export with `__getattr__`"
status: "PROPOSED"
---
# ADR-054: Core Module Export Policy
**Date:** 2026-04-13  
**Status:** PROPOSED  
**Audit:** AUDIT 05

## Context

The `core/__init__.py` currently only re-exports a small subset of core functionality:
- `classify_complexity`, `select_model` (from `model_router`)
- `FallbackChain`, `get_fallback_chain` (from `fallback_chain`)

However, code often uses patterns like:
```python
from core import soul_engine      # Works via Python's submodule caching
from core import memory_engine    # Works via Python's submodule caching
from core import intent_router    # Works via Python's submodule caching
```

This works because Python caches imported modules, but it means `core/__init__.py` doesn't explicitly re-export these — they bypass the package init entirely.

## Decision

**Option A (Selected):** Explicit Re-Export Policy
Add explicit re-exports for all commonly used modules in `core/__init__.py`:

```python
from core import soul_engine
from core import memory_engine
from core import skill_registry
from core import system_prompt_builder
from core import intent_router
from core import autonomous_router
# ... etc
```

**Option B:** Document the Direct Import Pattern
Document that callers should use `from core import module_name` (direct) and the package init is only for cross-cutting concerns.

**Option C:** Lazy Export with `__getattr__`
Use `__getattr__` to lazily import and cache submodules on first access.

## Consequences

### Option A (Selected)
**Pros:**
- Explicit, discoverable exports
- Consistent with `from core import X` pattern
- IDE autocompletion works

**Cons:**
- Circular import risk if modules depend on each other
- Slower import if many modules are loaded
- Need to maintain list of exports

### Option B (Documentation)
**Pros:**
- No code changes needed
- Leverages Python's module caching

**Cons:**
- Implicit behavior, harder to discover
- Documentation may go stale

### Option C (Lazy)
**Pros:**
- Fast initial import
- Only loads what's needed

**Cons:**
- More complex `__getattr__` implementation
- Type checking may suffer

## Recommendation

Implement **Option A** but with lazy loading to avoid circular imports:

```python
_LAZY_EXPORTS = {
    "soul_engine": "core.soul_engine",
    "memory_engine": "core.memory_engine",
    "skill_registry": "core.skill_registry",
    "system_prompt_builder": "core.system_prompt_builder",
    "intent_router": "core.intent_router",
    "autonomous_router": "core.autonomous_router",
}

def __getattr__(name: str):
    if name in _LAZY_EXPORTS:
        return importlib.import_module(_LAZY_EXPORTS[name])
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
```

This preserves the explicit export list while keeping imports lazy and avoiding circular dependencies.

## Implementation Notes

- Current `core/__init__.py` already uses `_LAZY_CORE_SUBMODULES` pattern with `__getattr__`
- Add new `__all__` list to explicitly declare public API
- Keep `_LAZY_CORE_SUBMODULES` for backward compatibility with lazy imports
