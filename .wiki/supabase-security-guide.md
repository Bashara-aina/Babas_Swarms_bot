---
title: Supabase Security Guide
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- supabase-security-guide.md
created: '2026-04-14'
updated: '2026-04-14'
summary: 'domain: "RLS policies, API key storage, injection prevention"'
wikilinks: []
confidence: medium
source: research
---
# SUPABASE SECURITY GUIDE
# SUPABASE SECURITY GUIDE

---
domain: "RLS policies, API key storage, injection prevention"
cycle: "15 — SUPABASE & DATABASE"
date: "2026-04-12"
status: "candidate"
---

## 1. API Key Management

### 1.1 Environment Variables

All Supabase credentials are read from environment variables — **never hardcoded**.

```python
# tools/supabase_client.py
_url = url or os.getenv("SUPABASE_URL", "")
_anon = anon_key or os.getenv("SUPABASE_ANON_KEY", "")
_svc = service_role_key or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

# tools/business_ops.py
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
```

**Env vars required:**
| Variable | Purpose | Access Level |
|----------|---------|--------------|
| `SUPABASE_URL` | Project endpoint | Public (embedded in client) |
| `SUPABASE_ANON_KEY` | Public anon key | Public (PostgREST RLS enforcement) |
| `SUPABASE_SERVICE_ROLE_KEY` | Admin key | **Server-only** — bypasses RLS |

### 1.2 Key Separation Principle

```
ANON_KEY (public) → RLS policies enforced → users can only see permitted rows
SERVICE_ROLE_KEY → bypasses RLS → bot-internal operations only
```

The anon key is safe to expose in client-side code. The service role key **must never** reach the client.

### 1.3 Current Risk: Duplicate Key Env Names

Two different env var names are used across the codebase:

| File | Env Var for Service Key |
|------|------------------------|
| `tools/supabase_client.py` | `SUPABASE_SERVICE_ROLE_KEY` |
| `tools/business_ops.py` | `SUPABASE_SERVICE_KEY` |

`.env.example` only documents `SUPABASE_KEY` (line 49). **This inconsistency means some deployments may have Supabase working via `supabase_client.py` but failing silently via `business_ops.py`.**

**Fix needed**: Standardize on one env var name.

---

## 2. Row-Level Security (RLS)

### 2.1 cekwajar.id RLS Policies

Documented in `.wiki/architecture/block_02_database_schema.md`.

```sql
-- users: auth.users FK, subscription gates access
-- raw_salary_submissions: users see ONLY own submissions
-- verdict_logs: users see only their own verdicts
-- benchmark_* tables: PUBLIC read, no direct writes
-- api_usage_logs: B2B clients see only own usage
```

### 2.2 rumahlabuh.com RLS Status

**Not documented in codebase.** The `SupabaseClient` introspects schema at runtime via PostgREST OpenAPI, but RLS policies are not audited.

**Risk**: If rumahlabuh.com tables don't have RLS policies, anyone with the anon key could query all bookings/guests.

### 2.3 RLS Enforcement Points

```
Request → PostgREST API → checks RLS policies → returns filtered data
 ↓
 service_role key bypasses RLS entirely
```

SupabaseClient defaults to `use_service_role=True` for all CRUD operations, meaning **RLS is bypassed by default**. This is appropriate for bot-internal operations but means the client is not testing RLS enforcement.

---

## 3. Injection Prevention

### 3.1 SQLite (Legion Core)

All SQLite queries use `aiosqlite` with **parameterized queries exclusively**.

```python
# tools/persistence.py — correct
await db.execute("DELETE FROM key_value_store WHERE key = ?", (key,))

# tools/memory.py — correct
await db.execute("SELECT COUNT(*) FROM memories")
await db.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
```

**No raw SQL string interpolation found** across the codebase. The only string building is for index/table names, not user data.

### 3.2 Supabase REST API

PostgREST uses **server-side parameterized queries**. The client builds filter expressions:

```python
# tools/supabase_client.py — filter building
for col, val in (eq or {}).items():
 p[col] = f"eq.{val}" # PostgREST syntax, val is escaped server-side

# tools/business_ops.py — same pattern
params[f"{k}"] = f"eq.{v}"
```

**No raw SQL executed against Supabase** — all queries go through PostgREST, which handles escaping.

### 3.3 LLM-Generated Queries

`SupabaseClient.query_natural()` uses an LLM to translate natural language to PostgREST params. This introduces **indirect injection risk** if the LLM output is not validated.

```python
# tools/supabase_client.py: query_natural()
# LLM output is parsed via regex JSON extraction, then passed to self.query()
query_params = json.loads(json_match.group(0))
# No schema validation of the parsed params before executing
```

**Risk**: Prompt injection could cause the LLM to output a crafted JSON object that, when parsed, produces unexpected filter values.

**Mitigation**: `table` name is extracted and checked; unknown tables produce an error. Filter values pass through PostgREST's escaping.

---

## 4. Credential Exposure Risks

### 4.1 Audit Findings

| Risk | Location | Severity |
|------|----------|----------|
| SERVICE_ROLE_KEY logged on init | `supabase_client.py:559` | Low (info level) |
| Duplicate env var names | `business_ops.py` vs `supabase_client.py` | Medium |
| rumahlabuh RLS not verified | `SupabaseClient` | Medium |
| LLM query output not schema-validated | `query_natural()` | Low |

### 4.2 Git History

Supabase credentials are **not currently in git history** (no accidental commits). `.env.example` documents the vars without values.

### 4.3 Supabase Key Rotation

No key rotation mechanism exists. Rotation requires updating the env var and restarting the bot.

---

## 5. Secure Usage Patterns

### 5.1 Recommended SupabaseClient Usage

```python
from tools.supabase_client import get_client, is_configured

# Check configuration before use
if is_configured():
 db = get_client()
 # Use service_role only for internal bot ops
 rows = await db.query("internal_table", use_service_role=True)
else:
 # Graceful degradation
 return "Supabase not configured"
```

### 5.2 Health Check Before Critical Ops

```python
health = await db.health_check()
if not health["ok"]:
 logger.error("Supabase unavailable: %s", health.get("error"))
 # fallback to cached data or error response
```

### 5.3 Rate Limiting

Supabase Pro plan enforces connection limits. The `SupabaseClient` uses a single `httpx.AsyncClient` with `timeout=20.0`. For high-throughput scenarios, connection pooling should be considered.

---

## 6. Privacy Architecture (cekwajar.id)

From `block_02_database_schema.md`:

```
User Submission (encrypted)
 ↓
raw_salary_submissions / raw_land_submissions (private, never published)
 ↓
crowdsource_queue (pending AI validation)
 ↓
AI Agent Pipeline (Swarms agent validates data quality)
 ↓
benchmark_salary / benchmark_land_prices / benchmark_cost_of_living
 (aggregated, k-anonymity ≥ 10)
 ↓
Users query via verdict_logs (anonymized, RLS-protected)
```

**Key principles:**
- Raw submissions never touch published benchmarks
- k-anonymity threshold: minimum 10 submissions per aggregation cell
- B2B API rate limiting per client
- Audit trails via `data_sources` for compliance

---

## 7. Recommendations

1. **Standardize SUPABASE_SERVICE_KEY env var** — currently `SUPABASE_SERVICE_ROLE_KEY` in one file, `SUPABASE_SERVICE_KEY` in another
2. **Audit rumahlabuh.com RLS policies** — run `introspect_schema()` and verify RLS exists on all tables
3. **Add schema validation to query_natural()** — validate table name against `list_accessible_tables()`
4. **Use anon_key for read operations when possible** — only use service_role for writes
5. **Add Supabase connection pooling** — if high throughput needed, consider PgBouncer pattern
6. **Document backup/recovery** — no backup strategy found in codebase

---

tokens_estimated: 520
injects_into: security-audit.md, tools-inventory.md, architecture/block_02_database_schema.md

## DEBATE RECORD
Advocate: 8 | Skeptic: 7 | Judge: WRITE 8
Advocate note: RLS bypass via service role is documented clearly. Duplicate env var names are a real risk.
Skeptic note: Internal bot, single user — RLS bypass may be acceptable.
Judge note: Security pages score high — documenting the gap is more valuable than ignoring it.
