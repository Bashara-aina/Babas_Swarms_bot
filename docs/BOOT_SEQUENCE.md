# Legion Bot — Boot Sequence

> How Legion starts up, initializes all subsystems, and becomes ready to serve.

---

## Startup Methods

### Method 1: systemd Service (Production)

File: `scripts/legion.service`

```ini
[Unit]
Description=Legion AI Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=newadmin
WorkingDirectory=/home/newadmin/swarm-bot
EnvironmentFile=/home/newadmin/swarm-bot/.env
ExecStart=/home/newadmin/swarm-bot/venv/bin/python main.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=legion-bot
CPUQuota=80%
MemoryMax=4G

[Install]
WantedBy=multi-user.target
```

Install and enable:
```bash
sudo cp scripts/legion.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable legion.service
sudo systemctl start legion.service
```

### Method 2: Watchdog (Zero-Downtime Upgrades)

File: `scripts/start_with_watchdog.sh`

```bash
#!/bin/bash
# Start Legion with watchdog for auto-restart on crash or upgrade
python core/watchdog.py &
WATCHDOG_PID=$!
echo $WATCHDOG_PID > data/.watchdog.pid
```

The watchdog (`core/watchdog.py`) monitors the bot process and restarts it automatically. Use this instead of `python main.py` for zero-downtime deployments.

### Method 3: Direct Execution (Development)

```bash
python main.py
# or with make:
make run
```

---

## Boot Sequence (main.py)

### Phase 0: Environment Loading

```
main.py import
  → load_dotenv(Path(__file__).parent / ".env")
  → verify TELEGRAM_BOT_TOKEN and ALLOWED_USER_ID are set
  → RuntimeError if missing → bot does not start
```

### Phase 1: Core Imports

```python
import agents           # Agent registry (76 agents, 9 departments)
import computer_agent   # Desktop control agent
import handlers         # Handler package
import handlers.shared  # Shared state (ALLOWED_USER_ID, _start_time)
from handlers import register_all_routers
from llm_client import verify_api_keys, init_humanization_layer
from core.daily_harvester.scheduler import DailyHarvesterScheduler
from core.health_check import FEATURE_FLAGS, print_health_report, run_health_check
from core.observability import init_observability
from core.wiki_scheduler import WikiQualityScheduler
```

### Phase 2: Bot & Dispatcher Initialization

```python
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
dp.message.middleware(ActivityLogMiddleware())  # Logs all inbound Telegram messages
register_all_routers(dp)  # Registers 38 routers in specific order
```

### Phase 3: on_startup() — Full Initialization

The `on_startup()` async function is called by aiogram when the bot connects. It initializes all subsystems in three groups:

#### Group A: Parallel Initialization (30s timeout)

All of these run concurrently via `asyncio.gather`:

| Task | What it does |
|------|-------------|
| `_start_observability()` | Initialize observability/metrics |
| `_start_humanization()` | Load memory + emotion state for humanized responses |
| `_start_registry()` | Load 76 agents from `config/departments.yaml` |
| `_start_personality()` | Initialize personality state from `tools.letta_personality` |
| `_start_memoryos()` | Initialize MemoryOS hierarchical memory tiers |
| `_start_n8n()` | Start n8n webhook listener |
| `_start_monitors()` | Start proactive monitors (GPU, site health, etc.) |
| `_start_proactive_scheduler()` | Start ProactiveScheduler (daily briefing, business checks) |
| `_start_curiosity_engine()` | Start curiosity loop (Legion initiates contact) |
| `_start_voice_prewarm()` | Pre-warm voice engine |
| `_start_gemma4_prep()` | Ensure gemma4 local model available via Ollama |
| `_start_daily_harvester()` | Start DailyHarvesterScheduler |
| `_start_wiki_quality_scheduler()` | Start WikiQualityScheduler |
| `_register_lifecycle_hooks()` | Register builtin hooks + observation queue |

#### Group B: Sequential Initialization (after Group A completes)

| Task | What it does |
|------|-------------|
| init_db() | Initialize SQLite persistence DB |
| TaskScheduler.start() | Start task scheduler |
| start_legiona_scheduler() | Start Legiona autonomous maintenance scheduler |
| init_memory_db() | Initialize memory database |
| `_init_conv_db()` | Initialize conversation history DB (SQLite-backed) |
| get_transcript_store().init() | Initialize session transcript store |

#### Group C: Fire-and-Forget Tasks

These are scheduled via `asyncio.create_task()`:

| Task | Schedule |
|------|----------|
| `_bootstrap_supabase_skill()` | On startup (weekly regeneration) |
| `schedule_nightly_capability_report()` | Daily at 03:40 AM |
| `_run_memory_consolidation_nightly()` | Daily at 02:00 AM |
| `_run_memory_consistency_weekly()` | Monday at 03:00 AM |
| `_run_github_intel_daily()` | Daily at 09:00 AM |
| `start_proactive_initiator()` | On startup |
| `run_proactive_loop()` | Continuous monitoring loop |
| Screenpipe monitor | Conditional on `SCREENPIPE_ENABLED=1` |

### Phase 4: Sidecar Processes

#### ruflo (OpenRouter / Anthropic proxy)
```python
if os.getenv("OPENROUTER_API_KEY") or os.getenv("ANTHROPIC_API_KEY"):
    subprocess.Popen(["node", "tools/ruflo/server.js"])
    _wait_for_ruflo_health()  # probe at 127.0.0.1:7834/health
    _ruflo_restart_monitor()   # background loop → restart if dies
```

#### opencode (CLI agent)
```python
subprocess.Popen(["opencode", "serve", "--port", "4096"])
_wait_for_opencode_health()
```

### Phase 5: Server Processes

| Server | Port | Purpose |
|--------|------|---------|
| Health endpoint | 8080 | `GET /health` → `200 {"status": "ok"}` for uptime monitors |
| Webhook server | dynamic | GitHub PR merges, system alerts |
| MCP servers | dynamic | Brave, GitHub, Filesystem, Obsidian, Supabase, Browser |

### Phase 6: Telegram Commands Registration

```python
await bot.set_my_commands([
    BotCommand(command="do", description="Autonomous computer control"),
    BotCommand(command="autopilot", description="Vision-action loop"),
    BotCommand(command="screen", description="Take desktop screenshot"),
    BotCommand(command="run", description="LLM chat (no computer)"),
    BotCommand(command="cmd", description="Run shell command"),
    # ... 60+ total commands
])
```

### Phase 7: Start Polling

```python
await dp.start_polling(bot, ...)


async def main():
    await on_startup(bot)  # full init
    await dp.start_polling(bot, ...)  # begin receiving Telegram updates

if __name__ == "__main__":
    asyncio.run(main())
```

---

## LEGION BOOT Health Checks

On startup, `run_legion_boot_health(bot)` probes all subsystems:

| Check | Critical? | On Failure |
|-------|-----------|-----------|
| Telegram API | ✅ YES | Bot refuses to start |
| LLM (primary model) | ✅ YES | Bot refuses to start |
| ChromaDB | No | "unavailable (memory degraded)" |
| .wiki/ directory | No | Warning logged |
| data/ directory | No | Warning logged |
| VoiceVox | No | "not running (voice mode disabled)" |
| DuckDuckGo search | No | Warning logged |

---

## Graceful Shutdown

SIGTERM / SIGINT handlers set `_shutdown_flag = True`. The bot finishes
processing the current request, then exits cleanly.

```python
def _handle_signal(sig, frame):
    global _shutdown_flag
    _shutdown_flag = True
    logger.warning("Received signal %d — graceful shutdown initiated", sig)

signal.signal(signal.SIGTERM, _handle_signal)
signal.signal(signal.SIGINT, _handle_signal)
```

---

## Watchdog Process (core/watchdog.py)

The watchdog is a separate Python process that:
1. Launches `main.py` as a child process
2. Monitors for crashes or upgrade signals
3. Restarts the bot with <3 second Telegram connection gap
4. Stores its PID in `data/.watchdog.pid`

Use `scripts/start_with_watchdog.sh` to start with watchdog.

---

## Environment Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `TELEGRAM_BOT_TOKEN` | YES | Telegram bot API token |
| `ALLOWED_USER_ID` | YES | Telegram user ID (owner) |
| `BASHARA_TELEGRAM_ID` | alt | Alternative to ALLOWED_USER_ID |
| `LEGION_LLM_MODEL` | no | Override default LLM (default: minimax/MiniMax-M2.7) |
| `OPENROUTER_API_KEY` | no | Enable ruflo sidecar |
| `ANTHROPIC_API_KEY` | no | Enable ruflo sidecar |
| `SCREENPIPE_ENABLED` | no | Enable Screenpipe desktop monitoring |
| `LEGION_GITNEXUS_AUTO_ANALYZE` | no | Auto-refresh GitNexus index on startup |

---

## Startup Verification

After bot starts, check `bot.log` for:
```
🚀 LEGION BOOT — 2026-04-21 HH:MM:SS
✅ Telegram: @your_bot_username
✅ LLM: minimax/MiniMax-M2.7
⚠️ ChromaDB: unavailable (memory degraded)
✅ Wiki: 42 documents loaded
✅ Data: writable
⚠️ VoiceVox: not running (voice mode disabled)
✅ Search: OK
Legion ready. Degraded mode: memory.
```

---

## Common Startup Failures

| Error | Cause | Fix |
|-------|-------|-----|
| `TELEGRAM_BOT_TOKEN not set` | .env missing or variable name wrong | Check .env file |
| `ALLOWED_USER_ID must be set` | .env missing or value = 0 | Set ALLOWED_USER_ID |
| `ruflo sidecar launch failed` | Node.js not installed | `apt install nodejs` or check PATH |
| `opencode serve failed` | opencode CLI not in PATH | Install opencode |
| ChromaDB unavailable | Docker not running | `docker-compose up -d` |
| LLM probe failed | Network or API key issue | Check internet + API keys |