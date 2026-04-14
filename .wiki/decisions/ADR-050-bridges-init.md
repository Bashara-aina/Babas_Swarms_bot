---
title: Adr 050 Bridges Init
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
# ADR-050: bridges Package — Missing `__init__.py`

**Date:** 2026-04-12
**Status:** Accepted
**Decider:** @planner

## Context

The `bridges/` directory contains bridge modules (whatsapp_bridge, screenpipe_bridge, discord_bridge, livekit_bridge, mastra_bridge, ruflo_bridge) but lacks an `__init__.py`, making `import bridges` return an empty namespace with no re-exports.

Callers use direct imports (`from bridges.whatsapp_bridge import WhatsAppBridge`) which work, but the package itself has no public API surface.

## Decision

Create `bridges/__init__.py` that re-exports all bridge classes as the official public API:

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

## Consequences

- `import bridges` will expose all bridge classes
- Existing direct imports (`from bridges.whatsapp_bridge import ...`) continue to work unchanged
- New code can use `from bridges import WhatsAppBridge` as a shorter import

## Implementation

Assign to @worker — see AUDIT 11 subtask list.