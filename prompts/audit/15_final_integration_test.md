# AUDIT 15 — FINAL INTEGRATION TEST (The Big One)
> Run this ONLY after completing Audits 01–14.
> Paste this entire prompt into a new OpenCode session.
> Goal: simulate 10 real user scenarios and verify actual data flows
> end-to-end — from Telegram input to final sent reply.
> This is the ONLY audit that catches logic bugs, not just import bugs.

---

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  LEGION AUDIT 15 — FINAL INTEGRATION TEST                        ┃
┃  The biggest audit. Runs after all 14 are done.                 ┃
┃  Tests real data flow, not just imports.                        ┃
┃  Output: tests/test_integration.py + INTEGRATION_REPORT.md      ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

════════════════════════════════════════════════════════════════════
PHILOSOPHY: WHY THIS AUDIT IS DIFFERENT
════════════════════════════════════════════════════════════════════

Audits 01–13 fix wires. Audit 14 checks imports.
This audit answers the ONLY question that matters:

  "If a real user sends this message RIGHT NOW,
   does Legion give a correct, useful, non-broken reply?"

We test by:
  1. Creating mock Telegram Update objects
  2. Calling the REAL handler code (not mocked handlers)
  3. Mocking ONLY external I/O (Telegram API, LLM API, search API)
  4. Asserting on what ACTUALLY flows through the pipeline

The 3 things we assert for EVERY scenario:
  A. DATA REACHES LLM — messages[] contains soul + memory + relevant context
  B. LLM IS CALLED — call_llm() or litellm.acompletion() is invoked with real args
  C. REPLY IS SENT — update.message.reply_text() or reply_voice() is called with content

If any of these 3 fail for any scenario → broken pipeline → must fix.

════════════════════════════════════════════════════════════════════
STEP 1 — BUILD THE TEST HARNESS
════════════════════════════════════════════════════════════════════

Create tests/test_integration.py with this harness:

```python
"""
Legion Final Integration Test Suite
Tests 10 real user scenarios through the actual pipeline.
External I/O is mocked. Internal logic runs REAL code.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, call
from typing import Any

# ──────────────────────────────────────────────────────────────────
FIXTURES — Mock Telegram objects
# ──────────────────────────────────────────────────────────────────

def make_update(text: str, user_id: int = 12345, chat_id: int = 67890) -> MagicMock:
    """Creates a realistic mock Telegram Update."""
    update = MagicMock()
    update.effective_user.id = user_id
    update.effective_user.first_name = "TestUser"
    update.effective_chat.id = chat_id
    update.message.text = text
    update.message.chat_id = chat_id
    update.message.message_id = 1
    update.message.reply_text = AsyncMock(return_value=MagicMock())
    update.message.reply_voice = AsyncMock(return_value=MagicMock())
    update.message.reply_document = AsyncMock(return_value=MagicMock())
    update.message.reply_photo = AsyncMock(return_value=MagicMock())
    return update

def make_context(user_id: int = 12345) -> MagicMock:
    """Creates a realistic mock PTB context."""
    context = MagicMock()
    context.bot.send_message = AsyncMock()
    context.bot.send_voice = AsyncMock()
    context.user_data = {}
    context.chat_data = {}
    context.bot_data = {}
    return context

LLM_MOCK_RESPONSE = "Legion here. I understand your request and I\'m on it."

def mock_llm_call(*args, **kwargs):
    """Mock LLM that captures what was sent to it."""
    messages = kwargs.get(\'messages\', args[0] if args else [])
    # Store last call for assertion
    mock_llm_call.last_messages = messages
    mock_llm_call.call_count = getattr(mock_llm_call, \'call_count\', 0) + 1
    return LLM_MOCK_RESPONSE

mock_llm_call.last_messages = []
mock_llm_call.call_count = 0
```

════════════════════════════════════════════════════════════════════
STEP 2 — THE 10 SCENARIOS (implement each as a pytest test)
════════════════════════════════════════════════════════════════════

For each scenario below, implement a pytest async test that:
  1. Creates mock update + context using the harness above
  2. Patches ONLY external I/O (LLM API, Telegram send, search API)
  3. Calls the REAL handler function
  4. Asserts the 3 mandatory conditions (data reaches LLM, LLM called, reply sent)
  5. Asserts scenario-specific conditions listed below

■ SCENARIO 1: Plain Chat Message (the most basic case)
  Input: update.message.text = "Hei Legion, lo siapa?"
  Handler: handlers/message_handler.py OR handlers/ai.py (whichever handles plain text)
  Patch: call_llm → return LLM_MOCK_RESPONSE
  Assert:
    A. call_llm was called exactly once
    B. messages[0]["role"] == "system"  (soul is first)
    C. "Legion" in messages[0]["content"] OR soul content present
    D. Any message in messages[] contains "Lo siapa" or the user text
    E. update.message.reply_text was called with non-empty string
    F. reply text is NOT empty, NOT None, NOT "None"

■ SCENARIO 2: Web Search Intent
  Input: update.message.text = "Cari berita terbaru tentang AI di 2026"
  Patch:
    search_tool.execute → return [{"title": "AI News", "snippet": "AI is advancing"}]
    call_llm → return LLM_MOCK_RESPONSE
  Assert:
    A. search_tool.execute was called (search was triggered)
    B. LLM messages[] contains "AI News" or "AI is advancing" (search result injected)
    C. call_llm was called AFTER search completed
    D. update.message.reply_text called with non-empty content
  CRITICAL: if assertion B fails → search results are NOT reaching LLM → this is the
  search injection bug. Fix: find where results are returned and inject into messages[].

■ SCENARIO 3: Memory Write Then Read
  Input part 1: update.message.text = "Ingat ya, gw suka kopi hitam"
  Input part 2: update.message.text = "Gw suka minum apa?"
  Patch: call_llm → return LLM_MOCK_RESPONSE
  Do NOT mock memory engine — let it run real.
  Assert after part 1:
    A. memory_engine.write_memory was called with user_id=12345
    B. "kopi hitam" stored in memory for user 12345
  Assert after part 2:
    A. memory_engine.read_memory(12345) was called
    B. LLM messages[] contains "kopi hitam" (memory injected into context)
    C. reply sent
  CRITICAL: if B fails → memory not flowing to LLM context.

■ SCENARIO 4: Soul Is Always First
  Input: any 3 different messages from 3 different users
  Patch: call_llm → capture messages[], return LLM_MOCK_RESPONSE
  Assert for EACH of the 3 calls:
    A. messages[0]["role"] == "system"
    B. len(messages[0]["content"]) > 100
    C. soul identity keywords present in messages[0]["content"]
       (check SOUL.md for the exact identity keywords to look for)
    D. No other message comes before the soul system message
  CRITICAL: if any assertion fails → soul is not always first.

■ SCENARIO 5: /nihongo Command Then Message
  Input part 1: /nihongo command
  Input part 2: update.message.text = "What is the weather today?"
  Patch: call_llm → return "それはいい質問ですね。"
  Assert after /nihongo:
    A. nihongo flag set True for user_id=12345
    B. confirmation message sent in Japanese
  Assert after part 2 message:
    A. nihongo pipeline was invoked (not normal pipeline)
    B. LLM system prompt contains sensei/nihongo persona
    C. Soul identity STILL present (soul not replaced by nihongo persona)
    D. Reply sent
  Assert user isolation:
    A. different_user_id nihongo flag is False

■ SCENARIO 6: Unknown / Gibberish Input
  Input: update.message.text = "asdkljasdlkjaslkdjaslkdj 12312312"
  Patch: call_llm → return LLM_MOCK_RESPONSE
  Assert:
    A. Bot does NOT crash (no exception propagates)
    B. Bot does NOT return None silently
    C. update.message.reply_text IS called (user gets a reply, even for gibberish)
    D. Reply is not empty
  This tests the fallthrough/default case in the router.

■ SCENARIO 7: Command with Arguments (/model gpt-4o)
  Input: /model gpt-4o (or whatever model-switching command exists)
  Assert:
    A. Handler for /model command is invoked
    B. Model preference stored for user_id
    C. Confirmation reply sent
    D. Next LLM call uses the new model
  If /model command doesn\'t exist: replace with any command that takes arguments.
  Use the actual command that exists in the bot.

■ SCENARIO 8: Sequential Multi-Turn Conversation
  Message 1: "Gw lagi nulis paper tentang computer vision"
  Message 2: "Kasih feedback dong"
  Message 3: "Sekarang ubah jadi lebih formal"
  Patch: call_llm → return LLM_MOCK_RESPONSE (but capture all messages[])
  Assert for message 3:
    A. messages[] contains conversation history (messages 1 and 2)
    B. "computer vision" appears somewhere in message 3\'s context
    C. "feedback" context from message 2 is present
    D. call_llm called 3 times total (once per message)
  This tests conversation context is maintained across turns.

■ SCENARIO 9: Simultaneous Messages from Two Different Users
  User A (id=11111): sends "Hitung 2 + 2"
  User B (id=22222): sends "Siapa presiden Indonesia?"
  Run both handlers concurrently: await asyncio.gather(handler_a, handler_b)
  Assert:
    A. User A gets a reply
    B. User B gets a reply
    C. User A\'s reply does NOT contain "presiden Indonesia"
    D. User B\'s reply does NOT contain "2 + 2"
    E. No exception from either handler
  This tests user isolation and concurrent handling.

■ SCENARIO 10: LLM Failure Graceful Degradation
  Input: update.message.text = "Hei Legion"
  Patch: call_llm → raises Exception("API rate limit exceeded")
  Assert:
    A. Bot does NOT crash or raise unhandled exception
    B. update.message.reply_text IS called (user gets error message)
    C. Error message is user-friendly (not a raw Python traceback)
    D. Error is logged (logger.error called)
  This tests the error recovery path.

════════════════════════════════════════════════════════════════════
STEP 3 — RUN THE TESTS
════════════════════════════════════════════════════════════════════

Run:
  python -m pytest tests/test_integration.py -v --tb=short 2>&1 | tee INTEGRATION_RUN.txt

For EVERY test that fails:

  1. Read the full traceback
  2. Identify WHICH of the 3 mandatory conditions failed:
     - "call_llm not called" → pipeline broken BEFORE LLM
     - "messages[] missing soul" → context injection broken
     - "reply_text not called" → pipeline broken AFTER LLM
  3. Trace backward in the code from the failure point
  4. Find the exact broken wire
  5. Fix the minimum code needed to make the test pass
  6. Re-run ONLY that test to confirm fix: pytest tests/test_integration.py::TestScenario2 -v
  7. Then re-run ALL tests to confirm no regressions

Repeat until:
  python -m pytest tests/test_integration.py -v → 10/10 PASSED

════════════════════════════════════════════════════════════════════
STEP 4 — DEEP INSPECTION FOR EACH PASSED TEST
════════════════════════════════════════════════════════════════════

After all 10 pass, do a quality check on WHAT was in messages[] for each scenario.

For each test, print and inspect:
  print(f"Scenario X messages:")
  for i, msg in enumerate(mock_llm_call.last_messages):
      print(f"  [{i}] role={msg[\'role\']} content_length={len(msg[\'content\'])} preview={msg[\'content\'][:80]}")

Verify this order for EVERY scenario:
  messages[0]: role=system, content=SOUL (identity, personality, rules)
  messages[1]: role=system, content=MEMORY (user memories, if any)
  messages[2]: role=system, content=CONTEXT (wiki/search results, if triggered)
  messages[3..N-1]: role=user/assistant (conversation history)
  messages[N]: role=user, content=current message

If the order is wrong: go back and fix system_prompt_builder.py to enforce this order.

════════════════════════════════════════════════════════════════════
STEP 5 — TIMING & PERFORMANCE BASELINE
════════════════════════════════════════════════════════════════════

For each test, measure time from handler entry to reply_text call:

  import time
  start = time.monotonic()
  await handler(update, context)
  elapsed = time.monotonic() - start
  print(f"Scenario X pipeline latency (excl. LLM): {elapsed*1000:.1f}ms")

Expected baselines (excluding LLM API time):
  Plain chat:              < 50ms
  Search triggered:        < 200ms (search mock is instant, but routing overhead)
  Memory read+write:       < 100ms
  Nihongo mode:            < 100ms
  Concurrent users (x2):  < 100ms each (asyncio, so should be parallel)

If any baseline exceeds 2x the expected: trace the pipeline for blocking operations.
Most likely cause: blocking I/O left in async functions (see Audit 10).

════════════════════════════════════════════════════════════════════
STEP 6 — RUN BOTH SCRIPTS TOGETHER (the final gate)
════════════════════════════════════════════════════════════════════

The FINAL gate. BOTH must pass before the bot is considered production-ready:

  python scripts/verify_wiring.py && python -m pytest tests/test_integration.py -v

Expected output:
  🟢 ALL WIRING CHECKS PASSED
  ======================== 10 passed in X.Xs ========================

If ANY test fails: the bot is NOT production-ready. Fix and re-run.

════════════════════════════════════════════════════════════════════
STEP 7 — GENERATE INTEGRATION_REPORT.md
════════════════════════════════════════════════════════════════════

After all 10 pass, create INTEGRATION_REPORT.md:

# Legion Integration Report — [date]

## Test Results
| # | Scenario | Result | Pipeline Latency | LLM Called | Reply Sent | Soul First |
|---|----------|--------|-----------------|------------|------------|------------|
| 1 | Plain chat | ✅ PASS | 12ms | ✅ | ✅ | ✅ |
| 2 | Web search | ✅ PASS | 45ms | ✅ | ✅ | ✅ |
| 3 | Memory R/W | ✅ PASS | 28ms | ✅ | ✅ | ✅ |
| 4 | Soul always first | ✅ PASS | 8ms | ✅ | ✅ | ✅ |
| 5 | Nihongo isolation | ✅ PASS | 15ms | ✅ | ✅ | ✅ |
| 6 | Gibberish input | ✅ PASS | 5ms | ✅ | ✅ | ✅ |
| 7 | Command + args | ✅ PASS | 10ms | ✅ | ✅ | ✅ |
| 8 | Multi-turn memory | ✅ PASS | 35ms | ✅ | ✅ | ✅ |
| 9 | Concurrent users | ✅ PASS | 18ms | ✅ | ✅ | ✅ |
| 10 | LLM failure recovery | ✅ PASS | 6ms | N/A | ✅ | N/A |

## Messages[] Structure (verified)
For every scenario: soul → memory → context → history → current ✅

## Bugs Found and Fixed During This Session
| Bug | File | Fix |
|-----|------|-----|
| Search results not injected | handlers/ai.py:145 | Added messages.append(search_ctx) |
...

## Final Gate
`python scripts/verify_wiring.py && pytest tests/test_integration.py` → EXIT 0 ✅

## Legion is production-ready as of [date]. 🟢

════════════════════════════════════════════════════════════════════
HARD RULES — NEVER VIOLATE:
════════════════════════════════════════════════════════════════════

1. Do NOT mock the handler itself — only mock external I/O
   RIGHT: patch("llm_client.call_llm", mock_llm_call)
   WRONG: patch("handlers.ai.handle_ai", AsyncMock())

2. Do NOT make tests pass by weakening assertions
   If assert messages[0]["role"] == "system" fails:
   WRONG: remove the assertion
   RIGHT: fix the handler to put soul first

3. Do NOT skip a scenario because it\'s "too hard to test"
   Every scenario must be implemented. If the feature doesn\'t exist yet:
   mark the test as xfail with the reason:
   @pytest.mark.xfail(reason="Nihongo handler not yet implemented")

4. Do NOT modify SOUL.md, CLAUDE.md, or LEGION_MASTER.md

5. Every fix must be the MINIMUM change to make the test pass
   Do NOT refactor unrelated code during this session
```
