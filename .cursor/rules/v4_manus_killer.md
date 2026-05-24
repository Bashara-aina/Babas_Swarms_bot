# LEGION MANUS-KILLER UPGRADE — CURSOR MASTER PROMPT v4
# Mission: Make Legion structurally superior to Manus AI on every dimension
# Repos: OpenManus-OWL + OpenHands + CAMEL + browser-use + MetaGPT
# Project: Bashara-aina/Babas_Swarms_bot
# Engineer: Bashara | Ubuntu Linux, RTX 3060 12GB, 64GB RAM, Tokyo JST
# Stack: Python 3.13, aiogram 3.x, LiteLLM, Supabase, Ollama, Docker, n8n, Swarms

---

## CURSOR PRIME DIRECTIVE

You are upgrading Legion from "smart Telegram bot" to "better than Manus AI."
Manus's core weakness is: single-agent, linear execution, no memory, closed source.
Legion's core advantage must be: parallel multi-agent, persistent memory, self-hosted, Telegram-native.

Every architectural decision must be made with this in mind.
When you write code, ask: "Would Manus do this in 2 hours linearly? 
Can Legion do this in 15 minutes in parallel?" — if yes, you're on the right track.

BEFORE TOUCHING ANY FILE:
1. Run: find . -name "*.py" | head -40 to see what exists
2. Read core/system_prompt_builder.py fully
3. Read main.py fully
4. Read agents.py or agents/ directory fully
5. Read llm_client.py fully
6. ONLY THEN start writing

---

## MANUS WEAKNESS → LEGION STRENGTH MAPPING

| Manus Weakness              | Legion Fix                        | Repo                    |
|-----------------------------|-----------------------------------|-------------------------|
| Single-agent linear loop    | Parallel multi-agent swarm        | OpenManus-OWL + CAMEL   |
| No persistent memory        | mem0 + LLM Wiki + Screenpipe      | Already planned         |
| No proactive behavior       | n8n + Screenpipe monitor          | Already planned         |
| Closed source, locked model | LiteLLM routing any model         | Already your stack      |
| Gets stuck on paywalls      | browser-use vision-capable        | browser-use             |
| No private repo access      | OpenHands + your GitHub token     | OpenHands               |
| Expensive credits           | Self-hosted RTX 3060 + Ollama     | Already your stack      |
| No personality / memory     | masterprompt.md + memory stack    | Already planned         |
| No messaging-native UX      | Telegram + WhatsApp natively      | Already your stack      |
| Freezes on complex tasks    | Task queue + parallel swarm       | CAMEL + n8n             |

---

## ARCHITECTURE: HOW LEGION BEATS MANUS

```
When Bashara sends a message:

[MESSAGE RECEIVED]
       │
       ▼
[INTENT CLASSIFIER] ← minimax-coding-plan/MiniMax-Text-01 (fast classification)
       │
       ├── Simple chat → Legion responds directly (no agent spawning)
       ├── Research task → ResearchSwarm (parallel agents)
       ├── Code task → OpenHands agent
       ├── Browser task → browser-use agent
       ├── Business analysis → MetaGPT role-team
       ├── Computer control → Agent-S
       └── Complex multi-step → OWL orchestrator (parallel execution)

[TASK ROUTER] assigns to correct agent/swarm
       │
       ▼
[PARALLEL EXECUTION] ← THIS is what beats Manus
  Agent A: research    ──┐
  Agent B: browser     ──┤──► [SYNTHESIZER] → Legion's final response
  Agent C: code        ──┘
       │
       ▼
[MEMORY WRITE-BACK]
  mem0.add() + wiki.ingest() + n8n.log()
```

---

## REPO INTEGRATION (reference implementations)

The original v4 spec included full Python stubs for:

- **OpenManus-OWL** → `agents/owl_orchestrator.py` (CAMEL-AI); **Legion today:** `agents/owl_agent.py` + parallel path in `core/task_router.py`.
- **OpenHands** → `agents/code_agent.py` (HTTP client); **Legion today:** `agents/code_agent.py` is sandbox `run_code_agent`; add OpenHands REST when Docker service is up.
- **CAMEL** → `agents/camel_swarm.py`; **Legion today:** parallel `asyncio.gather` + `llm_client.chat` in `core/task_router.py` (no hard dependency on `camel-ai`).
- **browser-use** → `tools/browser_tool.py`; **Legion today:** Playwright `fetch_page_text` in `tools/browser_tool.py` — optional `browser-use` layer later.
- **MetaGPT** → `agents/meta_agent.py`; **Legion today:** multi-role document path in `core/task_router.py` via parallel specialist chats.

**Live router:** `core/task_router.py` — classify → route → parallel where applicable. Enable with `LEGION_TASK_ROUTER_ENABLED=1`.

---

## WIRE INTO main.py / handlers (summary)

- Do **not** replace the entire aiogram stack in one step.
- Optional early hook in `handlers/message_handler.py` runs `TaskRouter.route()`; if it returns `None`, existing `AutonomousRouter` + chat paths run unchanged.

---

## IMPLEMENTATION ORDER

```
DAY 1 — Router foundation
  1. Read main.py, agents.py, llm_client.py fully
  2. Create core/task_router.py
  3. Wire into message handler (feature flag)
  4. Test: "fix this bug" → code path | "hi" → None (fallback chat)

DAY 2 — Browser (highest ROI)
  ...

DAY 3 — Code Agent (OpenHands)
  ...

DAY 4 — OWL Parallel Orchestrator
  ...

DAY 5 — MetaGPT + CAMEL
  ...

DAY 6 — THE MANUS TEST (end-to-end)
  ...
```

---

## THE ONE-LINE PITCH

> Manus: one agent, one task, one LLM, your data on their servers, $X/month.
> Legion: parallel swarm, persistent memory, any model, your server, your RTX 3060, free.

---

_Repository note: Full original code blocks from the Cursor master message are archived in chat history; implement against actual `llm_client.chat`, `get_fallback_chain`, and existing `tools/` modules._
