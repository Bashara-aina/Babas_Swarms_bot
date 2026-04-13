---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/logging-strategy.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-13T01:00:00.131935"
}
---

---
title: logging-strategy
domain: deployment-cicd
impact_score: 7
last_updated: 2026-04-12
injects_into: system
tokens_estimated: 480
---

# Logging Strategy

## ONE-LINE SUMMARY
Dual-output logging (stdout + bot.log) with rotating file handler (10MB/5 backups) and secret redaction, but no persistent crash logging and no structured crash recovery.

## FACTS

### Logging Configuration

#### main.py (current active config)
```python
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot.log", encoding="utf-8"),
    ],
)
```
- Console handler: stdout (visible in journalctl -f)
- File handler: bot.log (plain, no rotation, no size limit)
- No secret redaction
- No log rotation

#### `core/log_config.py` (unused alternative)
```python
RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
RedactingFormatter: strips API keys, Bearer tokens, Telegram bot tokens
```
- 10 MB max per file, 5 backup files kept
- Secret redaction: sk-*, AIza*, Bearer tokens, bot[0-9]:*
- Console + file handler
- Suppresses httpx, aiogram, litellg to WARNING level
- NOT used by main.py (never imported)

### Log Outputs
| Output | Handler | Rotation | Secret Redaction | Content |
|--------|---------|----------|------------------|---------|
| stdout | StreamHandler | none | no | all levels |
| bot.log | FileHandler | none | no | all levels |
| systemd journal | StreamHandler (via stdout) | journald managed | no | all levels |
| bot.log.X (backup) | (none - not configured) | N/A | N/A | N/A |

### Activity Logging Middleware
`ActivityLogMiddleware` in main.py logs:
- All inbound Telegram messages: `[IN][chat=X][user=Y|@username] message`
- All outbound messages via bot.send_message/edit_message_text/send_photo: `[OUT][chat=X][method] content`
- User ID tracking for curiosity engine

### Observability Metrics
- **Prometheus** (`core/observability/metrics.py`): Port 8001, counters for requests/latency/errors/cache hits, gauges for active threads/cache hit rate
- **AgentOps** (optional): `AGENTOPS_API_KEY` env var enables session tracking
- **Cost tracking** (`swarms_bot/routing/budget_manager.py`): In-memory only, no persistence
- **Session transcripts** (`core/session/transcript.py`): SQLite at data/session_transcripts.db, 8000 char truncation

### Log Retention
- bot.log: grows indefinitely until manually rotated or disk fills
- systemd journal: managed by journald (default /var/log/journal), subject to systemd-journald config
- No automatic cleanup of old log files

### Crash Behavior
1. Exception raised → logger.error/logger.warning logged to bot.log + stdout
2. asyncio tasks cancelled in on_shutdown
3. systemd restarts service after 10s (Restart=on-failure)
4. Previous bot.log contents lost on next start (unless journald persisted them)
5. **No persistent crash log** — crash details may only exist in systemd journal

### Health Monitoring
- **Heartbeat daemon**: Checks `systemctl is-active swarm-bot` every 30 min during active hours
- **Ruflo health monitor**: Pings ruflo /health every 5 minutes, logs warning if dead
- **Proactive failures**: Completely silent — no monitoring hook for scheduler/curiosity engine failures

## LEGION BEHAVIOR RULES
1. All inbound/outbound Telegram messages are logged with chat_id and user_id
2. API keys and tokens are NOT redacted in current main.py logging (security gap)
3. Proactive engine failures are silent — no Telegram alert sent
4. BudgetManager cost data is lost on restart (in-memory only)
5. Session transcripts truncate at 8000 chars — long code blocks may be cut mid-token
6. PII (user messages) logged verbatim to bot.log without redaction

## EXAMPLES
Checking bot logs:
```bash
# Via systemd journal
journalctl -u legion-bot -f

# Direct log file
tail -f /home/newadmin/swarm-bot/bot.log
```

Investigating a crash:
Legion (with journal): `journalctl -u legion-bot --since "1 hour ago" | grep ERROR`
Legion (without persistent crash log): crash details may have rotated out of systemd journal

## ANTI-PATTERNS
1. API keys logged in plain text to bot.log — Telegram tokens, OpenAI keys visible if logged
2. No log rotation on bot.log — eventually fills disk if unattended
3. core/log_config.py with RedactingFormatter is written but never imported in main.py
4. Proactive failures completely silent — CuriosityEngine crash goes unnoticed until manual check
5. In-memory BudgetManager loses all cost history on restart
6. Session transcript truncation at 8000 chars corrupts long code block preservation

## GAPS
1. **No persistent crash log** — crashes from hours ago may be lost when bot.log rotates
2. **RedactingFormatter not wired** — core/log_config.py exists but unused
3. **No log aggregation** — no ELK stack, no Grafana Loki, no remote log shipping
4. **No proactive failure alerting** — scheduler failures only visible in log files
5. **No structured crash context** — exceptions logged with stack traces but no crash ID, no environment snapshot
6. **No disk space monitoring** — bot.log could fill /home partition silently
7. **No log compression** — bot.log and backups are uncompressed plain text

## DEBATE RECORD
Advocate: 7 | Skeptic: 8 | Judge: WRITE 7
Judge note: RedactingFormatter exists but isn't used, proactive failures are silent, and no crash persistence mechanism — all real gaps confirmed.
