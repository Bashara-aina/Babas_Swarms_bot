---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/raw/prompts/legion-concerns.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-05-08T01:00:01.114002"
}
---

---
title: Legion Concerns
type: reference
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- prompts
created: '2026-04-14'
updated: '2026-04-14'
summary: '> Single session. Paste everything inside the code block into OpenCode.'
wikilinks: []
confidence: medium
source: research
---
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

════════════════════════════════════════════════════════════════════
CONCERN 1 — DUAL llm_client (CONFIRMED: both exist in repo)
════════════════════════════════════════════════════════════════════

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
   b. Replace llm_client.py root file with a pure shim:
      # llm_client.py — shim for backward compatibility
      from llm_client.client import call_llm, stream_llm  # adjust to actual exports
      __all__ = ["call_llm", "stream_llm"]
   c. Verify every import that used llm_client.py still works via the shim.
6. Ensure llm_client/ has ONE canonical function:
   async def call_llm(messages: list, model: str = None, tools: list = None,
                      stream: bool = False, **kwargs) -> str | dict
   → Returns: str for normal responses
   → Returns: dict {"type":"tool_call", "name":..., "args":...} when LLM returns tool_call
   → NEVER returns raw litellm ModelResponse object
7. Verify model fallback chain is wired:
   FALLBACK_CHAIN = [primary_model, "anthropic/claude-3-5-haiku", "openai/gpt-4o-mini"]
   Try primary → on RateLimitError/APIError → try next in chain
8. Verify: python -c "from llm_client import call_llm; print('OK')"

════════════════════════════════════════════════════════════════════
CONCERN 2 — DUAL agents (CONFIRMED: agents.py AND agents/ both exist)
════════════════════════════════════════════════════════════════════

EVIDENCE: agents.py (4021 bytes root file) AND agents/ (directory) both exist.
Same pattern as Concern 1 — an unfinished refactor.

FIX STEPS:

1. Read agents.py (root) completely.
2. Read agents/__init__.py and all files in agents/ completely.
3. Run: grep -rn "from agents" . --include="*.py" && grep -rn "import agents" . --include="*.py"
4. Determine which version task_orchestrator.py imports from.
   task_orchestrator.py is the primary consumer — it defines which one is canonical.
5. Consolidate — same strategy as Concern 1:
   a. Keep agents/ as canonical.
   b. Make agents.py root a shim.
   c. Ensure task_orchestrator.py uses the canonical import.
6. Verify agents/ directory has at minimum:
   agents/__init__.py — exports key agent classes
   agents/base_agent.py — base class with .run(task) interface
   (check if these exist; if not, create minimal versions)
7. Verify: python -c "from agents import BaseAgent; print('OK')"
   (or whatever the actual export name is after reading the files)

════════════════════════════════════════════════════════════════════
CONCERN 3 — SWARM IS THE HEART BUT SWARM_HANDLER IS A STUB
════════════════════════════════════════════════════════════════════

EVIDENCE:
  handlers/swarm_handler.py = 906 bytes (almost certainly a stub — no real logic fits in 906 bytes)
  task_orchestrator.py = 19,608 bytes (the REAL orchestration engine exists!)
  The problem: swarm_handler.py is not wired to task_orchestrator.py

FIX STEPS:

1. Read handlers/swarm_handler.py fully. Confirm it\'s a stub.
2. Read task_orchestrator.py fully. Understand its interface:
   → What is the main entry function? (likely: orchestrate(task) or run(task))
   → What does it return? (task result as string)
   → Does it need any initialization?
3. Read handlers/orchestrate.py. Is it different from swarm_handler.py?
   Understand how these two files are supposed to relate.
4. Implement handlers/swarm_handler.py properly:

   from task_orchestrator import TaskOrchestrator  # or whatever the class/function is
   import logging
   logger = logging.getLogger(__name__)

   orchestrator = TaskOrchestrator()  # initialize once at module level

   async def handle_swarm(update, context):
       """Routes complex multi-step tasks to the swarm orchestrator."""
       user_id = update.effective_user.id
       task = update.message.text

       # Remove /swarm prefix if present
       if task.startswith("/swarm"):
           task = task[6:].strip()

       if not task:
           await update.message.reply_text(
               "🧠 Swarm mode: kasih gw task yang complex.\n"
               "Contoh: /swarm Analisis repo ini dan buat improvement plan"
           )
           return

       thinking_msg = await update.message.reply_text("⏳ Swarm sedang bekerja...")

       try:
           result = await orchestrator.run(task, user_id=user_id)
           await thinking_msg.edit_text(result[:4000])  # Telegram limit
       except Exception as e:
           logger.error(f"Swarm error for user {user_id}: {e}")
           await thinking_msg.edit_text(
               f"❌ Swarm gagal: {str(e)[:200]}\nCoba lagi atau sederhanakan task-nya."
           )

5. Register in main.py:
   from handlers.swarm_handler import handle_swarm
   app.add_handler(CommandHandler("swarm", handle_swarm))

6. Verify task_orchestrator.py can actually be imported:
   python -c "from task_orchestrator import TaskOrchestrator; print('OK')"
   Fix any ImportError before proceeding.

════════════════════════════════════════════════════════════════════
CONCERN 4 — SEARCH RESULT INJECTION BUG (confirmed by developer)
════════════════════════════════════════════════════════════════════

EVIDENCE: The developer identified this bug directly — search is triggered but
results are NOT injected into the LLM context. LLM answers without search data.
This is the #1 functional bug: the most visible feature doesn\'t work end-to-end.

FIX STEPS:

1. Find where web search / DuckDuckGo is executed:
   grep -rn "duckduckgo\|ddg\|web_search\|search_web\|brave_search" . --include="*.py"
   Identify the function that returns search results.

2. Find ALL places where litellm.acompletion() or call_llm() is called:
   grep -rn "acompletion\|call_llm" . --include="*.py"
   For EACH call site: read the messages[] being passed.

3. Find the gap:
   Trace from search execute() → follow the return value → does it reach messages[]?
   If the return value is:
   a. Discarded after search → fix at search call site
   b. Returned but not added to messages → fix at context assembly
   c. Added to messages but AFTER call_llm → fix ordering

4. The correct injection pattern (implement this):

   # In the handler or system_prompt_builder, BEFORE call_llm:
   search_context = ""
   if should_search(user_message):  # intent detection
       try:
           results = await asyncio.wait_for(
               search_tool.execute(query=user_message),
               timeout=8.0
           )
           if results:
               search_context = format_search_results(results)
       except asyncio.TimeoutError:
           search_context = "[Search timed out]"
       except Exception as e:
           logger.warning(f"Search failed: {e}")
           search_context = ""

   # Build messages with search injected:
   messages = [
       {"role": "system", "content": soul_prompt},
       {"role": "system", "content": memory_context},
   ]
   if search_context:
       messages.append({"role": "system",
                        "content": f"[Real-time Search Results]\n{search_context}"})
   # ... add conversation history ...
   messages.append({"role": "user", "content": user_message})

   response = await call_llm(messages=messages)

5. Add a simple VERIFICATION LOG (keep this permanently):
   logger.info(f"LLM call: {len(messages)} messages, "
               f"has_search={'search' in str(messages).lower()}, "
               f"has_soul={messages[0]['role']=='system'}")

6. Manual test: send a message asking about current news.
   Check logs: does "has_search=True" appear?
   If yes → bug fixed.

════════════════════════════════════════════════════════════════════
CONCERN 5 — DAILY HARVESTER NOT SCHEDULED (2244 bytes, likely orphan)
════════════════════════════════════════════════════════════════════

EVIDENCE: daily_harvester.py exists at root (2244 bytes).
Self-learning / wiki auto-ingest is one of Legion\'s key selling points.
But at 2244 bytes it\'s likely very minimal, AND it\'s almost certainly not
scheduled to actually run on a timer.

FIX STEPS:

1. Read daily_harvester.py fully.
2. Identify its main entry function (likely: run() or harvest()).
3. Check main.py for scheduler initialization:
   grep -n "APScheduler\|AsyncIOScheduler\|schedule\|harvester" main.py
   If NOT found → the harvester never runs automatically.

4. Add scheduler to main.py:

   from apscheduler.schedulers.asyncio import AsyncIOScheduler
   from daily_harvester import DailyHarvester  # or run_harvest, check actual name

   # In the main() or setup() function, after app is created:
   scheduler = AsyncIOScheduler(timezone="Asia/Tokyo")  # JST for Bashara
   harvester = DailyHarvester()

   # Run daily at 3:00 AM JST
   scheduler.add_job(
       harvester.run,
       trigger="cron",
       hour=3,
       minute=0,
       id="daily_harvest",
       replace_existing=True
   )
   # Also run immediately on startup to test it works:
   scheduler.add_job(
       harvester.run,
       trigger="date",  # run once immediately
       id="startup_harvest"
   )
   scheduler.start()
   logger.info("✅ Daily harvester scheduled: 03:00 JST daily")

5. Ensure apscheduler is in requirements.txt:
   apscheduler>=3.10.0
   (check if already there; if not, add it)

6. If daily_harvester.py is too minimal (stub), implement the core:
   async def run(self):
       logger.info("Daily harvest starting...")
       topics = self._get_harvest_topics()  # from config or wiki
       for topic in topics[:5]:  # limit to 5 per day
           try:
               results = await search_tool.execute(topic)
               await wiki_manager.ingest(topic, results)
               logger.info(f"Harvested: {topic}")
           except Exception as e:
               logger.error(f"Harvest failed for {topic}: {e}")
       logger.info("Daily harvest complete")

════════════════════════════════════════════════════════════════════
CONCERN 6 — GROWTH WITHOUT VERIFICATION (the root cause of all bugs)
════════════════════════════════════════════════════════════════════

EVIDENCE: The repo has MANY features added over time but no automated
regression testing. Every new feature potentially breaks old ones.
The dual llm_client, dual agents, stub handlers — all symptoms of the same
problem: features were added but old connections were never verified.

FIX: Install a permanent regression guard that runs on every git push.

STEP 1 — Create scripts/verify_wiring.py (if not exists from Audit 14):
  Check: python scripts/verify_wiring.py
  If it doesn\'t exist yet: create it (see prompts/audit/14_verify_wiring_script.md)

STEP 2 — Update .github/workflows/ for CI:
  Check .github/workflows/ directory for existing CI files.
  If a workflow file exists: add the verify step to it.
  If none exists: create .github/workflows/legion_guard.yml:

```yaml
name: Legion Wiring Guard
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  wiring-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: \'3.11\'
      - name: Install minimal deps
        run: pip install python-telegram-bot litellm aiofiles httpx
      - name: Verify wiring
        run: python scripts/verify_wiring.py
      - name: Run integration tests
        run: python -m pytest tests/test_integration.py -v --tb=short
        if: hashFiles(\'tests/test_integration.py\') != \'\'
```

STEP 3 — Add pre-commit hook (local guard before push):
  Check if .pre-commit-config.yaml exists (it does in this repo).
  Add a local hook:

  # In .pre-commit-config.yaml, add:
  - repo: local
    hooks:
      - id: legion-wiring
        name: Legion Wiring Check
        entry: python scripts/verify_wiring.py
        language: python
        pass_filenames: false
        always_run: true

STEP 4 — Update Makefile:
  Check Makefile (it exists in this repo).
  Ensure it has:
    verify:
        python scripts/verify_wiring.py

    test:
        python -m pytest tests/ -v

    guard: verify test
        @echo "✅ All guards passed — safe to deploy"

    deploy: guard
        ./deploy.sh

  This forces "make guard" to pass before deploy is allowed.

════════════════════════════════════════════════════════════════════
CONCERN 7 — SOUL INTEGRITY UNDER ALL CONDITIONS
════════════════════════════════════════════════════════════════════

EVIDENCE: SOUL.md exists and is 4312 bytes. But with 36 handler files,
many different pipelines, and features like nihongo mode, computer agent,
and swarm mode — there is high risk that some code paths bypass soul injection.

FIX STEPS:

1. Read SOUL.md. Note the first 100 characters as a fingerprint:
   SOUL_FINGERPRINT = SOUL.md[:100]

2. Find every place messages[] is built for an LLM call:
   grep -rn "messages = \[\|messages.append\|\"role\".*\"system\"" . --include="*.py"
   Build a list of all LLM call assembly points.

3. For EACH assembly point: verify messages[0] is the soul system prompt.
   Any assembly point that does NOT start with soul → broken.

4. The correct pattern that must exist in system_prompt_builder.py or
   equivalent (create it if it doesn\'t have this):

   async def build_messages(user_id: int, user_message: str,
                             history: list = None,
                             search_context: str = "",
                             wiki_context: str = "") -> list:
       """CANONICAL message builder. All LLM calls MUST use this."""
       messages = []

       # 1. SOUL — always first, always present, never conditional
       soul = soul_engine.get_system_prompt()
       assert len(soul) > 100, "Soul empty!"
       messages.append({"role": "system", "content": soul})

       # 2. MEMORY — second, if available
       memory = await memory_engine.read_memory(user_id)
       if memory:
           messages.append({"role": "system",
                            "content": f"[Memories about this user]\n{memory}"})

       # 3. WIKI CONTEXT — third, if available
       if wiki_context:
           messages.append({"role": "system",
                            "content": f"[Knowledge Base]\n{wiki_context}"})

       # 4. SEARCH CONTEXT — fourth, if available (real-time data)
       if search_context:
           messages.append({"role": "system",
                            "content": f"[Live Search Results]\n{search_context}"})

       # 5. CONVERSATION HISTORY
       if history:
           messages.extend(history[-20:])  # last 20 turns max

       # 6. CURRENT MESSAGE — always last
       messages.append({"role": "user", "content": user_message})

       return messages

5. Refactor EVERY LLM call site to use build_messages() instead of
   building messages[] manually.
   This ensures soul is always first, forever, in every code path.

6. Add a soul integrity assertion at bot startup in main.py:
   soul_text = soul_engine.get_system_prompt()
   assert len(soul_text) > 100, "🚨 CRITICAL: Soul not loaded! Check SOUL.md"
   assert "Legion" in soul_text or "legion" in soul_text, \
       "🚨 CRITICAL: Soul identity missing!"
   logger.info(f"✅ Soul loaded: {len(soul_text)} chars")

════════════════════════════════════════════════════════════════════
FINAL VERIFICATION — Run all checks in sequence
════════════════════════════════════════════════════════════════════

After all 7 concerns are fixed, run this exact sequence:

  # 1. Import check
  python -c "
  from llm_client import call_llm
  from agents import BaseAgent  # or actual export
  from task_orchestrator import TaskOrchestrator
  from handlers.swarm_handler import handle_swarm
  from core.soul_engine import get_system_prompt
  import daily_harvester
  print(\'All critical imports OK ✅\')
  "

  # 2. Wiring check
  python scripts/verify_wiring.py

  # 3. Integration tests (if tests/test_integration.py exists)
  python -m pytest tests/test_integration.py -v --tb=short

  # 4. Single combined gate
  python scripts/verify_wiring.py && echo "✅ Wiring OK" && \
  python -m pytest tests/ -v --tb=short -q && echo "✅ Tests OK" && \
  echo "🟢 Legion is production-ready"

All 4 must succeed with 0 errors before this session is complete.

════════════════════════════════════════════════════════════════════
CREATE CONCERNS_FIXED_REPORT.md AFTER COMPLETION
════════════════════════════════════════════════════════════════════

Create CONCERNS_FIXED_REPORT.md with:

# Legion Concerns Fixed — [date]

## Summary
| # | Concern | Status | Key Fix Applied |
|---|---------|--------|-----------------|
| 1 | Dual llm_client | ✅ Fixed | llm_client.py made shim, dir is canonical |
| 2 | Dual agents | ✅ Fixed | agents.py made shim, dir is canonical |
| 3 | Swarm handler stub | ✅ Fixed | Connected to task_orchestrator.py |
| 4 | Search injection bug | ✅ Fixed | Results injected before call_llm |
| 5 | Daily harvester unscheduled | ✅ Fixed | APScheduler added to main.py |
| 6 | Growth without verification | ✅ Fixed | CI + pre-commit + make guard |
| 7 | Soul integrity | ✅ Fixed | build_messages() canonical builder |

## Final Gate
`python scripts/verify_wiring.py && pytest tests/` → EXIT 0 ✅

## Legion status: 🟢 Wide AND Deep
```
