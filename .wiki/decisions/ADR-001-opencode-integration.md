---
title: Adr 001 Opencode Integration
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
summary: '**Author**: Bashara (via three-agent pipeline)'
wikilinks: []
confidence: medium
source: research
---
# ADR-001: LEGION × OPENCODE INTEGRATION

**Date**: 2026-04-11
**Status**: ACCEPTED
**Author**: Bashara (via three-agent pipeline)

## Context

Legion needs to integrate with opencode CLI to enable autonomous task execution
via Telegram. The integration enables the full pipeline: Plan → Build → Review →
Test → Commit → Report via opencode's agent system.

## Decision

1. **Master prompt**: Create `LEGION_MASTER_PROMPT.md` in repo root as the
   operational prompt loaded by Legion on every Telegram-triggered opencode task.

2. **Bridge module**: Create `core/opencode_bridge.py` implementing:
   - `build_opencode_prompt()` — constructs the full prompt with context
   - `run_opencode_task()` — async execution via `opencode run`
   - `extract_report()` — parses LEGION TASK COMPLETE block from output

3. **Handler integration**: Add `/opencode` command to `handlers/dev.py` that
   routes user tasks through the bridge to opencode CLI.

4. **Command registration**: Add `BotCommand(command="opencode", ...)` to
   main.py's command list.

5. **Shared state**: Expose `_opencode_bridge` via `handlers/shared.py` for
   future use by other handlers.

## Files Changed

- `LEGION_MASTER_PROMPT.md` — new (5000+ line master prompt)
- `core/opencode_bridge.py` — new (77 lines)
- `handlers/dev.py` — modified (+45 lines for /opencode handler)
- `handlers/shared.py` — modified (+2 lines for _opencode_bridge)
- `main.py` — modified (+1 BotCommand)

## Consequences

- Legion can now delegate tasks to opencode with full pipeline execution
- opencode server must be running (`opencode serve --port 4096`)
- Default model: `openrouter/anthropic/claude-sonnet-4-5` (configurable via
  `LEGION_DEFAULT_MODEL` env var)
