---
title: Audit 13 Subtask C
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
summary: '**Task:** Add Feature Flags to /status command'
wikilinks: []
confidence: medium
source: research
---
# AUDIT-13 SUBTASK C — Log Entry

**Date:** 2026-04-12
**Task:** Add Feature Flags to /status command
**File Modified:** `handlers/system.py`

## What Was Done

Added a `_feature_flags_block()` helper function and integrated it into `cmd_status()` to display all feature flags with emoji indicators.

### Implementation Details

1. **New function `_feature_flags_block()`** (lines 336–407) returns an HTML-formatted string with three sections:

   - **🔧 Feature Flags** — Planned features (explicit `FEATURE_*_ENABLED` flags from codebase):
     - `FEATURE_GIT_LOG_ANALYSIS_ENABLED` — Git log analysis [ON/OFF (v2.0)]
     - `FEATURE_BRIEFING_CONSOLIDATION_ENABLED` — Briefing consolidation [ON/OFF (v2.0)]
     - `FEATURE_WEB_SEARCH_ENABLED` — Web search integration [ON/OFF (v2.0)]
     - `FEATURE_TOPIC_WEIGHTS_ENABLED` — Topic weights engine [ON/OFF (v2.0)]
     - ✅ shown when env var is set to "1", "true", "yes", or "on"
     - 🔇 shown when disabled

   - **📦 Conditional Features** — From `core/health_check.py` `FEATURE_FLAGS` and `_ARCHIVED_FEATURES`:
     - Shows `gemma4_local` and other health-checkable features
     - ✅ for available, ⚠️ for unavailable, 🔇 for archived

   - **🔗 External Services** — Optional dependency checks:
     - `VOICEVOX` — checked via `importlib.util.find_spec("voicevox_core")`
     - `CHROMADB` — checked via `import chromadb`
     - ✅ for loaded/connected, ⚠️ for not installed/not connected

2. **Modified `cmd_status()`** — Added `feature_block = _feature_flags_block()` call and appended `{feature_block}` to the output text, separated by `\n\n`.

### Emoji Legend
- ✅ = Active/enabled feature
- 🔇 = Disabled feature (flag off or archived)
- ⚠️ = Conditional feature (optional dependency missing)

### Verification
- Syntax check passed: `python -c "import ast; ast.parse(open('handlers/system.py').read())"`