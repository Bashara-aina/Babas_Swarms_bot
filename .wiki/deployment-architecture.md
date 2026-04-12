---
title: deployment-architecture
domain: deployment-cicd
impact_score: 8
last_updated: 2026-04-12
injects_into: system
tokens_estimated: 520
---

# Deployment Architecture

## ONE-LINE SUMMARY
Legion runs as a systemd service with a 10s auto-restart on failure, parallel startup orchestration, and 4-layer health monitoring (feature flags, HTTP endpoint, sidecar probes, heartbeat daemon).

## FACTS

### systemd Service (`scripts/legion.service`)
- **Type**: simple — systemd forks the process directly, no PID file needed
- **User**: newadmin (non-root)
- **WorkingDirectory**: /home/newadmin/swarm-bot
- **EnvironmentFile**: /home/newadmin/swarm-bot/.env (loaded before bot starts)
- **ExecStart**: /home/newadmin/swarm-bot/venv/bin/python main.py
- **Restart policy**: Restart=on-failure, RestartSec=10s
- **Logging**: StandardOutput=journal, StandardError=journal (systemd journal only, no file)
- **Resource limits**: CPUQuota=80%, MemoryMax=4G
- **Wants**: network-online.target (waits for network before starting)

### Startup Sequence (main.py `on_startup`)
**Group A** (parallel, 30s timeout):
1. observability init (AgentOps optional)
2. humanization layer (soul engine v6)
3. agent registry YAML load (76 agents)
4. personality state (Letta)
5. MemoryOS client
6. n8n webhook listener
7. proactive monitors
8. ProactiveScheduler
9. CuriosityEngine
10. voice engine prewarm
11. gemma4 local prep
12. DailyHarvesterScheduler
13. WikiQualityScheduler
14. lifecycle hooks registration

**Group B** (sequential after Group A):
15. SQLite persistence init (legion.db)
16. TaskScheduler
17. Memory DB init
18. Conversation history DB init (SQLite)
19. Session transcript store init

**Group C** (fire-and-forget create_task):
20. Supabase skill bootstrap
21. Daily briefing at 07:30
22. Nightly capability report at 03:40
23. Nightly memory consolidation at 02:00
24. Daily GitHub intel at 09:00
25. ProactiveInitiator + ProactiveEngine
26. Screenpipe bridge (conditional on SCREENPIPE_ENABLED=1)
27. ruflo sidecar launch + health probe
28. opencode sidecar launch + health probe
29. swarms_bot enterprise layer init

### Health Check Layers
1. **Feature flag check** (`core/health_check.py`): run_health_check() validates pip packages, env vars, Ollama models, ruflo server.js exists — fires before polling starts
2. **HTTP health endpoint** (`core/health.py`): GET /health → {"status":"ok","bot":"@LegionBot"} on port 8080 (not started by default in current main.py)
3. **Sidecar probes** (main.py startup): _wait_for_ruflo_health(7834), _wait_for_opencode_health(4096) — 8 attempts × 0.5s = 4s max
4. **Background monitor** (`core/ruflo_manager.py`): ruflo_health_monitor() pings /health every 5 minutes
5. **Heartbeat daemon** (`core/heartbeat/daemon.py`): checks `systemctl is-active swarm-bot` every 30 min during active hours (9AM–11PM JST)

### Sidecar Management
- **ruflo** (`tools/ruflo/server.js`): launched via subprocess.Popen if OPENROUTER_API_KEY or ANTHROPIC_API_KEY set; health probe on startup; background 5-min monitor
- **opencode**: launched via subprocess.Popen unconditionally; health probe on startup

### Required Environment Variables
- TELEGRAM_BOT_TOKEN (required, checked at import time)
- ALLOWED_USER_ID or BASHARA_TELEGRAM_ID (required)
- Optional: OPENROUTER_API_KEY, ANTHROPIC_API_KEY (enable ruflo), SCREENPIPE_ENABLED, SCREENPIPE_PROACTIVE_ENABLED, AGENTOPS_API_KEY, PROACTIVE_MIN_INTERVAL_SEC

## LEGION BEHAVIOR RULES
1. Legion must not start if TELEGRAM_BOT_TOKEN or ALLOWED_USER_ID is missing — RuntimeError raised at import time
2. All Group A startup failures are non-fatal (wrapped in try/except with logger.warning)
3. ruflo sidecar launch failures are non-fatal — bot continues without it
4. opencode sidecar launch failures are non-fatal — bot continues without it
5. Health probe timeouts (4s total) do not block bot startup — sidecars may be unhealthy at boot
6. Heartbeat daemon only runs during active hours (9AM–11PM JST)
7. Resource limits: bot cannot exceed 80% CPU or 4GB RAM under systemd
8. Bot logs to systemd journal only when run via systemd — no separate log file in that mode

## EXAMPLES
Bashara restarts bot after adding a new API key:
Legion (with systemd): `systemctl restart legion` → 10s later bot is back online with new key loaded from .env
Legion (without): Would need to manually kill and restart python process

Bashara checks if bot is healthy:
Legion (with health endpoint): `curl http://localhost:8080/health` → {"status":"ok","bot":"@LegionBot"}
Legion (without): Must check `systemctl status legion` and read journalctl

## ANTI-PATTERNS
1. Restart storms: Restart=on-failure without RestartSec=10 would cause tight restart loops on persistent errors
2. Blocking health probes: If ruflo/opencode never come up, 4s startup delay adds to boot time
3. Silent sidecar death: ruflo_health_monitor logs warnings but does not restart the sidecar — ruflo must die silently
4. No /health endpoint started by default: core/health.py exists but start_health_server() is never called in main.py

## GAPS
1. **No /health HTTP server started by default** — uptime monitors cannot hit it
2. **No automatic sidecar restart** — ruflo death only logged, not recovered
3. **No startup timeout watchdog** — Group A has 30s timeout but Group B/C have no overall timeout
4. **No graceful SIGTERM handling** — on_shutdown cancels tasks but no final flush of bot.log
5. **Resource limits hardcoded in service file** — cannot change without editing .service file
6. **No pre-start validation** — bot starts even if Ollama is down or Supabase is unreachable

## DEBATE RECORD
Advocate: 8 | Skeptic: 6 | Judge: WRITE 8
Judge note: Solid systemd setup with correct restart policy but health endpoint not wired up and no sidecar auto-recovery.
