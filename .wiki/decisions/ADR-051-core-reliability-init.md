---
title: Adr 051 Core Reliability Init
type: decision
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- decisions
created: '2026-04-14'
updated: '2026-04-14'
summary: '**Decider:** @planner'
wikilinks: []
confidence: medium
source: research
---
# ADR-051: core.reliability — Empty `__init__.py` Needs Re-exports

**Date:** 2026-04-12
**Status:** Accepted
**Decider:** @planner

## Context

`core/reliability/__init__.py` is 0 bytes (completely empty), but the `core/__init__.py` already re-exports `FallbackChain`, `get_fallback_chain`, `classify_complexity`, `select_model` from this submodule.

Callers also use direct imports:
- `from core.reliability.provider_health import check_provider_health, record_rate_limit, get_all_provider_status, reset_provider_health`
- `from core.reliability.error_recovery import get_recovery`
- `from core.reliability.request_throttle import RequestThrottle`

## Decision

Populate `core/reliability/__init__.py` with re-exports matching the pattern of other core subpackages:

```python
"""Reliability subsystem — fallback chains, provider health, rate limiting."""
from __future__ import annotations

try:
    from .fallback_chain import FallbackChain, get_fallback_chain
    from .model_router import select_model, classify_complexity
    from .provider_health import (
        check_provider_health,
        record_rate_limit,
        get_all_provider_status,
        reset_provider_health,
        _provider_health,
    )
    from .error_recovery import get_recovery
    from .request_throttle import RequestThrottle

    __all__ = [
        "FallbackChain",
        "get_fallback_chain",
        "select_model",
        "classify_complexity",
        "check_provider_health",
        "record_rate_limit",
        "get_all_provider_status",
        "reset_provider_health",
        "_provider_health",
        "get_recovery",
        "RequestThrottle",
    ]
except ImportError as e:
    import logging
    logging.getLogger(__name__).warning("core.reliability partially unavailable: %s", e)
    __all__ = []
```

Note: `core/__init__.py` also re-exports from here, so both files expose the same API. This is intentional redundancy for import flexibility.

## Consequences

- `from core import reliability; reliability.get_all_provider_status()` becomes valid
- Direct imports unchanged
- Module-level `__dir__()` will be accurate

## Implementation

Assign to @worker — see AUDIT 11 subtask list.