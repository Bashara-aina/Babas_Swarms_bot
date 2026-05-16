---
title: Supabase Query Patterns
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- supabase-query-patterns.md
created: '2026-04-14'
updated: '2026-04-14'
summary: Async httpx REST client, PostgREST API only, no native Postgres driver, RLS
  bypass via service role key, no query builder or ORM.
wikilinks: []
confidence: medium
source: research
---

# Supabase Query Patterns

## ONE-LINE SUMMARY
Async httpx REST client, PostgREST API only, no native Postgres driver, RLS bypass via service role key, no query builder or ORM.

## FACTS

### Client Architecture (`tools/supabase_client.py`)
- `SupabaseClient` class — thin async wrapper over httpx
- Single `httpx.AsyncClient(timeout=20.0)` shared instance
- **No PostgSQL native driver** — all queries go through PostgREST REST API
- Connection pooling: httpx default (100 conn limit, 5 conn per host)
- Singleton pattern via `get_client()` — single instance per process
- Service role key bypasses RLS — used for bot-internal operations

### Query Methods
- `query(table, select, eq, filters, order, limit, offset)` — SELECT via GET
- `insert(table, data, upsert, on_conflict)` — INSERT via POST
- `update(table, data, eq)` — UPDATE via PATCH
- `delete(table, eq)` — DELETE
- `rpc(function_name, params)` — Postgres function via /rpc/<name>
- `query_natural(nl_query)` — LLM translates NL → PostgREST JSON
- `health_check()` — returns latency_ms, ok status
- `introspect_schema()` — reads PostgREST OpenAPI spec

### RLS Handling
- Anon key used for public reads — RLS enforced
- Service role key used by default for all operations — **RLS BYPASSED**
- `use_service_role=False` flag available but not used in codebase
- Pattern: all current callers use service role → no RLS enforcement

### Connection Pooling
- httpx default connection pool: 100 total connections, 5 per host
- No explicit pool size tuning
- No idle connection timeout configuration
- 20-second timeout on all requests — hard limit

### Query Natural Language Interface
- `query_natural()` — LLM (groq/llama-3.3-70b-versatile) converts NL to PostgREST JSON
- Prompt includes schema context from skills/rumahlabuh-manager.md
- Falls back to schema introspection on demand
- No semantic caching of query results

### Usage in Codebase
- `tools/rumahlabuh_crew.py` — direct table queries with `eq={}` filters
- `handlers/computer.py` — user can ask to check Supabase dashboard
- `main.py` — `_bootstrap_supabase_skill()` calls `generate_skill_file()`
- `tools/scaffolder.py` — generates Supabase client TypeScript files for projects

## LEGION BEHAVIOR RULES
1. All Supabase queries are REST (PostgREST) — no direct Postgres connections
2. Service role key bypasses RLS — bot has full database access
3. `query_natural()` uses LLM for NL→query translation — potential for injection
4. No query result caching — every call hits the API
5. health_check() is the only latency monitoring — no per-query duration logging

## EXAMPLES
Basic query pattern:
```python
from tools.supabase_client import get_client
db = get_client()
rows = await db.query("bookings", select="id,status,guest_name", eq={"status": "confirmed"}, limit=10)
```

Natural language query:
```python
rows = await db.query_natural("Show me recent bookings with confirmed status")
```

## ANTI-PATTERNS
1. **RLS bypass by default** — service role key used everywhere, no RLS enforcement
2. **No query timeout per query** — global 20s timeout, but no per-query control
3. **No connection pool tuning** — 5 conn per host may be too low for bursty usage
4. **query_natural() LLM injection risk** — user NL goes into LLM prompt with schema context
5. **No query result caching** — repeated queries hit Supabase every time

## PERFORMANCE PATTERNS
1. Use `limit` parameter — PostgREST returns all rows without it
2. Use `select` to specify columns — reduce payload size
3. Use `order` with index columns — avoid full table scans
4. Use `eq` filters for indexed columns — leverages Postgres indexes
5. Batch inserts using `insert(table, [list of dicts])` — single HTTP call

## RLS PRODUCTION PATTERNS (Reference)
See [085-supabase-rls-patterns](knowledge/engineering/085-supabase-rls-patterns) for full RLS policy patterns.
For Legion's Supabase usage:
- Bot uses service role → RLS bypassed → external data isolation depends on bot logic
- For multi-tenant Supabase projects: anon key should be used for user-facing queries with RLS enforced

## DEBATE RECORD
Advocate: 7 | Skeptic: 6 | Judge: WRITE 7
Judge note: RLS bypass confirmed — but single-user internal bot use case makes this acceptable. Latency monitoring gap noted.
