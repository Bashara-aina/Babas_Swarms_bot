---
title: adr-2026-04-12-opencode-over-cursor-for-backend
type: decision
status: accepted
tags: [opencode, cursor, backend, decision]
created: 2026-04-12
updated: 2026-04-12
summary: OpenCode was selected over Cursor for backend coding tasks due to superior CLI integration and Telegram workflow compatibility.
wikilinks: [[opencode]], [[cursor]]
confidence: high
source: decision
---

# ADR: OpenCode Over Cursor for Backend

**Date**: 2026-04-12  
**Status**: ACCEPTED

## Context

Legion needed a coding agent for autonomous backend tasks. Two candidates were evaluated:
- **OpenCode**: CLI-first, server-mode, Telegram-compatible
- **Cursor**: IDE-first, GUI-based, limited CLI

## Decision

Select **OpenCode** for all backend coding tasks.

## Reasoning

| Criteria | OpenCode | Cursor |
|-----------|----------|--------|
| CLI access | ✅ Full | ❌ Limited |
| Telegram integration | ✅ Direct | ❌ None |
| Agent pipeline | ✅ Built-in | ✅ Agent mode |
| Self-hosted | ✅ | ✅ |
| Context window | ✅ Streaming | ✅ |

## Consequences

### Positive
- Direct Telegram integration via `/opencode` command
- Full CLI control
- Server mode for background tasks

### Negative
- Learning curve for new users
- Less visual debugging

## Implementation

- Created `core/opencode_bridge.py`
- Added `/opencode` handler in `handlers/dev.py`
- Master prompt: `LEGION_MASTER_PROMPT.md`

## Related Pages

- [[opencode]] — OpenCode integration
- [[cursor]] — Alternative not selected
