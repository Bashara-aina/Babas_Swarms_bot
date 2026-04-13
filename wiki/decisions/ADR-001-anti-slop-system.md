---
title: Adr 001 Anti Slop System
type: decision
status: stub
tags: [decisions, general]
created: 2026-04-13
updated: 2026-04-13
summary: Stub — needs enrichment. Auto-added frontmatter during QC restructure.
wikilinks: []
confidence: low
source: migration
project: general
---

# ADR-001: Anti-Slop Defense System

**Date**: 2026-04-11  
**Status**: Accepted  
**Decider**: Bashara (Planner Agent)  
**Supersedes**: N/A

---

## Context

Babas_Swarms_bot (Legion) sends every LLM response directly to Telegram users without content quality filtering. Users receive filler-heavy, generic, or repetitive "slop" responses that damage bot credibility.

The existing `core/wiki_quality_gate.py` provides a proven 2-guard (fast+deep) pattern for wiki writes. We extend this to all bot output.

---

## Decision

Implement a **4-guard pipeline** integrated into `llm_client` as a drop-in wrapper.

### Why 4 Guards (not 2 or 6)

| Config | Pros | Cons |
|--------|------|------|
| 2 guards | Simpler, fast | Misses repetition, grounding |
| 4 guards | Balanced coverage, per-guard responsibility | Moderate latency |
| 6 guards | Thorough | Too slow for Telegram, complexity |

4 guards were chosen because:
- Guard 1 (filler) and Guard 3 (repetition) are heuristic — <1ms, no I/O
- Guard 2 (toxicity) is lightweight pattern match — <2ms
- Guard 4 (grounding) is LLM — async, for NEEDS_IMPROVEMENT cases only

### Why NeMo Guardrails vs langchain-community

| Option | Pros | Cons |
|--------|------|------|
| NeMo Guardrails | Best-in-class for RAG grounding, active dev | Heavy, GPU helpful |
| langchain-community | Lightweight, familiar | Less rigorous grounding |
| Custom implementation | Full control | Rewriting proven patterns |

We choose **custom implementation** because:
- Existing `wiki_quality_gate.py` patterns are already proven
- Lightweight for Telegram latency requirements
- No GPU needed — Guard 4 uses existing `llm_client` async call

### Integration Point

**Option A**: Wrap `llm_client.chat()` — clean but changes the client interface  
**Option B**: Middleware in `handlers/` — surgical but per-handler  
**Option C**: Drop-in `LegionQualityGateway` class — additive, backward compatible

We choose **Option C** (`LegionQualityGateway` wrapper) because it:
- Is additive (no existing code breaks)
- Can be enabled/disabled per-session
- Follows the existing bot pattern of gateway wrappers

---

## Consequences

**Positive**:
- All bot output passes quality gates
- Rejected content logged with quarantine path
- Session-level slop statistics available

**Negative**:
- ~5-15ms added latency per response (Guard 4 LLM call)
- Guard 4 costs additional LLM tokens

**Mitigation**:
- Guards 1-3 are synchronous heuristics (<5ms total)
- Guard 4 only fires for NEEDS_IMPROVEMENT verdicts
- `anti_slop_off` command allows users to disable if needed

---

## Alternatives Considered

1. **2-guard (filler + repetition only)**: Too permissive — would let generic responses through
2. **6-guard (add toxicity + bias + hallucination + PII)**: Too slow for Telegram, hallucinations require RAG pipeline
3. **NeMo standalone**: Heavyweight for single-bot deployment

---

## References

- Existing `core/wiki_quality_gate.py` (proven pattern)
- Existing `llm_client.py` (integration point)
- Telegram message size limits (4096 chars)
- Legion existing quality gate commands (`/quality_gate`, `/verify`)
