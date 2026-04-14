---
title: Legion Audit 2026 04 12
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
summary: '| Bug | Location | Severity | Fix Applied |'
wikilinks: []
confidence: medium
source: research
---
# Legion Code Audit — 2026-04-12

## Status: COMPLETED (3-hour audit cycle)

## Bugs Fixed

| Bug | Location | Severity | Fix Applied |
|-----|----------|----------|-------------|
| Repetition detection too strict | `legion/anti_slop/core.py` | P1 | Changed `len(w) > 3` to `len(w) >= 2` |
| `_update_stats()` never called | `legion/anti_slop/core.py` | P1 | Added `_update_stats(result)` calls before all return paths |
| Missing `_verify_hmac()` | `core/webhooks/server.py` | P1 | Added `_verify_hmac()` method with proper security logic |
| Missing `handle()` functions | `core/webhooks/handlers/*.py` | P1 | Added `handle(payload, source)` to github, rumahlabuh, system |
| Duplicate `_update_stats()` call | `legion/anti_slop/integration.py` | P1 | Removed duplicate (now handled internally) |
| `init_personality_state()` missing | `tools/letta_personality.py` | P1 | Added `init_personality_state()` function |
| `datetime.utcnow()` deprecation | 6 files | P2 | Migrated to `datetime.now(timezone.utc)` |

## Wave Completion Status

### Wave 1 ✓
- W-1: Import Chain Audit ✓
- W-2: Agent Registry Loading ✓ (107 agents loaded)
- W-3: Soul/Personality Wiring ✓
- F-1: Async/Await Completeness ✓
- F-2: Error Handling Audit ✓

### Wave 2 ✓
- F-3: Type Hint Audit ✓ (handlers use proper Message type hints)
- C-1: Routing Logic Audit ✓ (no conflict - routers are complementary)
- C-2: Config Validation ✓ (all YAML files parseable)

### Wave 3 ✓
- H-1: Handler Signature Audit ✓ (proper aiogram signatures)
- H-2: Tool Integration Audit ✓ (screenpipe_tool works, init_personality_state added)

## Test Status
- **305 passed** (all tests passing)
- Before audit start: some failures in anti_slop tests

## Key Findings

1. **Dual router system works correctly** - Intent router and autonomous router are complementary
2. **Agent Registry healthy** - 107 agents loaded from departments.yaml
3. **PERSONALITY_WRAPPER** - 731 chars, properly used in system prompts
4. **get_disagreement_prompt()** - 2199 chars, properly wired

## Recommendations

1. Write integration tests for webhook handlers
2. Add runtime verification for YAML agent configs
3. Consider adding type hints to internal functions (P3)

## Logged by
- Worker agent (task_id: ses_280184632ffeVbrwXWH8yBDVeg)
- Reviewer findings: `.wiki/issues/reviewer-findings-2026-04-12.md`
