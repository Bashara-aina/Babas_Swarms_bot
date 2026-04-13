# Legion Self-Upgrade System

## How It Works

```
You (Telegram)            Legion Bot
     |                        |
     |-- /upgrade <request> -->|
     |                        |- LLM generates Python files
     |                        |- ast.parse() syntax check
     |                        |- Safety scan (no eval/exec/rm)
     |<-- "Generating..." --   |
     |                        |- pip install <new deps>
     |                        |- Write files to disk
     |                        |- Hot-reload module OR
     |                        |- Watchdog restarts main.py
     |<-- "✅ Upgrade done!" -- |
     |                        |
     |-- /dashboard ---------->|  <-- new command works immediately
```

## Zero-Downtime Guarantee

The watchdog (`core/watchdog.py`) runs as the **parent process**:
- Launches `main.py` as a child process
- Polls `data/.restart_requested` every second
- When a restart is needed: terminates `main.py`, relaunches it
- Telegram long-poll reconnects in **<3 seconds automatically**
- If `main.py` crashes: auto-relaunches after 3 seconds
- Sends you a Telegram notification on every restart

## Start Command

```bash
# Development
bash scripts/start_with_watchdog.sh

# Docker (recommended)
# CMD is already set to watchdog in docker-compose
docker-compose up -d
```

## Usage Examples

```
/upgrade add a /dashboard command that reads CSV and makes a Plotly chart
/upgrade add a /translate command that translates any text to English
/upgrade add a /weather command showing forecast for any city
/upgrade add a /stocks command with live price chart from Yahoo Finance
/upgrade add a /remind command that sets reminders
/upgrade add a /summarize_url command that summarizes any webpage
```

## Safety

All generated code is:
1. **Syntax-checked** with `ast.parse()` before writing
2. **Safety-scanned** for: `os.system`, `eval`, `exec`, `rm -rf`, path traversal
3. **Rollback-ready**: original files are backed up; restored on any failure
4. **Dep-sanitized**: package names validated against allowlist pattern

## Rollback

If an upgrade fails at any step, all written files are automatically
restored to their previous versions. Use `/upgrade_rollback` to manually
trigger rollback of the last successful upgrade.

## Architecture

| File | Role |
|---|---|
| `core/self_upgrade.py` | Engine: generate → validate → write → reload |
| `core/watchdog.py` | Parent process: crash recovery + restart-on-flag |
| `core/hot_reload_registry.py` | Dynamic Router registration without restart |
| `handlers/upgrade.py` | Telegram /upgrade command interface |
| `scripts/start_with_watchdog.sh` | Startup script |
