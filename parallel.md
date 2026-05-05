# Parallel Agent Execution

For parallel execution of multiple agents in swarm-bot, the system uses Symphony's Linear-backed orchestration (see `WORKFLOW.md`).

## Quick Reference

- **Parallel tasks**: use `/orchestrate` command in Telegram
- **Worktree parallelism**: for true multi-session parallel work, use `git worktree`
- **Symphony server**: `mcp_servers.symphony_server` — coordinate multiple OpenCode/Claude Code sessions via Linear

## State File Protocol (`/tmp/`)

| File | Purpose |
|------|---------|
| `/tmp/legion_bot.pid` | Single-instance lock (PID of running bot) |
| `/tmp/legion_session_context.txt` | Hot-tier session context |
| `/tmp/legion_*.txt` | Per-feature hot tier state |

## See Also

- [WORKFLOW.md](WORKFLOW.md) — agent definitions and workflow
- [CLAUDE.md](CLAUDE.md) — full project context