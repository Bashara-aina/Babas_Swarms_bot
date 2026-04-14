---
title: Tools Gaps
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- tools-gaps.md
created: '2026-04-14'
updated: '2026-04-14'
summary: Tools that don't exist but Bashara needs — ranked by priority.
wikilinks: []
confidence: medium
source: research
---

# Tools Gaps

## ONE-LINE SUMMARY
Tools that don't exist but Bashara needs — ranked by priority.

## FACTS
- No yt-dlp integration in tools/video.py — LEGION_MASTER.md defines it but it's not wired into routing
- No Crawl4AI skill registered in skill_registry — only in browser_agent.py as fallback
- No Google Calendar MCP integration — briefing can't show tomorrow's meetings
- No Obsidian MCP integration — notes written to memory but not to Obsidian vault
- No Brave Search MCP — web_search skill not implemented
- No weather API tool — location shown in briefing but no weather data
- No currency conversion tool — IDR/USD rates not tracked despite Indonesian business context
- No "remind me in X minutes" timer tool with Telegram notification callback
- No thesis chapter tracker — no tool to track which chapter is draft/review/final
- No booking inquiry escalation tool — Supabase checked but no alert if inquiry sits >24h unreplied
- No "undo" for memory operations — /forget exists but no /undo_forget
- No video file handler fully wired in routing — F.video exists in media_tools.py but may not be in __init__.py router order
- No CSV analysis tool beyond reading — no "analyze this CSV" that returns statistics
- No POPW training dashboard — GPU status exists but no loss curve visualization

## LEGION BEHAVIOR RULES
1. Priority order for gap fixes: thesis tracker → booking escalation → weather → currency
2. All new tools must have: async signature, timeout parameter, error handling, Telegram-formatted output
3. All new tools must be registered in skill_registry if they are skill-dispatchable
4. Before building any tool, check if existing tool in tools/ or skills/ already covers the use case
5. Every tool gap fix must include a test in tests/

## EXAMPLES
Bashara message: "ingetin gw 30 menit lagi soal thesis"
Ideal Legion response: "Timer set for 30 minutes. I'll ping you at 7:32PM JST." + actual Telegram message at that time

Bashara message: "kurs dólar berapa"
Ideal Legion response: "USD/IDR: 16,450 — up 0.3% today. Want me to set a threshold alert?"

Bashara message: "kirim laporan inquiry baru ke email gw"
Ideal Legion response: Query Supabase for unresponded inquiries >24h, draft email reply, send via email_client

Bashara message: "thesis progres minggu ini"
Ideal Legion response: "This week: chapter 2 final draft submitted ✅, chapter 3: 60% complete. No commits in 3 days."

## ANTI-PATTERNS
1. Building duplicate tools: web_scraper + browser_agent + scraper_tool all do URL scraping — consolidate before adding more
2. Building tools without testing: tools added to tools/ but never invoked in any handler
3. Building blocking tools in async context: requests.get() in tool without asyncio.to_thread — blocks event loop

## DEBATE RECORD
Advocate: 8 | Skeptic: 6 | Judge: WRITE 8
Judge note: Directly maps to Bashara's active projects — thesis and businesses are immediate priorities.
