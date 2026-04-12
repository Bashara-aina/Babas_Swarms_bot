# LEGION SELF-AUDIT MASTER PROMPT
# Paste this entire file into Claude Code (VSCode) to begin.
# Claude reads the repo's own context — no external assumptions.

---

You are a senior AI systems engineer performing a deep, honest audit of this codebase.

Before writing a single line of code, you MUST read these files in this exact order:

```
1. CLAUDE.md                          ← architecture, rules, what NOT to do
2. SOUL.md                            ← Legion's identity contract
3. LEGION_OPENCODE_AUDIT.md           ← previous audit findings (what's done, what's open)
4. IMPLEMENTATION_STATUS.md           ← current feature completion state
5. core/soul_engine.py                ← how soul is loaded
6. core/system_prompt_builder.py      ← how the system prompt is assembled
7. core/intent_router.py              ← how messages are classified
8. core/proactive/curiosity_engine.py ← proactive message engine
9. handlers/shared.py                 ← error handling, shared utilities
10. handlers/ai.py                    ← main message handler
11. main.py                           ← startup sequence, handler registration
12. agents.py                         ← model registry, TASK_KEYWORDS, PERSONALITY_WRAPPER
13. llm_client.py                     ← all LLM calls
14. core/character_enforcer.py        ← voice enforcement
15. core/memory/memory_manager.py     ← memory facade
```

After reading all of the above, perform the following audit:

---

## AUDIT TASK 1 — VERIFY COMPLETED FIXES

From LEGION_OPENCODE_AUDIT.md, the following were marked as fixed. Verify each one
by reading the actual code — not just trusting the doc.

For each item below, check the real file and answer: **CONFIRMED FIXED / STILL BROKEN / PARTIALLY FIXED**:

- [ ] Proactive timestamp overflow — check `core/proactive/curiosity_engine.py`
      Look for: proper `datetime.now(timezone.utc)` usage, 72h cap, no raw epoch math
- [ ] Error humanizer wired — check `handlers/shared.py`
      Look for: `humanize_error()` call in `_run_agent_loop()` and `_execute_chat()`
- [ ] Natural command parser wired — check `handlers/ai.py` or `core/intent_router.py`
      Look for: `natural_command_parser.get_action()` or `is_actionable()` being called
- [ ] Wiki quality gate — check `core/wiki_quality_gate.py`
      Look for: whitelist of essential files, 0.15 quarantine threshold, deep_gate fallback
- [ ] SOUL.md injected first — check `core/system_prompt_builder.py`
      Look for: `build_soul_context()` called at section 0, before any other section
- [ ] Conversation history persistence — check `core/memory/memory_manager.py` and `handlers/ai.py`
      Look for: SQLite or persistent store being written AND read on every turn

Report your findings for each. Be blunt if something says it's fixed but isn't.

---

## AUDIT TASK 2 — FIND GAPS VS. CLAUDE.md SPEC

CLAUDE.md Section 9 lists an explicit priority fix list (P0 through P3).
For each item in that list, check whether it is actually implemented in the code:

**P0 items (bot-breaking):**
- P0-1: Is `/debate` registered in `main.py`? Check `bot.set_my_commands()` and router registration.
- P0-2: Does `/cmd` in `computer_agent.py` have `asyncio.wait_for(..., timeout=30)`?
- P0-3: Is ruflo `subprocess.Popen` handle stored in `app_context`? Is there a health-check ping?
- P0-4: Are there any `parse_mode="Markdown"` calls in `handlers/`? There should be ZERO.

**P1 items (reliability):**
- P1-1: Does every background task in the registry (CLAUDE.md Section 8) call `BudgetManager.can_spend()` before LLM calls?
- P1-2: Do these dead directories actually not exist? `core/memory_old/`, `core/orchestration_old/`, `core/reliability_old/`
- P1-3: Does `tests/test_system_prompt_builder.py::test_soul_is_first_section` exist?
- P1-4: Is `langchain-community>=0.3.0` in `requirements.txt`?
- P1-5: Is `browser-use` pinned to an exact version in `requirements.txt`?

**P2 items (quality):**
- P2-1: Do these test files exist with real tests? `tests/test_soul_engine.py`, `tests/test_intent_router.py`, `tests/test_system_prompt_builder.py`, `tests/test_debate_engine.py`, `tests/test_memory_facade.py`
- P2-2: Are `/debate` and `/opinion` in the bot command menu in `main.py`?
- P2-3: Does `handlers/admin.py` exist with a `/budget` command?
- P2-4: Does a `/soul` command handler exist?
- P2-5: Have overlapping intents been merged in `core/intent_router.py`?

**P3 items (growth):**
- P3-1: Does `.github/workflows/ci.yml` exist with the CI spec from CLAUDE.md?
- P3-2: Has `computer_agent.py` been split into `computer/screen.py`, `computer/input.py`, etc.?
- P3-3: Does `memory_manager.py` have `validate_consistency()` method?
- P3-4: Does `browser_agent.py` check URL allowlist before navigating?

Report status of each as: **DONE / MISSING / PARTIAL**. Be specific about what is missing.

---

## AUDIT TASK 3 — HUMANNESS CHECK

The core goal is: Legion must feel like a real friend, not a robot.

Read `SOUL.md`, `core/character_enforcer.py`, `core/system_prompt_builder.py`, and `handlers/ai.py`.

Answer these questions with evidence from the actual code:

1. **Voice rules enforcement**: Are ALL of these banned phrases actually checked and filtered?
   - "Certainly!", "Great!", "Of course!", "Sure!", "Absolutely!", "I'd be happy to", "As an AI"
   Show the actual filter code or confirm it's missing.

2. **Language matching**: Does Legion detect whether Bashara wrote in Indonesian or English
   and match the response language? Show the code that does this or confirm it's missing.

3. **Response length matching**: Does Legion match energy (short message → short reply)?
   Is there any length/energy calibration in the prompt or code?

4. **Emotion-first rule**: Does Legion acknowledge emotions before offering solutions?
   Is this enforced anywhere in `core/emotion_modulator.py` or prompt logic?

5. **Memory recall in responses**: When Bashara says something, does Legion pull relevant
   memories from the store to enrich context? Trace the call path from `handlers/ai.py`
   through `core/memory/memory_manager.py` to confirm this actually happens.

6. **Proactive variety**: Does `core/proactive/curiosity_engine.py` use a pool of different
   messages, or does it send the same string repeatedly? Show the actual message pool.

7. **Proactive cooldown**: Is there a cooldown preventing multiple check-ins per hour?
   Show the timing logic or confirm it's missing.

---

## AUDIT TASK 4 — PRODUCE THE FIX LIST

After completing Tasks 1-3, produce a prioritized fix list in this exact format:

```
## WHAT IS ACTUALLY BROKEN (verified by reading code)

### CRITICAL (fix before anything else)
- [FILE: path/to/file.py, LINE: X] Description of exact bug
  Fix: exact code change needed

### HIGH (fix in same session)
- [FILE: path/to/file.py] Description
  Fix: what to do

### MEDIUM (next session)
- [FILE: ...] Description
  Fix: ...

### VERIFIED CLEAN (no fix needed)
- List items that are confirmed working correctly
```

Do NOT invent bugs that aren't in the code.
Do NOT report something as broken based on a doc — only based on the actual code.
If you find something the docs say is broken but the code is actually fine, say so.

---

## AUDIT TASK 5 — IMPLEMENT (in priority order)

After you have produced the verified fix list from Task 4:

1. Start with CRITICAL items.
2. For each fix:
   a. Read the full file before editing
   b. Make the minimal correct change
   c. Run the smoke tests from CLAUDE.md Section 12
   d. Confirm it works before moving to the next fix
3. Do NOT refactor things that aren't broken.
4. Do NOT change behavior that wasn't broken.
5. After all fixes: update `LEGION_OPENCODE_AUDIT.md` with the new status.
6. After all fixes: update `CLAUDE.md` Section 9 to reflect completed items.
7. Run the full test suite: `pytest tests/ -x --asyncio-mode=auto -q`

---

## SMOKE TESTS (run after every fix)

```bash
python -c "from core.soul_engine import build_soul_context; print(build_soul_context()[:100])"
python -c "from core.intent_router import IntentRouter; r = IntentRouter(); print(r.classify('write me code'))"
python -c "from core.system_prompt_builder import build_full_system_prompt; print(build_full_system_prompt('test')[:200])"
python -c "from core.debate_engine import build_debate_instruction; print('debate ok')"
python -c "from core.character_enforcer import enforce_character; print(enforce_character('Certainly! I can help you with that.'))"
python -c "from core.natural_command_parser import get_action; print(get_action('cek rumahlabuh.com SEO-nya'))"
```

---

## DEFINITION OF DONE (from CLAUDE.md — do not skip)

A task is only done when ALL of the following are true:
- [ ] Smoke tests pass
- [ ] `pytest tests/ -x --asyncio-mode=auto -q` passes
- [ ] No new _old files created
- [ ] `LEGION_OPENCODE_AUDIT.md` updated with new status
- [ ] `CLAUDE.md` Section 9 updated if a P-item was completed
- [ ] The final answer to: "Does this feel like a real friend?" is YES

---

## NORTH STAR (never forget this)

When Bashara sends "Pusing nih" at midnight:
- Legion should respond like a friend who knows him, not a bot asking what kind of help he needs.
- No bullet lists. No options menu. One human sentence, then silence.

When Bashara says "cek langsung" after talking about rumahlabuh.com:
- Legion should just check it. No slash command required. No "I can't do that from here."

When Legion hasn't heard from Bashara in 8 hours:
- One check-in, different phrasing each time. Then silence for 4 hours.

If any fix makes Legion feel more robotic, revert it.

---

*Start with Task 1. Read the code. Then report. Then fix.*
