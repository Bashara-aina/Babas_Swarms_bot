# Worker Log — 2026-04-12/13

## Task: Fix Telegram bot garbled text (Russian/Cyrillic in Matsuya/Toyosu response)

### Problem
- User "Bas" asked about eating karage at Matsuya in Toyosu
- Bot responded with garbled text containing Russian words ("конкрет", "памяти") and gibberish ("nexeny")
- Response should use proper English and Japanese only

### Root Cause
`core/character_enforcer.py` only stripped CJK (Chinese/Japanese/Korean) and Arabic scripts, but did **NOT** handle Cyrillic (Russian) script.

The LLM was producing Russian text which passed through the character enforcer unchanged.

### Fix Applied
**File:** `core/character_enforcer.py`

1. **Added Cyrillic script detection pattern** (line 34):
   ```python
   CYRILLIC_PATTERN = _re.compile(r"[\u0400-\u04ff\u0500-\u052f\u2de0-\u2dff\ua640-\ua69f]")
   ```

2. **Updated `has_non_allowed_script()`** to check for Cyrillic (line 48-49):
   ```python
   def has_non_allowed_script(text: str) -> bool:
       """Returns True if text contains CJK, Arabic, or Cyrillic characters."""
       return bool(CJK_PATTERN.search(text)) or bool(ARABIC_PATTERN.search(text)) or bool(CYRILLIC_PATTERN.search(text))
   ```

3. **Updated `strip_non_allowed_script()`** to strip Cyrillic characters (line 76-79):
   ```python
   # Strip any remaining CJK/Arabic/Cyrillic
   text = CJK_PATTERN.sub("", text)
   text = ARABIC_PATTERN.sub("", text)
   text = CYRILLIC_PATTERN.sub("", text)
   ```

### Verification
- `python -m py_compile core/character_enforcer.py` — ✅ Passed
- `pytest tests/ -x --asyncio-mode=auto -q` — ✅ 383 tests passed

### Status
✅ Complete — Cyrillic script is now detected and stripped before responses are sent to Telegram

---
*Executed: 2026-04-13 | Worker: @worker | Review: pending*
