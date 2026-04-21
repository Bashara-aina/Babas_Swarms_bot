---
title: M2.7 OPTIMIZATION GUIDE
type: reference
status: active
tags: [m2.7, optimization, performance, temperature, reasoning]
created: 2026-04-21
updated: 2026-04-21
summary: Optimization patterns for MiniMax M2.7 — temperature, reasoning_split, token budgets, and surface-specific tuning
confidence: high
source: implementation
project: legion
---

# M2.7 Optimization Guide

MiniMax M2.7 (ablation7b) is the primary reasoning model for all Legiona surfaces. This guide covers optimal configuration.

---

## Temperature

**Default: 1.0**

M2.7 at temperature 1.0 provides optimal balance between coherence and creativity for reasoning tasks. Lower temperatures (0.7, 0.5) tend to truncate reasoning chainsprematurely. Higher temperatures (1.2+) introduce noise without quality gains.

Exception: For strictly deterministic tasks (code formatting, math), 0.7 may be appropriate.

---

## Reasoning Split

**Always: enabled**

`reasoning_split=True` interleaves chain-of-thought with final output. This is critical for:
- Debugging complex code paths
- Architectural decision-making
- Multi-step problem decomposition

The interleaved format allows mid-reasoning course correction without losing context.

---

## Token Budget

| Context Window | Max Output | Recommended Reserve |
|----------------|------------|---------------------|
| 196,608 | 32,768 | 8,192 (25%) |

Reserve acts as buffer for context expansion during complex tasks.

---

## Surface-Specific Settings

### Claude Code
- Temperature: 1.0
- reasoning_split: True
- Max tokens: 32,768

### OpenCode
- Temperature: 1.0
- reasoning_split: True
- Max tokens: 32,768

### Copilot
- Temperature: 0.8 (more deterministic for code completion)
- reasoning_split: False (inline completion doesn't benefit)
- Max tokens: 4,096

---

## Common Pitfalls

1. **Setting temperature too low** — reasoning chains get cut off
2. **Disabling reasoning_split on complex tasks** — loses mid-chain course correction
3. **Max tokens too low** — cuts off reasoning mid-chain
4. **Using system prompts >2000 tokens** — dilutes model attention on task

---

## Related

- [ANTI_HALLUCINATION.md](./ANTI_HALLUCINATION.md) — accuracy protocols
- [LEGIONA_SYSTEM.md](./LEGIONA_SYSTEM.md) — LLM configuration section