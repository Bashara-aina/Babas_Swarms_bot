---
title: Observability Stack
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- observability-stack.md
created: '2026-04-14'
updated: '2026-04-14'
summary: Prometheus metrics on :8001, AgentOps optional, local structured JSON logs,
  in-memory cost tracking — no unified dashboard.
wikilinks: []
confidence: medium
source: research
---

# Observability Stack

## ONE-LINE SUMMARY
Prometheus metrics on :8001, AgentOps optional, local structured JSON logs, in-memory cost tracking — no unified dashboard.

## FACTS

### Metrics Infrastructure (`core/observability/`)
**metrics.py** — Prometheus metrics server on port 8001:
- `swarm_requests_total{agent, status}` — Counter
- `swarm_latency_seconds{agent}` — Histogram with buckets [0.5, 1, 2, 5, 10, 20, 30, 60, 120] seconds
- `swarm_cache_hits_total{agent}` — Counter
- `swarm_cache_misses_total{agent}` — Counter
- `swarm_errors_total{agent, error_type}` — Counter
- `swarm_active_threads` — Gauge (active conversation threads)
- `swarm_cache_hit_rate{agent}` — Gauge (rolling cache hit rate)
- Graceful fallback if prometheus_client not installed — logs "metrics disabled"
- Structured JSON logs emitted to swarm-bot.log via `StructuredLogger` class

**__init__.py** — Local observability + AgentOps:
- `_PROVIDER_STATS` dict: per-provider {calls, tokens, latency_ms, errors}
- `track_agent()` decorator wraps async functions to record latency + tokens
- `get_metrics_snapshot()` — returns current stats dict
- `render_metrics_html()` — formats metrics for Telegram display
- `notify_limit_warnings()` — sends Telegram warning when provider at 80%+ daily limit
- AgentOps integration: `init_observability()` tries to init if `AGENTOPS_API_KEY` set, tags with ["legionswarm", "telegram-bot", "rtx3060"]

### Cost Tracking (`swarms_bot/routing/budget_manager.py`)
- `BudgetManager` class — in-memory only (no Redis/SQLite persistence)
- `CostEntry` dataclass: timestamp, agent, model, cost_usd, tokens_in, tokens_out, task_type
- `record_cost()` — appends entry, keeps max 10000 (FIFO trim)
- `check_budget()` — daily/monthly spend vs limits (default $50/day, $500/month)
- `get_cost_breakdown(period)` — by_agent, by_model, by_task_type, total_tokens
- `format_budget_html()` — Telegram-formatted status
- No automatic cost recording from LLM client — must be called explicitly by callers

### Supabase Query Monitoring (`tools/supabase_client.py`)
- `health_check()` — returns {ok, status_code, latency_ms} for Supabase project
- `introspect_schema()` — reads PostgREST OpenAPI spec (no custom metrics)
- `query_natural()` — LLM translates NL → PostgREST, latency tracked via time.monotonic()
- No query-level performance metrics (duration per query, slow query log)
- Connection: single `httpx.AsyncClient(timeout=20.0)` shared instance

### Session Transcripts (`core/session/transcript.py`)
- SQLite at `data/session_transcripts.db`
- Schema: id, thread_id, user_id, role, content, model_used, timestamp
- Content truncated to 8000 chars on save
- No automatic recording — callers invoke `save_turn()` explicitly

### Memory Storage (`tools/memory.py`)
- SQLite at `~/.legion_memory.db` (or `MEMORY_DB_PATH` env var)
- Schema: id, text, tags, source, tfidf, created, accessed
- No encryption at rest
- Mem0 and OpenViking write to external services (their own observability)

## LEGION BEHAVIOR RULES
1. Prometheus metrics available at http://localhost:8001/metrics for scraping
2. Budget limits enforced before LLM calls — `check_budget()["allowed"]` gates execution
3. Cost recording is opt-in — no automatic instrumentation in llm_client
4. AgentOps is passive (no active session tracking visible in code)
5. Structured logs use JSON — machine-parseable for log aggregation

## EXAMPLES
Prometheus scrape example:
```bash
curl http://localhost:8001/metrics | grep swarm_latency
```
Telegram budget check: `/budget` command calls `format_budget_html()`

## ANTI-PATTERNS
1. BudgetManager in-memory only — single process, no cross-restart persistence
2. No automatic cost recording from LLM responses — callers must call `record_cost()` manually
3. No slow query logging for Supabase — queries that timeout just raise RuntimeError
4. Session transcript truncation at 8000 chars — long code blocks may be cut mid-token

## GAPS
1. **No Prometheus alerting rules** — no Alertmanager integration
2. **No Grafana dashboard** — metrics exist but no visualization
3. **No distributed tracing** — no request ID / correlation ID across agent calls
4. **No query-level Supabase metrics** — cannot identify slow tables or missing indexes
5. **No cost per-user breakdown** — BudgetManager aggregates all users, not per-user spend
6. **No PII redaction in structured logs** — user message content logged verbatim

## DEBATE RECORD
Advocate: 9 | Skeptic: 5 | Judge: WRITE 9
Judge note: Observability gaps confirmed — no Grafana, no alerting, no per-user cost tracking, PII in logs.
