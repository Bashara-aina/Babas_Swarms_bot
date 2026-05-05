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

<!-- octogent:suggested-skills:start -->
<!-- octogent:suggested-skills:end -->