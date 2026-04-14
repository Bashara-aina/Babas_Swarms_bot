---
title: System Prompt Spec
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- system-prompt-spec.md
created: '2026-04-14'
updated: '2026-04-14'
summary: Canonical system prompt structure for each of Legion's 5 main task types.
wikilinks: []
confidence: medium
source: research
---

# System Prompt Spec

## ONE-LINE SUMMARY
Canonical system prompt structure for each of Legion's 5 main task types.

## FACTS
- 5 main task types: code/debug, research/analysis, emotional/support, media processing, system/utility
- No task-type-specific system prompt templates exist — all tasks use same base structure
- Personality/persona injected via LEGION_PERSONALITY.to_description() in SystemPromptBuilder
- Soul context: build_enhanced_soul_context() provides dynamic time/emotion/mood context
- Role prompts: vary by agent_key (general, coding, analyst, researcher) — from agents.py agent registry
- Debate block: conditional — only injected when user assertion matches known stance topic
- Beliefs.json: injected via soul_engine — all stances, not filtered by relevance

## LEGION BEHAVIOR RULES
1. CODE/DEBUG tasks (agent_key=coding):
   - SOUL (section 0) + personality + disagreement_protocol
   - Profile (relevant projects only) + episodic (debugging history)
   - Semantic (relevant code patterns) + last 8 turns + role_prompt (coder)
   - BANNED_PHRASES reminder + BEHAVIORAL_RULES
   - Target: ~4000 tokens

2. RESEARCH/ANALYSIS tasks (agent_key=researcher/analyst):
   - SOUL (section 0) + personality
   - Profile (projects context) + semantic (topic matches)
   - Last 6 turns + role_prompt (researcher)
   - Target: ~3000 tokens

3. EMOTIONAL/SUPPORT tasks:
   - SOUL (section 0) + personality + emotion_modifier (FOCUSED/CURIOUS/TIRED/PLAYFUL)
   - Last 3 turns only (fast warm response) + pending follow-ups from beliefs
   - NO role prompt — conversational mode only
   - Target: ~1500 tokens

4. MEDIA PROCESSING tasks (vision, voice, video):
   - SOUL (section 0) + personality
   - Profile + last 2 turns (context for what's being shared)
   - Media-specific role prompt if applicable
   - Target: ~2000 tokens

5. SYSTEM/UTILITY tasks (admin, config, stats):
   - SOUL (section 0) + personality + disagreement_protocol
   - Last 4 turns + system_admin role prompt
   - NO beliefs injection (pure utility)
   - Target: ~2500 tokens

6. ALL tasks:
   - SOUL context MUST be section 0 — non-negotiable
   - SOUL must include: cached SOUL.md + time_context + emotional_state + mood_momentum + banned_phrases_reminder
   - BEHAVIORAL_RULES always appended last

## EXAMPLES
Task: code/debug, user says "python scraper for shopee error 403"
Prompt sections: SOUL(section0) + personality + disagreement + profile(cekwajar/rumahlabuh) + episodic(past scraping) + semantic(python, shopee) + last8turns + role(coder) + banned_phrases + behavioral_rules

Task: emotional, user says "pusing masteran skripsi"
Prompt sections: SOUL(section0) + personality + emotion_modifier(TIRED) + last3turns + pending_followups — skip role prompt

Task: system, user says "/budget"
Prompt sections: SOUL(section0) + personality + last4turns + system_admin role — skip beliefs

## ANTI-PATTERNS
1. Wrong task type routing: emotional query routed to coding agent — over-formatted response instead of warm single sentence
2. Beliefs injection on utility tasks: beliefs.json stances injected into "/budget" query — wastes tokens
3. Soul not section 0: if soul_engine fails, personality becomes section 0 — identity instability

## DEBATE RECORD
Advocate: 7 | Skeptic: 6 | Judge: WRITE 7
Judge note: Task-type-specific prompt specs enable the 30-50% token reduction identified in context-optimization.md.
