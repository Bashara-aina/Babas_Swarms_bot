---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/intent-routing-map.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-13T01:00:00.091597"
}
---

---
title: Intent Routing Map
domain: intent-routing
impact_score: 9
last_updated: 2026-04-12
injects_into: all
tokens_estimated: 600
---

# INTENT ROUTING MAP

## ONE-LINE SUMMARY
23 intent types → 9 agent keys via two-stage classification (pattern match + LLM fallback), confidence threshold 0.70.

## INTENT CLASSIFICATION (core/intent_router.py)
- 24 intents defined in `Intent` enum
- Two-stage pipeline:
  1. Fast pattern-match (sub-millisecond, heuristic keywords)
  2. LLM classification (`classify_intent_llm`) when confidence < 0.70
- LLM classification uses `minimax/ai-01` model

## THE 23 INTENTS (from Intent enum)
1. COMPUTER_CONTROL — open apps, click, type, OS control
2. CODE_GENERATION — write/fix/generate code, scripts, functions
3. CODE_REVIEW — review/audit existing code, security scans
4. WEB_RESEARCH — search, lookup, explain topics
5. WEB_SCRAPE — scrape specific URL, extract data
6. MEMORY_SEARCH — "what did I say about..."
7. MEMORY_STORE — "remember that..."
8. SCHEDULE_TASK — reminders, cron-style scheduling
9. EMAIL_READ — read/summarize emails
10. EMAIL_WRITE — draft/send emails
11. SITE_ANALYSIS — site audits, performance, SEO
12. DATABASE_AUDIT — Supabase/DB operations, SQL queries
13. WEATHER_QUERY — weather, forecasts
14. LOCATION_QUERY — restaurants, hotels, directions, near me
15. FILE_OPERATION — read/write/move/delete files
16. TRANSLATION — translate text between languages
17. MATH_REASONING — calculations, proofs, matrix operations
18. CREATIVE_WRITE — essays, posts, stories, poems
19. DATA_ANALYSIS — CSV/JSON/stats analysis, plotting
20. API_CALL — call external APIs, HTTP requests
21. SELF_UPGRADE — GitHub trending, self-update
22. CASUAL_CHAT — conversation, opinions, jokes
23. DEEP_REASONING — complex multi-step thinking, tradeoffs
24. (implicit) — intents with no keyword match → CASUAL_CHAT fallback

## ROUTING TO AGENTS (9 agents via _INTENT_TO_AGENT)
Only 9 agents are targeted by the intent system:

| Intent | Agent Key | Notes |
|--------|-----------|-------|
| CODE_GENERATION | coding | groq/llama-3.3-70b primary |
| CODE_REVIEW | reviewer | groq/llama-3.3-70b primary |
| MATH_REASONING | math | zai/glm-4 (CoT) |
| DEEP_REASONING | think | cerebras/qwen-3-32b |
| DATA_ANALYSIS | analyst | groq/moonshotai/kimi-k2-instruct |
| CREATIVE_WRITE | general | ollama_chat/gemma4:e4b primary |
| WEB_RESEARCH | researcher | groq/moonshotai/kimi-k2-instruct |
| COMPUTER_CONTROL | computer | groq/llama-3.3-70b + ollama_chat/gemma4:e4b |
| TRANSLATION | general | ollama_chat/gemma4:e4b primary |

**All other intents (16)** default to `general` agent — no dedicated routing entry.

## CONFIDENCE THRESHOLDS
- **0.95** — URL pattern match (video domains: YouTube, TikTok, etc.)
- **0.50-0.95** — Pattern match based on keyword hit count
- **0.85** — LLM classification result
- **< 0.70** — Triggers LLM fallback for CASUAL_CHAT detection
- **< 0.65** — No intent hint injected into system prompt

## ROUTING LOGIC
1. Message → `classify_intent_fast()` — pattern matching
2. If confidence >= 0.70 → use result directly
3. If confidence < 0.70 AND intent == CASUAL_CHAT → `classify_intent_llm()` refinement
4. Return `IntentResult(intent, confidence, method, suggested_agent, needs_tools, needs_research)`
5. `build_intent_hint()` — injects hint into system prompt if confidence >= 0.65

## TOOLS/RESEARCH FLAGS
Intents that **need tools** (`_INTENT_NEEDS_TOOLS`):
- COMPUTER_CONTROL, FILE_OPERATION, EMAIL_READ, EMAIL_WRITE, WEB_SCRAPE, DATABASE_AUDIT, SCHEDULE_TASK, SELF_UPGRADE

Intents that **need research** (`_INTENT_NEEDS_RESEARCH`):
- WEB_RESEARCH, WEATHER_QUERY, LOCATION_QUERY, SITE_ANALYSIS

## URL AUTO-DETECTION
Video URLs (YouTube, TikTok, Instagram, Twitter/X, Facebook, Vimeo) auto-classify as WEB_SCRAPE with 0.95 confidence.

## ANTI-PATTERNS
- Routing to wrong agent due to keyword collision
- Missing intent classification for new task types
- Not using the two-stage pipeline (calling LLM for every message)
- Silently defaulting to general when confidence is low
