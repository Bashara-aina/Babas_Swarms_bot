---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/logs/worker-subtask-3-gsa-wire-2026-04-12.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-13T01:00:00.244519"
}
---

# Worker Subtask 3: Wire GSA Voice into System Prompt Builder

**Date:** 2026-04-12  
**Status:** ✅ COMPLETED

## Changes Made

### File: `core/system_prompt_builder.py`

1. **Added import** (line 28):
   ```python
   from core.gsa_voice import classify_message_context, get_gsa_injection
   ```

2. **Added GSA injection block** after SOUL context (after line 85):
   ```python
   # 0b. GSA voice injection — comes AFTER soul but BEFORE task-specific context
   if user_msg:
       try:
           gsa_context = classify_message_context(user_msg)
           gsa_injection = get_gsa_injection(gsa_context)
           if gsa_injection:
               parts.append(gsa_injection)
       except Exception as e:
           logger.debug("[PromptBuilder] gsa_voice skipped: %s", e)
   ```

## Order Verification
- ✅ SOUL context remains section 0 (first)
- ✅ GSA injection is section 0b (after soul, before personality)
- ✅ Task-specific context (role_prompt) comes after GSA

## Smoke Test
```bash
python -c "from core.system_prompt_builder import build_full_system_prompt; print(build_full_system_prompt('', user_msg='pusing nih')[:500])"
```
**Result:** PASSED — output starts with `[LEGION SOUL` confirming correct ordering

## Notes
- Uses `user_msg` parameter to classify message context
- Gracefully falls back if `gsa_voice` module unavailable
- All existing parameters preserved in function signature
