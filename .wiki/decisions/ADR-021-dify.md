---
title: "ADR-021: Dify Integration"
agent: "worker"
date: "2026-04-12"
status: "Accepted"
---
# ADR-021: Dify Integration

**Date:** 2026-04-12
**Status:** Accepted
**Agent:** worker

## Context

Legion needs a self-hosted AI workflow platform for:
1. Long-form document drafting (legal, compliance, reports)
2. Complex multi-step analysis
3. Workloads that shouldn't hit external APIs (privacy/compliance)

Dify (langgenius/dify) is an open-source self-hosted platform with:
- Workflow editor (no-code to low-code)
- Chat apps with conversation memory
- REST API for external callers
- Docker-based deployment

## Decision

Wire Dify as a new skill layer (`dify_analysis`) and HTTP client (`DifyClient`).

## Implementation

### Files Created

1. **`docker/dify-compose.yml`** — Standalone compose for Dify (api, worker, web, postgres:15-alpine, redis:7-alpine)
   - Ports: 5001 (api), 3001 (web)
   - Uses `OPENROUTER_API_KEY` from env for LLM backend
   - Persists data in named Docker volumes

2. **`core/integrations/dify_client.py`** — `DifyClient` class
   - `run_workflow(workflow_id, inputs, user_id)` → blocking workflow execution
   - `chat(app_id, message, conversation_id, user_id)` → chat app interaction
   - `health_check()` → bool
   - Graceful degradation when `DIFY_API_KEY` not set (logs warning, returns unavailable)
   - 120s timeout on all requests

3. **`core/skills/dify_analysis.py`** — Skill module
   - `execute(task_type, content, workflow_id)` entry point
   - `WORKFLOW_MAP` dict for task_type → workflow_id routing
   - Trigger keywords: draft, tulis, buat dokumen, analisis dokumen, review kontrak, legal, compliance, ToS, disclaimer, laporan panjang
   - Auto-registers in `SKILL_REGISTRY` via `_register_dify_analysis_skill()`

### Files Modified

- `core/skills/__init__.py` — Added `dify_analysis` import
- `core/skills/dify_analysis.py` — Added skill registration function
- `.env.example` — Added `DIFY_API_URL`, `DIFY_API_KEY`, `DIFY_SECRET_KEY`, `DIFY_DB_PASSWORD`

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Separate client class + skill module | Clean separation: client handles HTTP, skill handles orchestration |
| Graceful degradation | Bot continues working if Dify not configured; user gets helpful setup message |
| Blocking response_mode | Simpler integration for MVP; streaming can be added later |
| Skill registered via `_register_*()` at import time | Consistent with `code_review.py` and `deep_research.py` pattern |
| Workflow IDs empty strings initially | User must create actual workflows in Dify Web UI and fill in IDs |

## Consequences

**Positive:**
- Self-hosted LLM workflow execution (privacy, compliance, cost control)
- No-code workflow creation via Dify Web UI
- Extensible: can add more workflows over time

**Negative:**
- Additional docker service to maintain
- Requires user to create and configure workflows in Dify Web UI

## Alternative Considered

- **LangFlow**: Similar but Dify has better chat app support and simpler deployment
- **Direct API calls without client class**: Less testable, more duplication across handlers
- **Airflow/Luigi**: Overkill for this use case; too heavyweight

## Notes

- Docker compose file uses `---` document separator which is valid for Docker Compose 2.x multi-document YAML but the trailing `---` after volumes is redundant. The file is valid.
- `dify-worker` uses same image as `dify-api` but with `MODE: worker` env var — this is the standard Dify pattern.