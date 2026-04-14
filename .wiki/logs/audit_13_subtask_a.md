---
title: Audit 13 Subtask A
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
summary: '**Task:** Document & Archive ABANDONED features in `core/health_check.py`'
wikilinks: []
confidence: medium
source: research
---
# AUDIT-13 Subtask A — Log Entry

**Date:** 2026-04-12  
**Task:** Document & Archive ABANDONED features in `core/health_check.py`

## Actions Taken

1. **Read** `core/health_check.py` — identified 8 abandoned feature entries
2. **Removed** from `FEATURE_FLAGS`:
   - `openai_agents` (pkg: agents)
   - `owl` (pkg: camel)
   - `ag2` (pkg: autogen)
   - `smolagents` (pkg: smolagents)
   - `pydantic_ai` (pkg: pydantic_ai)
   - `agentops` (pkg: agentops, env: AGENTOPS_API_KEY)
   - `mirofish` (pkg: None, env: None)
   - `ruflo` (pkg: None, env: OPENROUTER_API_KEY)

3. **Created** `_ARCHIVED_FEATURES` dict at bottom of file with all 8 entries, each containing `status: abandoned`

4. **Added comment** at top of archive section:
   ```
   # Archived in AUDIT-13 — no pip package ever installed / key never set
   ```

## Result

- `FEATURE_FLAGS` now only contains `gemma4_local`
- `_ARCHIVED_FEATURES` contains all 8 abandoned features with `status: abandoned` field
- Health check logic unchanged — only active features are checked
- Tests pass (pre-existing failure in `test_humanization.py` unrelated to this change)
