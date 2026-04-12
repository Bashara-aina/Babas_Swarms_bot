# Fix 2 Log: Chinese Characters Leak

**Date**: 2026-04-12
**Status**: ✅ COMPLETE

## Subtasks Completed

### 2A: Added language enforcer to `core/character_enforcer.py`
- Added `CJK_PATTERN` regex to detect Chinese/Japanese/Korean characters
- Added `ARABIC_PATTERN` regex to detect Arabic script
- Added `has_non_allowed_script()` function
- Added `strip_non_allowed_script()` function with CJK→Indonesian replacements
- Added `enforce_language()` main enforcement function
- **Verify**: ✅ `has_non_allowed_script('好奇')` returns True, `enforce_language('kamu好奇吗')` returns 'kamupenasaran?'

### 2B: Added language rules to `SOUL.md`
- Added "LANGUAGE RULES (absolute, no exceptions)" section at end of SOUL.md
- Rules: Indonesian primary, English technical, NEVER Chinese characters, "好奇" → "penasaran"
- **Verify**: ✅ `grep -A5 "LANGUAGE RULES" SOUL.md` shows the rules

### 2C: Wired `enforce_language()` into `enforce_character()`
- Added call to `enforce_language()` at the START of `enforce_character()` function
- Runs BEFORE any other processing (forbidden phrases, GSA banned, etc.)
- **Verify**: ✅ `enforce_character('test好奇response')` returns 'Testpenasaranresponse' with no Chinese

### 2D: Checked for Chinese-leaking models
- **Found**: qwen (Alibaba), glm (Zhipu/Chinese), deepseek models in config files
- These are used extensively as primary/fallback models in `config/departments.yaml`
- The `enforce_language()` function will strip any CJK characters that leak through
- **Report**: Chinese models are widespread - language enforcement is the correct approach

### 2E: Full Fix 2 Verification
- All tests passed:
  - `has_non_allowed_script('好奇')` → True
  - `has_non_allowed_script('halo')` → False
  - `enforce_language('kamu好奇吗')` → 'kamupenasaran?'

## Next
Proceed to Fix 3: No Web Search
