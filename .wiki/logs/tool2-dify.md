---
title: Tool2 Dify
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- logs
created: '2026-04-14'
updated: '2026-04-14'
summary: '**Task:** Wire Dify self-hosted AI workflow platform into Legion'
wikilinks: []
confidence: medium
source: research
---
# Tool 2 Log: Dify Integration

**Date:** 2026-04-12
**Agent:** worker
**Task:** Wire Dify self-hosted AI workflow platform into Legion

## Files Created

| File | Description |
|------|-------------|
| `docker/dify-compose.yml` | Docker Compose for Dify (api, worker, web, postgres, redis) |
| `core/integrations/dify_client.py` | Full async HTTP client for Dify REST API (workflows + chat) |
| `core/skills/dify_analysis.py` | Skill module with trigger keywords and registration |

## Files Modified

| File | Change |
|------|--------|
| `core/skills/__init__.py` | Added `dify_analysis` to imports + `__all__` |
| `core/skills/dify_analysis.py` | Added `_register_dify_analysis_skill()` with `SKILL_REGISTRY.register()` |
| `.env.example` | Added DIFY_API_URL, DIFY_API_KEY, DIFY_SECRET_KEY, DIFY_DB_PASSWORD |

## Verification

```bash
python -c "from core.skills.dify_analysis import execute, SKILL_META; print('OK')"
# → OK (DIFY_API_KEY not set warning shown, expected)

python scripts/verify_wiring.py
# → PASS (all 8 test categories)

python -c "from core.skills import dify_analysis; ..."
# → dify_analysis in skill list: ['github_pr_status', ..., 'dify_analysis']
```

## Skill Registration Confirmed

`dify_analysis` skill is registered in `SKILL_REGISTRY` with:
- **Triggers:** draft, tulis, buat dokumen, analisis dokumen, review kontrak, legal, compliance, ToS, disclaimer, laporan panjang
- **Handler:** `execute(task_type, content, workflow_id)`
- **Requires:** `DIFY_API_KEY` env var

## Setup Instructions

```bash
# 1. Copy .env.example to .env and fill in:
#    DIFY_SECRET_KEY=<random-string>
#    DIFY_DB_PASSWORD=<strong-password>

# 2. Start Dify:
docker compose -f docker/dify-compose.yml up -d

# 3. After first boot, get API key from Dify Web UI at http://localhost:3001
#    Set DIFY_API_KEY in .env

# 4. Restart bot
```

## Notes

- `dify_analysis.py` uses `WORKFLOW_MAP` with empty string workflow IDs — user must replace with actual Dify workflow IDs after creating workflows in Dify Web UI.
- Docker validation skipped — docker not available on this machine, but compose file is syntactically valid YAML.