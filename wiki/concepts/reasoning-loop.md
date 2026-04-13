---
title: reasoning-loop
type: concept
status: active
tags: [reasoning, llm, planning, agent]
created: 2026-04-13
updated: 2026-04-13
summary: The reasoning loop enables Legion to plan, execute, observe results, and refine approach iteratively before responding.
wikilinks: [[concepts/intent-routing.md]], [[concepts/multi-agent-orchestration.md]], [[concepts/self-improvement-loop.md]]
confidence: high
source: implementation
---

# Reasoning Loop

## TL;DR
Legion uses an internal reasoning loop where the LLM thinks through complex requests step-by-step before committing to a response.

## Loop Structure

1. **Parse**: Understand what the user is asking
2. **Plan**: Break down into steps
3. **Execute**: Call tools/APIs as needed
4. **Observe**: Get results
5. **Refine**: Adjust approach if needed
6. **Respond**: Final output to user

## When It Activates

- Complex multi-step tasks
- Code generation requests
- Research queries
- Problem-solving tasks

## Implementation

In `core/intent_router.py`, certain intents trigger extended reasoning:
- `research` intent → full reasoning chain
- `code` intent → plan → implement → verify
- `analysis` intent → decompose → analyze → synthesize

## Related Pages

- [[concepts/self-improvement-loop.md]] — Learning from past reasoning
- [[concepts/multi-agent-orchestration.md]] — Multi-agent reasoning
