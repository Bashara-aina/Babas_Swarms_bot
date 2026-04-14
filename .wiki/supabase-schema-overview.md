---
title: Supabase Schema Overview
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- supabase-schema-overview.md
created: '2026-04-14'
updated: '2026-04-14'
summary: 'domain: "Database schema, table relationships, API patterns"'
wikilinks: []
confidence: medium
source: research
---
# SUPABASE SCHEMA OVERVIEW
# SUPABASE SCHEMA OVERVIEW

---
domain: "Database schema, table relationships, API patterns"
cycle: "15 — SUPABASE & DATABASE"
date: "2026-04-12"
status: "candidate"
---

## 1. Architecture Summary

Legion uses a **two-tier database architecture**:

| Layer | Technology | Purpose |
|-------|------------|---------|
| Local persistent | SQLite (`aiosqlite`) | Task scheduling, sessions, KV store, audit log, instincts |
| Long-term memory | SQLite (`aiosqlite`) | TF-IDF cosine similarity search |
| External business | Supabase PostgREST | rumahlabuh.com (villa rental), cekwajar.id (salary benchmarks) |
| Semantic memory | OpenViking + Mem0 | Tiered L0/L1/L2 context (optional, falls back to TF-IDF) |

**Supabase is NOT used for Legion's core operations.** It is a *client* tool — queried on-demand for external business projects.

---

## 2. Local SQLite Databases

### 2.1 `legion.db` (project root)

Initialized by `tools/persistence.py`, schema created on first run via `init_db()`.

**Tables:**

```sql
-- Task scheduler
CREATE TABLE scheduled_tasks (
    id TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    command TEXT NOT NULL,
    task_type TEXT NOT NULL,
    interval_sec INTEGER DEFAULT 0,
    next_run REAL NOT NULL,
    last_run REAL DEFAULT 0,
    status TEXT DEFAULT 'active',
    alert_condition TEXT DEFAULT '',
    created_at REAL NOT NULL
);

CREATE TABLE task_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,
    executed_at REAL NOT NULL,
    result TEXT,
    success INTEGER DEFAULT 1
);

-- Conversation memory
CREATE TABLE conversation_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    thread_id TEXT NOT NULL,
    agent TEXT NOT NULL,
    task TEXT NOT NULL,
    result TEXT NOT NULL,
    created_at REAL NOT NULL
);
CREATE INDEX idx_conv_thread ON conversation_memory(thread_id);

-- Key-value store
CREATE TABLE key_value_store (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at REAL
);

-- Audit log
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL NOT NULL,
    action TEXT NOT NULL,
    detail TEXT NOT NULL,
    model TEXT,
    tokens_in INTEGER DEFAULT 0,
    tokens_out INTEGER DEFAULT 0,
    duration_ms INTEGER DEFAULT 0,
    success INTEGER DEFAULT 1
);
CREATE INDEX idx_audit_ts ON audit_log(timestamp);

-- Session management
CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    thread_id TEXT NOT NULL,
    agent_key TEXT,
    context_json TEXT,
    status TEXT DEFAULT 'active',
    created_at REAL NOT NULL,
    last_active REAL NOT NULL
);

-- Learned instincts
CREATE TABLE instincts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    content TEXT NOT NULL,
    source TEXT DEFAULT 'manual',
    weight REAL DEFAULT 1.0,
    uses INTEGER DEFAULT 0,
    created_at REAL NOT NULL
);

-- Response cache
CREATE TABLE response_cache (
    cache_key TEXT PRIMARY KEY,
    response TEXT NOT NULL,
    agent TEXT NOT NULL,
    model TEXT NOT NULL,
    tokens_used INTEGER DEFAULT 0,
    created_at REAL NOT NULL,
    expires_at REAL NOT NULL
);
```

**Wrapper class**: `Persistence` in `tools/persistence.py`

### 2.2 `.legion_memory.db` (home directory)

Initialized by `tools/memory.py`, used for `/recall` and `/memories` commands.

```sql
CREATE TABLE memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    tags TEXT DEFAULT '',
    source TEXT DEFAULT 'manual',
    tfidf TEXT DEFAULT '{}',  -- JSON-encoded TF-IDF vector
    created REAL NOT NULL,
    accessed REAL NOT NULL
);
CREATE INDEX idx_memories_created ON memories(created DESC);
CREATE INDEX idx_memories_tags ON memories(tags);
```

**Search fallback chain**: Mem0 → OpenViking → TF-IDF cosine similarity

---

## 3. Supabase Schema (External Projects)

### 3.1 rumahlabuh.com (Villa Rental)

Schema bootstrapped via `SupabaseClient.introspect_schema()` → LLM → `skills/rumahlabuh-manager.md`

**Env vars:**
```
SUPABASE_URL=https://<project>.supabase.co
SUPABASE_ANON_KEY=<public anon key>
SUPABASE_SERVICE_ROLE_KEY=<service role key>
```

**API wrapper**: `tools/supabase_client.py::SupabaseClient`
- Wraps PostgREST API v2 (not direct Postgres connection)
- Supports: `query()`, `insert()`, `update()`, `delete()`, `rpc()`, `storage_*()`
- Auth via Bearer token in `Authorization` header
- Used by: `tools/business_ops.py`, `handlers/business_handler.py`

**Tables (introspected from PostgREST OpenAPI):**
- `listings` — villa/property listings with status
- `bookings` — reservation records
- `guests` — guest information
- `revenue` — financial records

### 3.2 cekwajar.id (Salary Benchmarks)

Full schema documented in `.wiki/architecture/block_02_database_schema.md`.

**Core tables:**
- `users` — auth + subscription tracking (free/premium/enterprise)
- `raw_salary_submissions` — private, never published directly
- `raw_land_submissions` — private land price submissions
- `benchmark_salary` — aggregated, k-anonymity ≥ 10
- `benchmark_land_prices` — aggregated land benchmarks
- `benchmark_cost_of_living` — cost-of-living indices
- `verdict_logs` — user query results (anonymized)
- `api_usage_logs` — B2B client rate limiting
- `subscription_plans` — plan definitions
- `data_sources` — audit trail for compliance

**pgvector integration**: Semantic job title fuzzy matching via `embedding` column.

**RLS enforced**: users see only own submissions; benchmark tables are publicly readable.

---

## 4. Query Patterns

### 4.1 SQLite (Legion Core)

All queries use `aiosqlite` with **parameterized queries only** — no string interpolation.

```python
# ✅ Correct — parameterized
await db.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
await db.execute("SELECT * FROM memories WHERE id IN ({seq})", (','.join(ids),))

# Legion uses parameterized queries throughout
async with aiosqlite.connect(DB_PATH) as db:
    await db.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
```

### 4.2 Supabase REST API

```python
# Via SupabaseClient (tools/supabase_client.py)
rows = await db.query(
    table="bookings",
    select="id,status",
    eq={"user_id": uid}
)

# Direct via business_ops.py (tools/business_ops.py)
url = f"{SUPABASE_URL}/rest/v1/{table}"
params[f"{k}"] = f"eq.{v}"  # PostgREST filter syntax
```

### 4.3 Natural Language Query

```python
# SupabaseClient.query_natural() — LLM translates NL → PostgREST
result = await db.query_natural("Show my active bookings this month")
```

---

## 5. Key Relationships

```
legion.db
├── scheduled_tasks ← task_history (task_id FK)
├── sessions (session_id, thread_id)
└── conversation_memory (thread_id index)

.legion_memory.db
└── memories (no foreign keys, standalone)

Supabase (rumahlabuh)
├── listings ← bookings (listing_id FK)
└── bookings ← guests (guest_id FK)

Supabase (cekwajar)
├── users ← raw_salary_submissions (user_id FK)
├── users ← verdict_logs (user_id FK)
├── raw_salary_submissions → benchmark_salary (aggregation)
└── subscription_plans ← users (plan_id FK)
```

---

## 6. Noteworthy

- **No Supabase for Legion**: Core bot state (tasks, sessions, memory) is SQLite only
- **No raw SQL to Supabase**: All queries go through PostgREST API (no psycopg2)
- **Dual Supabase usage**: rumahlabuh.com and cekwajar.id share same Supabase project
- **Schema bootstrap**: rumahlabuh schema auto-generated via LLM from PostgREST OpenAPI spec
- **MEM0_USE_SUPABASE=0**: Mem0 uses local Chroma, not Supabase pgvector
- **No migrations**: SQLite schema created with `CREATE TABLE IF NOT EXISTS` — no migration files

---

tokens_estimated: 580
injects_into: tools-inventory.md, memory-architecture.md, architecture/block_02_database_schema.md

## DEBATE RECORD
Advocate: 8 | Skeptic: 7 | Judge: WRITE 8
Advocate note: Two-tier DB architecture is well-documented and correct. SQLite for Legion core, Supabase for external projects only.
Skeptic note: No migrations for SQLite is a gap — schema changes require DB deletion.
Judge note: Architecture is sound and clearly documented — high value for future developers.
