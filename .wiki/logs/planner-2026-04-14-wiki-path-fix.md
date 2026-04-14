---
title: Planner 2026 04 14 Wiki Path Fix
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- logs
created: '2026-04-14'
updated: '2026-04-14'
summary: '- Found 3 files in core/ with incorrect `wiki/` (no dot) path instead of
  `.wiki/`:'
wikilinks: []
confidence: medium
source: research
---
## Plan: Fix wiki/ → .wiki/ path references in core/
Date: 2026-04-14
Type: BUG_FIX

Context gathered:
- Found 3 files in core/ with incorrect `wiki/` (no dot) path instead of `.wiki/`:
  - core/wiki_quality_gate.py line 28
  - core/wiki_loader.py line 12
  - core/wiki_scheduler.py line 30
- .opencode/agents/wikibot.md already correctly references `.wiki/` paths

Risk assessment:
- Low risk - simple string path corrections
- Could break imports if wiki path is wrong, but verification will catch

Approach:
- Fix all 3 Path references from `/home/newadmin/swarm-bot/wiki` to `/home/newadmin/swarm-bot/.wiki`
- Verify wikibot.md alignment (already correct)
- Run Python import test to verify no breakage
