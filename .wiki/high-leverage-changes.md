---
title: High Leverage Changes
type: concept
status: legacy
tags:
- /
- home
- newadmin
- swarm-bot
- high-leverage-changes.md
created: '2026-04-14'
updated: '2026-04-14'
summary: Top 5 architectural changes ranked by impact per hour of development time.
wikilinks: []
confidence: medium
source: research
---

# High-Leverage Changes

## ONE-LINE SUMMARY
Top 5 architectural changes ranked by impact per hour of development time.

## FACTS
- LEGION_MASTER.md defines 63% complete, 4 phases of upgrades remaining
- Highest ROI change: context optimizer for quick questions (30-50% token reduction = cost savings + speed)
- Second highest ROI: proactive consolidation (3 engines → 1 unified) = debuggability + reliability
- Third: MCP backbone = connects Legion to external services without custom integrations
- Fourth: job queue for long tasks = better UX for thesis/coding tasks without blocking
- Fifth: capability audit automation = catches regressions before production

## LEGION BEHAVIOR RULES
1. Priority 1 — CONTEXT OPTIMIZER: Per-task-type context injection
   - Estimated dev time: 2-3 hours
   - Impact: 30-50% token reduction = ~$0.50/day savings on $2/day budget
   - Impact: 20-30% faster response on simple queries
   - File: core/system_prompt_builder.py + core/unified_prompt_context.py

2. Priority 2 — PROACTIVE CONSOLIDATION: Merge 3 engines into 1
   - Estimated dev time: 3-4 hours
   - Impact: single point of debug, consistent DND handling, no duplicate fires
   - Files: core/proactive/scheduler.py + core/proactive/curiosity_engine.py + core/proactive/proactive_initiator.py + core/proactive_engine.py

3. Priority 3 — MCP BACKBONE: Unified MCP client + 3 initial servers
   - Estimated dev time: 4-5 hours
   - Impact: Brave Search (web), GitHub (PR status), Obsidian (notes) — covers 60% of missing tools
   - Files: core/mcp_client.py (if exists) + skills/* registry

4. Priority 4 — JOB QUEUE: Async job queue for tasks >30s
   - Estimated dev time: 4-5 hours
   - Impact: thesis chapter tracking, POPW training monitoring, booking escalation — non-blocking
   - Files: core/job_queue.py (new) + llm_client.py update

5. Priority 5 — CAPABILITY AUDIT: Automated monthly regression suite
   - Estimated dev time: 2-3 hours
   - Impact: catches capability regressions before production, documents what works
   - Files: tests/test_capabilities.py (new) + tools/capability_nightly.py update

## EXAMPLES
Before: "pusing" → SOUL + personality + profile + 6 turns + all beliefs = ~3500 tokens
After: SOUL + emotion_modifier + last 2 turns = ~1500 tokens — same quality, 57% fewer tokens

Before: 3 separate proactive engines with different DND logic → potential for 3AM fires from engine 2
After: 1 unified orchestrator with shared DND guard → consistent quiet hours

Before: "cekl SEO rumahlabuh" → no skill registered → falls to general agent → poor response
After: MCP Brave Search → web_audit skill fires → PageSpeed score returned in <5 seconds

## ANTI-PATTERNS
1. Doing P2-1/P2-2 refactoring (main.py swarm migration) before context optimizer — refactoring yields no new capability, context optimizer yields immediate cost/speed improvement
2. Adding more proactive triggers before consolidating engines — adds complexity without fixing fragmentation
3. Building custom integrations (e.g., Supabase client) before MCP backbone — MCP provides standard interface, custom code becomes legacy

## DEBATE RECORD
Advocate: 8 | Skeptic: 6 | Judge: WRITE 8
Judge note: Ranked by impact-per-hour — enables optimal task selection for next sprint.
