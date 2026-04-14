---
title: Context Window Map
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- context-window-map.md
created: '2026-04-14'
updated: '2026-04-14'
summary: Every section injected into the LLM context — token count, purpose, and injection
  frequency.
wikilinks: []
confidence: medium
source: research
---

# Context Window Map

## ONE-LINE SUMMARY
Every section injected into the LLM context — token count, purpose, and injection frequency.

## FACTS
- system_prompt_builder.py: build_full_system_prompt() assembles 8 sections in order
- Section 0: SOUL context — from core/soul_engine.py build_soul_context() — cached 5 min TTL
- Section 1: PERSONALITY_WRAPPER — from agents.py — ~500 tokens
- Section 2: DISAGREEMENT_PROTOCOL — from core/character/disagreement_protocol.py — ~200 tokens
- Section 3: BASHARA PROFILE — from core/memory/user_profile.py build_context_block() — ~300 tokens
- Section 4: EPISODIC MEMORY — from core/memory/episodic_store.py build_context_block() — ~400 tokens
- Section 5: SEMANTIC MEM0 — from mem0 lines or SystemPromptBuilder — ~400 tokens
- Section 6: EMOTION MODIFIER — from core/emotion_modulator.py — ~150 tokens
- Section 7: DEBATE INSTRUCTION — conditional, from core/debate_engine.py — ~200 tokens
- Section 8: ROLE PROMPT — specialist agent instructions — variable
- Section 9: CONVERSATION CONTEXT — last 6 turns from get_conversation_summary_prompt() — ~600 tokens
- Total estimate: ~3000–4000 tokens base system prompt (excluding role + conversation)
- Memory injection: episodic store uses auto_extract_and_store() on every user message — extract facts
- Memory recall: semantic_memory_lines injected on-demand, not always
- Time context injected: get_time_context() from soul_engine.py — JST-aware, 1 line
- Emotional state: get_emotional_state() injected — FOCUSED/CURIOUS/TIRED/PLAYFUL based on hour
- Mood momentum: get_mood_momentum() — "direct" if last 3 messages <30 chars
- SOUL.md file: no fixed location, SOUL_PATH = repo_root/SOUL.md — lives at workspace root
- beliefs.json: stances, pending follow-ups, bashara_facts — injected via soul_engine

## LEGION BEHAVIOR RULES
1. SOUL context MUST be section 0 — verified by testSoulIsFirstSection test
2. System prompt token budget: target <3500 tokens total (leaving ~1500 for user message + response)
3. Memory auto-extraction: only from substantive user messages (>10 words) — skip short acknowledgments
4. Conversation history: last 6 turns — older turns not injected unless semantic recall brings them back
5. Debate instruction: only injected when user makes assertive claim — not on every message
6. Role prompt: variable length — if empty (general agent), inject nothing extra
7. JST time context: injected on every request via soul_engine.get_time_context()
8. Max items per memory section: 5 items (episodic), 8 items (mem0 archival)

## EXAMPLES
Bashara message: "pusing nih" (2 words)
Context injected: SOUL, personality, profile, last 6 turns — NO episodic memory (short message triggers no extract)
Legion response: Single empathic sentence, no bullet list — emotional vocabulary from soul_engine

Bashara message: "write me a scraper for shopee using crawl4ai"
Context injected: SOUL + personality + profile + episodic memory (relevant past scraper tasks) + semantic mem0 hits + role prompt (coder)
Legion response: Full code + explanation — technical depth appropriate for coding task

Bashara message: "thesis progress minggu ini"
Context injected: SOUL + personality + profile + episodic memory (thesis-related past) + semantic (thesis thesis) + beliefs.json stances
Legion response: Context-aware answer about thesis progress

## ANTI-PATTERNS
1. SOUL not section 0: if soul_engine fails to load, SOUL section disappears — personality becomes section 0
2. Memory bloat: auto_extract_and_store() on every message including "ok" and "thanks" — pollutes memory store
3. No conversation summarization: last 6 turns only — long conversations lose context mid-stream
4. Semantic recall irrelevant: mem0 returns keyword matches, not semantically relevant matches — may inject noise

## DEBATE RECORD
Advocate: 9 | Skeptic: 5 | Judge: WRITE 9
Judge note: Context window is the core performance lever — this page enables systematic optimization.
