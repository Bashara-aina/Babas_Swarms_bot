---
# AUDIT 11 — Task List
**Date:** 2026-04-12
**Status:** IN PROGRESS

---

## SUBTASK 1: bridges/__init__.py — Create with re-exports
**Priority:** P1 (will break if missing)
**ADR:** ADR-050
**File:** `/home/newadmin/swarm-bot/bridges/__init__.py`

Create `bridges/__init__.py` with re-exports of all bridge classes. Read each bridge file first to find the class/function names:

```python
"""Bridges — external service integrations for LegionSwarm."""
from bridges.whatsapp_bridge import WhatsAppBridge
from bridges.screenpipe_bridge import ScreenpipeBridge
from bridges.discord_bridge import DiscordBridge
from bridges.livekit_bridge import LiveKitBridge, meet_join_url
from bridges.mastra_bridge import MastraBridge
from bridges.ruflo_bridge import RufloBridge

__all__ = [
    "WhatsAppBridge",
    "ScreenpipeBridge", 
    "DiscordBridge",
    "LiveKitBridge",
    "meet_join_url",
    "MastraBridge",
    "RufloBridge",
]
```

**Verification:** `python -c "from bridges import WhatsAppBridge, ScreenpipeBridge, DiscordBridge, LiveKitBridge, MastraBridge, RufloBridge; print('bridges OK')"`

---

## SUBTASK 2: core/reliability/__init__.py — Populate with re-exports
**Priority:** P1
**ADR:** ADR-051
**File:** `/home/newadmin/swarm-bot/core/reliability/__init__.py`

Populate `core/reliability/__init__.py` with re-exports matching what's already in `core/__init__.py` (which re-exports from here). Read each file to get exact names:

```python
"""Reliability subsystem — fallback chains, provider health, rate limiting."""
from __future__ import annotations

from .fallback_chain import FallbackChain, get_fallback_chain
from .model_router import select_model, classify_complexity
from .provider_health import (
    check_provider_health,
    record_rate_limit,
    get_all_provider_status,
    reset_provider_health,
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
    "get_recovery",
    "RequestThrottle",
]
```

**Verification:** `python -c "from core.reliability import FallbackChain, get_fallback_chain, select_model, classify_complexity, check_provider_health, record_rate_limit, get_all_provider_status, reset_provider_health, get_recovery, RequestThrottle; print('core.reliability OK')"`

---

## SUBTASK 3: core/orchestration/__init__.py — Add docstring
**Priority:** P2
**ADR:** ADR-052
**File:** `/home/newadmin/swarm-bot/core/orchestration/__init__.py`

Add docstring only (files exist in this dir):
```python
"""Orchestration subsystem — supervisor and swarm patterns."""
```

**Verification:** `python -c "import core.orchestration; print(core.orchestration.__doc__)"`
Expected: "Orchestration subsystem — supervisor and swarm patterns."

---

## SUBTASK 4: core/optimization/__init__.py — Add docstring
**Priority:** P2
**ADR:** ADR-052
**File:** `/home/newadmin/swarm-bot/core/optimization/__init__.py`

Add docstring only:
```python
"""Optimization subsystem — usage tracking and feedback learning."""
```

**Verification:** `python -c "import core.optimization; print(core.optimization.__doc__)"`
Expected: "Optimization subsystem — usage tracking and feedback learning."

---

## SUBTASK 5: core/utils/__init__.py — Add docstring
**Priority:** P2
**ADR:** ADR-052
**File:** `/home/newadmin/swarm-bot/core/utils/__init__.py`

Add docstring only:
```python
"""Utility functions — formatters, UI helpers, multimodal processing."""
```

**Verification:** `python -c "import core.utils; print(core.utils.__doc__)"`
Expected: "Utility functions — formatters, UI helpers, multimodal processing."

---

## SUBTASK 6: core/tools/__init__.py — Add docstring
**Priority:** P2
**ADR:** ADR-052
**File:** `/home/newadmin/swarm-bot/core/tools/__init__.py`

Add docstring only:
```python
"""Tool agents — computer control, Playwright browser automation, VSCode bridge."""
```

**Verification:** `python -c "import core.tools; print(core.tools.__doc__)"`
Expected: "Tool agents — computer control, Playwright browser automation, VSCode bridge."

---

## SUBTASK 7: prompts/__init__.py — Add docstring
**Priority:** P2
**ADR:** ADR-052
**File:** `/home/newadmin/swarm-bot/prompts/__init__.py`

Add docstring only:
```python
"""Prompt templates and message builders."""
```

**Verification:** `python -c "import prompts; print(prompts.__doc__)"`
Expected: "Prompt templates and message builders."

---

## SUBTASK 8: swarms_bot/agents/__init__.py — Add docstring
**Priority:** P3
**ADR:** ADR-052
**File:** `/home/newadmin/swarm-bot/swarms_bot/agents/__init__.py`

Update the existing single-line docstring to be more descriptive. Current is: `"""Specialized agent implementations."""`

Keep as-is since it's already a docstring. Mark complete.

---

## FINAL VERIFICATION

After all tasks complete, run:
```bash
python -c "import handlers; import core; import skills; import bridges; import swarms_bot; import computer_agent; import config; print('all OK')"
```

And specifically test bridges exports:
```bash
python -c "from bridges import WhatsAppBridge, ScreenpipeBridge, DiscordBridge, LiveKitBridge, MastraBridge, RufloBridge; print('bridges exports OK')"
```

And reliability:
```bash
python -c "from core.reliability import FallbackChain, get_fallback_chain, select_model, classify_complexity, check_provider_health, RequestThrottle; print('reliability OK')"
```