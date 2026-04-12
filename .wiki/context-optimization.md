---
title: context-optimization
domain: context-window
impact_score: 8
last_updated: 2026-04-12
injects_into: all
tokens_estimated: 340
---

# Context Optimization

## ONE-LINE SUMMARY
What to cut, what to add, and how to optimize context per task type.

## FACTS
- System prompt ~3000–4000 tokens: leaves ~6000–10000 tokens for user input + model response in 128k context
- Profile block: injected on every request even when not relevant — wastes tokens on purely technical questions
- Beliefs.json stances: always injected, even when unrelated to current topic
- Conversation history: fixed 6 turns — doesn't adapt to task type (coding needs more history, quick questions need less)
- Semantic mem0: injected on-demand only — not always present
- No task-type-specific prompt templates: same context structure for all 5 main task types
- Soul context re-read from file every 5 min even when file unchanged — no file hash check
- Time context: 1 line, negligible — optimal
- Emotional state: 1 line, negligible — optimal
- Banned phrases reminder: injected every time — could be in system prompt once at init

## LEGION BEHAVIOR RULES
1. Quick questions (1-2 sentences): inject only SOUL + profile + last 2 turns — skip episodic + semantic
2. Technical/coding tasks: inject SOUL + profile + episodic + semantic + last 8 turns — include relevant beliefs
3. Emotional/depersonalized tasks: inject SOUL + profile + last 3 turns + emotion_modifier — skip technical context
4. Research tasks: inject SOUL + profile + semantic (topic matches) + role prompt (researcher) — skip episodic
5. Media tasks (images/video): inject SOUL + profile + vision context + last 2 turns — skip everything else
6. Profile block: conditional — only inject if task relates to Bashara's projects, schedule, or personal context
7. Beliefs block: conditional — only inject if user message contains keywords matching stance topics
8. Conversation history: dynamic — 2 turns for quick questions, 8 for complex multi-step tasks

## EXAMPLES
Task type: "what time is it" (quick question)
Current context: SOUL + personality + profile + 6 turns + time_context — ~3500 tokens
Optimized: SOUL + time_context — ~200 tokens — 93% reduction with same quality answer

Task type: "debug my python code" (coding)
Current context: SOUL + personality + profile + 6 turns — ~3500 tokens
Optimized: SOUL + profile + episodic (debugging history) + semantic (python errors) + last 8 turns — ~4000 tokens — better debugging context

Task type: "pusing nih" (emotional)
Current context: SOUL + personality + profile + 6 turns + beliefs (all) — ~3500 tokens
Optimized: SOUL + emotion_modifier + last 3 turns — ~1500 tokens — faster, warmer response

## ANTI-PATTERNS
1. Uniform context: same structure for all tasks — wastes tokens on irrelevant sections
2. Memory bloat: auto_extract_and_store() on every message — including "ok" and "👍" — fills memory with noise
3. Stance injection: all beliefs.json stances injected every time — only inject topic-matched ones
4. No context budget: no token counting — potential for context overflow on very long conversations

## DEBATE RECORD
Advocate: 8 | Skeptic: 6 | Judge: WRITE 8
Judge note: Per-task-type context optimization could reduce token usage 30-50% on simple queries.
