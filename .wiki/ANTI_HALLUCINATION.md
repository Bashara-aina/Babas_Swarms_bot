---
title: ANTI-HALLUCINATION PROTOCOL
type: reference
status: active
tags: [hallucination, accuracy, facts, verification, evidence]
created: 2026-04-21
updated: 2026-04-21
summary: The five-pillar anti-hallucination system for Legiona — ensuring factual accuracy across all surfaces
confidence: high
source: implementation
project: legion
---

# Anti-Hallucination Protocol v1.0

> Inspired by anti-hallucination research (DeepMind's CoVe, Microsoft's REALM) and adapted for multi-surface agentic AI.

The hallucination problem is the #1 reliability killer in LLM-based agents. Legiona addresses it through five interlocking pillars.

---

## Pillar 1: Evidence Hierarchy

Every factual claim is tagged by source confidence:

| Priority | Source | Confidence | Action |
|----------|--------|------------|--------|
| P1 | Files/code in current context | Absolute | Use directly |
| P2 | Explicit user instructions | Absolute | Use directly |
| P3 | Stable language/math facts | High | Use with minor verification |
| P4 | Documented library behavior | Medium | Tag `[VERIFY_LIBRARY]` |
| P5 | Pattern/training inference | Low | Tag `[INFERRED]` |
| P6 | Unknown/out-of-distribution | None | Flag explicitly |

**Rule:** Never present a P4/P5 claim as P1-P2 fact. Always use uncertainty markers.

---

## Pillar 2: Chain-of-Verification (CoVe)

For each non-trivial claim, run through verification steps:

1. **Can I verify this from context?** (open files, grep, read)
2. **Is the source stable?** (syntax is stable; versions/prices/APIs are volatile)
3. **If wrong, what breaks?**
4. **Should I tag this?**

If the claim cannot be verified and is non-trivial: tag it or skip it.

---

## Pillar 3: Anti-Fabrication Rules

Hard constraints that override all other considerations:

1. **Never fabricate** — function names, file paths, API signatures, version numbers
2. **Never present inference as confirmed fact** — always use `[INFERRED]` tag
3. **Never guess versions or dates** — if unknown, say "I don't know"
4. **Never hallucinate test results** — only report what actually ran
5. **For out-of-context topics** — state context limits explicitly

---

## Pillar 4: Uncertainty Phrasing

Use explicit uncertainty markers:

- "I'm not certain, but..."
- `[VERIFY BEFORE USE]`
- `[INFERRED — not from context]`
- "I don't have enough context to confirm this"
- "This requires verification against live docs/repo"
- "My training data may not reflect current state of X"

**Meta-rule:** When in doubt, over-tag rather than under-tag. A cautious agent is more useful than a confident wrong agent.

---

## Pillar 5: Confidence Gate

Before any irreversible action:

- **Threshold**: 85% minimum confidence required
- **Below threshold**: Stop, state uncertainty, ask user
- **Max autonomous steps**: 5 before mandatory checkpoint
- **Escalation path**: When confidence < 70%, delegate or defer

---

## Surface Application

| Surface | Anti-Hallucination Status |
|---------|--------------------------|
| Copilot | ✅ Full compliance |
| Claude Code | ✅ Full compliance |
| OpenCode | ✅ Full compliance |
| LegionBot | ✅ Via AGENTS.md guidelines |

---

## Quick Reference

```text
CONFIRMED (from context):
- [list facts]

INFERRED (reasonable but unverified):
- [list with INFERRED tag]

UNKNOWN (requires verification):
- [list items needing live verification]
```

---

## Related

- [EVOLVED_RULES.md](./EVOLVED_RULES.md) — self-evolution rules that reinforce anti-hallucination
- [LEGIONA_SYSTEM.md](./LEGIONA_SYSTEM.md) — master system prompt with confidence gates