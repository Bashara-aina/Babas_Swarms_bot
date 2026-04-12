# AUDIT 03 — Router Layer Coverage
> Paste this entire prompt into a new OpenCode session.
> Goal: every intent has a handler; every router returns a usable value.

---

```
╔══════════════════════════════════════════════════════════════════╗
║  LEGION AUDIT 03 — Router Layer Coverage                        ║
║  Fix: full intent coverage, no fallthrough to None              ║
╚══════════════════════════════════════════════════════════════════╝

STEP 1 — READ ALL 4 ROUTERS
Read completely:
  router.py (root)
  core/autonomous_router.py
  core/intent_router.py
  core/task_router.py

STEP 2 — BUILD INTENT COVERAGE MAP
For each router, list every intent/case it handles.
Then list every feature in the bot (from handlers/ filenames as a guide).
For each feature: which router case covers it?
Mark any feature with NO router case → broken wire.

STEP 3 — AUDIT ROUTER CHAIN
Verify the call chain:
  router.py calls → autonomous_router.py calls → intent_router.py calls → task_router.py
For each link: find the exact line where the call happens.
If a router is imported but never called → dead import → fix by calling it.

STEP 4 — AUDIT RETURN VALUES
Every router function must return a meaningful value (not None by default).
Every caller must check the return value:
  result = await route(message)
  if result is None:
      result = await fallback_llm_chat(message)
Fix any router that returns None without a fallback.

STEP 5 — FIX MISSING CASES
For every feature identified in Step 2 with no router case:
  Add the case to the appropriate router.
  Route it to the correct handler function.
  Ensure the handler is imported at the top of the router file.

STEP 6 — VERIFY
Re-read all 4 routers.
Confirm every feature now has a case.
Confirm the chain is fully connected.
List every fix made with file:line.

DO NOT modify SOUL.md, CLAUDE.md, or LEGION_MASTER.md.
```
