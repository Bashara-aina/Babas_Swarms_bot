---
title: Memory Gaps
domain: memory
impact_score: 8
last_updated: 2026-04-12
injects_into: all
tokens_estimated: 400
---

# MEMORY GAPS

## ONE-LINE SUMMARY
What gets forgotten that shouldn't, and what never gets deleted but should.

## CRITICAL GAPS

### 1. Short-term → Long-term handoff
- Problem: No clear trigger for "this memory is important, promote to core"
- What gets lost: Insights from deep conversations not explicitly "remember"-ed
- Fix: Add importance heuristic — messages with facts ("my RTX...", "I need to...") auto-promote

### 2. Cross-store consistency
- Problem: mem0, chromadb, episodic, graph can have conflicting facts
- What gets lost: Trust in retrieved memories when they're inconsistent
- Fix: Weekly validation check (cosine similarity drift > 0.15 = alert)

### 3. Memory decay not aggressive enough
- Problem: 30-day TTL for episodic means old habits/preferences persist
- What gets lost: Fresh context about rapidly changing situations
- Fix: Shorter TTL for context-dependent memories (project blockers = 7 days)

### 4. Bashara vocabulary not remembered
- Problem: "pusing", "nanti", etc. are understood but not stored
- What gets lost: Deep language/intent patterns
- Fix: Add vocabulary mapping to semantic memory

## WHAT SHOULD NEVER BE FORGOTTEN
- Thesis deadline and status
- Current project blockers
- Key life decisions (ADB scholarship, wedding plan)
- Bashara's communication preferences

## WHAT SHOULD BE DELETED
- Episodic memories older than 30 days
- Semantic memories with low relevance scores
- Graph relationships with negative sentiment

## LEGION BEHAVIOR RULES
1. After any "remember" command, also update core profile
2. During consolidation, flag memories with conflicting facts
3. Report memory drift > 0.15 to Bashara via Telegram

## ANTI-PATTERNS
- Storing everything (bloat)
- Forgetting to promote important insights to core
- Not validating cross-store consistency
