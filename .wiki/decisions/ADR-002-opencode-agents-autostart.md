# ADR-002: OPENCODE AGENTS + AUTOSTART

**Date**: 2026-04-11
**Status**: ACCEPTED
**Author**: Bashara (via three-agent pipeline)

## Context

Legion needs persistent opencode agents for specialized roles (researcher, coder,
reviewer, wikibot, devops) and the opencode server should auto-start with the bot
to avoid cold-boot latency on every Telegram-triggered task.

## Decision

### 1. Create 5 opencode agents

| Agent | File | Purpose |
|-------|------|---------|
| researcher | `research-agent.md` | Read-only research, find info, bullet reports |
| coder | `focused-implementer.md` | Implement exactly what architect specifies |
| reviewer | `diff-analyzer.md` | Code review with severity levels |
| wikibot | `paper-wiki-writer.md` | POPW research wiki documentation |
| devops | `deployment-engineer.md` | Git, Vercel, Docker, CI/CD, migrations |

**Model**: `minimax-coding-plan/MiniMax-M2.7` (set in YAML frontmatter of each agent)

### 2. Wire opencode serve into bot startup

Add to `main.py` `on_startup()`:
- `_opencode_health_probe_sync()` — HTTP health check to port 4096
- `_wait_for_opencode_health()` — async wait loop with retry
- Startup block following ruflo sidecar pattern (non-fatal, warning-only on failure)

## Files Changed

| File | Action |
|------|--------|
| `.opencode/agent/research-agent.md` | Created |
| `.opencode/agent/focused-implementer.md` | Created |
| `.opencode/agent/diff-analyzer.md` | Created |
| `.opencode/agent/paper-wiki-writer.md` | Created |
| `.opencode/agent/deployment-engineer.md` | Created |
| `main.py` | Modified (+38 lines) |

## Reviewer Findings

- **HIGH**: Missing `model:` field in agent YAML frontmatter — fixed

## Consequences

- opencode agents available via `opencode run --agent <name>`
- opencode server auto-starts with bot on port 4096
- If opencode serve fails, bot continues (non-fatal startup)
