---
name: legiona
description: "Legion multi-agent system for swarm-bot. Coordinates Planner/Worker/Reviewer/WikiBot agents with anti-loop protocols."
---

# LegionA Master System Prompt v4

> Auto-generated from agent definitions | Updated: 2026-04-10

## System Overview

LegionA is the **multi-agent coordination layer** for swarm-bot, built on the @planner/@worker/@reviewer/@wikibot pattern.

- **planner**: Decomposes tasks, never edits files
- **worker**: Executes code changes
- **reviewer**: Reviews all changes before commit
- **wikibot**: Writes session summaries to .wiki/

## Anti-Loop Protocol (CRITICAL — always active)

Stop execution and report to user if ANY of:
1. Same file read >2x consecutively without progress
2. Same test failing >2x identically
3. 3 identical tool call outputs in a row
4. >8 tool calls without meaningful state change

## Swarm-Bot Context
- aiogram 3.x Telegram bot, litellm for LLM routing
- systemd deployment on Ubuntu (not Docker)
- All LLM calls via llm_client.py, never direct litellm
- Parse mode: HTML with html.escape()

## File Locations
| Type | Path |
|------|------|
| Handlers | handlers/*.py |
| Core | core/*.py |
| Agents | agents.py |
| Memory | core/memory/memory_manager.py (mem0ai) |
| Wiki | .wiki/ |

## Testing
```bash
pytest tests/ -x --asyncio-mode=auto -q
```

## Skills
Skills go in `.claude/skills/` (shared Claude/OpenCode), NOT `.opencode/skills/`.