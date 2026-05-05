---
title: adr-2026-04-11-opencode-integration
type: decision
status: accepted
tags: [opencode, integration, legion]
created: 2026-04-11
updated: 2026-04-11
summary: Initial decision to integrate OpenCode CLI into Legion's Telegram interface for autonomous task execution.
wikilinks:
  - [[entities/opencode]]
  - [[projects/legion-bot]]
confidence: high
source: decision
---

# ADR: OpenCode Integration

**Date**: 2026-04-11  
**Status**: ACCEPTED

## Context

Legion needed autonomous code execution capability beyond simple command running. OpenCode provides:
- Full agent pipeline (Plan → Build → Review → Test → Commit)
- Server mode for long-running tasks
- CLI interface for Telegram integration

## Decision

1. Create bridge module: `core/opencode_bridge.py`
2. Add `/opencode` command handler
3. Create `LEGION_MASTER_PROMPT.md` as operational prompt
4. Wire via `BotCommand` registration

## Files Changed

- `core/opencode_bridge.py` — new (77 lines)
- `handlers/dev.py` — +45 lines
- `handlers/shared.py` — +2 lines
- `main.py` — +1 BotCommand

## Consequences

- Legion can delegate complex coding tasks
- Requires opencode server running
- Default model: `openrouter/anthropic/claude-sonnet-4-5`

## Related Pages

- [[entities/opencode]] — OpenCode entity
- [[projects/legion-bot]] — Legion project
