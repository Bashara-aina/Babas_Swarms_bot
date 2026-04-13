# LEGION — MASTER CONCERN FIX PROMPT
> Single session. Paste everything inside the code block into OpenCode.
> This prompt is written from direct inspection of the actual repo.
> Every concern listed here is based on REAL observed evidence, not assumptions.
> Fix in order. Do not skip. Do not batch.

---

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  LEGION MASTER CONCERN FIX — Real Issues, Real Fixes            ┃
┃  Based on direct repo inspection on 2026-04-12                 ┃
┃  7 critical concerns. Fix all 7. Verify each before moving on. ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

BEFORE ANYTHING — READ THESE FILES FIRST:
  SOUL.md
  DEEP_AUDIT_2026-04-10.md
  IMPLEMENTATION_STATUS.md
  WIRING_VERIFIED_2026-04-12.md
  main.py (full read)
  router.py (full read)

Do not touch: SOUL.md, CLAUDE.md, LEGION_MASTER.md, LEGION_NIHONGO_MODE.md

═══════════════════════════════════════════════════════════════════
CONCERN 1 — DUAL llm_client (CONFIRMED: both exist in repo)
═══════════════════════════════════════════════════════════════════

EVIDENCE: llm_client.py (671 bytes root file) AND llm_client/ (directory) both exist.
This means there was a refactor that was never finished.
Some files import from llm_client.py, others from llm_client/ — inconsistent behavior.

FIX STEPS:

1. Read llm_client.py (root) completely.
2. Read llm_client/__init__.py and all files in llm_client/ completely.
3. Determine which one has the REAL implementation (the bigger, more complete one).
4. Run: grep -rn "from llm_client" . --include="*.py" && grep -rn "import llm_client" . --include="*.py"
   Map which files use which version.
5. Consolidate:
   a. Keep llm_client/ as the canonical package (directory wins).
   b. Replace llm_client.py root file with a pure shim.
   c. Verify every import that used llm_client.py still works via the shim.
6. Ensure llm_client/ has ONE canonical function.
7. Verify model fallback chain is wired.
8. Verify: python -c "from llm_client import call_llm; print('OK')"

═══════════════════════════════════════════════════════════════════
CONCERN 2 — DUAL agents (CONFIRMED: agents.py AND agents/ both exist)
═══════════════════════════════════════════════════════════════════

EVIDENCE: agents.py (4021 bytes root file) AND agents/ (directory) both exist.
Same pattern as Concern 1 — an unfinished refactor.

FIX STEPS:

1. Read agents.py (root) completely.
2. Read agents/__init__.py and all files in agents/ completely.
3. Run: grep -rn "from agents" . --include="*.py" && grep -rn "import agents" . --include="*.py"
4. Determine which version task_orchestrator.py imports from.
5. Consolidate — same strategy as Concern 1.
6. Verify: python -c "from agents import BaseAgent; print('OK')"

═══════════════════════════════════════════════════════════════════
CONCERN 3 — SWARM IS THE HEART BUT SWARM_HANDLER IS A STUB
═══════════════════════════════════════════════════════════════════

EVIDENCE:
  handlers/swarm_handler.py = 906 bytes (almost certainly a stub)
  task_orchestrator.py = 19,608 bytes (the REAL orchestration engine exists!)
  The problem: swarm_handler.py is not wired to task_orchestrator.py

FIX STEPS:

1. Read handlers/swarm_handler.py fully. Confirm it\'s a stub.
2. Read task_orchestrator.py fully. Understand its interface.
3. Read handlers/orchestrate.py. Understand how these two files are supposed to relate.
4. Implement handlers/swarm_handler.py properly.
5. Register in main.py.
6. Verify task_orchestrator.py can actually be imported.

═══════════════════════════════════════════════════════════════════
CONCERN 4 — SEARCH RESULT INJECTION BUG (confirmed by developer)
═══════════════════════════════════════════════════════════════════

EVIDENCE: The developer identified this bug directly — search is triggered but
results are NOT injected into the LLM context. LLM answers without search data.

FIX STEPS:

1. Find where web search / DuckDuckGo is executed.
2. Find ALL places where litellm.acompletion() or call_llm() is called.
3. Find the gap.
4. Implement the correct injection pattern.
5. Add a simple VERIFICATION LOG (keep this permanently).
6. Manual test.

═══════════════════════════════════════════════════════════════════
CONCERN 5 — DAILY HARVESTER NOT SCHEDULED (2244 bytes, likely orphan)
═══════════════════════════════════════════════════════════════════

EVIDENCE: daily_harvester.py exists at root (2244 bytes).
Self-learning / wiki auto-ingest is one of Legion\'s key selling points.
But at 2244 bytes it\'s likely very minimal, AND it\'s almost certainly not
scheduled to actually run on a timer.

FIX STEPS:

1. Read daily_harvester.py fully.
2. Identify its main entry function.
3. Check main.py for scheduler initialization.
4. Add scheduler to main.py.
5. Ensure apscheduler is in requirements.txt.
6. If daily_harvester.py is too minimal (stub), implement the core.

═══════════════════════════════════════════════════════════════════
CONCERN 6 — GROWTH WITHOUT VERIFICATION (the root cause of all bugs)
═══════════════════════════════════════════════════════════════════

EVIDENCE: The repo has MANY features added over time but no automated
regression testing. Every new feature potentially breaks old ones.
The dual llm_client, dual agents, stub handlers — all symptoms of the same
problem: features were added but old connections were never verified.

FIX: Install a permanent regression guard that runs on every git push.

STEP 1 — Create scripts/verify_wiring.py (if not exists from Audit 14)
STEP 2 — Update .github/workflows/ for CI
STEP 3 — Add pre-commit hook (local guard before push)
STEP 4 — Update Makefile

═══════════════════════════════════════════════════════════════════
CONCERN 7 — SOUL INTEGRITY UNDER ALL CONDITIONS
═══════════════════════════════════════════════════════════════════

EVIDENCE: SOUL.md exists and is 4312 bytes. But with 36 handler files,
many different pipelines, and features like nihongo mode, computer agent,
and swarm mode — there is high risk that some code paths bypass soul injection.

FIX STEPS:

1. Read SOUL.md. Note the first 100 characters as a fingerprint.
2. Find every place messages[] is built for an LLM call.
3. For EACH assembly point: verify messages[0] is the soul system prompt.
4. Implement build_messages() as the CANONICAL message builder.
5. Refactor EVERY LLM call site to use build_messages().
6. Add a soul integrity assertion at bot startup in main.py.

═══════════════════════════════════════════════════════════════════
FINAL VERIFICATION — Run all checks in sequence
═══════════════════════════════════════════════════════════════════

After all 7 concerns are fixed, run this exact sequence:

  # 1. Import check
  python -c "
  from llm_client import call_llm
  from agents import BaseAgent
  from task_orchestrator import TaskOrchestrator
  from handlers.swarm_handler import handle_swarm
  from core.soul_engine import get_system_prompt
  import daily_harvester
  print(\'All critical imports OK ✅\')
  "

  # 2. Wiring check
  python scripts/verify_wiring.py

  # 3. Integration tests
  python -m pytest tests/test_integration.py -v --tb=short

  # 4. Single combined gate
  python scripts/verify_wiring.py && echo "✅ Wiring OK" && \
  python -m pytest tests/ -v --tb=short -q && echo "✅ Tests OK" && \
  echo "🟢 Legion is production-ready"

All 4 must succeed with 0 errors before this session is complete.

═══════════════════════════════════════════════════════════════════
CREATE CONCERNS_FIXED_REPORT.md AFTER COMPLETION
═══════════════════════════════════════════════════════════════════

Create CONCERNS_FIXED_REPORT.md with summary table of all 7 concerns fixed.

## Final Gate
`python scripts/verify_wiring.py && pytest tests/` → EXIT 0 ✅

## Legion status: 🟢 Wide AND Deep
```