---
title: Audit 13 Plan
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
summary: Every disabled feature must have an explicit flag and user message. No permanently
  dead code masquerading as live.
wikilinks: []
confidence: medium
source: research
---
# AUDIT 13 — Feature Flag Audit Plan
## Executive Summary
Every disabled feature must have an explicit flag and user message. No permanently dead code masquerading as live.

## Step 1 — Feature Flags Inventory

### From `core/health_check.py` — Experimental Agent SDKs (all permanently disabled)
| Flag | Default | Ever Set True? | Classification |
|------|---------|----------------|----------------|
| `openai_agents` | False | NO | ABANDONED — pip package never installed |
| `owl` (camel) | False | NO | ABANDONED — pip package never installed |
| `ag2` (autogen) | False | NO | ABANDONED — pip package never installed |
| `smolagents` | False | NO | ABANDONED — pip package never installed |
| `pydantic_ai` | False | NO | ABANDONED — pip package never installed |
| `agentops` | False | NO | ABANDONED — API key never set |
| `mirofish` | False | NO | ABANDONED — tools/mirofish not present |
| `ruflo` | False | NO | ABANDONED — server.js not present + API key missing |
| `gemma4_local` | False | NO | CONDITIONAL — requires Ollama + model pull |

### From environment variables — Core toggles (mixed status)
| Flag | Default | Ever Set True? | Classification |
|------|---------|----------------|----------------|
| `STREAM_RESPONSES` | true | YES | LIVE — streaming is active |
| `LEGION_SOUL_ENABLED` | true | YES | LIVE — soul engine is active |
| `LEGION_WIKI_ENABLED` | true | YES | LIVE — wiki is active |
| `LEGION_TASK_ROUTER_ENABLED` | false | NO | PLANNED — Layer 3 router for v2.0 |
| `LEGION_JARVIS_AUTOROUTE_ENABLED` | true | YES | LIVE — autoroute is active |
| `SCREENPIPE_ENABLED` | false | YES | CONDITIONAL — screen capture, opt-in |
| `SCREENPIPE_PROACTIVE_ENABLED` | true | YES | CONDITIONAL — proactive screenpipe |
| `LEGION_RAG_ENABLED` | false | NO | PLANNED — RAG pipeline for v2.0 |
| `LEGION_RAG_PROMPT_ENABLED` | false | NO | PLANNED — RAG prompt injection |
| `LEGION_EMOTION_PROMPT_ENABLED` | true | YES | LIVE — emotion modulation active |
| `LEGION_SKILLS_PROMPT_ENABLED` | true | YES | LIVE — skills system active |
| `LEGION_KNOWLEDGE_GRAPH_ENABLED` | false | NO | PLANNED — knowledge graph for v2.0 |
| `LEGION_UNIFIED_CONTEXT_ENABLED` | true | YES | LIVE — unified context active |
| `LEGION_WORKING_MEMORY_ENABLED` | true | YES | LIVE — working memory active |
| `COGNEE_ENABLED` | false | NO | CONDITIONAL — cognee dependency |
| `MCP_FILESYSTEM_ENABLED` | false | YES (rarely) | CONDITIONAL — MCP server |
| `MCP_OBSIDIAN_ENABLED` | false | YES (rarely) | CONDITIONAL — MCP server |
| `MCP_BROWSER_ENABLED` | false | YES (rarely) | CONDITIONAL — MCP server |

### Stub Code Found
| File | Stub Type | Classification |
|------|-----------|----------------|
| `core/daily_harvester/topic_budget.py:50` | `TODO: implement real git log analysis` | PLANNED |
| `core/daily_harvester/harvest_pipeline.py:167` | `TODO: use aiogram bot to send to BASHARA_TELEGRAM_ID` | PLANNED |
| `core/daily_harvester/source_strategy.py:68` | `TODO: real search integration` | PLANNED |
| `core/daily_harvester/topic_evolution.py:23` | `TODO: cross-reference with existing TOPIC_WEIGHTS.json` | PLANNED |
| `main.py:551` | `TODO: Consolidate into single briefing mechanism` | PLANNED |

---

## Step 2 — Dead Features (Never Set True)
1. **openai_agents** — ABANDONED
2. **owl** — ABANDONED  
3. **ag2** — ABANDONED
4. **smolagents** — ABANDONED
5. **pydantic_ai** — ABANDONED
6. **agentops** — ABANDONED
7. **mirofish** — ABANDONED
8. **ruflo** — ABANDONED
9. **LEGION_TASK_ROUTER_ENABLED** — PLANNED (keep stub)
10. **LEGION_RAG_ENABLED** — PLANNED (keep stub)
11. **LEGION_RAG_PROMPT_ENABLED** — PLANNED (keep stub)
12. **LEGION_KNOWLEDGE_GRAPH_ENABLED** — PLANNED (keep stub)
13. **COGNEE_ENABLED** — CONDITIONAL (keep, depends on optional cognee)

---

## Step 3 — Subtask Assignments

### SUBTASK A: Document ABANDONED features (health_check.py)
**Assigned to:** @worker  
**Files:** `core/health_check.py`  
**Action:** Add `status: abandoned` and `reason: "<reason>"` to each ABANDONED entry in `FEATURE_FLAGS` dict. Add user-facing message when triggered (disabled handler message).

### SUBTASK B: Archive dead feature entries
**Assigned to:** @worker  
**Files:** `core/health_check.py`  
**Action:** Move ABANDONED feature entries (openai_agents, owl, ag2, smolagents, pydantic_ai, agentops, mirofish, ruflo) to a `_ARCHIVED_FEATURES` section at bottom of the file with comment: `# Archived in AUDIT-13 — no pip package ever installed / key never set`.

### SUBTASK C: Add explicit flags to PLANNED stub files
**Assigned to:** @worker  
**Files:** `core/daily_harvester/topic_budget.py`, `core/daily_harvester/harvest_pipeline.py`, `core/daily_harvester/source_strategy.py`, `core/daily_harvester/topic_evolution.py`, `main.py`  
**Action:** Add `FEATURE_GIT_LOG_ANALYSIS_ENABLED = False  # Planned: v2.0` etc. at top of each file with user message when triggered.

### SUBTASK D: Add feature flags section to /status command
**Assigned to:** @worker  
**Files:** `handlers/system.py`  
**Action:** Add `FEATURE_FLAGS` display section to `cmd_status()` and `cmd_stats()` showing all flags and their current state.

### SUBTASK E: Verify all disabled features have user messages
**Assigned to:** @reviewer  
**Files:** All modified files  
**Action:** Run verification to ensure every disabled feature path has a corresponding user-facing message.

---

## Step 4 — Review
**Assigned to:** @reviewer  
Verify all changes are coherent, no dead code remains, and all user-facing messages are appropriate.

---

## Output Artifacts
- `.wiki/logs/audit_13_plan.md` — This file
- `.wiki/decisions/ADR-013-feature-flags.md` — Final decisions (do not modify SOUL.md, CLAUDE.md, LEGION_MASTER.md)
- Updated `core/health_check.py`
- Updated `handlers/system.py`
- Updated stub files with explicit flags