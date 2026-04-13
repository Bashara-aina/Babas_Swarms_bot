---

---
# AUDIT 02 — Message Pipeline Connectivity
> Planner: @planner | Created: 2026-04-12 | Status: IN PROGRESS
## Overview
Trace plain text message end-to-end through the SwarmBot pipeline and fix every broken hop.
## Happy Path (Expected)
```
main.py: dp.start_polling()
     ↓
handlers/__init__.py: register_all_routers(dp)
     ↓
handlers/ai.py: @router.message(F.text) → handle_nl()
     ↓ await
handlers/message_handler.py: handle_plain_message()
     ↓ await
core/autonomous_router.py: AutonomousRouter.analyze_async()
     ↓ await
llm_client/: chat() / agent_loop() / _call_model()
     ↓ return
handlers/shared.py: send_chunked()
     ↓ await
msg.answer(response)
```

## SUBTASK 1: Trace Hop-1 — aiogram Dispatcher → ai.router
**Assigned to**: @worker

Read and document:
- `main.py`: How is the Dispatcher started? What message filter triggers ai.router?
- `handlers/__init__.py`: Confirm router registration order — ai.router must be LAST
- `handlers/ai.py` line 738: `@router.message(F.text)` — confirm this is the primary TEXT entry point
- `handlers/message_handler.py`: confirm it's imported/used by ai.py or registered separately

**Expected**: main.py → dp.start_polling() → aiogram → ai.router → handle_nl()

**Deliverable**: Report exact file:line_number for each hop in the chain.

---

## SUBTASK 2: Trace Hop-2 — handle_nl() → handle_plain_message()
**Assigned to**: @worker

Read `handlers/ai.py` lines 738-922 (`handle_nl`):
- Line 782: `await handle_plain_message(msg, _ar)` — confirm _ar (auto_router) is not None
- Lines 766-793: primary path with autonomous router — verify _router_handled flag logic
- Lines 795-922: keyword fallback path — confirm all awaits are correct

Read `handlers/message_handler.py` lines 129-365 (`handle_plain_message`):
- Line 179: `await auto_router.analyze_async(user_msg)` — await present ✓
- Line 166: `await get_task_router().route(...)` — await present ✓
- Lines 195, 217, 223, etc.: `await _execute_chat(...)` and `await _run_agent_loop(...)` — verify all
- Line 356: final generic fallback — await ✓

**Deliverable**: List every function call in handle_plain_message() that should be awaited, and confirm each is awaited. Report any missing await.

---

## SUBTASK 3: Trace Hop-3 — autonomous_router.analyze_async() → _llm_classify()
**Assigned to**: @worker

Read `core/autonomous_router.py`:
- Line 464: `analyze()` — synchronous fast path, no await needed (ok)
- Line 513: `analyze_async()` — confirm it awaits `self._llm_classify()` at line 522 ✓
- Line 535: `_llm_classify()` — confirm it awaits `litellm.acompletion()` at line 549 ✓
- Line 557: Check if `raw.replace("-", "_").strip("`*")` normalization is correct

Verify: Does `SkillMatch` returned from analyze_async() have its `confidence` and `skill_name` fields used correctly in `handle_plain_message()`?

**Deliverable**: Report any missing awaits or return value not being captured.

---

## SUBTASK 4: Trace Hop-4 — llm_client.chat() entry point
**Assigned to**: @worker

Read `llm_client/__init__.py`:
- Line 857: `chat()` function signature — is it async?
- Line 1192: `_call_model()` is awaited ✓
- Line 1009-1069: Memory/context gathering — check if any are NOT awaited but should be (async functions called without await)
- Lines 1017-1023: `gather_parallel_prompt_layers()` — is it awaited? Should it be?

**Deliverable**: List any function calls inside `chat()` that are async but missing await.

---

## SUBTASK 5: Duplicate Pipeline Check — message_handler.py vs ai.py
**Assigned to**: @worker

Read both files:
- `handlers/message_handler.py`: What triggers `handle_plain_message()`?
- `handlers/ai.py`: What triggers `handle_nl()`? Is `handle_plain_message` imported and used?

Check `handlers/__init__.py` router order (line 50-82):
- Is message_handler.router registered?
- If both message_handler and ai handle TEXT, which takes precedence?

**Goal**: Determine if plain text messages are processed TWICE through different paths.

**Deliverable**: Document the exact entry point for a plain text message. If duplicate, propose fix.

---

## SUBTASK 6: Router Fallthrough — verify no crash on unknown intent
**Assigned to**: @worker

Read `handlers/ai.py` handle_nl fallback section (lines 795-922):
- Lines 800-808: OpenClaw delegation — is result awaited and used?
- Lines 811-922: Keyword dispatch — are all `_run_agent_loop()` and `_execute_chat()` awaited?

Read `core/autonomous_router.py`:
- `analyze()` (line 464): What does it return if no keywords match? → SkillMatch(skill_name="conversation", confidence=0.90)
- `analyze_async()` (line 513): What if `_llm_classify()` returns None?

Read `core/intent_router.py`:
- `classify_intent()` (line 467): Returns IntentResult with intent=CASUAL_CHAT as fallback ✓

**Goal**: Verify that if a message doesn't match any skill, it falls through to conversation without crashing.

**Deliverable**: Document every code path where a function returns None or raises unhandled exception for unrecognized input.

---

## SUBTASK 7: Reply Always Sent — fallback reply verification
**Assigned to**: @worker

Search for all `msg.answer` calls in:
- `handlers/message_handler.py` — confirm every branch has a reply
- `handlers/ai.py` handle_nl fallback section
- `handlers/shared.py` send_chunked(), _execute_chat(), _run_agent_loop()

Check for bare `return` with no reply before it (e.g., line 139 in message_handler.py has `return` after checking `if not user_msg or user_msg.startswith("/")` — this is correct for command messages).

**Goal**: Find any code path that exits without replying to the user.

**Deliverable**: List every `return` in handlers/message_handler.py and handlers/ai.py that does NOT send a reply first. Confirm whether each is correct (e.g., command filtering) or a bug.

---

## SUBTASK 8: Fix Broken Hops
**Assigned to**: @worker

After completing Subtasks 1-7, apply all fixes:
- Add missing `await` keywords
- Fix return value not captured (e.g., `result = await func()`)
- Ensure arguments match function signatures
- Add fallback reply where user would be left with no response

**Deliverable**: Complete list of changes made with file:line references.

---

## SUBTASK 9: Run Tests
**Assigned to**: @worker

After fixes, run:
```bash
cd /home/newadmin/swarm-bot && pytest tests/ -x --asyncio-mode=auto -q
```

If tests fail, report which tests and why. Fix only if the failure is directly related to the audit fixes (do not fix unrelated test breakage).

**Deliverable**: Test results — pass/fail with error details if any.

---

## Review Task (post-fix)
**Assigned to**: @reviewer

Review all changes from Subtask 8:
- Confirm every `await` added is correct (callee is truly async)
- Confirm no new bugs introduced
- Verify all return values are used properly
- Confirm fallback reply added where needed

**Deliverable**: Approval or request for corrections.