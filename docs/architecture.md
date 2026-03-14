# Legion v4 — Architecture

## Component Flow

```
Telegram User
     │
     ▼
 main.py  (entry point, 230 lines)
     │  initialises bot/dp, calls register_all_routers()
     ▼
 handlers/  (aiogram Router per domain)
 ├── computer.py   /do /screen /click /type /key /cmd /install /upgrade
 ├── system.py     /start /stats /keys /models /git /maintenance /gpu
 ├── ai.py         /run /think /agent /swarm /loop* + NL catch-all
 ├── research.py   /scrape /research /paper /ask_paper
 ├── brain.py      /remember /recall /memories /briefing
 ├── sessions.py   /save /resume /sessions /audit
 ├── tasks.py      /monitor /schedule /tasks /cancel
 ├── dev.py        /scaffold /build /vuln_scan /review
 ├── pm.py         /task_from /tasks_due /post /email
 ├── enterprise.py /budget /routing_stats /security_stats /audit_summary
 └── shared.py     auth, send_chunked, _keep_typing, _run_agent_loop
     │
     ▼
 llm_client.py
 ├── chat()         single-turn Q&A, cloud-first fallback chain
 ├── agent_loop()   multi-turn agentic loop with tool use (300s timeout)
 ├── analyze_screenshot()  vision: Ollama → Groq fallback
 └── chunk_output() Telegram-safe message splitting
     │
     ├──► router.py → agents.py
     │    ├── AGENT_MODELS     model per agent key
     │    ├── FALLBACK_CHAIN   provider priority order
     │    ├── detect_agent()   keyword-based routing
     │    └── get_fallback_chain()
     │
     └──► computer_agent.py
          ├── TOOL_DEFINITIONS  JSON schema for LLM tool calling
          ├── execute_tool()    async dispatcher
          ├── run_shell()       async subprocess
          ├── take_screenshot() scrot / Pillow
          ├── mouse_click/type/key_press
          └── open_app/open_url/read_file/write_file...

Enterprise Layer (swarms_bot/)
├── ChiefOfStaff     validate → classify → budget check → route → execute → track
├── CostAwareRouter  complexity classification, cascade pattern
├── BudgetManager    per-user daily/monthly spend limits
├── SecurityGuard    prompt injection, PII redaction, credential blocking
├── AuditLogger      SQLite-backed compliance log
├── CostMetricsCollector  token + cost dashboard
└── SessionManager   save/resume sessions with SQLite persistence

Tools Layer (tools/)
├── web_browser.py   Playwright scraping + deep research
├── persistence.py   cache_get/set, instinct context
├── skill_loader.py  per-agent skill injection
├── orchestrator.py  decompose_task, execute_parallel, synthesize
└── ...
```

## LLM Provider Priority

| Priority | Provider | Models | Strength |
|---|---|---|---|
| 1 | ZAI / GLM-4 | glm-4 | math, debug |
| 2 | Groq | llama-3.3-70b, llama-4-scout | speed, function calling |
| 3 | Cerebras | qwen-3-235b-a22b | throughput 1500 tok/s |
| 4 | Gemini | gemini-2.0-flash | 1M context |
| 5 | OpenRouter | free tier models | fallback |
| Local | Ollama | gemma3:12b | vision only (private) |

## Key Design Decisions

- **Single source of truth**: `agents.py` owns all model config; `router.py` only re-exports
- **Cloud-only for text**: Ollama is only used for vision tasks to keep latency low
- **Fail-open startup**: every enterprise module wrapped in `try/except` so partial failures never crash the bot
- **Context compaction**: messages >12 turns are summarized into a single system message to reduce token cost
- **300s hard cap**: `asyncio.wait_for()` prevents runaway agent loops from blocking the bot
