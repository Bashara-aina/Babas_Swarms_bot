---
title: Adr 001 Circuit Breaker
type: decision
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- decisions
created: '2026-04-14'
updated: '2026-04-14'
summary: '**Decider:** @planner'
wikilinks: []
confidence: medium
source: research
---
# ADR-001: Circuit Breaker Design

**Date:** 2026-04-12  
**Status:** PROPOSED  
**Decider:** @planner  
**Reviewer:** @reviewer

## Context
Legion makes multiple external API calls (LLM providers, web search, browser automation). When these services degrade or fail repeatedly, the bot continues to make requests that will fail, wasting tokens and degrading user experience.

## Decision
Implement per-component circuit breakers with 3 states:
- **CLOSED** (normal): requests pass through, failures are counted
- **OPEN** (failing fast): after N failures in a window, reject requests immediately for 60s
- **HALF_OPEN** (testing): after timeout, allow 1 test request; success → CLOSED, failure → OPEN

## Components Protected
1. LLM calls (`llm_client/__init__.py`)
2. Web search (`tools/web_search.py`, `tools/deep_research.py`)
3. Browser automation (`tools/browser_agent.py`)
4. External APIs (email, GitHub, etc.)

## Configuration
```python
CIRCUIT_BREAKER_CONFIG = {
    "failure_threshold": 5,      # failures before OPEN
    "recovery_timeout": 60,       # seconds before HALF_OPEN
    "expected_exception": Exception,
}
```

## Consequences
**Pros:**
- Prevents cascade failures to healthy services
- Saves API tokens on known-failed endpoints
- Automatic recovery when service comes back

**Cons:**
- Adds latency complexity to call paths
- Requires careful tuning of thresholds
- State must be per-component, not global

## Implementation
File: `core/circuit_breaker.py`
