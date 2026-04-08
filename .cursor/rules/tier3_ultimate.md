---
description: Legion Ultimate Upgrade v3 — 10-repo architecture, tiers 1–3, Jarvis acceptance test
alwaysApply: false
---

# LEGION ULTIMATE UPGRADE — CURSOR MASTER PROMPT v3

**Repos:** Screenpipe + Pipecat + LiveKit + Agent-S + MCP Servers + OpenClaw + AgentMail + MiroFish + LLM Wiki  
**Project:** Bashara-aina/Babas_Swarms_bot  
**Engineer:** Bashara | **Machine:** Ubuntu Linux, RTX 3060 12GB, 64GB RAM, JST Tokyo  
**Stack:** Python 3.13, aiogram 3.x, LiteLLM, Supabase, Ollama, Docker, n8n

---

## CURSOR RULES — READ BEFORE DOING ANYTHING

1. READ every existing file before modifying it — never assume what's inside  
2. READ `core/system_prompt_builder.py`, `main.py`, `llm_client.py`, `agents.py` FIRST  
3. NEVER break existing Telegram bot functionality — new features are additive only  
4. ALWAYS use async/await — this is an aiogram bot, all I/O must be non-blocking  
5. ALWAYS add new pip packages to `requirements.txt`  
6. ALWAYS add new Docker services to `docker-compose.yml`  
7. ALWAYS document new env vars in `.env.example`  
8. NEVER hardcode API keys — use `os.getenv()` only  
9. USE Groq (`llama-3.1-8b-instant`) for fast/cheap mechanical ops; Claude/GPT for real Legion responses  
10. IMPLEMENT one tier at a time — do not skip ahead  
11. WRITE tests in `tests/` for every new module  
12. LOG everything with Python `logging`, never `print()`  
13. KEEP the existing Legion personality and `masterprompt.md` intact — ADD capabilities, do not replace the soul  

**Integration note (this repo):** Prefer existing patterns — e.g. wiki ops use `llm_client.wiki_raw_completion`, not a fictional `llm.complete(prompt=...)`. Telegram user id must come from `ALLOWED_USER_ID` / env, not hardcoded `BASHARA_TELEGRAM_ID` unless aliased in `.env.example`.

---

## FINAL TARGET ARCHITECTURE

When complete, Legion will have these layers running simultaneously:

```
[BASHARA]
    │
    ├── Telegram (text) ──────────────────────────────┐
    ├── Voice call (Pipecat + LiveKit) ────────────────┤
    └── WhatsApp (MCP) ────────────────────────────────┤
                                                       ▼
                                              [LEGION CORE]
                                         aiogram + LiteLLM router
                                                       │
              ┌────────────────────────────────────────┼──────────────────────────────────────┐
              ▼                                        ▼                                      ▼
    [MEMORY STACK]                           [TOOL STACK]                          [AGENT STACK]
    mem0 (episodic)                          Tavily (web search)                   ResearchAgent (DeerFlow)
    Screenpipe (screen/audio)                browser-use (browser)                 CodeAgent (OpenHands)
    LLM Wiki (synthesized)                     Agent-S (GUI control)                 SimulationAgent (MiroFish)
    cognee (knowledge graph)                   MCP servers (email/cal/gh)            VoiceAgent (Pipecat)
                                             Firecrawl (scraping)
                                             AgentMail (email identity)
                                                       │
                                              [PROACTIVE LOOP]
                                         n8n scheduler → Screenpipe context
                                         → Legion initiates Telegram message
```

---

## FOLDER STRUCTURE TO CREATE

```
core/
  memory_manager.py          ← mem0 + screenpipe + wiki query unified interface
  wiki_manager.py            ← Karpathy LLM Wiki
  knowledge_manager.py       ← cognee knowledge graph
  skill_registry.py          ← dynamic skill auto-loading
  emotion_tracker.py         ← emotional state signals
  response_filter.py         ← post-generation self-critique
  system_prompt_builder.py   ← MODIFY: inject all memory layers + context
  mcp_client.py              ← MCP protocol client — connects to all MCP servers

tools/
  search_tool.py             ← Tavily web search
  browser_tool.py            ← browser-use
  agent_s_tool.py            ← Agent-S GUI computer control
  scraper_tool.py            ← Firecrawl
  rag_tool.py                ← RAGFlow
  interpreter_tool.py        ← Open Interpreter
  simulation_tool.py         ← MiroFish scenario simulation
  screenpipe_tool.py         ← Screenpipe query interface

agents/
  research_agent.py          ← DeerFlow research pipeline
  code_agent.py              ← OpenHands coding
  voice_agent.py             ← Pipecat + LiveKit voice pipeline
  simulation_agent.py        ← MiroFish multi-agent simulation

bridges/
  n8n_bridge.py              ← n8n workflow triggers
  whatsapp_bridge.py         ← WhatsApp MCP bridge
  whatsapp_service/          ← Node.js service
  screenpipe_bridge.py       ← Screenpipe local API client
  livekit_bridge.py          ← LiveKit room management

mcp_servers/
  gmail_mcp/                 ← Google Workspace MCP (email + calendar)
  github_mcp/                ← GitHub MCP server
  whatsapp_mcp/              ← WhatsApp MCP server
  agentmail_mcp/             ← AgentMail MCP server

scripts/
  self_update_watcher.py     ← GitHub trending + awesome-ai-agents-2026 watcher
  wiki_lint_scheduler.py     ← Weekly wiki health check
  screenpipe_digest.py       ← Daily screen activity digest for Legion

config/
  mcp_config.json            ← All MCP server configs in one place
  n8n_workflows/             ← n8n workflow JSONs
  memory_config.py           ← mem0 + cognee config
  voice_config.py            ← Pipecat + LiveKit config

wiki/                        ← Legion's knowledge wiki
```

---

## TIER 1 — IMPLEMENT FIRST

### REPO 1: screenpipe/screenpipe — TOTAL RECALL MEMORY

**What it is:** Continuous screen + audio capture, OCR, transcription, local SQLite + AI search. Optional “always-on context” layer.

**Installation (reference):**

```bash
curl -fsSL https://raw.githubusercontent.com/screenpipe/screenpipe/main/install.sh | sh
screenpipe &
pip install screenpipe
```

**Deliverables:**

- `tools/screenpipe_tool.py` — `ScreenpipeTool` with `search()`, `get_recent_activity()`, `get_app_context()` calling local HTTP API (default `SCREENPIPE_URL`, e.g. `http://localhost:3030`). Fail silent with `logger.warning` if unavailable.
- `bridges/screenpipe_bridge.py` — optional proactive loop; use **`wiki_raw_completion` or existing LLM helpers**, not `llm.complete(prompt=...)`. Chat IDs from **`os.getenv("ALLOWED_USER_ID")`** (or project’s multi-id pattern if adopted).
- Wire context into **`llm_client.chat()`** `prompt_sections` or unified memory builder (match how LLM Wiki was integrated — async, non-blocking).
- `main.py` — `asyncio.create_task(...)` for monitor only when `SCREENPIPE_ENABLED` is true.
- `.env.example` — `SCREENPIPE_URL`, `SCREENPIPE_ENABLED`.

**Verify Screenpipe’s real REST paths** against current docs; adjust `/search` params if the API differs.

---

### REPO 2: pipecat-ai/pipecat + livekit/agents — VOICE INTERFACE

**Deliverables:**

- `agents/voice_agent.py` — Pipecat pipeline + LiveKit transport (STT → LLM → TTS). Align imports with installed `pipecat-ai` / `livekit-agents` versions.
- Handler `/voice` — allowed-user check, spawn room + join link, background agent task.
- `docker-compose.yml` — `livekit` service (keys via env).
- `.env.example` — `DEEPGRAM_API_KEY`, `CARTESIA_*`, `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`.

**Soul:** Reuse Legion system prompt / routing; voice mode = shorter, spoken-friendly instructions.

---

### REPO 3: simular-ai/Agent-S — GUI COMPUTER CONTROL

**Deliverables:**

- `tools/agent_s_tool.py` — wrapper with safety gate for destructive keywords; **`run_in_executor`** if the upstream API is sync. Verify real import path (`agent_s` vs package name on PyPI).
- `.env.example` — `AGENT_S_ENGINE`, `AGENT_S_MODEL`.

**Note:** This repo already has `computer_agent.py` / Playwright patterns — extend or bridge rather than duplicating.

---

## TIER 2 — IMPLEMENT SECOND

### REPO 4: modelcontextprotocol/servers — MCP

**Deliverables:**

- `core/mcp_client.py` — stdio MCP client; load server definitions from **`config/mcp_config.json`**; `connect`, `call_tool`, `list_tools`; no broken `stdio_client(...).__aenter__()` one-liners — use proper `async with`.
- `config/mcp_config.json` — server registry + metadata.
- `.env.example` — Google, `GITHUB_TOKEN`, AgentMail, WhatsApp session, `WORKSPACE_DIR`.

---

### REPO 5: agentmail-to/agentmail-mcp — LEGION EMAIL IDENTITY

Wire via MCP. Add convenience method e.g. `setup_legion_inbox()` if supported by the server.

**Append to `masterprompt.md` (new section):**

```markdown
## LEGION EMAIL IDENTITY

You have a dedicated email address: legion@bashara.agentmail.to
You use this for:
- Receiving notifications from services on Bashara's behalf
- Sending draft replies for Bashara's review before sending
- Business communications for rumahlabuh.com
- Never send email without Bashara's explicit confirmation first
- When you draft an email, always show it to Bashara and wait for /confirm or /reject
```

---

### REPO 6: 666ghj/MiroFish — SIMULATION

**Deliverables:**

- `tools/simulation_tool.py` — trigger phrases, `simulate()`, import MiroFish only if `tools/mirofish_src` (or chosen path) exists; **LLM fallback** via `wiki_raw_completion` / `chat` as appropriate.
- `.env.example` — `MIROFISH_MODEL`, `OPENROUTER_API_KEY` if used.

**Fix in implementations:** `SimulationAgent.handle` must `return await self.sim.simulate(...)` (spec snippet was incomplete).

---

### REPO 7: self_update_watcher

**Deliverables:**

- `scripts/self_update_watcher.py` — trending + awesome list; evaluate with cheap model; write `wiki/legion/update_proposals/YYYY-MM-DD.md`; optional GitHub issue via MCP; Telegram summary using **aiogram `Bot`** + `ALLOWED_USER_ID`, not `python-telegram-bot` unless already in deps.

---

## TIER 3 — WIRE TOGETHER

### Unified system prompt / context

The spec proposes a large async `build_system_prompt` with parallel `asyncio.gather`. **In this codebase**, context is assembled in **`llm_client.chat()`** via `prompt_sections` + `SystemPromptBuilder`. When adding layers:

- Keep **&lt; 800ms** budget where possible; use `asyncio.wait_for` for MCP/calendar.
- Add Screenpipe + wiki + mem0 in a consistent order (emotion → time → screen → memories → wiki → tools).

### docker-compose additions (reference)

Add services only when actually run: `livekit`, optional `screenpipe` image, optional `ragflow`, optional `openhands`. Declare named **volumes**. Match host paths and GPU/devices to the deployment machine.

### `.env.example` consolidation

Merge with existing project keys (`ALLOWED_USER_ID`, `TELEGRAM_BOT_TOKEN`, mem0, wiki, etc.). Prefer one canonical name per concept (`ALLOWED_USER_ID` vs `BASHARA_TELEGRAM_ID` — document alias if both appear).

---

## IMPLEMENTATION ORDER — REFERENCE SEQUENCE

**Week 1 — Memory & soul**

- Day 1: mem0 / semantic memory injection (if not done)  
- Day 2: Screenpipe tool + context injection  
- Day 3: LLM Wiki + ingest  
- Day 4: Emotion tracker + response filter  
- Day 5: Test memory + wiki + screen together  

**Week 2 — Eyes & ears**

- Voice (Pipecat + LiveKit)  
- Agent-S (or integration with existing computer agent)  
- Screenpipe proactive monitor  

**Week 3 — Integrations**

- MCP client + Gmail/Calendar  
- AgentMail  
- WhatsApp bridge  
- GitHub MCP  

**Week 4 — Intelligence**

- DeerFlow / research agent  
- MiroFish / simulation tool  
- Self-update watcher + n8n  
- End-to-end Jarvis test  

---

## THE JARVIS TEST (FINAL ACCEPTANCE)

Legion passes when one message can drive:

1. Screenpipe → see error on screen  
2. Code path → fix or propose fix  
3. Research → better library / docs  
4. `WikiManager.ingest()` → update wiki  
5. MCP WhatsApp → read guest message  
6. Draft reply → **confirm with Bashara** before send  
7. Detect affect (“cape banget”) → concise, supportive tone  
8. Preferably **without** requiring slash commands for every step  

---

## RELATED IN-REPO ARTIFACTS

- **LLM Wiki:** `wiki/SCHEMA.md`, `core/wiki_manager.py`, `handlers/wiki_handler.py`, `scripts/wiki_lint_scheduler.py`  
- **Prior master prompts:** store alongside this file under `.cursor/rules/` (e.g. mem0 tier, wiki brain) for stacked context  

---

## APPENDIX — Verbatim templates from v3 draft (adapt before use)

### `tools/screenpipe_tool.py` (template)

```python
"""
Screenpipe integration — gives Legion total recall of Bashara's screen + audio.
Screenpipe runs as local service (default port from SCREENPIPE_URL).
"""
import os
import aiohttp
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

SCREENPIPE_URL = os.getenv("SCREENPIPE_URL", "http://localhost:3030")


class ScreenpipeTool:

    async def search(self, query: str, limit: int = 5,
                     hours_back: int = 168) -> str:
        start_time = (datetime.now() - timedelta(hours=hours_back)).isoformat()
        params = {
            "q": query,
            "limit": limit,
            "start_time": start_time,
            "content_type": "all",
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{SCREENPIPE_URL}/search",
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as resp:
                    if resp.status != 200:
                        return ""
                    data = await resp.json()
            if not data.get("data"):
                return ""
            results = []
            for item in data["data"][:limit]:
                content = item.get("content", {})
                timestamp = item.get("timestamp", "")[:16]
                if item.get("type") == "OCR":
                    text = content.get("text", "")
                    app = content.get("app_name", "unknown app")
                    results.append(f"[{timestamp}] Screen ({app}): {text[:200]}")
                elif item.get("type") == "Audio":
                    text = content.get("transcription", "")
                    results.append(f"[{timestamp}] Audio: {text[:200]}")
            if not results:
                return ""
            return "## SCREENPIPE CONTEXT (what Bashara was doing recently):\n" + "\n".join(results)
        except Exception as e:
            logger.warning("Screenpipe unavailable: %s", e)
            return ""

    async def get_recent_activity(self, hours: int = 2) -> str:
        return await self.search(
            query="recent activity code error terminal",
            limit=10,
            hours_back=hours,
        )

    async def get_app_context(self, app_name: str) -> str:
        return await self.search(query=app_name, limit=5, hours_back=24)
```

_Add `import os` at top of this template; confirm Screenpipe HTTP API paths against current docs._

### `bridges/screenpipe_bridge.py` (template — fix LLM + chat id)

Replace any `llm.complete(prompt=..., model=...)` with **`wiki_raw_completion`** (or project equivalent). Replace **`BASHARA_TELEGRAM_ID`** with **`ALLOWED_USER_ID`** from env / shared handler pattern.

### Voice / Agent-S / MCP / MiroFish / self_update_watcher

The v3 message includes full drafts for `voice_agent.py`, `agent_s_tool.py`, `mcp_client.py`, `simulation_tool.py`, `self_update_watcher.py`, async `build_system_prompt`, `docker-compose` snippets, and a consolidated `.env.example`. Those are long; keep them in your chat export or split into `docs/legion_v3_templates.md` if you need byte-for-byte copies inside the repo.

---

## Repo wiring status (interconnection map)

| Area | Modules | Notes |
|------|---------|--------|
| Parallel prompt | `core/unified_prompt_context.py` → `llm_client.chat` | `LEGION_UNIFIED_CONTEXT_ENABLED=1` (default) |
| Mem0 + wiki + Screenpipe (tools) | `core/legion_memory_facade.py` | `get_memory_facade().contextual_snapshot()` for orchestrators |
| Plain-text simulation | `core/autonomous_router.py` (`strategic_simulation`) → `handlers/message_handler.py` | Routes to `agents/simulation_agent.py` |
| `/research` fast path | `handlers/research.py` | `LEGION_RESEARCH_USE_PIPELINE=1` → `agents/research_agent.py` |
| RAG | `tools/rag_tool.py` | `LEGION_RAG_BACKEND=ragflow` + `RAGFLOW_*` envs |
| Voice | `handlers/legion_extras.py` (`/voice`, `/voice_room`) + `bridges/livekit_bridge.py` | `meet_join_url()`; Pipecat worker separate |
| Agent-S | `tools/agent_s_tool.py` | Package or `AGENT_S_WEBHOOK_URL` |
| Proactive screen | `bridges/screenpipe_bridge.py` | Started from `main.py` when `SCREENPIPE_*` on |
| Weekly proposals file | `scripts/legion_trending_watcher.py` | n8n cron; `LEGION_TRENDING_NOTIFY` |
| Git-behind ping | `scripts/self_update_watcher.py` | Unchanged; `SELF_UPDATE_NOTIFY` |
| `/jarvis` one-shot | `core/jarvis_orchestrator.py` + `handlers/legion_extras.py` | Parallel gather + synthesis; **no sends**; `LEGION_JARVIS_*` |
| Plain-text Jarvis | `core/autonomous_router.py` (`jarvis_orchestrate`) → `handlers/message_handler.py` | Same bundle as `/jarvis`; `LEGION_JARVIS_AUTOROUTE_ENABLED=1` |

---

_End of tier3_ultimate.md — implement incrementally; verify external APIs and this repo’s actual LLM/Telegram patterns before merging._
