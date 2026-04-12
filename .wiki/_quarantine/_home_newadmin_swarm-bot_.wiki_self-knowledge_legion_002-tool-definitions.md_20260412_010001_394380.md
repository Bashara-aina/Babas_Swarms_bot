---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/self-knowledge/legion/002-tool-definitions.md",
  "reason": "daily_fast_scan: score=0.150 < 0.3",
  "score": 0.15000000000000002,
  "quarantined_at": "2026-04-12T01:00:01.394416"
}
---

---
title: "Legion Tool Definitions"
source_type: CODE_EXTRACTION
extracted_from: swarm-bot
date: 2026-04-11
tags: [legion, tools, functions, capabilities]
---

# Legion/SwarmBot Tool Definitions

## Overview
72 Python tool files in `/home/newadmin/swarm-bot/tools/` with 1050+ function definitions.

## Key Tool Categories

### Business Operations
- `supabase_query()` — Query Supabase database
- `get_business_summary()` — Get business metrics
- `check_vercel_deployments()` — Check deployment status

### GitHub Intelligence
- `fetch_trending()` — Fetch GitHub trending repos
- `fetch_readme()` — Fetch repository README
- `evaluate_relevance()` — Evaluate repo relevance
- `generate_intel_report()` — Generate daily scan report
- `_discover_skill()` — Auto-discover skills from repos
- `_draft_skill_file()` — Create skill file from evaluation
- `_sandbox_smoke_test()` — Run package smoke test

### Browser/Computer Control
- `browser_agent()` — Browser automation agent
- `take_screenshot()` — Capture screen
- `execute_task()` — Execute computer task

### Voice & Audio
- `transcribe_voice()` — Whisper transcription
- `synthesize_speech()` — Kokoro TTS synthesis
- `prewarm()` — Prewarm voice engines

### Screenpipe (Activity Monitoring)
- `search()` — Search screen history
- `get_recent_activity()` — Get recent activity
- `get_app_context()` — Get app-specific context

### Research & RAG
- `scrape_url()` — Web scraping
- `web_search()` — Tavily search
- `rag_query()` — RAG flow query
- `deep_research()` — Deep research mode
- `arxiv()` — ArXiv paper lookup

### Memory & Sessions
- `set_current_task()` — Set current task context
- `complete_current_task()` — Archive task to episodic memory
- `get_recent_episodes()` — Get recent memory episodes
- `store_semantic_fact()` — Store semantic fact
- `get_semantic_fact()` — Retrieve semantic fact

### Runbook Engine
- `execute_runbook()` — Execute multi-step runbook
- `list_runbook_summaries()` — List available runbooks
- `match_runbook_from_text()` — Match runbook to message

### Location & Weather
- `search_nearby_places()` — Google Places search
- `get_weather()` — OpenWeather API

### Briefing & Proactive
- `generate_briefing()` — Generate daily briefing
- `schedule_daily_briefing()` — Schedule daily briefing
- `start_proactive_initiator()` — Start proactive check-ins

### Crew/Rumahlabuh
- `run_crew_task()` — Run multi-agent crew task
- `check_website_uptime()` — Check rumahlabuh.com uptime
- `draft_guest_reply()` — AI draft guest message reply
- `check_booking_alerts()` — Check booking system alerts

### Model Context Protocol (MCP)
- `MCPClient` class — MCP client implementation

### Misc Tools
- `agentops_client` — AgentOps monitoring
- `capability_benchmark` — Benchmark capabilities
- `citation` — Citation lookup
- `codebase_reader` — Read codebase files
- `code_reviewer` — Review code
- `deep_think` — Deep thinking mode
- `simulation_tool` — MiroFish simulation

## Tool Environment Variables
Key env vars used by tools:
- `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` — Database
- `SCREENPIPE_URL`, `SCREENPIPE_ENABLED` — Activity monitoring
- `RAGFLOW_API_BASE`, `RAGFLOW_API_KEY` — RAG backend
- `CHROMADB_HOST`, `CHROMADB_PORT` — ChromaDB
- `GOOGLE_PLACES_API_KEY` — Places API
- `OPENWEATHER_API_KEY` — Weather API
- `SERPAPI_KEY` — Search API
- `FIRECRAWL_API_KEY` — Web scraping
- `TAVILY_API_KEY` — Research search
- `WHISPER_MODEL`, `WHISPER_DEVICE` — Transcription
- `KOKORO_VOICE`, `KOKORO_SPEED` — Speech synthesis

---
*Extracted: 2026-04-11 by @worker*
