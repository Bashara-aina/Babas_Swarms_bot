---
title: Webhook Patterns
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- webhook-patterns.md
created: '2026-04-14'
updated: '2026-04-14'
summary: Single webhook endpoint in n8n_bridge (no verification, no retry, no queue);
  retry/backoff infrastructure exists only in skill_guardian.py for tool calls, not
  for external webhooks.
wikilinks: []
confidence: medium
source: research
---

# Webhook Patterns

## ONE-LINE SUMMARY
Single webhook endpoint in n8n_bridge (no verification, no retry, no queue); retry/backoff infrastructure exists only in skill_guardian.py for tool calls, not for external webhooks.

## FACTS

### Webhook Infrastructure

**n8n webhook listener** (`tools/n8n_bridge.py:35-49`):
```python
async def _run_listener() -> None:
    async def handle_webhook(request: web.Request) -> web.Response:
        payload = await request.json() if request.can_read_body else {}
        logger.info("n8n webhook received: %s", payload)
        return web.json_response({"ok": True})

    app = web.Application()
    app.router.add_post("/webhook", handle_webhook)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=N8N_PORT)
    await site.start()
```
- Route: `POST /webhook` on port 7835
- No HMAC verification, no secret validation
- Returns `{"ok": True}` immediately after logging
- No persistent event queue — payload discarded after log

### Retry & Backoff Infrastructure

**skill_guardian.py** — only retry mechanism in codebase:
```python
_BACKOFF = [0, 1.0, 4.0, 16.0]  # seconds before each attempt

class FailureType(str, Enum):
    TRANSIENT = "TRANSIENT"     # network, rate-limit → retry
    INVALID_INPUT = "INVALID_INPUT"  # bad params → fix + retry
    PERMISSION = "PERMISSION"   # 401/403 → escalate
    NOT_FOUND = "NOT_FOUND"     # 404 → stop
    FATAL = "FATAL"             # crash → stop

async def guarded_call(fn, *args, tool_name="unknown", max_attempts=4, **kwargs):
    for attempt in range(max_attempts):
        wait = _BACKOFF[attempt]
        await asyncio.sleep(wait)
        try:
            return await fn(*args, **kwargs)
        except Exception as exc:
            failure = classify_error(exc)
            if failure not in SAFE_RETRYABLE:  # {TRANSIENT, INVALID_INPUT}
                raise
    raise last_exc
```

**Key classification logic**:
- TRANSIENT keywords: `timeout`, `rate limit`, `429`, `503`, `connection`, `reset`
- PERMISSION keywords: `401`, `403`, `unauthorized`, `forbidden`
- NOT_FOUND keywords: `404`, `not found`, `does not exist`

**Used by**: Composio actions, GitHub intel, general tool calls
**NOT used by**: n8n webhook delivery, Supabase queries, LLM calls

### Webhook Delivery Behavior
| Scenario | Behavior |
|----------|----------|
| Webhook arrives | Log payload, return `{"ok": True}`, discard |
| Bot offline | Event lost (no persistent queue) |
| n8n sends duplicate | No deduplication — both processed identically |
| Invalid payload | Logs error, returns `{"ok": True}` (no error response) |

### Health Check Pattern
```python
async def n8n_status() -> dict[str, Any]:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{N8N_BASE_URL}/healthz",
                                   timeout=aiohttp.ClientTimeout(total=3)) as resp:
                return {"healthy": resp.status == 200, "status": resp.status}
    except Exception as exc:
        return {"healthy": False, "error": str(exc)}
```
- One-shot check, 3s timeout
- No retry on failure
- Returns `{healthy: bool, status: int, base_url: str, error?: str}`

### Composio OAuth Token Refresh
```python
# composio_hub.py
_composio_toolset = ComposioToolSet(api_key=api_key)
# Composio SDK handles token refresh automatically
```
- Token refresh managed by Composio SDK
- No manual refresh code in bot
- Works for Gmail, Calendar, GitHub via Composio's 850+ connectors

## LEGION BEHAVIOR RULES
1. n8n webhook listener accepts all POST requests — no authentication
2. Webhook payloads logged and discarded — no event bus or task queue
3. Retry only via skill_guardian.py for tool calls — not for webhooks or Supabase
4. Health check is one-shot with 3s timeout — no circuit breaker
5. Composio OAuth tokens refreshed automatically by SDK

## EXAMPLES

Guarded tool call with retry:
```python
from tools.skill_guardian import guarded_call, FailureType

try:
    result = await guarded_call(
        get_unread_emails,
        max_results=5,
        tool_name="gmail",
        max_attempts=4,
    )
except FailureType.PERMISSION:
    await notify_admin("Gmail API permission denied")
except FailureType.FATAL:
    await notify_admin("Gmail call failed after all retries")
```

Webhook verification (missing — documented as gap):
```python
# CURRENT: No verification
async def handle_webhook(request: web.Request) -> web.Response:
    payload = await request.json()
    return web.json_response({"ok": True})

# SHOULD BE (not implemented):
async def handle_webhook(request: web.Request) -> web.Response:
    signature = request.headers.get("X-n8n-Signature", "")
    if not verify_hmac(payload, signature, os.getenv("N8N_WEBHOOK_SECRET")):
        return web.json_response({"error": "unauthorized"}, status=401)
    # process event...
```

## ANTI-PATTERNS
1. **No webhook verification** — any client can POST to `:7835/webhook`; no HMAC, no secret, no IP allowlist
2. **No persistent event queue** — bot restart loses all pending webhook events
3. **No retry on webhook delivery** — n8n sends once, no acknowledgment retry
4. **No deduplication** — duplicate webhook deliveries processed twice
5. **No circuit breaker** — health check failure doesn't prevent retries or trigger fallback

## GAPS
1. **No webhook HMAC verification** — n8n webhook signature not validated
2. **No event persistence** — webhooks lost on bot restart
3. **No retry for webhooks** — only skill_guardian retry for tool calls, not for webhook delivery
4. **No Supabase retry** — SupabaseClient has no exponential backoff on query failure
5. **No circuit breaker** — no automatic Open/Closed/Half-Open state for external APIs
6. **No webhook dead-letter queue** — failed events not stored for later replay

## DEBATE RECORD
Advocate: 7 | Skeptic: 7 | Judge: WRITE 7
Judge note: Very thin webhook infrastructure. n8n_bridge has zero retry/verification/queue. skill_guardian provides good retry pattern but is not wired to external API calls. Webhook gap confirmed. Score 7 — marginal approval, note as high-priority gap.