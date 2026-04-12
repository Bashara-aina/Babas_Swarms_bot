# Priority 5 — Clarifying Questions Log
**Date:** 2026-04-12
**Agent:** worker (Bashara)
**Task:** Implement Priority 5 from Legion depth upgrade

## What was done

### 1. Created `core/clarification.py`
Two async functions as specified:
- `should_clarify(message, intent, confidence)` — returns True when confidence < 0.4 AND word_count < 8, excluding greetings
- `generate_clarification(message, intent)` — returns ONE specific question, no lists

Key design decisions:
- 8-word threshold (not 15) — shorter, more responsive
- `NEVER_CLARIFY` set for greetings/courtesies
- Rule-based generation (no LLM call) — fast and deterministic
- Intent-specific question patterns for common ambiguous phrases

### 2. Wired into `handlers/message_handler.py`
Inserted clarification intercept in `handle_plain_message()` at line ~190:
```python
try:
    from core.clarification import ask_if_needed
    clarification_q = await ask_if_needed(user_msg, skill_match.skill_name, skill_match.confidence)
    if clarification_q:
        await msg.answer(clarification_q)
        auto_router.record_performance(skill_match.skill_name, True)
        return
except Exception:
    pass  # Non-fatal — proceed to normal routing
```

Fires BEFORE the chat fallback, so ambiguous messages get a clarifying question instead.

### 3. Verification
```
python scripts/verify_wiring.py
All wiring checks passed!
```

## Expected behavior
| Message | Condition | Result |
|---------|-----------|--------|
| "fix this" | 2 words, low conf | "Fix what exactly? Paste the code or error." |
| "Hei" | 1 word, in NEVER_CLARIFY | proceeds normally |
| "Analisis sistem memory..." | 7 words, specific intent | proceeds normally |
| "search" | 1 word, low conf | "Search for what topic?" |

## Notes
- No new LLM call needed — question generation is pure rules
- All exceptions caught and logged, never propagates
- Does not affect command messages (starts with `/`)