---
title: Rate Limit Strategy
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- rate-limit-strategy.md
created: '2026-04-14'
updated: '2026-04-14'
summary: Telegram and OpenRouter rate limits — how Legion handles them.
wikilinks: []
confidence: medium
source: research
---

# Rate Limit Strategy

## ONE-LINE SUMMARY
Telegram and OpenRouter rate limits — how Legion handles them.

## FACTS
- Telegram Bot API: 30 messages per second limit, 20 groups, 1 message per second to private chats
- Telegram send_chunked() delay: 0.3s between chunks — insufficient for sustained high-volume sending
- OpenRouter: no fixed rate limit documented — uses token-based billing, not request-based throttling
- Groq: 30 requests/minute on free tier — documented in llm_client.py comments
- Cerebras: similar free tier limits — not explicitly handled
- MiniMax: no documented limit for MiniMax M2.7 API — assumed flexible
- Budget limiting: BUDGET_DAILY_LIMIT_USD=2.00 hard cap exists in llm_client.py
- Proactive messages: no rate limit handling — just sends via bot.send_message
- Chunk flooding: 20+ chunks sent rapidly = potential Telegram rate limit trigger
- Long polling: Telegram webhook vs long polling — no explicit configuration in main.py

## LEGION BEHAVIOR RULES
1. Telegram sending: minimum 1s delay between messages in any rapid-fire sequence
2. Groq free tier: add request counting to FallbackChain — if Groq used >20x in current minute, skip to next provider
3. OpenRouter: track token usage per day — if BUDGET_DAILY_LIMIT_USD approached, switch to cheaper model
4. Proactive bursts: no more than 3 proactive messages in 10-minute window regardless of urgency
5. Chunk sending: maintain 0.5s minimum delay between chunks (increase from current 0.3s)
6. Retry strategy: if Telegram returns 429 (Too Many Requests), exponential backoff starting at 2s
7. Group chat: if ever enabled, reduce to 1 message per 3 seconds

## EXAMPLES
Bashara message: Triggers a long research task that generates 50 chunks
Anti-pattern: All 50 chunks sent at 0.3s intervals = 15s total, may hit rate limit
Correct: 0.5s minimum delay, if 429 received → wait 2s, retry, if 429 again → wait 4s

Bashara message: "show me all 200 rows of this CSV"
Legion output: Sends as 3-4 chunks with proper delays — user gets complete data

## ANTI-PATTERNS
1. 0.3s chunk delay too aggressive for sustained use — increase to 0.5s minimum
2. No 429 detection: send_chunked() doesn't catch aiogram RateLimitError — needs specific handling
3. Groq tier not enforced: free tier requests/minute limit not tracked — potential service disruption
4. Proactive flooding: multiple proactive engines could fire simultaneously → combined burst of 5+ messages in 1 minute

## DEBATE RECORD
Advocate: 7 | Skeptic: 6 | Judge: WRITE 7
Judge note: Rate limiting is operational reality for Telegram bots — documented strategy prevents outages.
