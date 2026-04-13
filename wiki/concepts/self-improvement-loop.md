---
title: self-improvement-loop
type: concept
status: active
tags: [improvement, learning, feedback, iteration]
created: 2026-04-13
updated: 2026-04-13
summary: The self-improvement loop enables Legion to learn from conversations, update memory, and refine future responses based on outcomes.
wikilinks: [[concepts/memory-architecture.md]], [[concepts/reasoning-loop.md]]
confidence: medium
source: design
---

# Self-Improvement Loop

## TL;DR
Legion continuously learns from interactions by saving important facts, tracking error patterns, and incorporating feedback into future reasoning.

## Loop Phases

1. **Observe**: Track what worked/didn't work
2. **Record**: Save to memory with context
3. **Recall**: Pull relevant past learnings
4. **Apply**: Use learnings to improve future responses

## Implementation

- `core/proactive/curiosity_engine.py`: Checks for learning opportunities
- `core/memory/memory_manager.py`: Stores learnings
- Feedback from `/opinion` and `/debate` commands refines stance

## Learning Triggers

- User correction of Legion's output
- Successful problem resolution
- Failed approach (recorded to avoid next time)
- Explicit `/remember` commands

## Related Pages

- [[concepts/memory-architecture.md]] — Where learnings are stored
- [[concepts/reasoning-loop.md]] — How learnings inform reasoning
