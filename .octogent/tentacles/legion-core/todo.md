# Todo

## /goal System
- [x] Implement /goal v2 with Meta-Harness + RecursiveMAS
- [x] Set TELEGRAM_AUTHORIZED_USER_ID in .env (find via @userinfobot)
- [ ] Run first real /goal: "/goal Write unit tests for tools/goal_auditor.py"
- [ ] Verify PR gets opened automatically after goal completion
- [ ] Run 3+ goals then execute ./scripts/evolve_harness.sh to improve harness

## /goal Evolved Commands
- [ ] /goal_evolve -- run Meta-Harness proposer (Claude Opus reads all traces, proposes H_{n+1})
- [ ] After 5+ goals: check Pareto frontier in .goal/harnesses/pareto_frontier/

## Remaining
- [ ] Verify bot starts cleanly after all integrations (hermes + mirofish)
- [ ] Add /octogent command to Telegram that shows current agent status
- [ ] Add error recovery: auto-restart on unhandled exceptions with Telegram alert
- [ ] Write tools/health_check.py — checks all services (MiroFish, Hermes, Redis)
- [ ] Add rate limiting to all Telegram commands (cooldown per user)
- [ ] Implement tools/session_bridge.py — lets Octogent terminals send results back to Telegram
- [ ] Add daily 23:00 WIB digest: summarize all tool calls made that day
- [ ] Update CLAUDE.md to include Octogent tentacle IDs for routing context