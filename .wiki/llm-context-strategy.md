---
title: LLM Context Strategy
domain: llm-routing
impact_score: 7
last_updated: 2026-04-12
injects_into: all
tokens_estimated: 350
---

# LLM CONTEXT STRATEGY

## ONE-LINE SUMMARY
What to inject per task type, token budget per layer, and how to avoid context bloat.

## CONTEXT INJECTION ORDER (CLAUDE.md verified)
1. Soul context (from soul_engine.py) — MUST be section 0
2. Personality state
3. Disagreement protocol
4. User profile
5. Episodic memory (SQLite, 30-day retention)
6. Semantic mem0 + ChromaDB
7. Emotion modifier
8. Debate block
9. Role prompt
10. Conversation context

## TOKEN BUDGET GUIDE
- System prompt base: ~2000 tokens
- Soul context: ~500 tokens
- Memory injection: ~1000 tokens max
- Conversation history: ~1500 tokens
- Total target: Stay under 8192 for most tasks

## PER-TASK TYPE CONTEXT
| Task Type | Extra Context Needed |
|-----------|---------------------|
| Code | Project files, relevant functions |
| Research | Mem0 semantic search, web context |
| Emotional | Recent emotional events, SOUL opinions |
| Debate | beliefs.json, recent stance updates |

## LEGION BEHAVIOR RULES
1. Soul MUST be section 0 — verify in tests/test_system_prompt_builder.py
2. Never inject more than 3000 chars of memory context
3. Truncate conversation history if total exceeds 4096 tokens
4. Chunk long LLM responses at 4000 chars before Telegram

## ANTI-PATTERNS
- Injecting all memory tiers for every request (bloats tokens)
- Forgetting soul context (Loses Legion's identity)
- Not chunking long responses (Telegram limit: 4096 chars)
