# Worker: Fix Wiki Blockers — 2026-04-12

## Task
Fix 2 critical blockers found by reviewer in cycles 1-5 wiki pages:
1. `intent-routing-map.md` — incorrect routing description
2. `llm-routing-map.md` — incorrect "general" agent model

## Source Files Verified

### core/intent_router.py (491 lines)
- `Intent` enum has **24 intents** (not 23)
- `_INTENT_TO_AGENT` maps to only **9 agents**: coding, reviewer, math, think, analyst, general, researcher, computer
- 16 intents fall through to `general` agent (no dedicated mapping)
- Two-stage pipeline: `classify_intent_fast()` → `classify_intent_llm()` when confidence < 0.70
- Confidence thresholds: 0.95 (URL), 0.50-0.95 (pattern), 0.85 (LLM), 0.70 (LLM trigger), 0.65 (hint injection)

### core/agent_registry.py (831 lines)
- `_LEGACY_AGENT_MODELS` dict (lines 282-306) shows actual primary model per agent
- Line 290: `"general": "ollama_chat/gemma4:e4b"` — **NOT MiniMax M2.7!**
- `LEGACY_FALLBACK_CHAIN` dict (lines 313-374) shows full fallback chains
- MiniMax-M2.7 is first fallback for all agents, NOT the primary

## Changes Made

### intent-routing-map.md
**Before**: Claimed 23 handlers with handler-based routing
**After**: Accurate description of:
- 24 intents (full list)
- 9 agents via `_INTENT_TO_AGENT`
- Two-stage classification pipeline
- Confidence thresholds and flags
- Tools/research flags per intent

### llm-routing-map.md
**Before**: Listed "general" as `MiniMax M2.7`
**After**: 
- Corrected "general" primary to `ollama_chat/gemma4:e4b`
- Added critical warning that "general" is a vision model, not text
- Full table of 22 agents with correct primary models
- Full fallback chains with cost estimates
- Hardware constraints (RTX 3060 VRAM limits)

## LOOP_LOG Updated
- Added "Blocker Fixes (Post-Review)" section
- Documents both fixes with before/after summary

## Verification
Both pages now verified against actual source code:
- intent-routing-map.md: matches `core/intent_router.py` implementation
- llm-routing-map.md: matches `core/agent_registry.py:_LEGACY_AGENT_MODELS`

## Status: COMPLETE
