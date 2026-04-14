---
title: Bot Commands Agent Architecture
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- self-knowledge
created: '2026-04-14'
updated: '2026-04-14'
summary: '- **Type**: Python Telegram bot with multi-agent orchestration'
wikilinks: []
confidence: medium
source: research
---

# Legion/SwarmBot Bot Commands and Agent Architecture

## Overview
- **Type**: Python Telegram bot with multi-agent orchestration
- **Framework**: aiogram 3.4+ (async Telegram bot), litellm 1.57+ (LLM routing)
- **Python**: 3.11+, asyncio-first, no threading/blocking I/O
- **Key Files**: main.py (bot startup), agents.py (agent registry), llm_client.py (LLM calls)

## Router Order (Critical)
 Routers are registered in this specific order in `handlers/__init__.py`:

1. `computer.router` — `/do /screen /click /type /key /cmd /install`
2. `communications.router` — `/emails /inbox /calendar`
3. `runbook_handler.router` — `/runbook`
4. `business_handler.router` — `/db /site_health /bookings /db_schema`
5. `github_intel_handler.router` — `/github_intel /eval_repo /upgrade_from`
6. `whatsapp_handler.router` — `/wa /wa_reply /wa_qr /wa_status`
7. `system.router` — `/start /stats /keys /models /git /maintenance /gpu`
8. `research.router` — `/scrape /research /paper /ask_paper`
9. `memory_commands.router` — `/memory /remember /recall /emotion /opinions /forget /profile /teach`
10. `wiki_handler.router` — `/wiki /wiki_ingest /wiki_lint`
11. `brain.router` — `/memories /briefing /learn /instincts`
12. `session_handler.router` — `/task /task_done /task_sessions /semantic_set /semantic_get`
13. `sessions.router` — `/save /resume /sessions /audit`
14. `tasks.router` — `/monitor /schedule /tasks /cancel`
15. `dev.router` — `/scaffold /build /vuln_scan /review`
16. `pm.router` — `/task_from /tasks_due /post /email`
17. `enterprise.router` — `/budget /routing_stats /security_stats /audit_summary`
18. `artifact.router` — `/preview`
19. `upgrade.router` — `/upgrade /upgrade_status /upgrade_history`
20. `debate_handlers.router` — `/debate /opinion`
21. `overnight_handler.router` — `/overnight /dashboard /overnight_*`
22. `voice.router` — F.voice + F.audio + `/voice_on /voice_off /voice_status /voice_toggle`
23. `inline.router` — inline_query
24. `skills.router` — `/skills /skill /skill_reload`
25. `persona_handler.router` — `/persona /mood /persona_reset /persona_note`
26. `ecc_compat.router` — `/harness_audit /model_route /quality_gate /verify /plan /checkpoint`
27. `e2e.router` — `/e2etest /e2eplan /dbquery /dbhealth /dbtables`
28. `orchestrate.router` — `/orchestrate /orchestrate_cancel`
29. `legion_extras.router` — `/simulate /screenpipe_status /mcp_status /voice_room /websearch /quickscrape`
30. `wiki_router` — `/wiki_audit /wiki_flush /wiki_restore /wiki_scan /wiki_stats`
31. `ai.router` — `/run /think /agent /swarm + NL catch-all (LAST)

**Key Rule**: `ai.router` MUST be last (NL catch-all via F.text)

## Agent System
- **Planner** (@planner): Decomposes tasks, never edits files directly
- **Worker** (@worker): Executes code changes, full file + bash access
- **Reviewer** (@reviewer): Reviews all changes before commit, read-only
- **WikiBot** (@wikibot): Writes session summaries and decisions to .wiki/

## 76+ Agents across 9 Departments
From `config/departments.yaml`:
- `engineering/` — Code generation, debugging, refactoring
- `design/` — UI/UX, creative assets  
- `research/` — Web scraping, paper analysis, fact checking
- `marketing/` — Content generation, social media
- `operations/` — System maintenance, deployment
- `product/` — Feature planning, roadmapping
- `legal_compliance/` — Policy review, compliance checking
- `creative/` — Writing, brainstorming
- `vision_multimodal/` — Image analysis, OCR
- `nexus/` — Strategy and coordination hub
- `strategy_nexus/` — Long-term planning

## Agent Model Strategy
From `agents/__init__.py`:
- **MiniMax M2.7** is the ONLY paid API — use for everything
- **Local Ollama gemma4:e4b** (9.6GB VRAM) ONLY for vision (screen reading)
- **Free cloud fallbacks**: Groq, Gemini, OpenRouter free tier when MiniMax fails
- **RTX 3060**: NO llama3.3:70b, NO qwen3.5:35b — too heavy

## Debate Personas
Six personas for SwarmDebateOrchestrator:
- `strategist`: ⚔️ 10-year timeframes, leverage and compounding advantages
- `devil_advocate`: 🔥 Attack every assumption, find fatal flaws
- `researcher`: 📚 Cite evidence, needs source/precedent/data
- `pragmatist`: 🔧 What breaks first? Who builds? How long?
- `visionary`: 🚀 3 steps ahead, see connections others miss
- `critic`: ✂️ Find redundancy, weak framing, missing context

## Primary Model Registry
```python
AGENT_MODELS = {
    "vision": "ollama_chat/gemma4:e4b",
    "coding": "minimax/MiniMax-M2.7",
    "debug": "minimax/MiniMax-M2.7",
    "math": "minimax/MiniMax-M2.7",
    "architect": "minimax/MiniMax-M2.7",
    "analyst": "minimax/MiniMax-M2.7",
    "computer": "minimax/MiniMax-M2.7",
    "general": "minimax/MiniMax-M2.7",
    "researcher": "minimax/MiniMax-M2.7",
    # ... 20+ more agents
}
```

---
*Extracted: 2026-04-11 by @worker*
