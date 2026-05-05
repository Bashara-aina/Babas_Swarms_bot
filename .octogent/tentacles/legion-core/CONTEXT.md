# Legion Core — Bot Engine & Swarm Orchestration

The central nervous system of the Legion stack. This tentacle owns the Telegram
bot, swarm agent routing, tool registration, scheduler, and the overall
Babas_Swarms_bot codebase health.

## What this area owns
- main.py / bot.py — Telegram bot entrypoint
- tools/ directory — all Legion-callable tool modules
- tools/autonomous_loop.py — the main agent loop
- tools/briefing.py — daily briefing system
- tools/scheduler.py or equivalent — APScheduler jobs
- .env — environment configuration
- requirements.txt — Python dependencies

## Important files
- CLAUDE.md — OpenCode context for Legion (do not delete or overwrite)
- AGENTS.md — agent routing rules (do not delete or overwrite)
- tools/__init__.py — tool registry

## What already exists (do not break)
- Hermes agent integration (tools/mirofish submodule + Hermes MCP)
- market_intel.py bridge (MiroFish × Legion)
- browser_agent.py, arxiv.py, citation.py — research tools
- agentops_client.py — observability

## Constraints
- Python 3.11+
- All async — never introduce sync blocking calls
- NEVER modify tools/mirofish/ (it is a git submodule, read-only)
- APScheduler runs on Asia/Jakarta timezone
- Telegram bot token in .env as TELEGRAM_BOT_TOKEN

## Active bot commands to maintain
- /start, /help, /status — core
- /market, /signal, /simulate — MiroFish market intel
- /brief — morning briefing
- /research — academic search via arxiv + Hermes
- /goal, /goal_status, /goal_stop, /goal_evolve — autonomous delivery (Meta-Harness + RecursiveMAS)

## /goal System (v2 — Meta-Harness + RecursiveMAS)
Grounded in [1] Meta-Harness (arXiv:2603.28052) + [2] RecursiveMAS (arXiv:2604.25917)

Key insight: Full execution traces >> scalar scores. "Scores Only" = 34.6 median accuracy.
"Full traces" = 50.0 median accuracy. The harness around the model matters.

Architecture:
  Telegram /goal
  → goal_planner.py (Claude decomposes → PLAN.md, logs traces)
  → goal_runner.py (RecursiveMAS: mini-SWE-agent per task, latent state transfer)
  → goal_auditor.py (full audit: pytest + ruff + bandit + git sanity)
  → GitHub PR auto-opened
  → goal_harness_proposer.py (Meta-Harness outer loop: reads traces, evolves harness)

Harness evolution loop:
  .goal/harnesses/current/harness.py (H_0 initial)
  → after each /goal run: traces logged to .goal/traces/<goal_id>/
  → ./scripts/evolve_harness.sh OR /goal_evolve → goal_harness_proposer.py (Claude Opus)
  → proposes improved H_{n+1} based on raw trace analysis
  → best harnesses tracked in .goal/harnesses/pareto_frontier/

Key files:
- tools/goal_planner.py — goal decomposition via Claude
- tools/goal_runner.py — RecursiveMAS orchestrator (latent state across tasks)
- tools/goal_auditor.py — end-to-end audit + Pareto scoring
- tools/goal_harness_proposer.py — Meta-Harness outer loop (Claude Opus reads traces)
- .goal/harnesses/current/harness.py — the evolving harness (H_0, H_1, ...)
- scripts/goal_daemon.sh — CLI runner (no Telegram needed)
- scripts/evolve_harness.sh — trigger harness evolution

Critical constraints:
- mini-sWE-agent is bash-only (no function calling)
- Every prompt must be 100% self-contained (zero memory between tasks)
- Log FULL traces not summaries (Meta-Harness key insight)
- HARNESS_VERSION increments each evolution
- Only Bashara's Telegram user ID in TELEGRAM_AUTHORIZED_USER_ID

<!-- octogent:suggested-skills:start -->
<!-- octogent:suggested-skills:end -->