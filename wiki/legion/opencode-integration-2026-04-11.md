# LEGION × OPENCODE INTEGRATION — 2026-04-11
_Last updated: 2026-04-11 by WikiBot_

## Summary
Three-agent pipeline (Planner → Worker → Reviewer) successfully integrated opencode CLI
into Legion's Telegram bot, enabling autonomous task execution via `/opencode` command.
All 276 tests pass, ruff clean.

## Architecture
```
[Telegram] → [/opencode handler] → [build_opencode_prompt()]
  → [run_opencode_task()] → [opencode CLI subprocess]
  → [extract_report()] → [Telegram report]
```

## Files Created/Modified

| File | Action | Lines |
|------|--------|-------|
| LEGION_MASTER_PROMPT.md | Created | 714 |
| core/opencode_bridge.py | Created | 77 |
| handlers/dev.py | Modified | +39 |
| handlers/shared.py | Modified | +2 |
| main.py | Modified | +1 |
| .wiki/decisions/ADR-001-opencode-integration.md | Created | — |
| .wiki/logs/2026-04-11-opencode-integration.md | Created | — |

## Bridge Module — core/opencode_bridge.py

### Functions

**`build_opencode_prompt(telegram_msg, project, user) -> str`**
Wraps user instruction in Legion master prompt context with timestamp and project.

**`run_openopencode_task(prompt, project_dir, agent, model, timeout) -> str`**
Async subprocess execution via `asyncio.create_subprocess_exec()`.
- Default timeout: 1800s (30 min)
- Default model: `LEGION_DEFAULT_MODEL` env var or `openrouter/anthropic/claude-sonnet-4-5`
- Zombie process prevention: `await process.wait()` after `kill()` and on error

**`extract_report(opencode_output) -> str`**
Parses output for `━━━━━━━━━━━━━━━━━━━━━━━━━━━` marker, returns last 4000 chars.

## /opencode Command Handler

Location: `handlers/dev.py` lines 181-219

```python
@router.message(Command("opencode"))
async def cmd_opencode(msg: Message) -> None:
```

Flow:
1. Check `is_allowed(msg)`
2. Extract task text after `/opencode`
3. Show typing indicator + status message
4. Call `build_opencode_prompt()` → `run_openopencode_task()`
5. Extract report with `extract_report()`
6. Send chunked response to Telegram

## Reviewer Findings Fixed

| Issue | Severity | Fix |
|-------|----------|-----|
| Unused `subprocess` import | MEDIUM | Removed |
| Unused `Any` import | MEDIUM | Removed |
| Missing `await process.wait()` after `kill()` | MEDIUM | Added `await process.wait()` |
| Missing `await process.wait()` on error path | MEDIUM | Added `await process.wait()` |

## Next Steps

- [ ] Start opencode server: `opencode serve --port 4096 &`
- [ ] Verify server: `curl http://localhost:4096/health`
- [ ] Create opencode agents: `opencode agent create` for researcher, coder, reviewer, wikibot, devops
- [ ] Test `/opencode list files` (safe read-only task)
- [ ] Add opencode server startup to bot's on_startup() if not already there

## Related Pages

- [[conversations_log]]
