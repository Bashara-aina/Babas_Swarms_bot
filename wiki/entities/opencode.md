---
title: opencode
type: entity
status: active
tags: [agent, coding, cli, autonomous]
created: 2026-04-13
updated: 2026-04-13
summary: OpenCode is a CLI agent system for autonomous code tasks, integrated with Legion via core/opencode_bridge.py.
wikilinks: [[projects/legion-bot.md], [architecture/legion-module-map.md]]
confidence: high
source: implementation
---

# OpenCode

## TL;DR
OpenCode is an autonomous coding agent accessed via CLI that Legion uses for complex code tasks, wired through the three-agent pipeline.

## Integration Architecture

```
[Telegram /opencode] → [handlers/dev.py] → [core/opencode_bridge.py]
    → [opencode CLI subprocess] → [extract_report()] → [Telegram]
```

## Commands

| Command | Description |
|---------|-------------|
| `opencode serve --port 4096` | Start server |
| `opencode agent create` | Create new agent |
| `opencode run <task>` | Execute task |

## Key Files

- `core/opencode_bridge.py` — Bridge module
- `handlers/dev.py` — Handler (lines 181-219)
- `LEGION_MASTER_PROMPT.md` — Master prompt for opencode

## Related Pages

- [[projects/legion-bot.md]] — Main project
- [[architecture/legion-module-map.md]] — System architecture
