---
title: "ADR-053: Orphan Module Classification Policy"
audit: "AUDIT 05"
date: "2026-04-13"
likely_candidates: "`character_voice.py`, `error_humanizer.py`, `health.py`, `intent_classifier.py`, `natural_command_parser.py`, `research_policy.py`, `self_awareness_gate.py`, `swarm.py`, `wiki_bridge.py`"
status: "PROPOSED"
---
# ADR-053: Orphan Module Classification Policy
**Date:** 2026-04-13  
**Status:** PROPOSED  
**Audit:** AUDIT 05

## Context

During AUDIT 05, 18 modules in `core/` were identified as having zero internal imports (no other core/ file imports them). These represent potential dead code, architectural drift, or intentionally standalone modules.

### Identified Orphan Modules

| Module | Est. Risk |
|--------|-----------|
| `core/agent.py` | Medium |
| `core/capability_audit.py` | Medium |
| `core/character_voice.py` | High |
| `core/emotion_tracker.py` | Low |
| `core/error_humanizer.py` | Medium |
| `core/health.py` | Medium |
| `core/intent_classifier.py` | High |
| `core/natural_command_parser.py` | Medium |
| `core/openai_agents_bridge.py` | Low (lazy) |
| `core/opencode_bridge.py` | Low (hooks) |
| `core/research_policy.py` | Low |
| `core/self_awareness_gate.py` | High |
| `core/swarm.py` | High |
| `core/task_router.py` | Low (tests) |
| `core/tmp_cleanup.py` | Low (tests) |
| `core/watchdog.py` | Medium |
| `core/wiki_auto_ingest.py` | High |
| `core/wiki_bridge.py` | Medium |

## Decision

Classify each orphan module into one of three categories:

### Category A: Wire-in (Keep, Integrate)
Modules that have external callers (handlers/, tools/, agents/, tests/) but lack internal core/ callers. These should remain but may need wiring.

**Likely candidates:** `agent.py`, `capability_audit.py`, `openai_agents_bridge.py`, `opencode_bridge.py`, `watchdog.py`

### Category B: Disable (Move to Graveyard)
Modules with no callers and no clear purpose. Move to `graveyard/` directory for 30-day retention before deletion.

**Likely candidates:** `emotion_tracker.py`, `task_router.py`, `tmp_cleanup.py`, `wiki_auto_ingest.py`

### Category C: Investigate (Standalone Purpose)
Modules that are intentionally standalone (bridges, hooks, policies) or have unclear purpose requiring investigation.

**Likely candidates:** `character_voice.py`, `error_humanizer.py`, `health.py`, `intent_classifier.py`, `natural_command_parser.py`, `research_policy.py`, `self_awareness_gate.py`, `swarm.py`, `wiki_bridge.py`

## Consequences

### Pros
- Clearer codebase with understood module purposes
- Reduced maintenance burden
- Faster CI/build times
- Lower security attack surface

### Cons
- Risk of removing modules that are called dynamically
- Investigation time required (est. 2-3 hours for full audit)
- Potential breaking changes if external callers exist

## Implementation

1. **Week 1:** Grep entire codebase for each orphan module name
2. **Week 2:** Classify each module (A/B/C)
3. **Week 3:** Wire-in Category A modules, move Category B to graveyard
4. **Week 4:** Investigate Category C, finalize disposition

## Notes

- `openai_agents_bridge.py` and `opencode_bridge.py` are likely intentionally lazy-loaded (see `_LAZY_CORE_SUBMODULES` in `__init__.py`)
- `health.py` may be superseded by `observability/` package
- `intent_classifier.py` appears to overlap with `intent_router.py`
