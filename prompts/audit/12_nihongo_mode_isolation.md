# AUDIT 12 — Nihongo Mode Isolation
> Paste this entire prompt into a new OpenCode session.
> Goal: nihongo mode is fully per-user and cannot leak between users.

---

```
╔══════════════════════════════════════════════════════════════════╗
║  LEGION AUDIT 12 — Nihongo Mode User Isolation                  ║
║  Fix: per-user flag, proper activation/deactivation, no leak    ║
╚══════════════════════════════════════════════════════════════════╝

STEP 1 — FIND NIHONGO MODE FLAG
Search entire codebase for where nihongo mode is activated:
  grep -r "nihongo" . --include="*.py"
Find the variable that stores whether nihongo mode is ON.

STEP 2 — VERIFY PER-USER STORAGE
The flag MUST be stored per-user:
  GOOD: nihongo_active: dict[int, bool] = {}  # keyed by user_id
  GOOD: context.user_data["nihongo_active"] = True  # PTB user_data
  BAD:  nihongo_active = True  # global variable — leaks to ALL users!

If it's a global variable: refactor to per-user storage.
Replace every read of the flag with: nihongo_active.get(user_id, False)
Replace every write with: nihongo_active[user_id] = True/False

STEP 3 — VERIFY ACTIVATION COMMAND
Find /nihongo command handler.
Verify it:
  1. Sets the flag for the specific user_id
  2. Sends confirmation message in Japanese
  3. Does NOT affect any other user

STEP 4 — VERIFY DEACTIVATION COMMAND
Find /nihongo_off or equivalent deactivation.
If it doesn't exist: create it:
  async def nihongo_off(update, context):
      user_id = update.effective_user.id
      nihongo_active[user_id] = False
      await update.message.reply_text("Nihongo mode OFF. Back to Legion mode.")
Register it in main.py.

STEP 5 — VERIFY MAIN MESSAGE HANDLER CHECKS FLAG
Find where every incoming text message is processed.
Verify there is a check:
  if nihongo_active.get(user_id, False):
      return await nihongo_handler.handle(update, context)
  else:
      return await normal_pipeline(update, context)
If this check is missing: add it at the top of the main message dispatcher.

STEP 6 — ISOLATION TEST
Write a simple test in tests/test_nihongo_isolation.py:
  user_1 activates nihongo mode
  user_2 sends a message
  assert nihongo_active.get(user_2_id, False) == False
  user_1 sends another message
  assert nihongo_active.get(user_1_id, False) == True
Run: python -m pytest tests/test_nihongo_isolation.py -v
Fix until test passes.

STEP 7 — SOUL PRESERVATION IN NIHONGO MODE
Read LEGION_NIHONGO_MODE.md for the spec.
Verify that even in nihongo mode, Legion's soul/identity is still injected.
The sensei persona should LAYER ON TOP of soul, not replace it.

DO NOT modify SOUL.md, CLAUDE.md, LEGION_MASTER.md, or LEGION_NIHONGO_MODE.md.
```
