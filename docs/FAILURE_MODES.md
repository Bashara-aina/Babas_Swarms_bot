# Failure Modes — Legion Swarm Bot

This document catalogs real, observed failure modes in this codebase with their symptoms, causes, and detection methods.

---

## 1. Telegram Bot Token Expiration

**Severity**: CRITICAL — bot goes fully offline.

**Symptoms**:
- `RuntimeError: Missing required env vars: ['TELEGRAM_BOT_TOKEN']` on startup
- Or: bot accepts no messages, returns 401 on all API calls

**Cause**: Telegram bot tokens are long-lived but can be revoked via @BotFather or when the owning account is compromised.

**Detection**:
- Health endpoint `GET /health` returns degraded status
- Legion BOOT startup check `_probe_telegram` returns `False`

**Recovery**: Obtain new token from @BotFather, update `.env`, restart bot.

---

## 2. LLM API Key Degradation / Rate Limiting

**Severity**: HIGH — bot responds but all LLM-powered commands fail.

**Symptoms**:
- `/do`, `/run`, `/think` all return error messages about context length or quota
- Individual LLM calls throw `RateLimitError` or `AuthenticationError`
- `llm_client.py` logs show `401` or `429` responses

**Cause**: MiniMax API key hit hourly/daily limits, or the key was rotated server-side.

**Detection**:
- `_probe_llm()` in Legion BOOT returns `False`
- `llm_client.py` logs `LLM call failed: rate_limit_exceeded`

**Recovery**: 
1. Check MiniMax dashboard for usage quotas
2. Rotate key in `.env` (`ANTHROPIC_AUTH_TOKEN` or `MINIMAX_API_KEY`)
3. Restart bot

---

## 3. Memory DB Corruption (ChromaDB)

**Severity**: MEDIUM — persistent memory features fail, bot still functions but loses context.

**Symptoms**:
- `chroma_db` probe in health check returns `False`
- User profile data appears stale or resets
- Memory search returns irrelevant results

**Cause**: ChromaDB SQLite backing store corrupted by abrupt shutdown (SIGKILL without graceful shutdown).

**Detection**:
- `_probe_chromadb()` fails
- `tools/memory.py` throws `OperationalError` on DB access

**Recovery**:
1. Stop bot
2. Delete `data/chroma/` directory
3. Restart bot (ChromaDB recreates empty store on boot)
4. Memory features recover but prior memories are lost

---

## 4. Handlers Shared State Corruption

**Severity**: MEDIUM — specific command categories fail silently.

**Symptoms**:
- Some command handlers (`/do`, `/run`) work, others return no response
- Error in `_shared` module causes handler import to fail
- Bot boots but a subset of commands are unregistered

**Cause**: `_shared.py` contains module-level mutable state (`_bot`, `_scheduler`, `_last_user_message_ts`) that can be None if initialization of that component failed but handlers try to use it.

**Detection**:
- `register_all_routers(dp)` throws `AttributeError` during boot
- Specific router files fail to import

**Recovery**:
1. Check `bot.log` for import errors at startup
2. Verify all required env vars are set
3. Restart bot

---

## 5. Wiki Index Staleness (GitNexus)

**Severity**: LOW — code intelligence tools return outdated results.

**Symptoms**:
- `gitnexus_query` returns symbols that no longer exist
- Impact analysis shows incorrect blast radius
- Refactoring operations miss file references

**Cause**: Code changes committed but `npx gitnexus analyze` not run to update the index.

**Detection**:
- `gitnexus_context` returns `[]` for recently-added symbols
- `gitnexus_detect_changes` warns about stale index

**Recovery**: Run `npx gitnexus analyze` to refresh the index.

---

## 6. Scheduler Task Queue Overflow

**Severity**: MEDIUM — scheduled tasks stop firing.

**Symptoms**:
- Daily briefing, nightly reports, proactive monitors all stop triggering
- Bot responds to commands but takes no autonomous action
- No error in logs — tasks just silently stop

**Cause**: `TaskScheduler` in `tools/scheduler.py` has an internal queue that overflows when the event loop is saturated, dropping tasks silently.

**Detection**:
- Schedules fire once then stop
- `tools/scheduler.py` logs show queue full warnings

**Recovery**:
1. Restart bot
2. If recurring, file issue to add backpressure handling to scheduler

---

## 7. Outbound Logging Monkey-Patch Breakage

**Severity**: LOW — debug logging fails, bot otherwise functions normally.

**Symptoms**:
- `[OUT]` log entries stop appearing in `bot.log`
- Message content no longer tracked in observability

**Cause**: If `_install_outbound_logging()` was called before and the bot object is reused across restarts, the patched methods can be in an invalid state.

**Note**: This monkey-patching has been REMOVED from main.py as of this audit. The outbound logging infrastructure is deprecated and replaced by `ActivityLogMiddleware` for inbound and native bot observability.

---

## 8. .env File Not Loaded Before Module Imports

**Severity**: CRITICAL — bot fails to start with missing env var errors even when `.env` is correctly configured.

**Symptoms**:
- `RuntimeError: Missing required env vars: ['TELEGRAM_BOT_TOKEN']`
- But `TELEGRAM_BOT_TOKEN` is clearly set in `.env`

**Cause**: On Windows or some Linux configurations, `load_dotenv()` fails silently if `.env` has wrong line endings (CRLF vs LF) or is saved as UTF-8 with BOM.

**Detection**:
- Bot fails before `_probe_telegram` runs
- `load_dotenv()` returns `False` (visible in debug logging)

**Recovery**:
1. Open `.env` in a hex editor and check for BOM prefix (byte order mark `EF BB BF`)
2. Convert line endings to LF only
3. Restart bot

---

## 9. Sidecar Process Crash Loop

**Severity**: MEDIUM — ruflo or opencode sidecars restart repeatedly.

**Symptoms**:
- `ruflo sidecar died (pid=X, exit=Y) — restarting in Zs` messages in log
- High CPU from repeated spawn/die cycles
- Bot functions normally but sidecar features ( Ruflo integration, OpenCode CLI) are unavailable

**Cause**: Sidecar binary not installed on system, or port already in use.

**Detection**:
- `_wait_for_ruflo_health()` returns `False` repeatedly
- `opencode serve --port 4096` exits with code 1

**Recovery**:
1. Verify `node` is installed (for ruflo)
2. Verify `opencode` CLI is in PATH
3. Check port 4096 is not in use: `lsof -i :4096`
4. If not needed, set `OPENROUTER_API_KEY` and `ANTHROPIC_API_KEY` to empty to disable ruflo auto-launch

---

## 10. Concurrent Write to SQLite (Memory OS / Conversation DB)

**Severity**: MEDIUM — intermittent database lock errors.

**Symptoms**:
- `database is locked` errors in logs
- Some memory operations fail with `sqlite3.OperationalError`
- Works sometimes, fails under high load

**Cause**: Multiple async tasks writing to the same SQLite file without proper busy timeout handling.

**Detection**:
- `tools/memoryos_client.py` logs `sqlite3.OperationalError: database is locked`
- `core/conversation_interface.py` logs same

**Recovery**:
1. Ensure only one writer at a time using `WAL` mode (already configured in `init_db()`)
2. Restart bot to clear locks
3. If persistent, increase busy timeout: `PRAGMA busy_timeout=5000`

---

*Document generated during security audit. Update this file when new failure modes are discovered.*