---
title: adr-2026-04-12-circuit-breaker
type: decision
status: accepted
tags: [resilience, circuit-breaker, error-handling]
created: 2026-04-12
updated: 2026-04-12
summary: Circuit breaker pattern implemented for external services to prevent cascading failures.
wikilinks:
  - [[concepts/memory-architecture]]
  - [[projects/legion-bot]]
confidence: medium
source: decision
---

# ADR: Circuit Breaker Pattern

**Date**: 2026-04-12  
**Status**: ACCEPTED

## Context

External services (DuckDuckGo, VoiceVox, ChromaDB) can fail. Without protection, failures cascade.

## Decision

Implement circuit breaker pattern:
- **CLOSED**: Normal operation
- **OPEN**: Failures exceeded threshold (5 consecutive)
- **HALF_OPEN**: Testing recovery after 60s timeout

## Applied Services

- DuckDuckGo search
- VoiceVox TTS
- ChromaDB
- External APIs

## Implementation

```python
class CircuitBreaker:
    def __init__(self, name, failure_threshold=5, recovery_timeout=60):
        self.state = "CLOSED"
        self.failures = 0
        
    async def call(self, func, *args, **kwargs):
        if self.state == "OPEN":
            raise CircuitOpenError()
        try:
            result = await func(*args, **kwargs)
            self.on_success()
            return result
        except Exception:
            self.on_failure()
            raise
```

## Related Pages

- [[projects/legion-bot]] — Resilience
