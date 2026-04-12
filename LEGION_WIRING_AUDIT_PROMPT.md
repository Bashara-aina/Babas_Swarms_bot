# LEGION WIRING CONNECTIVITY AUDIT — OPENCODE MASTER PROMPT
> This prompt is ONLY about wiring: tracing every connection from entry point to output.
> Goal: every file, function, and feature must be FULLY connected end-to-end.
> Paste everything inside the code block into OpenCode as a single session.

---

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  LEGION WIRING AUDIT — Full Connectivity Trace                        ┃
┃  Mission: trace EVERY wire. Fix every broken connection.               ┃
┃  Output: WIRING_AUDIT_REPORT.md + all fixes committed                  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

════════════════════════════════════════════════════════════════════
STEP 0 — WHAT "WIRING" MEANS (read this before anything else)
════════════════════════════════════════════════════════════════════

A "wire" is broken when any of these is true:

  TYPE A — IMPORT WIRE CUT
    File A imports from File B, but File B never exports the function.
    File A imports a name that doesn't exist in File B.
    __init__.py doesn't re-export what downstream expects.

  TYPE B — REGISTRATION WIRE CUT
    A handler function exists but is NEVER registered in main.py.
    A command exists but no CommandHandler/MessageHandler is added to app.
    A callback function exists but its callback_data string is never sent.

  TYPE C — CALL WIRE CUT
    A function is defined, imported, but never called anywhere.
    A router case is listed but falls through to "unhandled".
    An intent is detected but no action is dispatched for it.

  TYPE D — DATA WIRE CUT
    A function receives a parameter but never passes it to the next stage.
    A result is computed but never returned/passed to caller.
    A tool is called but its output is never used.

  TYPE E — ASYNC WIRE CUT
    An async function is called without await → result is a coroutine, not data.
    asyncio.create_task() is used for something that needs to be awaited.
    A generator/stream is created but never iterated.

  TYPE F — FEATURE FLAG WIRE CUT
    A feature is disabled by flag (FEATURE_X = False) and the flag is never
    set to True anywhere, making the feature permanently dead.

For EVERY wire found: classify it (A/B/C/D/E/F), locate the exact file+line,
and immediately fix it. Do not batch fixes — fix each wire as you find it.

════════════════════════════════════════════════════════════════════
STEP 1 — MAP THE MASTER ENTRY POINT (main.py)
════════════════════════════════════════════════════════════════════

Read main.py completely. Build two lists:

LIST 1 — REGISTERED HANDLERS (what IS wired in main.py):
  For every `app.add_handler(...)` call, note:
    - Handler type (CommandHandler, MessageHandler, CallbackQueryHandler, etc)
    - Command string or filter
    - Function it points to
    - File that function lives in

LIST 2 — ALL HANDLER FILES (what SHOULD be wired):
  Read every file in handlers/ directory:
    admin_handlers.py, ai.py, artifact.py, brain.py, business_handler.py,
    communications.py, computer.py, debate_handlers.py, dev.py, e2e.py,
    ecc_compat.py, enterprise.py, github_intel_handler.py, inline.py,
    legion_extras.py, media_tools.py, memory_commands.py, message_handler.py,
    orchestrate.py, overnight_handler.py, persona_handler.py, pm.py,
    research.py, runbook_handler.py, session_handler.py, sessions.py,
    shared.py, skills.py, streaming.py, swarm_handler.py, system.py,
    tasks.py, upgrade.py, voice.py, whatsapp_handler.py, wiki.py,
    wiki_handler.py

  For each file, list every public function/coroutine that is a Telegram handler
  (signature: `async def xxx(update: Update, context: ContextTypes.DEFAULT_TYPE)`
   OR: `async def xxx(update, context)` OR any function decorated with @handler)

DIFF the two lists. Every function in LIST 2 not in LIST 1 = TYPE B broken wire.
Fix by adding the missing handler registration in main.py.

════════════════════════════════════════════════════════════════════
STEP 2 — TRACE THE PRIMARY MESSAGE PIPELINE
════════════════════════════════════════════════════════════════════

Trace the exact code path for a plain text message (most common case).
Follow the code hop-by-hop. At each hop, verify the function ACTUALLY calls
the next one (not just imports it).

Expected path (verify each arrow is real code, not assumption):

  main.py: MessageHandler(filters.TEXT, ???)
       ↓ calls
  handlers/message_handler.py: handle_message()  OR  handlers/ai.py: handle_ai()
       ↓ calls
  core/autonomous_router.py OR core/intent_router.py: route()
       ↓ calls (based on intent classification result)
  core/task_router.py: dispatch()  OR  handlers/*: specific_handler()
       ↓ calls
  core/system_prompt_builder.py: build_system_prompt()
       ↓ returns prompt to
  llm_client/: call_llm() OR litellm.acompletion()
       ↓ returns response to
  handler: sends reply via update.message.reply_text()

For EACH arrow:
  - Find the exact line of code where the call happens
  - Verify the return value is actually USED (not discarded)
  - Check if it's properly awaited if async
  - Note the file:line_number

If ANY arrow is missing or broken: fix it immediately.

════════════════════════════════════════════════════════════════════
STEP 3 — TRACE EVERY NAMED FEATURE PIPELINE
════════════════════════════════════════════════════════════════════

For each feature below, trace the FULL wire from Telegram input to final output.
Mark each step ✅ (wired) or ❌ (broken wire found).

■ FEATURE: WEB SEARCH
  Entry: user says something triggering search intent
  Expected wire:
    1. intent detection → search intent classified
    2. search tool called: skills/search.py or tools/search/ → execute()
    3. search results returned as string/list
    4. results INSERTED into LLM context messages[] before LLM call
    5. LLM call includes search results
    6. LLM reply references search results
    7. Reply sent to user
  Broken wire test: add a print/log at step 4. Does it fire?
  Fix: if step 4 is missing, find where results are returned and inject them:
    messages.append({"role": "system", "content": f"[Search Results]\n{results}"})

■ FEATURE: WIKI RETRIEVAL
  Entry: user asks about a topic that should be in wiki/
  Expected wire:
    1. intent detection OR pre-retrieval hook triggers wiki lookup
    2. core/wiki_bridge.py: retrieve(query) OR wiki_manager.py: search()
    3. wiki context returned as string
    4. wiki context INSERTED into LLM context before LLM call
    5. LLM reply uses wiki knowledge
  Check: does handlers/wiki.py connect to core/wiki_bridge.py?
  Check: does core/system_prompt_builder.py inject wiki context?
  Fix any missing connection.

■ FEATURE: MEMORY (REMEMBER / RECALL)
  Entry: user says something memorable OR asks "lo inget gak..."
  Expected wire (WRITE path):
    1. message_handler detects save-worthy content
    2. core/memory_engine.py: write_memory(user_id, content) called
    3. memory actually persisted (ChromaDB or mem0 or JSON file)
  Expected wire (READ path):
    1. LLM call preparation stage
    2. core/memory_engine.py: read_memory(user_id) called
    3. memories returned and INJECTED into system prompt or context
    4. LLM uses memory in response
  Check: is memory read called BEFORE every LLM call? Or only sometimes?
  Check: handlers/memory_commands.py (/remember, /recall commands)
    → are these registered in main.py?
    → do they call memory_engine functions properly?
  Fix any missing connection.

■ FEATURE: NIHONGO MODE
  Entry: /nihongo command OR /n command
  Expected wire:
    1. CommandHandler("/nihongo") → handlers/nihongo_handler.py: activate()
       OR handlers/ai.py has nihongo mode embedded
    2. activation sets per-user flag: user_nihongo_active[user_id] = True
    3. subsequent messages from that user → routed to nihongo pipeline
    4. nihongo pipeline: pykakasi romanization + Japanese grammar checking
    5. SenseiSoul persona injected into system prompt
    6. response in Japanese/nihongo teaching style
    7. /nihongo_off deactivates flag
  Check: is the per-user flag stored in a dict keyed by user_id?
  Check: does the main message handler CHECK this flag for every message?
  Read LEGION_NIHONGO_MODE.md for the intended wiring spec and compare to
  actual code in handlers/ and core/.
  Fix any gap between spec and implementation.

■ FEATURE: VOICE (voice messages in / voice responses out)
  Entry: user sends voice message (audio file) to bot
  Expected wire (INPUT):
    1. MessageHandler(filters.VOICE) → handlers/voice.py: handle_voice()
    2. download voice file from Telegram
    3. transcribe: faster-whisper or openai-whisper → text
    4. transcribed text fed into normal message pipeline
  Expected wire (OUTPUT):
    1. after LLM response text is ready
    2. TTS called: VoiceVox or gTTS → audio bytes
    3. audio sent via update.message.reply_voice()
  Check: does VoiceVox bridge in bridges/ connect to handlers/voice.py?
  Check: is the whisper transcription result actually used as message text?
  Fix any missing connection.

■ FEATURE: SKILL REGISTRY (core/skill_registry.py)
  Expected wire:
    1. skills/ directory files each define a Skill class with .execute()
    2. core/skill_registry.py loads all skills at startup
    3. skill_registry is passed to OR accessible by the intent router
    4. when intent matches a skill, skill_registry.get(skill_name).execute(args)
    5. skill result returned to LLM context
  Check: does skill_registry.py actually scan skills/ directory?
  Check: which skills are registered vs which files exist in skills/?
  Check: is skill_registry used in handlers/ai.py or core/autonomous_router.py?
  Fix any missing registration or dispatch.

■ FEATURE: MCP TOOLS (legion/mcp*.py or bridges/mcp*.py)
  Expected wire:
    1. LLM returns tool_call in response
    2. tool dispatcher in handlers/ai.py or core/autonomous_router.py receives it
    3. correct tool function called with parsed arguments
    4. tool result appended to messages as role:tool
    5. second LLM call made with tool result
    6. final response sent to user
  Check: is there a tool dispatch loop (not just single-call)?
  Check: does the loop handle multiple sequential tool calls?
  Check: does bridges/ connect properly to legion/ MCP tools?
  Fix any missing dispatch or result injection.

■ FEATURE: SWARM ORCHESTRATION (task_orchestrator.py + handlers/orchestrate.py)
  Expected wire:
    1. user sends complex task OR /swarm command
    2. handlers/orchestrate.py: handle_orchestrate() receives it
    3. task_orchestrator.py: orchestrate(task) called
    4. task split into sub-tasks
    5. sub-tasks dispatched to agents/ or skills/
    6. results aggregated
    7. final synthesis sent to user
  Check: is orchestrate.py registered in main.py?
  Check: does task_orchestrator.py actually call agents/ files?
  Check: does agents.py or agents/ directory connect to task_orchestrator?
  Fix any missing connection.

■ FEATURE: COMPUTER AGENT (handlers/computer.py + computer_agent/)
  Expected wire:
    1. /computer command OR computer-use intent detected
    2. handlers/computer.py: handle_computer() called
    3. computer_agent/ module invoked with task description
    4. results returned as text/screenshot
    5. response sent to user
  Check: does computer_agent/ have an __init__.py with exports?
  Check: does handlers/computer.py import from computer_agent/?
  Fix any disconnection.

■ FEATURE: RESEARCH PIPELINE (handlers/research.py)
  Expected wire:
    1. /research command OR deep-search intent
    2. handlers/research.py: handle_research()
    3. multiple web searches executed
    4. results synthesized
    5. wiki ingest triggered if high-quality content found
    6. structured report sent to user
  Check: does research.py call the web search tool?
  Check: does research.py trigger wiki ingestion?
  Fix any gap.

■ FEATURE: GITHUB INTEL (handlers/github_intel_handler.py)
  Expected wire:
    1. /github command OR github URL detected in message
    2. handlers/github_intel_handler.py: handle_github_intel()
    3. GitHub API called (via bridges/ or direct httpx)
    4. repo/PR/issue data fetched
    5. analysis sent to user
  Check: is github_intel_handler registered in main.py?
  Fix missing registration.

■ FEATURE: DAILY HARVESTER (daily_harvester.py)
  Expected wire:
    1. scheduled job (APScheduler or asyncio periodic task)
    2. daily_harvester.py: run() called on schedule
    3. harvests web content
    4. ingests into wiki
    5. optionally sends digest to admin
  Check: is the scheduler started in main.py?
  Check: is daily_harvester.run() registered as a job?
  Fix any missing scheduler registration.

■ FEATURE: INLINE QUERIES (handlers/inline.py)
  Expected wire:
    1. InlineQueryHandler → handlers/inline.py: handle_inline()
    2. query processed
    3. InlineQueryResultArticle list returned
    4. answer_inline_query() called
  Check: is InlineQueryHandler registered in main.py?
  Fix if missing.

■ FEATURE: CALLBACK QUERIES (button presses)
  Expected wire:
    1. CallbackQueryHandler with pattern matching → handler function
    2. handler reads callback_data
    3. correct action dispatched
    4. message edited or new message sent
  List ALL callback_data strings used in reply_markup across entire codebase.
  For each callback_data string: verify there is a registered CallbackQueryHandler
  that catches it.
  Fix any unhandled callback_data.

■ FEATURE: STREAMING RESPONSES (handlers/streaming.py)
  Expected wire:
    1. LLM call made with stream=True
    2. chunks received in async for loop
    3. Telegram message updated incrementally (edit_message_text)
    4. final message finalized
  Check: is streaming actually enabled in llm_client/?  
  Check: does handlers/streaming.py get called anywhere?
  Fix if it's a dead module.

■ FEATURE: SOUL ENGINE (core/soul_engine.py)
  Expected wire:
    1. soul_engine loaded at startup
    2. soul_engine.get_system_prompt() called by system_prompt_builder.py
    3. soul content ALWAYS first in every LLM messages[] array
    4. soul NOT overridden by any downstream prompt injection
  Check: find every place system prompt is assembled — is soul always first?
  Fix any place where soul is skipped or added conditionally.

■ FEATURE: WHATSAPP BRIDGE (handlers/whatsapp_handler.py)
  Expected wire:
    1. incoming WhatsApp message webhook → whatsapp_handler.py
    2. message normalized to same format as Telegram message
    3. feeds into same main message pipeline
    4. response sent back via WhatsApp API
  Check: is this feature enabled? Is the webhook registered?
  If permanently disabled: add FEATURE_WHATSAPP_ENABLED = False flag.
  If intended to work: fix the wiring.

════════════════════════════════════════════════════════════════════
STEP 4 — AUDIT THE ROUTER LAYER (the brain of routing)
════════════════════════════════════════════════════════════════════

Read all 4 router files:
  router.py (root)
  core/autonomous_router.py
  core/intent_router.py
  core/task_router.py

For each router:

  4A — COVERAGE: list every intent/case the router handles.
       Then list every feature that SHOULD be routed.
       Find any feature with no router case → broken wire.

  4B — FALLTHROUGH: what happens when no case matches?
       Is there a default/fallthrough handler? Does it do something useful?
       Should route to general LLM chat, not crash or return None.

  4C — ROUTER CHAIN: does router.py call core/autonomous_router.py?
       Does autonomous_router call intent_router?
       Does intent_router call task_router?
       Map the chain. Find any router that is imported but never called.

  4D — RETURN VALUES: does every router function return a value?
       Is the return value checked by the caller?
       `result = await route(message)` then `if result is None` check?

Fix any router coverage gap, fallthrough gap, chain gap, or return value gap.

════════════════════════════════════════════════════════════════════
STEP 5 — AUDIT THE CORE LAYER (engine room)
════════════════════════════════════════════════════════════════════

List every file in core/. For EACH core module, answer:

  5A — Who CALLS this module? (search for imports of this file across codebase)
       If no file imports it → dead module → Type C broken wire.
       Either wire it in or mark FEATURE_X = False.

  5B — Does this module EXPORT what callers expect?
       Check: caller does `from core.xxx import YYY`
       Verify YYY actually exists in core/xxx.py.
       If not: Type A broken wire → fix the export.

  5C — Does core/__init__.py export the right names?
       Any downstream that does `from core import X` —
       verify X is in core/__init__.py.

  Core files to audit specifically:
    core/autonomous_router.py
    core/intent_router.py  
    core/task_router.py
    core/soul_engine.py
    core/memory_engine.py
    core/skill_registry.py
    core/system_prompt_builder.py
    core/conversation_interface.py
    core/multi_user.py (if exists)
    core/health.py (if exists)
    core/observability.py (if exists)
    core/rate_limiter.py (if exists)
    core/wiki_bridge.py (if exists)

════════════════════════════════════════════════════════════════════
STEP 6 — AUDIT THE LLM CLIENT LAYER
════════════════════════════════════════════════════════════════════

There are two llm_client locations: llm_client.py (root) AND llm_client/ (dir).

  6A — DUPLICATION: which one is actually used?
       Search all files for `from llm_client import` and `import llm_client`.
       If both are used: consolidate into one (keep llm_client/ dir).
       Make llm_client.py a shim that imports from llm_client/.

  6B — INTERFACE: what function do callers expect?
       Most likely: `call_llm(messages, model, ...)` or `acompletion(...)`
       Verify this function EXISTS and has the right signature.
       Verify it returns a string (extracted content), not a raw API response object.

  6C — MODEL SELECTION: is the model selection wired?
       Does llm_client use OPENROUTER_API_KEY from environment?
       Does it fall back properly when primary model fails?
       Is litellm configured with the right base_url for OpenRouter?

  6D — TOOL CALLING: does llm_client support tools parameter?
       When tools=[] is passed, does it properly forward to the API?
       When API returns a tool_call: is it returned to the caller, not discarded?

════════════════════════════════════════════════════════════════════
STEP 7 — AUDIT THE BRIDGES LAYER
════════════════════════════════════════════════════════════════════

List every file in bridges/. For each bridge:

  7A — Does it connect to its target service?
       bridge file → external service (VoiceVox, WhatsApp, GitHub, etc.)
       Find the function that makes the actual API/network call.
       Verify it's reachable from handlers/.

  7B — Is the bridge imported and called anywhere?
       Search for imports of each bridge file.
       If no imports found → dead bridge → either wire it or flag it.

  7C — Does bridges/__init__.py export the right interfaces?

════════════════════════════════════════════════════════════════════
STEP 8 — AUDIT THE SKILLS LAYER
════════════════════════════════════════════════════════════════════

List every file in skills/.

  8A — Does each skill have the required interface?
       Required: class-based OR function-based with execute() method OR
       a callable that skill_registry can load.
       Fix any skill that doesn't match the expected interface.

  8B — Is each skill registered in core/skill_registry.py?
       The registry should auto-discover skills by scanning skills/ directory.
       If not auto-discovering: manually check each skill is in the registry.

  8C — Can each skill be triggered from user input?
       For each skill: what user message or intent maps to it?
       If no intent maps to it: either add the mapping or mark the skill disabled.

════════════════════════════════════════════════════════════════════
STEP 9 — AUDIT __init__.py FILES (the import glue)
════════════════════════════════════════════════════════════════════

Check EVERY __init__.py in:
  handlers/__init__.py
  core/__init__.py
  skills/__init__.py
  agents/__init__.py
  bridges/__init__.py
  llm_client/__init__.py
  tools/__init__.py
  legion/__init__.py (if exists)

For each __init__.py:
  - Does it import and re-export the key classes/functions from submodules?
  - Does any downstream code `from handlers import handle_message` → 
    is handle_message in handlers/__init__.py?
  - Are there any ImportError risks (importing something that might not exist)?

Fix any __init__.py that is empty but should export things.
Fix any __init__.py that imports a name that doesn't exist in the submodule.

════════════════════════════════════════════════════════════════════
STEP 10 — AUTOMATED WIRING VERIFICATION (write a script, run it)
════════════════════════════════════════════════════════════════════

Create scripts/verify_wiring.py that performs automated wiring checks:

```python
#!/usr/bin/env python3
"""Legion Wiring Verification Script

Runs import checks, registration checks, and basic connectivity tests.
Output: PASS/FAIL per check with file:line references.
"""
import ast
import sys
import importlib
from pathlib import Path

failures = []

# CHECK 1: All handler files can be imported without error
HANDLER_FILES = [
    "handlers.admin_handlers", "handlers.ai", "handlers.artifact",
    "handlers.brain", "handlers.business_handler", "handlers.communications",
    "handlers.computer", "handlers.debate_handlers", "handlers.dev",
    "handlers.e2e", "handlers.ecc_compat", "handlers.enterprise",
    "handlers.github_intel_handler", "handlers.inline", "handlers.legion_extras",
    "handlers.media_tools", "handlers.memory_commands", "handlers.message_handler",
    "handlers.orchestrate", "handlers.overnight_handler", "handlers.persona_handler",
    "handlers.pm", "handlers.research", "handlers.runbook_handler",
    "handlers.session_handler", "handlers.sessions", "handlers.shared",
    "handlers.skills", "handlers.streaming", "handlers.swarm_handler",
    "handlers.system", "handlers.tasks", "handlers.upgrade",
    "handlers.voice", "handlers.whatsapp_handler", "handlers.wiki",
    "handlers.wiki_handler",
]

CORE_FILES = [
    "core.autonomous_router", "core.intent_router", "core.task_router",
    "core.soul_engine", "core.memory_engine", "core.skill_registry",
    "core.system_prompt_builder", "core.conversation_interface",
]

for mod in HANDLER_FILES + CORE_FILES:
    try:
        importlib.import_module(mod)
        print(f"\u2705 {mod}")
    except ImportError as e:
        print(f"\u274c {mod}: {e}")
        failures.append((mod, str(e)))
    except Exception as e:
        print(f"\u26a0\ufe0f  {mod}: runtime error: {e}")
        failures.append((mod, str(e)))

# CHECK 2: main.py registers handlers for key features
main_source = Path("main.py").read_text()
REQUIRED_REGISTRATIONS = [
    "handle_voice",       # voice input
    "handle_inline",      # inline queries
    "nihongo",            # nihongo mode
    "handle_memory",      # memory commands
    "handle_research",    # research pipeline
]
for reg in REQUIRED_REGISTRATIONS:
    if reg in main_source:
        print(f"\u2705 main.py registers: {reg}")
    else:
        print(f"\u274c main.py MISSING registration for: {reg}")
        failures.append(("main.py", f"missing: {reg}"))

# CHECK 3: Soul is present in system prompt builder
soul_builder = Path("core/system_prompt_builder.py").read_text()
if "soul" in soul_builder.lower() or "SOUL" in soul_builder:
    print("\u2705 system_prompt_builder.py references soul")
else:
    print("\u274c system_prompt_builder.py does NOT reference soul!")
    failures.append(("core/system_prompt_builder.py", "soul not injected"))

# SUMMARY
print(f"\n{'='*60}")
if failures:
    print(f"WIRING AUDIT: {len(failures)} FAILURES FOUND")
    for f in failures:
        print(f"  \u274c {f[0]}: {f[1]}")
    sys.exit(1)
else:
    print("WIRING AUDIT: ALL CHECKS PASSED \u2705")
    sys.exit(0)
```

Run: `python scripts/verify_wiring.py`
Fix every FAILURE until the script exits 0.

════════════════════════════════════════════════════════════════════
STEP 11 — FINAL OUTPUT: WIRING_AUDIT_REPORT.md
════════════════════════════════════════════════════════════════════

After completing all steps, create WIRING_AUDIT_REPORT.md with:

## WIRING AUDIT REPORT — [date]

### BROKEN WIRES FOUND AND FIXED
| # | Type | File | Line | Description | Fix Applied |
|---|------|------|------|-------------|-------------|
| 1 | B    | main.py | 245 | handle_voice not registered | Added CommandHandler |
...

### WIRES CONFIRMED CONNECTED
| Feature | Entry Point | Exit Point | Status |
|---------|-------------|------------|--------|
| Plain text chat | main.py MessageHandler | handlers/ai.py send_reply | ✅ |
| Web search | intent_router search | skills/search.py execute | ✅ |
...

### PERMANENTLY DISABLED FEATURES (by design)
| Feature | Flag | Reason |
|---------|------|--------|
| WhatsApp bridge | FEATURE_WHATSAPP = False | Not yet deployed |
...

### VERIFY SCRIPT RESULT
`python scripts/verify_wiring.py` → EXIT 0 ✅

════════════════════════════════════════════════════════════════════
HARD RULES — NEVER VIOLATE:
════════════════════════════════════════════════════════════════════

1. Never modify SOUL.md, CLAUDE.md, LEGION_MASTER.md
2. Never change a working wire — only fix broken ones
3. If a feature wire would require major refactor: add a clear TODO comment
   with the label WIRING_TODO and keep the feature behind a False flag
4. Every fix must be minimal — change only what's needed to connect the wire
5. Preserve all existing function signatures — only add missing calls/returns
6. After every batch of fixes: run python scripts/verify_wiring.py to confirm
   no regressions
```
