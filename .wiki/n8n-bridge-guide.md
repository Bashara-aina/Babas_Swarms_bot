---
title: N8N Bridge Guide
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- n8n-bridge-guide.md
created: '2026-04-14'
updated: '2026-04-14'
summary: n8n bridge is a lightweight webhook listener on port 7835 that enables Legion
  to receive external automation events; no built-in retry, polling, or n8n-to-Legion
  event processing.
wikilinks: []
confidence: medium
source: research
---

# n8n Bridge Guide

## ONE-LINE SUMMARY
n8n bridge is a lightweight webhook listener on port 7835 that enables Legion to receive external automation events; no built-in retry, polling, or n8n-to-Legion event processing.

## FACTS

### Architecture (`tools/n8n_bridge.py`)
```python
N8N_PORT = int(os.getenv("N8N_WEBHOOK_PORT", "7835"))
N8N_BASE_URL = os.getenv("N8N_BASE_URL", f"http://127.0.0.1:{N8N_PORT}")
N8N_DATA_DIR = Path(os.path.expanduser("~/.legion/n8n"))
```

**Three responsibilities:**
1. **Webhook listener** — aiohttp TCP server on port 7835 receiving POST `/webhook`
2. **Health check** — `n8n_status()` pings `/healthz` endpoint, returns `{healthy, status, base_url}`
3. **Auto-start** — `ensure_n8n_running()` runs `docker compose up -d n8n` if `ENABLE_N8N_AUTO_START=true`

**Startup flow (main.py:315-318):**
```python
from tools.n8n_bridge import start_n8n_webhook_listener
start_n8n_webhook_listener()
logger.info("n8n webhook listener scheduled")
```

### Webhook Handler
```python
async def handle_webhook(request: web.Request) -> web.Response:
    payload = await request.json() if request.can_read_body else {}
    logger.info("n8n webhook received: %s", payload)
    return web.json_response({"ok": True})
```
- Route: `POST /webhook`
- Always returns `{"ok": True}` — no processing, no event routing
- Payload is logged but discarded (no event bus, no task queue)
- No authentication/verification on incoming webhooks

### Configuration Environment Variables
| Env Var | Default | Purpose |
|---------|---------|---------|
| `N8N_WEBHOOK_PORT` | `7835` | TCP port for webhook listener |
| `N8N_BASE_URL` | `http://127.0.0.1:7835` | Health check target |
| `ENABLE_N8N_LISTENER` | `true` | Start webhook listener on boot |
| `ENABLE_N8N_AUTO_START` | `false` | Auto-start n8n via docker compose |

### What Triggers It
- **Boot**: `start_n8n_webhook_listener()` called in `main.py` on bot startup
- **External automation**: n8n workflow sends HTTP POST to `:7835/webhook`
- **Health check**: `n8n_status()` callable by any handler or admin command
- **Auto-start**: Only if `ENABLE_N8N_AUTO_START=true` — runs `docker compose up -d n8n` in project root

### Data Flow
```
n8n workflow → POST :7835/webhook → handle_webhook() → log payload → return {"ok": True}
```
No further processing. The webhook is acknowledged and discarded.

## LEGION BEHAVIOR RULES
1. Webhook listener starts automatically unless `ENABLE_N8N_LISTENER=false`
2. Incoming webhooks are logged but not processed — no event routing
3. Health check returns `{healthy: bool, status: int, base_url: str, error?: str}`
4. Docker compose auto-start only fires if `ENABLE_N8N_AUTO_START=true`
5. n8n data directory: `~/.legion/n8n/` (created on first import)

## EXAMPLES

Health check from handler:
```python
from tools.n8n_bridge import n8n_status
status = await n8n_status()
# {"healthy": True, "status": 200, "base_url": "http://127.0.0.1:7835"}
```

Manual listener start:
```python
from tools.n8n_bridge import start_n8n_webhook_listener
task = start_n8n_webhook_listener()
# returns asyncio.Task | None (None if disabled)
```

Auto-start n8n:
```bash
ENABLE_N8N_AUTO_START=true python main.py
```

## ANTI-PATTERNS
1. **No event processing** — webhook handler logs payload and returns `{"ok": True}`; no agent dispatch, no task creation, no message sent
2. **No HMAC verification** — incoming webhooks not authenticated; any client can POST to `:7835/webhook`
3. **No retry on health check failure** — `n8n_status()` is a one-shot HTTP check with 3s timeout; no circuit breaker
4. **Blocking docker compose** — `ensure_n8n_running()` uses `asyncio.to_thread(subprocess.run)` but no timeout; docker compose may hang

## GAPS
1. **No event routing** — webhook payloads are logged and discarded; no mechanism to trigger agent tasks from n8n events
2. **No webhook verification** — no HMAC signature or secret validation; potential abuse vector
3. **No retry logic** — health check and webhook delivery have no retry/backoff
4. **No persistent event queue** — if bot is down when n8n fires webhook, the event is lost
5. **No auto-start on docker failure** — `ensure_n8n_running()` catches exceptions but returns `{"started": False, "error": str(exc)}` without alerting

## DEBATE RECORD
Advocate: 8 | Skeptic: 7 | Judge: WRITE 8
Judge note: n8n bridge is minimal and functional for its scope. Key gap: no event routing from webhook to agent tasks. Verification gap noted (no HMAC). Auto-start gap noted.