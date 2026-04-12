# AUDIT 07 — Orphan & Stub Handlers
> Paste this entire prompt into a new OpenCode session.
> Goal: identify every handler that is a stub or dead — fix or explicitly disable.

---

```
╔══════════════════════════════════════════════════════════════════╗
║  LEGION AUDIT 07 — Orphan & Stub Handlers                       ║
║  Fix: no silent stubs; every handler either works or is flagged ║
╚══════════════════════════════════════════════════════════════════╝

STEP 1 — IDENTIFY STUBS
For each of these high-risk small files, read the full content and classify:

  handlers/swarm_handler.py       (906 bytes)
  handlers/runbook_handler.py     (970 bytes)
  handlers/streaming.py           (2915 bytes)
  handlers/whatsapp_handler.py    (6512 bytes)
  handlers/overnight_handler.py   (10063 bytes)
  handlers/enterprise.py          (3756 bytes)
  handlers/legion_extras.py       (3036 bytes)
  handlers/communications.py      (3010 bytes)
  handlers/session_handler.py     (3571 bytes)
  handlers/inline.py              (1891 bytes)

For each file classify as:
  WORKING  — has real implementation, registered in main.py, called by something
  STUB     — has pass, TODO, NotImplementedError, or returns None/empty
  ORPHAN   — has implementation but is NOT registered or called anywhere
  DEAD     — permanently disabled by flag, never intended to run

STEP 2 — FIX STUBS
For each STUB:
  Option A: Implement it properly (if the feature is needed)
  Option B: Add FEATURE_X_ENABLED = False guard and a clear log:
    if not FEATURE_X_ENABLED:
        await update.message.reply_text("Feature coming soon!")
        return

STEP 3 — FIX ORPHANS
For each ORPHAN:
  Add the missing registration in main.py (see Audit 01 for registration patterns)
  OR explicitly mark it as disabled with FEATURE_X_ENABLED = False

STEP 4 — SWARM HANDLER SPECIAL CHECK
Read handlers/swarm_handler.py.
Expected: it should call task_orchestrator.py or agents/ and distribute work.
If it's a stub: implement the minimum viable version:
  async def handle_swarm(update, context):
      task = update.message.text
      result = await orchestrator.run(task)
      await update.message.reply_text(result)

STEP 5 — STREAMING HANDLER SPECIAL CHECK
Read handlers/streaming.py.
If streaming is implemented: verify it's called from the main LLM call path.
If streaming is dead: either enable it by connecting it to call_llm(stream=True)
OR remove and replace with a single-call response.

STEP 6 — OVERNIGHT HANDLER SPECIAL CHECK
Read handlers/overnight_handler.py.
Check if it's registered as a scheduled job (APScheduler or asyncio periodic task).
If the scheduler is never started in main.py: add it:
  scheduler = AsyncIOScheduler()
  scheduler.add_job(overnight_handler.run_overnight, 'cron', hour=3)
  scheduler.start()

STEP 7 — REPORT
List every handler with its classification and what fix was applied.

DO NOT modify SOUL.md, CLAUDE.md, or LEGION_MASTER.md.
```
