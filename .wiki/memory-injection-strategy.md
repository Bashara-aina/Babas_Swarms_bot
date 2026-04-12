---
title: Memory Injection Strategy
domain: memory
impact_score: 7
last_updated: 2026-04-12
injects_into: all
tokens_estimated: 350
---

# MEMORY INJECTION STRATEGY

## ONE-LINE SUMMARY
Which memories to inject per task type, in what order, with token budget.

## INJECTION BY TASK TYPE

### Code Tasks
1. Project context (which project: rumahlabuh? cekwajar? thesis?)
2. Recent code decisions from episodic (last 7 days)
3. Core facts about Bashara's preferences (verbose? concise?)
Token budget: ~800 chars

### Research Tasks
1. Thesis context (what's the current focus)
2. Mem0 semantic search for related topics
3. Graph relationships (who knows what)
Token budget: ~1200 chars

### Emotional Tasks
1. Recent emotional events from Letta
2. Current mood state
3. Relevant SOUL.md opinions
Token budget: ~600 chars

### System/Admin Tasks
1. Bot status and health
2. Recent errors or issues
3. Project blockers from core profile
Token budget: ~500 chars

## MEMORY FORMATTING FOR LLM
```
[Legion Memory — relevant context:]
- (0.95) [memory content] — [when stored]
- (0.87) [memory content] — [when stored]
[End memory context]
```

## LEGION BEHAVIOR RULES
1. Max 3000 chars of memory context per request
2. Sort by relevance score descending
3. Include "when stored" for temporal context
4. Filter out memories with score < 0.5

## ANTI-PATTERNS
- Injecting ALL memory tiers for every request
- Including low-relevance memories (>0.5 threshold)
- Forgetting to sort by recency for emotional tasks
- Not formatting for LLM scannability
