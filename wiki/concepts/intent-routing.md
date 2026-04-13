---
title: intent-routing
type: concept
status: active
tags: [routing, intent, nlp, core]
created: 2026-04-13
updated: 2026-04-13
summary: Intent routing determines how user messages are classified and routed to appropriate handlers or agents based on predicted intent.
wikilinks: [[concepts/memory-architecture.md]], [[concepts/reasoning-loop.md]], [[architecture/legion-module-map.md]]
confidence: high
source: implementation
---

# Intent Routing

## TL;DR
Intent routing is the core classification system that reads user messages, predicts what the user wants to do, and routes the request to the appropriate handler or agent with appropriate confidence scoring.

## Overview

Intent routing uses a combination of:
- **Keyword matching** for fast, deterministic routing
- **LLM classification** for nuanced, ambiguous messages
- **URL detection** for web content links
- **Command parsing** for slash commands

## How Legion Implements It

The `core/intent_router.py` module provides:

1. **Fast path**: Keyword matching for commands like `/start`, `/help`, `/research`
2. **Slow path**: LLM classification for natural language
3. **URL detection**: Regex-based extraction of URLs with domain classification
4. **Fallback**: Returns general chat intent when no specific match

## Confidence Scoring

| Confidence | Action |
|------------|--------|
| 0.9+ | Direct handler dispatch |
| 0.7-0.9 | Handler with confirmation |
| 0.5-0.7 | Clarification question |
| <0.5 | Fallback to general chat |

## Related Pages

- [[concepts/reasoning-loop.md]] — How routing decisions are refined
- [[architecture/legion-module-map.md]] — Core modules overview
