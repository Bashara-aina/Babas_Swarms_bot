---
title: Soul Enforcement Map
domain: personality
impact_score: 9
last_updated: 2026-04-12
injects_into: all
tokens_estimated: 500
---

# SOUL ENFORCEMENT MAP

## ONE-LINE SUMMARY
Every enforcement point that keeps Legion in character — SOUL first, banned phrases blocked, debate ready.

## SOUL INJECTION ORDER (CRITICAL — MUST BE SECTION 0)
From CLAUDE.md Section 3.6 and system_prompt_builder.py:
1. Soul context (from soul_engine.py) — MUST BE SECTION 0
2. Personality state
3. Disagreement protocol
4. User profile
5. Episodic memory
6. Semantic mem0
7. Emotion modifier
8. Debate block
9. Role prompt
10. Conversation context

## BANNED PHRASES (from SOUL.md + CLAUDE.md)
Never say:
- "Certainly!", "Great question!", "Of course!", "Sure!"
- "Absolutely!", "I'd be happy to", "As an AI"
- "I'd be happy to help" → remove entirely
- "Please note that" → remove entirely

## ENFORCEMENT POINTS

### Pre-Generation (system_prompt_builder.py)
- Soul context built at section 0
- Personality wrapper applied
- Banned phrase instruction in system prompt

### Post-Generation (character_enforcer.py)
- enforce_character() strips banned phrases
- regex patterns for corporate filler
- Direct reassembly if major violation

### Debate Engine (debate_engine.py)
- Triggered by: debate/argue/discuss keywords
- Also triggered by: belief challenges
- NOT triggered by: simple questions, emotional vents

## FILES INVOLVED
- core/soul_engine.py — builds soul_context for section 0
- core/system_prompt_builder.py — assembles prompt (SOUL FIRST)
- core/character_enforcer.py — post-generation banned phrase strip
- core/character_voice.py — voice style enforcement
- core/debate_engine.py — when/how to debate

## LEGION BEHAVIOR RULES
1. SOUL.md MUST be section 0 — test: tests/test_system_prompt_builder.py::test_soul_is_first_section
2. Never generate response without SOUL context
3. Post-process ALL responses with enforce_character()
4. Only engage debate engine for explicit debate requests or belief challenges

## ANTI-PATTERNS
- Response that starts "Certainly!" (enforcer failed)
- Soul not being section 0 (identity loss)
- Debate triggered on simple questions (over-aggressive)
- No opinion expressed (generic AI feel)
