---
title: Compounding Knowledge Architecture
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- founder-mindset
created: '2026-04-14'
updated: '2026-04-14'
summary: 'Source: Karpathy LLM Wiki pattern + Glean Enterprise Context'
wikilinks: []
confidence: medium
source: research
---
# Compounding Knowledge Architecture

Source: Karpathy LLM Wiki pattern + Glean Enterprise Context

## The Core Insight
"Stop re-deriving. Start compiling."
Every time an agent solves a problem, that solution should be filed.
The wiki is not documentation. It is the agent's growing brain.

## 3-Tier Memory Model
```
Working Memory   → current session context (volatile)
Episodic Memory  → session summaries → wiki/log.md (persistent)
Semantic Memory  → cross-session facts → wiki/*.md (permanent)
```

## The Compounding Loop
```
Solve problem → Extract insight → File to wiki → 
Next time: retrieve wiki → solve faster → extract better insight → file
```

## Quality Gate
Only file if:
- It's a SOLVED problem with a concrete solution
- It's a CONFIRMED fact with evidence (not a guess)
- It's a DECISION with reasoning (not just the outcome)
- Quality score > 0.7

## Applied to Legion
- wiki_auto_ingest.py implements this loop
- SOUL.md = the agent's values (never auto-overwritten)
- wiki/*.md = the agent's growing expertise
- Target: wiki compounds 1 new page per 3 conversations
