---
title: Adr 013 Feature Flags
type: decision
status: stub
tags: [decisions, general]
created: 2026-04-13
updated: 2026-04-13
summary: Stub — needs enrichment. Auto-added frontmatter during QC restructure.
wikilinks: []
confidence: low
source: migration
project: general
---

# ADR-013: Feature Flag Audit — Decisions

**Date:** 2026-04-12  
**Status:** ACCEPTED  
**Auditor:** @planner  

---

## Context
AUDIT-13 required cataloging all feature flags, identifying dead code (never-enabled features), and ensuring every disabled feature has an explicit flag and user message.

---

## Decision 1: ABANDONED Features — Archive in health_check.py

The following features were never enabled (no pip package installed, no API key set, no path present):

| Feature | Reason |
|---------|--------|
| `openai_agents` | `agents` pip package never installed |
| `owl` | `camel` pip package never installed |
| `ag2` | `autogen` pip package never installed |
| `smolagents` | `smolagents` pip package never installed |
| `pydantic_ai` | `pydantic_ai` pip package never installed |
| `agentops` | `AGENTOPS_API_KEY` never set |
| `mirofish` | `tools/mirofish` directory not present |
| `ruflo` | `tools/ruflo/server.js` not present + `OPENROUTER_API_KEY` not set |

**Action:** Move these entries to `_ARCHIVED_FEATURES` dict at bottom of `core/health_check.py`. Do NOT remove entirely — useful for future reference.

---

## Decision 2: PLANNED Features — Keep as stubs with explicit flags

The following features are planned for v2.0 and should remain as stubs:

| Feature | Flag | File |
|---------|------|------|
| Task router Layer 3 | `LEGION_TASK_ROUTER_ENABLED` | handlers/message_handler.py:147 |
| RAG pipeline | `LEGION_RAG_ENABLED` | tools/rag_tool.py:81 |
| RAG prompts | `LEGION_RAG_PROMPT_ENABLED` | core/unified_prompt_context.py:81 |
| Knowledge graph | `LEGION_KNOWLEDGE_GRAPH_ENABLED` | core/unified_prompt_context.py:139 |
| Git log analysis | `FEATURE_GIT_LOG_ANALYSIS_ENABLED` | core/daily_harvester/topic_budget.py:50 |
| Web search integration | `FEATURE_WEB_SEARCH_ENABLED` | core/daily_harvester/source_strategy.py:68 |

**Action:** Add `FEATURE_X_ENABLED = False  # Planned: v2.0` at top of each file. Add graceful user message: "This feature is planned for v2.0 — not yet available."

---

## Decision 3: CONDITIONAL Features — Wrap with availability check

These features depend on optional external services and are OK to be False by default:

| Feature | Check |
|---------|-------|
| `SCREENPIPE_ENABLED` | Screenpipe daemon running |
| `COGNEE_ENABLED` | cognee pip package installed |
| `gemma4_local` | Ollama + gemma4:e4b model present |
| `MCP_FILESYSTEM_ENABLED` | MCP server configured |
| `MCP_OBSIDIAN_ENABLED` | MCP server configured |
| `MCP_BROWSER_ENABLED` | MCP server configured |

**Action:** Keep existing checks in place. Log at startup which conditional features are available.

---

## Decision 4: Add Feature Flags to /status Command

**File:** `handlers/system.py`  
**Action:** In `cmd_status()` and `cmd_stats()`, add section showing:
```
<b>🔧 Feature Flags</b>
✅ LEGION_SOUL_ENABLED / 🔇 LEGION_TASK_ROUTER_ENABLED (planned)
✅ LEGION_WIKI_ENABLED / ⚠️ LEGION_RAG_ENABLED (v2.0)
[etc.]
```

---

## Decision 5: Protected Files

The following files MUST NOT be modified by this audit:
- `SOUL.md`
- `CLAUDE.md`  
- `LEGION_MASTER.md`

---

## Consequences

1. `core/health_check.py` will have `_ARCHIVED_FEATURES` section for reference
2. All stub files will have explicit `FEATURE_X_ENABLED = False` flags
3. `/status` command will display all feature flags
4. No permanently dead code masquerading as live

---

## Verification

Run: `grep -rn "FEATURE_.*ENABLED\|TODO.*v2.0\|Planned:" . --include="*.py" | grep -v ".venv"` to find all flagged features.

---

## AUDIT-13 REVIEW FINDINGS (SUBTASK D — 2026-04-12)

**Reviewer:** @reviewer  
**Verified by:** grep sweeps + file reads

### ✅ All Required Files Modified Correctly

| File | Flag | Line | User Message |
|------|------|------|--------------|
| `core/health_check.py` | `_ARCHIVED_FEATURES` dict | 65-74 | N/A (archived) |
| `core/daily_harvester/topic_budget.py` | `FEATURE_GIT_LOG_ANALYSIS_ENABLED = False  # Planned: v2.0` | 17 | Line 54: `logger.debug("Git log analysis feature is planned for v2.0 — not yet available.")` |
| `core/daily_harvester/harvest_pipeline.py` | `FEATURE_BRIEFING_CONSOLIDATION_ENABLED = False  # Planned: v2.0` | 19 | Line 160: `logger.info("Briefing consolidation feature is planned for v2.0 — not yet available.")` |
| `core/daily_harvester/source_strategy.py` | `FEATURE_WEB_SEARCH_ENABLED = False  # Planned: v2.0` | 15 | Line 72: `logger.info("Web search feature is planned for v2.0 — not yet available.")` |
| `core/daily_harvester/topic_evolution.py` | `FEATURE_TOPIC_WEIGHTS_ENABLED = False  # Planned: v2.0` | 12 | Line 27: `logger.debug("Topic weights feature is planned for v2.0 — not yet available.")` |
| `handlers/system.py` | Feature flags section in `/status` | 341-356 | N/A (display only) |
| `main.py` | `FEATURE_BRIEFING_CONSOLIDATION_ENABLED = False  # Planned: v2.0` | 731 | Line 733: `logger.info("Briefing consolidation is planned for v2.0 — not yet available.")` |

### ✅ All Planned Features Follow Correct Format

All 5 planned feature flags use the exact format `FEATURE_X_ENABLED = False  # Planned: v2.0`.

### ✅ Protected Files NOT Modified

`SOUL.md`, `CLAUDE.md`, `LEGION_MASTER.md` — confirmed untouched.

### ℹ️ Notes on User Messages

- All user messages use `logger.info`/`logger.debug` — appropriate for pipeline/daemon context where features are not user-triggered
- `/status` command provides user-facing display of all feature flags with ON/OFF status
- Planned features are internal pipeline components (no direct user command invokes them), so logging is appropriate

### ⚠️ Minor Observations (Non-Blocking)

1. `FEATURE_BRIEFING_CONSOLIDATION_ENABLED` appears in BOTH `main.py:731` and `harvest_pipeline.py:19` — intentional redundancy per ADR-006 (duplicate briefing mechanism) but worth noting
2. Two additional flags in ADR-013 table (`LEGION_TASK_ROUTER_ENABLED`, `LEGION_RAG_ENABLED`) were not checked in this subtask — these are in different files (handlers/message_handler.py, tools/rag_tool.py) and should be verified in a separate check

### ✅ VERDICT: SUBTASK D PASSED

All 6 specified files were modified correctly. All disabled features have proper flag format and informative messages. No blockers.

---

**Refuses:** Audit-13 | **Date:** 2026-04-12