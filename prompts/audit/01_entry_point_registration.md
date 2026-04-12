# AUDIT 01 — Entry Point & Handler Registration
> Paste this entire prompt into a new OpenCode session.
> Goal: ensure every handler function is registered in main.py.

---

```
╔══════════════════════════════════════════════════════════════════╗
║  LEGION AUDIT 01 — Entry Point & Handler Registration           ║
║  Fix: every handler must be wired into main.py                  ║
╚══════════════════════════════════════════════════════════════════╝

STEP 1 — READ ENTRY POINT
Read main.py completely.
Build a list of every app.add_handler() call.
For each: note the handler type, command string/filter, and the target function name + its source file.

STEP 2 — SCAN ALL HANDLER FILES
Read every file in handlers/:
  admin_handlers.py, ai.py, artifact.py, brain.py, business_handler.py,
  communications.py, computer.py, debate_handlers.py, dev.py, e2e.py,
  ecc_compat.py, enterprise.py, github_intel_handler.py, inline.py,
  legion_extras.py, media_tools.py, memory_commands.py, message_handler.py,
  orchestrate.py, overnight_handler.py, persona_handler.py, pm.py,
  research.py, runbook_handler.py, session_handler.py, sessions.py,
  shared.py, skills.py, streaming.py, swarm_handler.py, system.py,
  tasks.py, upgrade.py, voice.py, whatsapp_handler.py, wiki.py, wiki_handler.py

For each file list every public async handler function:
  signature: async def xxx(update, context) or async def xxx(update: Update, context: ContextTypes.DEFAULT_TYPE)

STEP 3 — DIFF
Compare your two lists.
Every handler function NOT registered in main.py = broken wire.

STEP 4 — FIX
For each missing registration:
  - Determine the correct handler type:
    /command → CommandHandler("command", function)
    plain text → MessageHandler(filters.TEXT & ~filters.COMMAND, function)
    voice → MessageHandler(filters.VOICE, function)
    photo → MessageHandler(filters.PHOTO, function)
    inline → InlineQueryHandler(function)
    callback → CallbackQueryHandler(function, pattern="...")
  - Add it to main.py in the correct position (before app.run_polling())
  - Ensure the import for that handler file is at the top of main.py

STEP 5 — VERIFY
Re-read main.py.
Confirm every handler from Step 2 now appears in Step 1's list.
List every fix made.

DO NOT modify SOUL.md, CLAUDE.md, or LEGION_MASTER.md.
DO NOT change existing registered handlers — only add missing ones.
```
