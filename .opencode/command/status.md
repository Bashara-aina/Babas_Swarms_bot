---
allowed-tools: Read,Bash,Grep,Glob
argument-hint: [scope]
description: "Show current project status. Without args: overview. With scope: detailed status."
---

# /status — Project status

Show current project state, recent changes, and health metrics.

## Usage
```
/status
/status handlers/
/status tests/
/status --verbose
```

## Status Overview
```
## PROJECT
swarm-bot — Python Telegram bot with aiogram 3.x

## GIT
- Branch: main
- Last commit: <hash> <message>
- Changes: N files changed

## RECENT_CHANGES
<last 3 commits>

## TEST_HEALTH
- Last run: <timestamp>
- Passed: N / Failed: N
- Coverage: <X>%

## SERVICE_STATUS
- swarm-bot: running
- Last restart: <timestamp>
```

## Detailed Status (handlers)
```
## HANDLERS
Total: 45 handlers
By category:
- AI: handlers/ai.py
- Dev: handlers/dev.py
- Research: handlers/research.py
...

## RECENT_MODIFICATIONS
- handlers/ai.py — 2 days ago
- core/intent_router.py — 5 days ago
```

## Swarm-Bot Health Checks
```bash
# Service status
sudo systemctl status swarm-bot

# Recent logs
journalctl -u swarm-bot -n 20 --no-pager

# Test health
pytest tests/ -x --asyncio-mode=auto -q --tb=short
```

## Output
- Clean, scannable format
- Color-coded status indicators
- Actionable next steps if issues found
