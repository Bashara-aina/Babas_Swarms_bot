---
title: Mcp Native Status
type: concept
status: active
tags: [/]
created: 2026-05-03
updated: 2026-05-03
---

# MCP Integration Status
Generated: 2026-05-03 12:42 JST

## All 12 MCPs — Native Wiring

| MCP | Type | Role | Auto-called when |
|-----|------|------|-----------------|
| gitnexus | local/npx | Code intelligence | Before every code edit |
| git | local/npx | Version control | git ops, diff, log |
| filesystem | local/npx | File I/O | Direct file read/write |
| obsidian | local/npx | Wiki/knowledge | Architecture changes |
| hermes | local/python | Memory + messaging | Any memory op, start of session |
| sequential-thinking | local/npx | Task planning | Any task > 2 steps |
| browser-use | local/python | Autonomous browsing | Multi-step web, SPAs, forms |
| crawl4ai | local/python | Fast web scraping | Bulk extraction, static sites |
| exa | remote | Smart search | Quick facts, current data |
| firecrawl | local/npx | Deep scrape | Full page content |
| ruflo | local/python | Task orchestration | Background jobs, shell pipelines |
| latex | local/python | PDF generation | Document/paper output |
| symphony | local/python | Multi-agent coord | 3+ agent workflows |

## Model Policy
- ALL LLM calls: MiniMax M2.7 via http://localhost:4000
- browser-use: locked to minimax/MiniMax-M2.7
- hermes: uses MiniMax-M2.7 via LiteLLM proxy
- ruflo: orchestration only, no LLM calls

## Health Check
Run: bash /tmp/mcp_health_check.sh
All ✅ = system is native and working.

## Session Warmup
Run: bash /home/newadmin/swarm-bot/scripts/mcp_session_warmup.sh
Loads: hermes memory → /tmp/legion_hermes_skills.txt
       gitnexus context → /tmp/legion_temporal_context.txt

## Verified Working (2026-05-03)
- hermes ✅
- ruflo ✅  
- symphony ✅
- latex ✅
- browser-use ✅
- crawl4ai ✅
- gitnexus ✅ (outputs JSON on tools/list, not initialize)
- filesystem ✅ (verified manually)
- obsidian ✅ (verified manually)
- sequential-thinking ✅ (verified via node)
