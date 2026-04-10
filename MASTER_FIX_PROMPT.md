# MASTER FIX PROMPT — Legion v10 Revival

**For: Any AI Agent (Claude, Cursor, etc.) tasked with fixing Legion**
**Created: April 10, 2026**
**Context: Deep audit results from DEEP_AUDIT_2026-04-10.md**

---

## WHO YOU ARE

You are a senior AI systems engineer performing a surgical revival of Legion — a Telegram bot that is supposed to be Bashara's personal Jarvis-like AI assistant. The bot has a massive codebase with many powerful subsystems, but they are disconnected from each other. Your job is to wire them together so Legion feels alive, opinionated, intelligent, and genuinely useful.

**You are not building new features. You are connecting existing systems that are currently orphaned.**

---

## THE PROBLEM IN ONE SENTENCE

Legion has a soul, personality, emotion engine, debate system, memory tiers, 76 agents, proactive behaviors, tool integrations — but most of these are not wired into the actual message flow in `llm_client.py chat()`, making the bot feel like an empty shell.

---

## CRITICAL CONTEXT

- **Framework:** aiogram 3.4+ (async Telegram bot)
- **LLM:** litellm 1.57+ (cloud-first with fallback chains)
- **All LLM calls** go through `llm_client.chat()` or `llm_client.agent_loop()`
- **Entry point:** `main.py` → `handlers/ai.py handle_nl()` → `handlers/message_handler.py handle_plain_message()` → `handlers/shared.py _execute_chat()` → `llm_client.chat()`
- **The bot runs on a remote Linux machine** (RTX 3060 + 64GB RAM), not on the development machine
- **DO NOT** break existing functionality to add new functionality
- **DO NOT** use `threading` or `time.sleep()` — fully async project
- **DO NOT** hardcode API keys — always `os.getenv()`
- **DO NOT** log user message content
- **ALL changes must be tested** with the smoke tests in CLAUDE.md Section 12

---

## PHASE 1: MAKE LEGION ALIVE (Soul + Personality Wiring)

### Task 1.1: Move Soul to Prompt Position 0

**File:** `llm_client.py`, inside `chat()` function

**Current behavior:** `prompt_sections` starts with `build_base_persona()`. Soul context from `build_soul_context()` is nested inside `SystemPromptBuilder.build()` which is appended much later (5th+ position).

**Required change:**
1. At the beginning of `prompt_sections` assembly in `chat()`, add `build_soul_context()` as the FIRST section
2. Import `build_soul_context` from `core.soul_engine`
3. Wrap in try/except so it doesn't crash if SOUL.md is missing
4. The soul block should come BEFORE `build_base_persona()`

**Validation:** After this change, run:
```python
python -c "from core.soul_engine import build_soul_context; print(build_soul_context()[:100])"
```
And verify the system prompt in chat() starts with soul content.

### Task 1.2: Inject Disagreement Protocol

**File:** `llm_client.py`, inside `chat()` function

**Current behavior:** `get_disagreement_prompt()` from `core/character/disagreement_protocol.py` is only used in `build_full_system_prompt()` which `chat()` never calls.

**Required change:**
1. Import `get_disagreement_prompt` from `core.character.disagreement_protocol`
2. Add it to `prompt_sections` after the soul and persona sections
3. Wrap in try/except

**Validation:** Send "/run I think Python is the best language for everything" — Legion should push back with arguments, not agree blindly.

### Task 1.3: Fix PERSONALITY_WRAPPER Usage

**File:** `llm_client.py`, inside `chat()` function

**Current behavior:** `PERSONALITY_WRAPPER` (80+ lines of rich personality) in `agents.py` is completely unused by `chat()`. Instead, `build_base_persona()` from `core/character/persona.py` is used, which may be thinner.

**Required change:** Choose ONE of these approaches:
- **Option A (recommended):** Import `PERSONALITY_WRAPPER` from `router` and prepend it to `prompt_sections` right after soul context, REPLACING `build_base_persona()` (since PERSONALITY_WRAPPER is more comprehensive)
- **Option B:** Merge the content of `PERSONALITY_WRAPPER` into `build_base_persona()` / `legion_character.json`
- **Option C:** Add `PERSONALITY_WRAPPER` as an additional section alongside `build_base_persona()`

**Validation:** Send "/run hello, who are you?" — response should reflect Legion's full personality (direct, opinionated, matches language, no sycophancy), not a generic AI assistant.

### Task 1.4: Fix /debate Handler

**File:** `handlers/debate_handlers.py`

**Current behavior:** Calls `chat(messages=[...], system=...)` but `chat()` signature is `chat(task: str, agent_key=None, ...)`. This crashes with `TypeError`.

**Required change:**
1. Fix all `chat()` calls in this file to use the correct signature: `response, model = await chat(task=..., agent_key="debate", user_id=...)`
2. Handle the tuple return (response, model_used)
3. Use `send_chunked()` for the response

**Validation:** Send "/debate AI will take all jobs" — should work without crashing and Legion should push back with arguments.

### Task 1.5: Push SYSTEM_PROMPTS into prompt_sections

**File:** `llm_client.py`, inside `chat()` function

**Current behavior:** At line ~987, `system_prompt = SYSTEM_PROMPTS.get(agent_key, SYSTEM_PROMPTS["general"])` is set. At line ~1296, `system_prompt` is REPLACED by `"\n\n".join(prompt_sections)`. The per-agent role instructions are discarded.

**Required change:**
1. Check if `build_mode_instructions(agent_key)` already covers all agent keys in `SYSTEM_PROMPTS`
2. If not, add the `SYSTEM_PROMPTS[agent_key]` content to `prompt_sections` (probably near `build_mode_instructions`)
3. Remove the dead assignment at line ~987 or keep it only as a fallback if `prompt_sections` is empty

**Validation:** Send a coding question — response should reflect the coding agent's specialized instructions, not generic.

---

## PHASE 2: MAKE LEGION SMART (Routing & Auto-Skills)

### Task 2.1: Load 76 YAML Agents at Startup

**File:** `main.py`, inside `on_startup()`

**Current behavior:** `core/agent_registry.py` `load_registry()` is only called on SIGHUP signal. The 76 agents in `config/departments.yaml` are never loaded at startup.

**Required change:**
1. In `on_startup()`, after the initial setup block, add:
```python
try:
    from core.agent_registry import load_registry
    load_registry()
    logger.info("Agent registry loaded from YAML")
except Exception as e:
    logger.warning(f"Agent registry YAML load failed: {e}")
```

**Validation:** After startup, verify `AGENT_REGISTRY` has entries from departments.yaml.

### Task 2.2: Build Autonomous Skill Selection

**File:** New logic in `handlers/message_handler.py` or new file `core/jarvis_orchestrator.py`

**Current behavior:** User must use slash commands (`/do`, `/screen`, `/debate`, etc.) to trigger specific capabilities. Plain text goes through a basic keyword-matching `AutonomousRouter`.

**Required change:** Build a `JarvisOrchestrator` that:
1. Takes the user message
2. Uses `classify_intent_fast()` + keyword analysis to determine:
   - Is this a request for information? → May need web search
   - Is this about code? → Route to coding agent with code context
   - Is this about rumahlabuh.com? → Query Supabase
   - Is this a debate/opinion? → Activate debate mode with disagreement
   - Is this about email/calendar? → Check Composio
   - Is this about location? → Use location tools
   - Is this a computer control request? → Use agent_loop with tools
   - Is this casual chat? → Full personality + soul
3. Selects the appropriate agent_key, tools, and context
4. Calls `chat()` or `agent_loop()` with the right configuration
5. Handles multi-step tasks (research then answer, check then report)

**Key design principle:** This should enhance, not replace, the existing routing. If AutonomousRouter or JarvisOrchestrator can't decide, fall back to `general` agent with full personality.

**Validation:** 
- Send "what restaurants are good near me" → should trigger location/places tools
- Send "check my email" → should trigger Composio email
- Send "AI is overrated" → should trigger debate mode
- Send "hello" → should be casual chat with full personality

### Task 2.3: Make Intent Router Actually Route

**File:** `core/intent_router.py`

**Current behavior:** `classify_intent_fast()` returns an intent string, but in `chat()` it's only used to add a one-line "hint" to the system prompt. It doesn't change behavior.

**Required change:**
1. Make intent classification return structured data: `{intent, confidence, suggested_agent, needs_tools, needs_research}`
2. Use this in `JarvisOrchestrator` (Task 2.2) to drive real behavioral differences
3. Remove the dead `classify_intent_llm()` function

---

## PHASE 3: MAKE LEGION REMEMBER (Memory Fixes)

### Task 3.1: Consolidate Memory Writes

**File:** `llm_client.py` `chat()` function, `core/memory/memory_manager.py`

**Current behavior:** `chat()` makes direct writes to mem0, Letta, MemoryOS, episodic store, bypassing the `MemoryManager` facade.

**Required change:**
1. Identify all memory write points in `chat()`
2. Route them through `MemoryManager.store()` instead of direct calls
3. Let `MemoryManager` decide which tiers to write to

### Task 3.2: Add Automatic Fact Extraction

**File:** New function in `core/memory/memory_manager.py` or `core/cognition_pipeline.py`

**Current behavior:** When you tell Legion "I'm going to Tokyo next week", nothing extracts and stores this fact.

**Required change:**
1. After each conversation turn, run a lightweight fact extraction on the user's message
2. Extract: names, dates, preferences, plans, opinions, locations mentioned
3. Store extracted facts in `data/beliefs.json` `bashara_facts` and/or episodic memory
4. Keep this lightweight — don't call an LLM for every message, use pattern matching first

### Task 3.3: Persist Conversation History

**File:** `agents.py` or new file

**Current behavior:** `CONVERSATION_HISTORY` is a plain Python dict — lost on bot restart.

**Required change:**
1. Back `CONVERSATION_HISTORY` with SQLite (aiosqlite) or the existing episodic store
2. Load last N conversations on startup
3. Save conversations on each turn
4. Add TTL (e.g., 30 days) to prevent unbounded growth

### Task 3.4: Fix temporal_graph.py Async

**File:** `core/memory/temporal_graph.py`

**Current behavior:** Uses synchronous `sqlite3` which can block the event loop.

**Required change:** Replace `sqlite3` with `aiosqlite`, make all methods `async`.

---

## PHASE 4: MAKE LEGION PROACTIVE (Automation)

### Task 4.1: Fix Curiosity Engine Bug

**File:** `core/proactive/curiosity_engine.py`

**Current behavior:** Follow-up message formats as dict string `"{task}"` instead of the task text.

**Required change:** Fix the string formatting to extract the actual task text from the dict.

### Task 4.2: Build Proper Daily Briefing

**File:** `core/proactive/scheduler.py` and `tools/briefing.py`

**Current behavior:** Briefing exists but is split across files and may not run reliably.

**Required change:**
1. Ensure the daily briefing runs at the configured time (07:30 JST)
2. Include: weather, calendar events (if Composio configured), pending tasks, rumahlabuh.com health
3. Deliver via Telegram message to Bashara
4. Budget-gate the LLM calls but always send the briefing

### Task 4.3: Add /debate and /opinion to Command Menu

**File:** `main.py`, inside `set_my_commands` block

**Required change:** Add to the BotCommand list:
```python
BotCommand("debate", "Debate a topic with Legion"),
BotCommand("opinion", "Get Legion's honest opinion"),
```

---

## PHASE 5: CLEANUP

### Task 5.1: Delete Dead Code

Delete these directories and files:
- `core/memory_old/`
- `core/orchestration_old/`
- `core/reliability_old/`
- `core/task_orchestrator_old.py`
- Move `EMERGENCY_FIX.md` and `HOTFIX_2026-03-08.md` to `docs/hotfixes/`

### Task 5.2: Update CLAUDE.md

After all fixes, update CLAUDE.md Section 2 (Architecture Map) to reflect actual file names:
- `handlers/basic.py` → `handlers/system.py`
- `handlers/llm_handlers.py` → `handlers/ai.py`
- `handlers/memory_handlers.py` → `handlers/memory_commands.py`
- `handlers/_shared.py` → `handlers/shared.py`
- `tools/n8n_client.py` → `tools/n8n_bridge.py`
- `tools/letta_client.py` → `tools/letta_personality.py`
- Remove `tools/memory/` (doesn't exist)
- `.env RUFLO_PORT` → document actual port 7834

### Task 5.3: Wire handlers/streaming.py or Delete

**File:** `handlers/streaming.py`

Either add it to `register_all_routers` in `handlers/__init__.py` or delete it if unused.

---

## EXECUTION RULES

1. **Work in priority order** — Phase 1 first, then Phase 2, etc.
2. **Test after each task** — run smoke tests from CLAUDE.md Section 12
3. **Do not break existing functionality** — if a change risks breaking something, isolate it behind a try/except
4. **Keep changes minimal** — surgical fixes, not rewrites
5. **All imports at top of file** — no inline imports
6. **All LLM calls through llm_client** — never call litellm directly
7. **All memory writes through MemoryManager** — never write to stores directly
8. **parse_mode="HTML"** — never use bare `parse_mode="Markdown"`
9. **asyncio only** — no threading, no time.sleep()
10. **Commit after each phase** — with clear commit message describing what was fixed

---

## VALIDATION CHECKLIST

After ALL phases are complete, every one of these must pass:

### Smoke Tests
```bash
python -c "from core.soul_engine import build_soul_context; print(build_soul_context()[:100])"
python -c "from core.intent_router import classify_intent_fast; print(classify_intent_fast('write me some code'))"
python -c "from core.system_prompt_builder import build_full_system_prompt; print(build_full_system_prompt('test')[:200])"
python -c "from core.debate_engine import build_debate_instruction; print('debate ok')"
python -c "from core.character.disagreement_protocol import get_disagreement_prompt; print('disagree ok')"
```

### Live Bot Tests
- `/start` → greets with Legion's voice (direct, not sycophantic)
- `/run hello` → responds as Legion, not generic AI
- `/run I think Python is perfect for everything` → pushes back with arguments
- `/debate AI will take all jobs` → structured debate with opinions
- `/soul` → returns SOUL.md contents
- `/screen` → returns screenshot
- `/cmd echo hello` → returns "hello"
- Plain text "what's the weather like?" → intelligent response (research if possible)
- Plain text "remember that I love ramen" → acknowledges AND stores the fact
- Plain text "what do I love?" → recalls stored facts

### Character Tests
- Response never starts with "Certainly!", "Great!", "Of course!", "Sure!", "Absolutely!"
- Response matches input language (Indonesian → Indonesian, English → English)
- Response is direct and technically precise
- Response has opinions when appropriate
- Response length matches question complexity

---

## REFERENCE FILES

Read these files before starting any work:
- `CLAUDE.md` — Master engineering rules (READ ENTIRELY)
- `DEEP_AUDIT_2026-04-10.md` — Detailed audit results with specific issues
- `SOUL.md` — Legion's identity
- `data/beliefs.json` — Legion's stances and Bashara facts
- `llm_client.py` — THE critical file, all LLM calls flow through here
- `main.py` — Entry point and startup sequence
- `handlers/ai.py` — The NL message catch-all
- `handlers/message_handler.py` — Plain message routing
- `core/system_prompt_builder.py` — System prompt assembly
- `core/soul_engine.py` — Soul context builder
- `core/character/disagreement_protocol.py` — Disagreement rules
- `agents.py` — Agent definitions, PERSONALITY_WRAPPER, TASK_KEYWORDS
