# AUDIT 02 — Message Pipeline Connectivity
> Paste this entire prompt into a new OpenCode session.
> Goal: trace plain text message end-to-end and fix every broken hop.

---

```
╔══════════════════════════════════════════════════════════════════╗
║  LEGION AUDIT 02 — Message Pipeline Connectivity                ║
║  Fix: every hop from Telegram input → LLM reply must be real    ║
╚══════════════════════════════════════════════════════════════════╝

STEP 1 — TRACE THE HAPPY PATH
Trace a plain text message through the code hop-by-hop.
For EACH hop, find the EXACT line of code that makes the call.
The expected path:

  main.py: MessageHandler(filters.TEXT, ???)
       ↓ await
  handlers/message_handler.py OR handlers/ai.py: handle_message() / handle_ai()
       ↓ await
  core/autonomous_router.py OR core/intent_router.py: route()
       ↓ await
  core/task_router.py OR specific handler: dispatch()
       ↓ await
  core/system_prompt_builder.py: build_system_prompt()
       ↓ return
  llm_client/: call_llm() or litellm.acompletion()
       ↓ return
  handler: update.message.reply_text(response)

For each arrow:
  - Find exact file:line_number
  - Is the function awaited? If not → broken wire (Type E)
  - Is the return value used by the caller? If not → broken wire (Type D)

STEP 2 — FIX BROKEN HOPS
For each broken hop found:
  - Add missing await
  - Add missing return value usage
  - Add missing function call
  - Ensure arguments passed match function signature

STEP 3 — DUPLICATE PIPELINE CHECK
Check if handlers/message_handler.py AND handlers/ai.py BOTH handle plain text.
If yes: one should delegate to the other, not run in parallel.
Decide which is primary. Make the secondary call the primary.
Remove duplicate logic.

STEP 4 — ROUTER FALLTHROUGH
Read each router: router.py, core/autonomous_router.py, core/intent_router.py, core/task_router.py.
Find what happens when NO case matches.
The fallthrough MUST route to general LLM chat, not return None or raise exception.
Fix any router that returns None or crashes on unknown intent.

STEP 5 — REPLY ALWAYS SENT
Grep for every place where update.message.reply_text / bot.send_message is called.
Verify there is no code path where a user sends a message and gets NO reply.
Add a final fallback reply if needed:
  await update.message.reply_text("Gw lagi bingung, coba lagi ya.")

DO NOT modify SOUL.md, CLAUDE.md, or LEGION_MASTER.md.
```
