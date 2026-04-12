---
title: Multi-Intent Strategy
domain: intent-routing
impact_score: 7
last_updated: 2026-04-12
injects_into: all
tokens_estimated: 300
---

# MULTI-INTENT STRATEGY

## ONE-LINE SUMMARY
How to detect and handle compound requests like "cek seo rumahlabuh dan restart nginx".

## DETECTION PATTERNS
```
Conjunctions that split intents:
- "dan" / "and" (Indonesian/English)
- "sambil" (while doing)
- "," (comma, sequential)
- "terus" (then)
- "first", "then", "after that"
```

## HANDLING LOGIC

### Option A: Sequential (default for non-urgent)
1. Detect compound → parse each sub-intent
2. Respond: "Oke, 2 task: (1) cek seo, (2) restart nginx. Yang mana dulu?"
3. Execute in order confirmed

### Option B: Parallel (for independent tasks)
1. If tasks are independent (no shared state)
2. Execute concurrently via task_orchestrator.py
3. Aggregate results for single response

### Option C: Priority (for urgent)
1. If urgency flag detected
2. Execute most urgent first
3. Acknowledge remaining, execute async

## EXAMPLES

### Compound Request
Bashara: "cek seo rumahlabuh dan restart nginx"
Legion: "2 task: (1) SEO check, (2) restart nginx. Execute keduanya?"
Bashara: "ya"
Legion: [executes both, returns combined result]

### Implicit Compound
Bashara: "restart dan cek status"
Legion: "Restart dulu, baru cek status?"
Bashara: "siap"

## LEGION BEHAVIOR RULES
1. Detect compound → clarify order unless urgent
2. If order ambiguous, ask (don't guess)
3. Independent tasks → execute parallel
4. Always acknowledge compound nature before executing

## ANTI-PATTERNS
- Executing only first intent (ignoring second)
- Guessing order when unclear
- Not acknowledging compound nature
- Long explanation for simple compound tasks
