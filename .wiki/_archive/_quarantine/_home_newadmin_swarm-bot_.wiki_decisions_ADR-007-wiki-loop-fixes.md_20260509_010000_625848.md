---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/decisions/ADR-007-wiki-loop-fixes.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-05-09T01:00:00.625868"
}
---

---
title: Adr 007 Wiki Loop Fixes
type: decision
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- decisions
created: '2026-04-14'
updated: '2026-04-14'
summary: '**File**: `tools/browser_agent.py`'
wikilinks: []
confidence: medium
source: research
---
**File**: `tools/browser_agent.py`

Added URL validation with private IP blocking and scheme allowlisting:

```python
_PRIVATE_IP_PATTERNS = [
    re.compile(r"^10\."isely),
    re.compile(r"^172\.(1[6-9]|2[0-9]|3[0-1])\."),
    re.compile(r"^192\.168\."),
    re.compile(r"^127\."),
    re.compile(r"^localhost$", re.IGNORECASE),
    re.compile(r"^0\."),
    re.compile(r"^::1$"),
    re.compile(r"^fe80:"),
]

def validate_url(url: str) -> tuple[bool, str]:
    # Blocks: file://, ftp://, gopher://
    # Blocks: private IPs (10.x, 172.16-31.x, 192.168.x, 127.x, localhost, ::1, fe80:)
    # Respects: BROWSER_ALLOWED_DOMAINS env var allowlist
```

Applied to: `check_site_health()`, `browse_task()`, `_playwright_fallback()`

**Verification**: ✅ `file:///etc/passwd` blocked, `http://127.0.0.1` blocked, `https://google.com` allowed
---


### FIX 3: Duplicate briefing disabled
**File**: `main.py:525-534`

Commented out the 7:30AM briefing from `tools.briefing.schedule_daily_briefing` to prevent duplicate with ProactiveScheduler at 8AM (DAILY_BRIEFING_HOUR=8).

```python
# NOTE: ProactiveScheduler in core/proactive/scheduler.py ALSO fires a briefing at DAILY_BRIEFING_HOUR (default 8AM).
# This creates duplicate briefings. For now, let ProactiveScheduler handle it (8AM) and disable this one.
# TODO: Consolidate into single briefing mechanism — see ADR-006
```

---

### FIX 4: Health endpoint wired
**File**: `main.py:710-714`

Added health server startup to `on_startup()`:

```python
try:
    from core.health import start_health_server
    asyncio.create_task(start_health_server(port=8080))
    logger.info("Health endpoint scheduled on port 8080")
except Exception as e:
    logger.warning("Health server init failed (non-fatal): %s", e)
```

Exposes `GET /health → 200 {"status": "ok", "bot": "@LegionBot"}`

---

### FIX 5: cron_setup.py subprocess sandboxing
**File**: `core/daily_harvester/cron_setup.py`

The crontab modification subprocess calls are a KNOWN LIMITATION — they modify system crontab but are protected by:
1. Being called only from daily_harvester.py (not user-triggered)
2. Using hardcoded cron command for specific script only
3. Requires cron_setup.py to be explicitly called

**Note**: Full sandboxing would require restructuring to use a wrapper script. Documented in security-audit.md as MEDIUM priority.

---

## Security Notes

### ALLOWED_USER_ID Sources (Split-Brain Risk)
The following files each define their own ALLOWED_USER_ID from env:
- `main.py:170` — canonical source, sets `_shared.ALLOWED_USER_ID`
- `handlers/shared.py:69` — reads from main.py via `_shared`
- `handlers/admin_handlers.py:20` — re-reads from env
- `handlers/debate_handlers.py:19` — re-reads from env
- `handlers/business_handler.py:23` — re-reads from env
- `handlers/whatsapp_handler.py:23` — re-reads from env
- `handlers/github_intel_handler.py:22` — re-reads from env
- `core/proactive_engine.py:23` — re-reads from env

**Status**: All handlers that re-read from env fallback correctly when `handlers.shared` import fails. This is acceptable for now but should be consolidated.

### Remaining Issues (Documented in ADR-005/ADR-006)
- cron_setup.py: crontab modification subprocess (MEDIUM risk, known limitation)
- skill_guardian retry pattern exists but not wired to webhooks/Supabase
- 4 proactive engines remain separate (consolidation needed)
- Profile block injected on every request (token waste)

---

## Files Changed

| File | Change |
|------|--------|
| `tools/minimax_media.py` | +35 lines: `understand_audio()` implementation |
| `tools/browser_agent.py` | +50 lines: SSRF validation (`validate_url()`, `_is_private_ip()`) |
| `main.py` | -10 lines: commented out duplicate briefing; +10 lines: health endpoint |
| `core/health.py` | unchanged (already existed, just wired up) |

---

## Consequences

- Video/audio transcription now works (was silent failure)
- SSRF attacks blocked (file://, private IPs, non-allowed domains)
- Duplicate morning briefing eliminated
- HTTP health endpoint available for uptime monitors
- All 305 tests pass

---

## Test Results
```
pytest tests/ -x --asyncio-mode=auto -q
======================= 305 passed, 1 warning in 16.90s ========================
```
