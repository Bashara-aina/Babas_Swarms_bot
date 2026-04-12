# DATABASE RESILIENCE

**Domain**: Connection handling, fallback patterns, recovery
**Cycle**: 15 — SUPABASE & DATABASE
**Date**: 2026-04-12
**Status**: candidate

---

## 1. Architecture: Two-Tier Resilience

Legion's database resilience operates at two independent layers:

```
Layer 1: Local SQLite (legion.db, .legion_memory.db)
    ↓ failure → graceful degradation
Layer 2: External Supabase (optional, on-demand)
    ↓ failure → error response, no crash
```

**Core principle**: SQLite failures are **non-fatal**. Supabase failures are **contained**.

---

## 2. SQLite Resilience

### 2.1 Connection Handling

All SQLite operations use `aiosqlite.connect()` with context managers — connections are always closed.

```python
# tools/persistence.py — correct pattern
async with aiosqlite.connect(DB_PATH) as db:
    await db.execute(...)
    await db.commit()
# Connection auto-closed on exit

# tools/memory.py — same pattern
async with aiosqlite.connect(DB_PATH) as db:
    cursor = await db.execute(...)
# Always closes, even on exception
```

### 2.2 Schema Initialization

```python
# init_db() in persistence.py — idempotent
await db.executescript("""
    CREATE TABLE IF NOT EXISTS scheduled_tasks (...)
    CREATE TABLE IF NOT EXISTS ...
""")
# CREATE TABLE IF NOT EXISTS — safe to call multiple times
```

### 2.3 Failure Modes

| Failure | Result | Recovery |
|---------|--------|----------|
| DB file missing | Created automatically | Self-healing |
| Disk full | `aiosqlite.OperationalError` raised | Manual: clear space |
| Locked DB | `aiosqlite.OperationalError: database is locked` | Retry on next operation |
| Corrupt DB | Exception on read | Manual: delete + restart |

**No automatic recovery for disk full or corrupt DB** — these require manual intervention.

### 2.4 No Connection Pooling

SQLite uses file-level locking. `aiosqlite` opens/closes per operation — this is the **correct pattern** for SQLite. Connection pooling (e.g., `aiosqlite.pool`) is unnecessary and not used.

---

## 3. Supabase Resilience

### 3.1 Health Check

```python
# tools/supabase_client.py
async def health_check(self) -> Dict[str, Any]:
    t0 = time.monotonic()
    try:
        resp = await self._http.get(
            f"{self.url}/rest/v1/",
            headers=self._headers(use_service_role=False),
            timeout=5.0,
        )
        ok = resp.status_code < 500
    except Exception as e:
        return {"ok": False, "error": str(e), "latency_ms": None}
    latency = round((time.monotonic() - t0) * 1000)
    return {"ok": ok, "status_code": resp.status_code, "latency_ms": latency}
```

### 3.2 Graceful Degradation

When Supabase is unavailable:

```python
# tools/business_ops.py
if not SUPABASE_URL or not SUPABASE_KEY:
    return [{"error": "SUPABASE_URL or SUPABASE_SERVICE_KEY not set"}]

# tools/rumahlabuh_crew.py
if not is_configured():
    return "Supabase client not available — check SUPABASE_URL and SUPABASE_KEY"

# handlers/business_handler.py
"Supabase not configured. Add <code>SUPABASE_URL</code> and <code>SUPABASE_KEY</code> to .env."
```

**Result**: User gets a friendly error message. Bot continues operating.

### 3.3 HTTP Timeout

`httpx.AsyncClient(timeout=20.0)` — 20-second timeout on all Supabase requests.

### 3.4 Failure Modes

| Failure | Result |
|---------|--------|
| SUPABASE_URL not set | `ValueError` on `get_client()`, friendly error shown |
| Network unreachable | `httpx.ConnectError` → graceful error |
| Supabase project paused | HTTP 503 → graceful error |
| Rate limit exceeded | HTTP 429 → `RuntimeError` with detail |
| Invalid table name | HTTP 400 → error returned to user |
| RLS violation | HTTP 406 → filtered/empty response |

**No automatic retry** for Supabase failures — failed queries return errors directly to the user.

---

## 4. Memory System Fallback Chain

Legion has a **three-tier memory fallback**:

```
Mem0 (semantic search) 
    ↓ unavailable → 
OpenViking (tiered L0/L1/L2 context)
    ↓ unavailable → 
TF-IDF SQLite ( cosine similarity )
```

```python
# tools/memory.py: search_memory()
# Try Mem0 first
try:
    mem0_hits = await mem0_search(...)
    if mem0_hits:
        return mem0_hits
except Exception as e:
    logger.debug("Mem0 search failed, falling back...")

# Try OpenViking second
try:
    hits = await semantic_search(...)
    if hits:
        return hits
except Exception as e:
    logger.debug("OpenViking search failed, falling back...")

# TF-IDF always available (SQLite)
results = await search_memory_tf_idf(...)
```

**Result**: Memory search never fails completely — TF-IDF is always available.

---

## 5. LLM Fallback Chain (Database-Agnostic)

The LLM routing fallback chain provides resilience for AI operations:

```
groq/llama-3.3-70b-versatile
    ↓ rate limited/unavailable →
anthropic/claude-sonnet-4
    ↓ unavailable →
cerebras/qwen-3-235b-a22b
    ↓ unavailable →
ollama_chat/gemma4:e4b (local, RTX 3060)
    ↓ unavailable →
    "rate limited on all providers — retry in ~{wait_s}s"
```

See `core/reliability/fallback_chain.py` and `llm_client/__init__.py`.

---

## 6. Recovery Patterns

### 6.1 Session Recovery

```python
# tools/persistence.py
async def resume_session(name_or_id: str) -> Optional[dict[str, Any]]:
    """Load a session by name or ID. Returns None if not found."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """SELECT * FROM sessions
               WHERE (session_id = ? OR name = ?) AND status = 'active'
               ORDER BY last_active DESC LIMIT 1""",
            (name_or_id, name_or_id),
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None
```

Sessions are persisted to SQLite. On restart, sessions can be resumed.

### 6.2 Task Scheduling Recovery

```python
# tools/persistence.py
async def get_active_tasks() -> list[dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT * FROM scheduled_tasks WHERE status = 'active'"
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]
```

Scheduled tasks survive bot restarts. `next_run` timestamp determines if task should fire.

### 6.3 Audit Log

```python
# tools/persistence.py
async def log_audit(...) -> None:
    """Write one audit row. Called from the audit hook."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(...)  # Fire and forget — no retry
```

**No retry on audit log failure** — audit entries are best-effort.

---

## 7. Missing Resilience Patterns

| Pattern | Status | Location |
|---------|--------|----------|
| Retry on transient failure | **Missing** | No retry logic for SQLite or Supabase |
| Circuit breaker | **Missing** | No circuit breaker for Supabase calls |
| Bulkhead isolation | **Missing** | All Supabase calls share single client |
| Cache-aside pattern | **Partial** | `response_cache` table exists but not used by Supabase |
| Backup/restore | **Missing** | No backup mechanism for SQLite files |
| WAL mode | **Missing** | SQLite not running in WAL mode (better concurrency) |

---

## 8. Recommended Improvements

### 8.1 Enable SQLite WAL Mode

```python
async with aiosqlite.connect(DB_PATH) as db:
    await db.execute("PRAGMA journal_mode=WAL")
```

WAL mode allows concurrent reads during writes — improves responsiveness under load.

### 8.2 Add Retry with Backoff for Supabase

```python
async def query_with_retry(table, **kwargs):
    for attempt in range(3):
        try:
            return await db.query(table, **kwargs)
        except Exception as e:
            if attempt == 2:
                raise
            await asyncio.sleep(2 ** attempt)  # 1s, 2s, 4s
```

### 8.3 Cache Supabase Responses

```python
# Before: hit Supabase every time
rows = await db.query("listings", eq={"status": "active"})

# After: cache for 5 minutes
cache_key = f"listings:active"
cached = await cache_get(cache_key)
if cached:
    return json.loads(cached)
rows = await db.query("listings", eq={"status": "active"})
await cache_set(cache_key, json.dumps(rows), ttl=300)
```

### 8.4 Backup SQLite Nightly

```bash
# Daily backup of both SQLite databases
cp ~/.legion_memory.db ~/.legion_memory.db.bak.$(date +%Y%m%d)
cp legion.db legion.db.bak.$(date +%Y%m%d)
# Keep last 7 backups
```

---

tokens_estimated: 590
injects_into: stability-map.md, memory-architecture.md, security-audit.md

## DEBATE RECORD
Advocate: 8 | Skeptic: 7 | Judge: WRITE 8
Advocate note: No retry, no circuit breaker, no WAL mode — all gaps worth documenting.
Skeptic note: SQLite with aiosqlite is reliable enough for local use.
Judge note: Resilience gaps are real and actionable — worth documenting for future improvements.
