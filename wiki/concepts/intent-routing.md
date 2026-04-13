---
title: intent-routing
type: concept
status: active
tags: [routing, intent, nlp, classification, core]
created: 2026-04-13
updated: 2026-04-13
summary: Intent routing is Legion's two-stage classification system — fast pattern matching for deterministic cases, LLM classification for ambiguous messages — that determines how every user message is handled.
wikilinks:
  - [[reasoning-loop]]
  - [[memory-architecture]]
  - [[skill-registry]]
  - [[legion-module-map]]
confidence: high
source: implementation
---

# Intent Routing

## TL;DR
Intent routing classifies every incoming user message to determine the appropriate handler, agent, or skill. It uses a fast pattern-matching stage for deterministic cases (sub-millisecond) and falls back to LLM classification when confidence is low. The result includes the intent category, a confidence score, and flags for whether tools or web research are needed.

## Overview

Every message Bashara sends — whether a slash command like `/research`, a natural language query like "why is rumahlabuh slow today", or a raw URL — must be understood before Legion can respond. Intent routing is that understanding layer. It runs as a lightweight pre-pass before the LLM is invoked, injecting a structured `IntentResult` into the system prompt so the model leans toward the right mode without having to infer it from scratch.

## Context

Slash commands give explicit routing, but Bashara talks naturally. "pusing nih" at midnight needs a one-sentence empathic reply (casual chat). "cek seo rumahlabuh" needs a PageSpeed audit (web audit skill). "training gimana" needs nvidia-smi parsing (gpu_training_status skill). Intent routing bridges natural language to the correct handler without requiring Bashara to memorize command syntax.

## Key Properties

- **Two-stage classification**: pattern match → LLM fallback for confidence < 0.7
- **25 intent categories** covering code, web, memory, email, scheduling, translation, analysis, and more
- **URL auto-detection**: embeds regex for video domains (YouTube, TikTok, Instagram) and routes to web scraping
- **Skill registry fallback**: when confidence < 0.50, the intent router queries the skill registry for trigger-based matching
- **Confidence thresholds**: ≥0.9 → direct dispatch, 0.7–0.9 → handler with confirmation, 0.5–0.7 → clarification question, <0.5 → skill fallback or casual chat
- **Indonesian keyword support**: triggers like "buka", "tutup app", "ingatkan", "jadwalkan" are recognized
- **Sub-millisecond hot path**: `route_sync()` uses only pattern matching for performance-critical paths

## How It Works

### Stage 1: Fast Pattern Matching (`classify_intent_fast`)
A dictionary of regex patterns keyed by intent category is checked against the lowercase message. Each matching pattern increments a score for that intent. The highest-scoring intent wins, with confidence = min(0.95, 0.5 + total_matches × 0.15). This runs in sub-millisecond time with no LLM call.

### Stage 2: LLM Classification (`classify_intent_llm`)
When fast matching yields confidence < 0.7 AND the result is CASUAL_CHAT, the message is passed to the LLM for nuanced classification. Uses MiniMax/ai-01 for speed and cost. Returns the matched intent with 0.85 confidence if successful, falls back to CASUAL_CHAT at 0.5 on failure.

### Stage 3: Skill Registry Fallback
When confidence < 0.50, the router calls `get_skill_registry().find_by_example(message)`. This scores the message against all registered skill trigger keywords and returns the best match. If a skill fires, the intent becomes CASUAL_CHAT but needs_tools and needs_research are both set True.

### URL Detection
Before pattern matching, a regex extracts URLs. If the domain matches known video platforms, the intent is immediately set to WEB_SCRAPE with 0.95 confidence — no further pattern matching needed.

## Relationships

Intent routing is the entry point for almost every user interaction. It feeds directly into [[reasoning-loop]] — when the routing result includes DEEP_REASONING, the reasoning loop activates with plan → execute → observe → refine phases. The [[skill-registry]] is consulted as a fallback when pattern and LLM classification both fail to reach 0.50 confidence. The routing result also populates the `suggested_agent` field which determines which specialized agent (coder, reviewer, researcher, etc.) is invoked. [[memory-architecture]] provides context: past user messages and stated preferences are available to the LLM classifier to improve accuracy on ambiguous cases.

## Current Status

**Implemented.** The full two-stage pipeline is running in production. URL auto-detection for video domains was added in the 2026-04-12 session. Skill registry fallback is wired but the registry itself is still being populated (Phase 2 work). LLM classification uses MiniMax/ai-01 as primary with litellm fallback.

## See Also

- [[reasoning-loop]] — Reasoning that follows routing decisions
- [[skill-registry]] — Skill fallback when routing confidence is low
- [[memory-architecture]] — Context available to LLM classifier
- [[legion-module-map]] — Core modules overview
