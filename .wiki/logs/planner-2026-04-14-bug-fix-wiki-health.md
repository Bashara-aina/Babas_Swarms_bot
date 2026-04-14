---
title: Planner 2026 04 14 Bug Fix Wiki Health
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
summary: 'Type: BUG_FIX + SYSTEMIC_WIKI_FIX'
wikilinks: []
confidence: medium
source: research
---
## Plan: 40-Bug Audit Fixes + Wiki Health Crisis
Date: 2026-04-14
Type: BUG_FIX + SYSTEMIC_WIKI_FIX
Context gathered:
- 6 code bugs remaining from audit (BUG #6, #7, #8, #15, #17, #18, #19)
- Wiki health crisis: 214 missing frontmatter, 39 YAML failures, 38 broken wikilinks, 1980 orphans
- batch_fix_wikilinks.py script already exists but may not handle all cases
- session_synthesizer.py uses sync asyncio.run() for litellm calls (should be async)
- voice.py uses direct openai SDK instead of llm_client
- tiers.py uses sync sqlite3.connect() on class init
- pending_candidates.jsonl is 0 bytes empty

Risk assessment:
- Orphan count (1980) is likely structural (harvested INDEX pages, knowledge subdirs) - may not be "fixable"
- Frontmatter fixes require careful regex to not corrupt articles
- YAML validation needs careful parsing to not break valid articles
- Voice.py fix must maintain Groq fallback logic

Approach:
1. Batch-write 4 wiki repair scripts (frontmatter, YAML, wikilinks, orphan report)
2. Fix 5 code bugs in parallel where independent
3. Run all scripts in order: frontmatter → YAML → wikilinks
4. Final: verify all with targeted grep/bash commands
