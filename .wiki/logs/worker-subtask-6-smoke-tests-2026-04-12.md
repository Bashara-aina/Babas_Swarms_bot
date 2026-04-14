---
title: Worker Subtask 6 Smoke Tests 2026 04 12
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
summary: Run smoke tests for GSA Voice implementation (Step 6 from LEGION_VOICE_UPGRADE.md).
wikilinks: []
confidence: medium
source: research
---
# Worker Subtask 6: GSA Voice Smoke Tests — 2026-04-12

## Task
Run smoke tests for GSA Voice implementation (Step 6 from LEGION_VOICE_UPGRADE.md).

## Results

### Test 1: Banned Phrases Removed ✅
```python
assert "semangat" not in enforce_character("Semangat ya kamu pasti bisa!").lower()
assert not enforce_gsa_structure("Iya, saya akan bantu").lower().startswith("iya")
```
**Status**: PASSED (after fix)

**Fix Applied**: `GSA_BANNED_PHRASES` in `core/character_enforcer.py` had `"semangat terus ya"` but not the root word `"semangat"`. Added `"semangat"` to the list directly.

### Test 2: Context Classification ✅
```python
assert classify_message_context("pusing nih thesis stuck") == MessageContext.EMOTIONAL
assert classify_message_context("ada bug di handler") == MessageContext.TECHNICAL
assert classify_message_context("gimana menurut lo pasar properti?") == MessageContext.ANALYTICAL
assert classify_message_context("lagi ngopi") == MessageContext.CASUAL
```
**Status**: PASSED

### Test 3: GSA Injection in System Prompt ✅
```python
prompt = build_full_system_prompt(role_prompt='', user_msg='pusing nih')
assert "GSA Voice" in prompt
assert "validate" in prompt.lower() or "Validate" in prompt
```
**Status**: PASSED (after correcting call signature)

**Note**: The test originally called `build_full_system_prompt("pusing nih")` but the function signature is `build_full_system_prompt(role_prompt, user_id="", user_msg="", ...)`. The correct call passes `user_msg="pusing nih"`.

### Full Pytest Suite ✅
```
pytest tests/ -x --asyncio-mode=auto -q
======================= 305 passed, 1 warning in 20.67s ========================
```
No regressions.

## Files Modified
- `core/character_enforcer.py`: Added `"semangat"` to `GSA_BANNED_PHRASES` list (line 76)

## Completion
All GSA voice smoke tests passed. Ready for Step 7 (Live conversation test with user validation).