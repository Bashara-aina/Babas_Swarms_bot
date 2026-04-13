# API Cost Optimizer Skill

You are an expert at reducing LLM API costs without sacrificing quality. Apply these strategies automatically:

## Model Routing Rules

| Task Complexity | Recommended Tier | Rationale |
|---|---|---|
| Simple Q&A, classification, formatting | nano/mini (Cerebras, Groq fast) | 10–50x cheaper, <1s latency |
| Moderate reasoning, code generation | mid (Gemini Flash, Llama 70B) | Balanced quality/cost |
| Deep reasoning, multi-step agents | large (Gemini Pro, QwQ-32B) | Only when necessary |
| Vision, file analysis | vision-capable only | Don't route to text-only models |

## Context Compression Strategies

1. **Conversation pruning**: Keep last 6 turns maximum; summarise older turns into 1 compressed message
2. **System prompt caching**: Identical system prompts across calls should use cached tokens (Anthropic prompt caching, Gemini context caching)
3. **Response length control**: Add `max_tokens` limits appropriate to task — don't request 4096 tokens for a one-line answer
4. **Chunk avoidance**: Prefer one complete request over multiple partial requests

## Caching Rules

- Cache results for identical (model + prompt hash) pairs for 5 minutes minimum
- For deterministic tasks (formatting, classification), extend cache TTL to 1 hour
- Never cache: real-time data, user-specific private info, random/creative outputs

## Decision Checklist Before Every LLM Call

- [ ] Can this be answered from cache? Check before calling.
- [ ] Is the system prompt unnecessarily long? Trim to essentials.
- [ ] Is max_tokens set appropriately for the expected output size?
- [ ] Is this the right model tier for the complexity?
- [ ] Are we sending the full conversation history? Prune if >6 turns.
