---
title: Intent Gaps
domain: intent-routing
impact_score: 7
last_updated: 2026-04-12
injects_into: all
tokens_estimated: 350
---

# INTENT GAPS

## ONE-LINE SUMMARY
Missing intents for compound tasks, emotional nuance, and project-specific commands.

## CRITICAL GAPS

### 1. Compound Intent Detection
- Problem: "cek seo rumahlabuh dan restart nginx" = two intents
- Gap: No systematic compound detection
- Current behavior: First intent wins, second ignored
- Need: Split on "dan", "and", "sambil" conjunctions

### 2. Emotional State Intent
- Problem: "pusing", "frustrated", "stuck" = emotional, not task
- Gap: No dedicated emotional de-escalation intent
- Current behavior: Routes to general or misunderstands
- Need: Detect frustration → respond briefly, not with bullet list

### 3. Project Context Intent
- Problem: "rumahlabuh status" vs "thesis progress" = different context
- Gap: No project-scoped routing
- Current behavior: General research, loses project context
- Need: Project keyword → inject relevant core facts

### 4. Time-Sensitive Urgency
- Problem: "SEGERA", "urgent", "sekarang" = urgency
- Gap: No urgency modifier in intent
- Current behavior: Same priority as non-urgent
- Need: Urgency flag → prioritize response

### 5. Proactive Trigger Intent
- Problem: Proactive messages need "engagement" intent
- Gap: No internal trigger classification
- Current behavior: Scheduled only, not engagement-driven
- Need: Curiosity engine → engagement level → proactive or quiet

## LEGION BEHAVIOR RULES
1. When compound intent detected, ask "Yang mana dulu?" unless urgency
2. When "pusing/stuck" detected, drop to brief empathetic response
3. When project name detected, inject relevant core profile facts
4. When urgency words detected, mark priority regardless of intent type

## ADDING NEW INTENTS (from CLAUDE.md)
1. Add intent class to IntentRouter in core/intent_router.py
2. Add handler function in appropriate handlers/ file
3. Wire handler in main.py router registration
4. Add test in tests/test_intent_router.py

## ANTI-PATTERNS
- Not splitting compound requests
- Treating emotional messages as task requests
- Missing ALLOWED_USER_ID in new handlers
- Not adding tests for new intents
