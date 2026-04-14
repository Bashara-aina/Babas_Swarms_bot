---
title: Planner Wiki Quarantine Analysis 2026 04 14
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
summary: '- .wiki/ has 2211 articles across concepts, entities, decisions, architecture,
  etc.'
wikilinks: []
confidence: medium
source: research
---
## Plan: Investigate Wiki Quarantine Pattern
Date: 2026-04-14
Type: RESEARCH
Context gathered:
- .wiki/ has 2211 articles across concepts, entities, decisions, architecture, etc.
- _quarantine/ contains 1077 files (9.8MB) - backup copies of wiki pages that failed quality gate
- quarantine_reason: "daily_fast_scan: score=X < 0.3"
- Quality gate system: fast_gate (heuristic) + deep_gate (LLM)
- fast_gate scoring is heavily formatting-dependent (+points for LEGION RULE, wiki_links, code blocks, bullets, headers)
- 1 AM JST daily scan quarantines content scoring < 0.3

Risk assessment:
- Good content IS being quarantined because fast_gate scoring is biased toward specific formatting patterns
- Pages that are narratively written or lack "LEGION RULE" marker get low scores
- Indonesian regulatory content (labor law, tax) likely scores poorly due to different structure
- The quarantine threshold (0.3) may be too aggressive for legitimate content

Approach: Decompose into contracts that:
1. Analyze the quarantine file contents to understand WHAT is being quarantined
2. Analyze the fast_gate scoring to understand WHY good content scores low
3. Compare quarantined vs active content to find the pattern
4. Write deep analysis report with recommendations
