---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/llm-cost-optimization.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-13T01:00:00.079253"
}
---

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
