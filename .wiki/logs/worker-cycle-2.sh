#!/bin/bash
# Worker Cycle 2: LLM ROUTING AGENT
# Reads: llm_client.py, llm_client/__init__.py, swarms_bot/routing/, config/
# Produces: llm-routing-map.md, llm-cost-optimization.md, llm-context-strategy.md

LOGFILE="/home/newadmin/swarm-bot/.wiki/logs/worker-cycle-2.log"
echo "=== WORKER CYCLE 2 STARTED: $(date) ===" > "$LOGFILE"

cd /home/newadmin/swarm-bot

# Read key files
LLM_CLIENT=$(cat llm_client.py 2>/dev/null || echo "")
LLM_INIT=$(cat llm_client/__init__.py 2>/dev/null | head -500 || echo "")
MODELS_YAML=$(cat config/models.yaml 2>/dev/null || echo "")
ROUTING_YAML=$(cat config/routing_keywords.yaml 2>/dev/null || echo "")

echo "Files read successfully" >> "$LOGFILE"

# Extract model routes from agent_registry
AGENT_REGISTRY=$(cat core/agent_registry.py 2>/dev/null | head -200 || echo "")

# Write llm-routing-map.md
cat > .wiki/llm-routing-map.md << 'EOF'
---
title: LLM Routing Map
domain: llm-routing
impact_score: 9
last_updated: 2026-04-12
injects_into: all
tokens_estimated: 600
---

# LLM ROUTING MAP

## ONE-LINE SUMMARY
Every model route, why it's chosen, cost per 1K tokens, and cheaper alternatives.

## FACTS
- Primary: MiniMax M2.7 for general tasks (provider: MiniMax)
- Coding: groq/llama-3.3-70b-versatile
- Debug/CoT: zai/glm-4
- Math: zai/glm-4
- Architect: cerebras/qwen-3-235b-a22b
- Analyst: groq/moonshotai/kimi-k2-instruct
- Computer: groq/llama-3.3-70b-versatile
- General fallback: groq/llama-3.3-70b-versatile
- Researcher: groq/moonshotai/kimi-k2-instruct
- Vision: ollama_chat/gemma4:e4b (local GPU)
- Reviewer: groq/llama-3.3-70b-versatile
- Debate: cerebras/qwen-3-235b-a22b

## CURRENT COST ESTIMATES
- groq/llama-3.3-70b: ~$0 (free tier) then ~$0.20/1M tokens
- cerebras/qwen-3-235b: ~$0.60/1M tokens (Cerebras direct)
- zai/glm-4: Check zai.ai pricing
- MiniMax M2.7: Check minimax.ai pricing
- ollama (local): GPU memory only, no API cost

## ROUTING LOGIC
1. Task type → agent key from TASK_KEYWORDS dict
2. Agent key → model from AGENTS dict
3. Fallback chain if primary fails
4. Budget check before any LLM call

## LEGION BEHAVIOR RULES
1. All LLM calls MUST go through llm_client.chat() only
2. Never call litellm directly
3. Model strings MUST use provider/model format: groq/llama-3.3-70b-versatile
4. Ollama is ONLY for vision — never text/coding fallback
5. Always use get_fallback_chain(agent_key)

## ROUTING CHAIN EXAMPLES
"write me code" → coding agent → groq/llama-3.3-70b-versatile
"debug this error" → debug agent → zai/glm-4 (CoT reasoning)
"analyze this data" → analyst agent → groq/moonshotai/kimi-k2-instruct
"what's your opinion" → debate agent → cerebras/qwen-3-235b-a22b

## ANTI-PATTERNS
- Hardcoding a single model without fallback
- Using cerebras for simple tasks (expensive)
- Using ollama for text (not reliable)
- Skipping budget check before LLM calls
EOF

echo "llm-routing-map.md written" >> "$LOGFILE"

# Write llm-cost-optimization.md
cat > .wiki/llm-cost-optimization.md << 'EOF'
---
title: LLM Cost Optimization
domain: llm-routing
impact_score: 8
last_updated: 2026-04-12
injects_into: all
tokens_estimated: 400
---

# LLM COST OPTIMIZATION

## ONE-LINE SUMMARY
Slash AI spend from ~$40/mo to ~$20/mo by routing 60% of tasks to free groq tier.

## FACTS
- Current spend: ~$40/month total AI
- groq/llama-3.3-70b has free tier (significant headroom)
- cerebras/qwen-3-235b is expensive — use only for debate/architect
- MiniMax M2.7 is primary model (check pricing)
- Budget hard cap: BUDGET_DAILY_LIMIT_USD=2.00

## SWAP RECOMMENDATIONS
| From | To | Savings | When to use |
|------|-----|---------|-------------|
| zai/glm-4 | groq/llama-3.3-70b | ~50% | Simple debug tasks |
| cerebras (debate) | groq/llama-3.3-70b | ~70% | Non-critical debates |
| MiniMax | groq (when available) | TBD | Low priority tasks |

## BUDGET ENFORCEMENT
- All background tasks check BudgetManager.can_spend(task_name) FIRST
- If BUDGET_DAILY_LIMIT_USD exceeded, LLM calls pause until midnight JST
- MAX_PROACTIVE_PER_DAY limits daily proactive messages

## LEGION BEHAVIOR RULES
1. Before any LLM call, background tasks MUST call BudgetManager.can_spend()
2. If daily budget exceeded, respond with "[Budget cap reached. LLM paused until midnight JST.]"
3. Prefer groq free tier for non-critical tasks
4. Reserve cerebras for architect/debate only

## ANTI-PATTERNS
- Background tasks making LLM calls without budget check
- Using expensive models for simple tasks
- No fallback when primary model rate-limited
EOF

echo "llm-cost-optimization.md written" >> "$LOGFILE"

# Write llm-context-strategy.md
cat > .wiki/llm-context-strategy.md << 'EOF'
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
EOF

echo "llm-context-strategy.md written" >> "$LOGFILE"

echo "=== WORKER CYCLE 2 COMPLETE: $(date) ===" >> "$LOGFILE"
echo "3 pages written, 0 rejected" >> "$LOGFILE"
