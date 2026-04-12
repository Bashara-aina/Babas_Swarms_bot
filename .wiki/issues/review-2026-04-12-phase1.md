# Review: Phase 1 Session (2026-04-12)

## Files Reviewed
### Created:
- `core/session/transcript.py` — SessionTranscriptStore (SQLite-backed)
- `core/shell/sandbox.py` — SandboxConfig, SandboxExecutor
- `tools/video.py` — understand_video_url()

### Modified:
- `main.py` — ruflo_manager wiring, transcript init
- `llm_client/__init__.py` — budget hard-stop
- `conversation_interface.py` — save_turn() fire-and-forget
- `computer_agent/shell.py` — sandbox integration
- `core/proactive/curiosity_engine.py` — CHECKIN_POOL, 4h cooldown
- `handlers/media_tools.py` — F.video handler
- `tools/documents.py` — CSV, PPTX, EPUB handlers
- `browser_agent.py` → `tools/browser_agent.py` — Crawl4AI integration
- `core/intent_router.py` — URL auto-routing
- `requirements.txt` — new deps

---

## Test Results
```
pytest tests/ -x --asyncio-mode=auto -q
305 passed, 1 warning in 21.30s
```
✅ All tests pass

---

## ✅ Passed

- No hardcoded API keys, passwords, or secrets
- Type hints present on all public functions
- Docstrings/comments present on all public methods
- Async properly handled (transcript uses aiosqlite, fire-and-forget wrapped in try/except)
- Sandbox blocked patterns cover dangerous commands (rm -rf /, fork bombs, etc.)
- Budget guard code wrapped in try/except (safe fallback when module unavailable)
- parse_mode consistently HTML across all reviewed Telegram answer/edit calls
- All reviewed exception handlers use specific try/except (not bare except)

---

## ⚠️ Warnings

### 1. URL allowlist not implemented in browser_agent.py
**File:** `tools/browser_agent.py`
**Issue:** P3-4 in CLAUDE.md calls for `BROWSER_ALLOWED_DOMAINS` env-var allowlist before navigation, but the implementation does not enforce this. Currently any URL can be navigated.
**Severity:** Medium (P3 item, not blocking)
**Recommendation:** Add URL allowlist check before `page.goto()`.

### 2. Sandbox blocked pattern may false-match nested paths
**File:** `core/shell/sandbox.py` line 40
**Pattern:** `r"rm\s+-rf\s+/\s*"`
**Issue:** This regex matches `rm -rf /home/user/file.txt` (the `/home` satisfies `/\s*`).
**Severity:** Low (pattern is overly broad but in practice rm -rf on subdirectories is still dangerous)
**Recommendation:** Change to `r"^\s*rm\s+-rf\s+/\s*$"` to anchor to root-only deletion.

### 3. `_proactive_notify` in main.py missing parse_mode
**File:** `main.py` line 339
**Code:** `await bot.send_message(ALLOWED_USER_ID, text[:4000])`
**Issue:** No `parse_mode` specified. If proactive messages contain `<`, `>`, or `&` characters, Telegram will raise `BadRequest`.
**Severity:** Low
**Recommendation:** Add `parse_mode="HTML"` to the send_message call.

### 4. `budget_guard.py` import path does not exist
**File:** `llm_client/__init__.py` line 1322
**Code:**
```python
from swarms_bot.routing.budget_guard import get_budget_guard, BudgetExceededError
```
**Issue:** `swarms_bot/routing/budget_guard.py` does not exist. Only `budget_manager.py` exists with `BudgetManager` class. The import is wrapped in try/except so it silently passes, but the budget hard-stop feature is non-functional.
**Severity:** High (Budget hard-stop never fires — requests proceed even when budget exceeded)
**Recommendation:** Either create `swarms_bot/routing/budget_guard.py` with `get_budget_guard()` singleton + `BudgetExceededError`, or refactor `llm_client` to use `BudgetManager` from `budget_manager.py`.

---

## ❌ Blockers

### BLOCKER-1: Budget hard-stop is non-functional
**File:** `llm_client/__init__.py` line 1320-1329
**Problem:** `swarms_bot.routing.budget_guard` module does not exist. The code silently falls through the except block, and `BudgetExceededError` is never raised. Budget enforcement is completely bypassed.
**Impact:** No cost protection — LLM calls will continue even when daily/monthly budget is exceeded.
**Fix Required:** Create `budget_guard.py` module or refactor to use existing `BudgetManager`.

---

## Summary

| Category | Count |
|----------|-------|
| ✅ Passed | 8 |
| ⚠️ Warnings | 4 |
| ❌ Blockers | 1 |

**Action Required:** Fix BLOCKER-1 (budget guard module) before next production use.
