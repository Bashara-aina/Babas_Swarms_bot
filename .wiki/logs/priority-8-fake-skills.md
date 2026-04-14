---
title: Priority 8 Fake Skills
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
summary: '**Task:** Fix Timer (1/10) and Code Review (0/10) skills'
wikilinks: []
confidence: medium
source: research
---
# Priority 8: Fix Fake Skills — COMPLETION LOG

**Date:** 2026-04-12
**Task:** Fix Timer (1/10) and Code Review (0/10) skills
**Status:** ✅ COMPLETE

## What Was Done

### 1. Created `core/skills/timer.py` (NEW FILE)
- **Problem:** Old `_timer_handler` in `productivity.py` was a stub returning only text
- **Solution:** Created real async timer using `asyncio.create_task()`
- **Features:**
  - Parses natural language: "set timer 5 min for meeting", "timer 30 seconds"
  - Schedules background task that sleeps and sends Telegram message
  - Bot reference set via `set_bot()` called from `main.py` on_startup
  - Max duration: 2 hours
  - Returns confirmation with scheduled time

### 2. Created `core/skills/code_review.py` (NEW FILE)
- **Problem:** Code review existed in `tools/code_reviewer.py` but wasn't registered as skill
- **Solution:** Created proper skill with structured LLM-based review
- **Features:**
  - Registered in SkillRegistry with keywords: "review code", "cek bug", "review kode"
  - Uses `llm_client.call_llm()` with coding model
  - Returns structured output:
    1. BUGS
    2. PERFORMANCE  
    3. SECURITY
    4. IMPROVEMENTS
    5. VERDICT
  - Auto-detects language from code patterns

### 3. Updated `core/skills/__init__.py`
- Added imports for new `code_review` and `timer` modules

### 4. Fixed `core/skills/builtin/productivity.py`
- `_timer_handler` now delegates to `core.skills.timer.handle_timer_message()`

### 5. Updated `main.py` on_startup
- Added call to `timer.set_bot(bot)` after skills registry init
- Ensures timer skill has bot reference for sending notifications

## Verification Results

### verify_wiring.py
```
Skills: PASS - 28 skills registered (was ~26)
All 7 checks passed
```

### pytest
```
383 passed, 10 warnings in 97.23s
```

## Key Implementation Details

### Timer Task Creation
```python
async def send_reminder():
    await asyncio.sleep(duration_seconds)
    await bot.send_message(chat_id=user_id, text=f"⏰ Timer! {reminder_text}")

asyncio.create_task(send_reminder())
```

### Code Review Structured Output
```python
review_prompt = f"""Review this {language} code. Be specific and actionable.
Format your review as:
1. BUGS: Any actual bugs or errors (not style)
2. PERFORMANCE: Any O(n²) or unnecessary operations
3. SECURITY: Any injection, auth, or exposure risks
4. IMPROVEMENTS: Top 2-3 concrete improvements
5. VERDICT: Ship it / Needs work / Rewrite (pick one)"""
```

## Files Modified

| Path | Change |
|------|--------|
| `core/skills/timer.py` | CREATED |
| `core/skills/code_review.py` | CREATED |
| `core/skills/__init__.py` | MODIFIED - added imports |
| `core/skills/builtin/productivity.py` | MODIFIED - _timer_handler |
| `main.py` | MODIFIED - on_startup bot init |

## ADR

Written to: `.wiki/decisions/ADR-017.md`
