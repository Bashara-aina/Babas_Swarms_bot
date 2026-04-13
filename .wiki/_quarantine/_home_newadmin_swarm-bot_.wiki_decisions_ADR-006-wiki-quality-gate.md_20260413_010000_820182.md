---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/decisions/ADR-006-wiki-quality-gate.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-13T01:00:00.820210"
}
---

# ADR-006: Wiki Quality Gate System

**Date**: 2026-04-11
**Status**: Accepted
**Type**: Architecture Decision

## Context

The wiki system needs automated quality controls to prevent low-quality, spam, or malicious content from being persisted. This ADR defines a two-tier quality gate system with quarantine capabilities.

## Decision

Implement a two-tier wiki quality gate system with heuristic fast checks and LLM-based deep evaluation.

---

## Quality Gates

### 1. Fast Gate (Heuristic, <5ms target)

Synchronous checks that run before any I/O or LLM call:

| Check | Logic | Result |
|-------|-------|--------|
| Length | `< 50 chars` | `REJECT` |
| Path Traversal | Contains `../` or absolute path patterns | `REJECT` |
| Spam: Excessive Caps | `> 70%` uppercase characters | `REJECT` |
| Spam: Repeated Chars | `> 5` consecutive identical characters | `REJECT` |

### 2. Deep Gate (LLM Evaluation)

For content passing the fast gate, score on a 0.0–1.0 scale across four dimensions:

| Dimension | Description |
|-----------|-------------|
| **Clarity** | Writing is clear, well-structured, and understandable |
| **Actionability** | Contains actionable steps or verifiable information |
| **Factuality** | Claims are reasonable and not obviously false |
| **Wikic-value** | Net score = clarity + actionability + (factuality * 0.5) |

**Threshold**: Score must be `>= 0.3` to pass

---

## Core Function

```python
def evaluate_before_write(page_path: str, content: str) -> EvaluationResult:
    """
    Evaluate wiki content before writing.
    
    Returns:
        PASS: Fast gate passed, deep gate score >= 0.3
        REJECT: Fast gate failed or deep gate score < 0.3
        NEEDS_IMPROVEMENT: Deep gate score 0.3-0.5, recommend revision
    """
```

---

## Quarantine System

### Directory
```
.wiki/_quarantine/
```

Content that fails evaluation is moved to quarantine rather than deleted, enabling recovery.

### Auto-Quarantine Rules

| Trigger | Schedule | Action |
|---------|----------|--------|
| Deep gate score < 0.3 | Daily scan at **1 AM JST** | Move to `.wiki/_quarantine/` |

---

## Scheduled Jobs

| Job | Schedule | Description |
|-----|----------|-------------|
| Daily Quarantine Scan | 1 AM JST (daily) | Auto-quarantine content with score < 0.3 |
| Weekly Deep LLM Evaluation | 2 AM JST Sunday | Re-evaluate all wiki content, update scores |

---

## Bot Commands

| Command | Description |
|---------|-------------|
| `/wiki_audit` | Run full quality audit on all wiki pages |
| `/wiki_flush` | Purge all quarantine content older than 7 days |
| `/wiki_restore <page>` | Restore a quarantined page to wiki |
| `/wiki_scan` | Scan and score all wiki pages |
| `/wiki_stats` | Show quality statistics (avg score, pass/fail rates) |

---

## Consequences

### Positive
- Prevents spam and low-quality content from polluting wiki
- Automatic recovery via quarantine system
- LLM-based scoring provides consistent evaluation

### Negative
- Additional latency on wiki writes (fast gate adds ~5ms, deep gate adds LLM call)
- Weekly LLM evaluation has cost implications

## References

- Related to ADR-001 (LLM provider selection)
- Implements wiki quality requirements from system spec
