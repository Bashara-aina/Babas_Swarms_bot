---
title: OpenCode
type: entity
status: active
tags: [agent, coding, cli, autonomous]
created: 2026-04-13
updated: 2026-04-13
summary: OpenCode is an autonomous CLI coding agent integrated with Legion via core/opencode_bridge.py. It replaces Cursor for all backend Legion tasks, chosen for its CLI-first design and native Telegram integration. Runs as a subprocess on port 4096.
wikilinks:
  - [[legion-bot]]
  - [[legion-module-map]]
  - [[llm-cost-routing]]
confidence: high
source: implementation
project: legion
---

# OpenCode

## TL;DR
OpenCode is an autonomous CLI coding agent that Legion uses for complex code tasks, wired through `core/opencode_bridge.py`. It replaces Cursor as the selected tool for backend coding, chosen over Cursor for its CLI-first approach and native Telegram integration. The ADR decision is documented in [[adr-2026-04-12-opencode-over-cursor-for-backend]].

## Integration Architecture
```
[Telegram /opencode <task>]
  → handlers/dev.py (lines 181-219)
  → core/opencode_bridge.py
  → opencode serve --port 4096 (subprocess)
  → extract_report() from stdout
  → Telegram response
```

## Server Commands
```bash
opencode serve --port 4096    # Start server (auto-started by main.py)
opencode agent create          # Create new agent definition
opencode run <task>           # Execute task via running server
opencode agents list          # List available agents
```

## Legion's OpenCode Agents
Per `wiki/raw/docs/opencode-external-tools.md`, Legion configures:
- `@coding` — primary code generation agent (uses devstral via openrouter)
- `@reviewer` — code review agent
- `@debug` — error analysis agent

## Key Files
- `core/opencode_bridge.py` — Bridge module: starts/stops server, sends tasks, parses results
- `handlers/dev.py` — `/opencode` command handler (lines 181-219)
- `config/departments.yaml` — Agent definitions for coding, reviewer, debug

## Budget
OpenCode agents use `groq/llama-3.3-70b-versatile` for general tasks and `openrouter/qwen/qwen3-coder:free` for coding-specific tasks (free tier). Cost tracked via BudgetManager.

## Failure Modes
- Server not running: bridge starts it automatically via `subprocess.Popen`
- Task timeout: asyncio.wait_for with 120s timeout on the bridge call
- Malformed report output: returns error message to user

## See Also
[[legion-bot]] — Main project using OpenCode
[[legion-module-map]] — System architecture overview
[[llm-cost-routing]] — Cost optimization for coding tasks
