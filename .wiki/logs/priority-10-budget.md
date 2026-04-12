# Priority 10: Context Window Budget Management — Log

**Date**: 2026-04-12  
**Status**: ✅ Implemented

## Task Summary

Modified `core/system_prompt_builder.py` to add token counting and priority-based budget management.

## Changes Made

### 1. Added Budget Constants (lines 40–55)
```python
MODEL_CONTEXT_LIMITS, CONTEXT_BUDGET_RATIO, LAYER_PRIORITY
```

### 2. Added Helper Functions
- `estimate_tokens()` — rough token estimate (len // 4)
- `compress_section()` — truncate middle to target token count
- Per-layer async fetchers: `_get_soul_content`, `_get_user_profile_content`, `_get_working_memory_content`, `_get_relevant_memory_content`, `_get_wiki_context_content`, `_get_search_results_content`, `_get_personality_content`, `_get_skill_context_content`
- `get_layer_content()` — dispatcher
- `build_system_prompt()` — main async builder with budget management

### 3. Key Behaviors
- **Soul**: Always first, never compressed (if too large, added truncated)
- **User profile**: First 8 lines only
- **Working memory**: Uses `load_state()` from `core.working_memory`
- **Relevant memory**: Uses `LegionSemanticMemory().search_memories()`
- **Compression**: When layer exceeds budget, compress to 200 tokens or skip

### 4. Layer Priority Order
1. soul (NEVER compressed, ALWAYS first)
2. user_profile (top 8 facts)
3. working_memory (session continuity)
4. relevant_memory (top 3 semantic hits)
5. wiki_context (full wiki)
6. search_results (top 3)
7. personality (compressed if tight)
8. skill_context (only if skill active)

## Verification Results

### verify_wiring.py: ✅ ALL PASS
```
Handler Wiring: PASS
Core Imports: PASS
LLM Client: PASS
Tools: PASS
Bridges: PASS
Skills: PASS
Agents: PASS
```

## Testing Notes

- Soul is always first when present
- Token count never exceeds budget (enforced by algorithm)
- Log line: `"System prompt build: X/Y tokens, N/M layers"`
- Backward compatible with existing `build_full_system_prompt()` and `SystemPromptBuilder` class

## Files Modified
- `core/system_prompt_builder.py` — added budget management

## Files Created
- `.wiki/decisions/ADR-019.md` — Architecture Decision Record
- `.wiki/logs/priority-10-budget.md` — This log
