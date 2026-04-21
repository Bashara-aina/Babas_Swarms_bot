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

## Pillar 6: Source Provenance Tracking

Every factual claim carries its source lineage — where it came from, when it was learned, and how to re-verify it.

**Provenance fields per claim:**
- `source_type`: file | conversation | user_input | external_api | inferred | memory
- `source_path`: file path, conversation ID, or external reference
- `timestamp`: when the information was acquired (ISO 8601)
- `confidence_weight`: 0.0–1.0 derived from evidence hierarchy
- `re_verification_cost`: low | medium | high | unknown

**Example provenance block:**
```
PROVENANCE: file:///home/newadmin/swarm-bot/core/memory/tiers.py:45
  source_type: file
  timestamp: 2026-04-21T14:23:00Z
  confidence_weight: 0.95
  re_verification_cost: low
```

**Rule:** When citing code, always include file path + line number. Never cite memory as hard fact — memory has drift (see Pillar 8).

**Implementation:**
- `lib/legiona/memory/rules.md` — source attribution required for every factual claim
- `core/memory/tiers.py` — ArchivalMemory stores `source` field for every stored memory
- `lib/legiona/memory/global_memory.md` — provenance-tagged project facts from evolve()
- `observation_store.py` — captures provenance metadata with every observation

---

## Pillar 7: Consistency Verification

Before acting on stored information, verify it is consistent with current context. Information that contradicts itself across memory tiers or against live filesystem state is flagged as unreliable.

**Consistency check types:**
1. **Cross-tier verification**: CoreMemory vs ArchivalMemory — contradictory facts trigger warning
2. **Semantic drift detection**: Chroma semantic search vs mem0 records — when the two semantic stores diverge, surface the inconsistency
3. **Temporal context check**: Conversation history vs current facts — verify if stored "facts" are still valid

**Drift threshold:** 0.15 cosine similarity difference triggers `drift_detected` status

**Implementation:**
- `memory_manager.py::validate_consistency()` — runs semantic alignment check between mem0 and Chroma, reports `average_drift`, `max_drift` against `drift_threshold`
- `build_context_block()` — reconstructs memory state from CoreMemory + profile + recent RecallMemory, allowing the agent to spot contradictions before acting
- `progressive_search()` — Layer 1 (index) + Layer 2 (timeline) + Layer 3 (full) enables progressive consistency checking without token overflow

**Rule:** If `validate_consistency()` returns `status: drift_detected`, treat stored facts as `UNCERTAIN` until re-verified against live context.

---

## Pillar 8: Temporal Decay Awareness

Information has a half-life. Memory stores timestamps on every record. Facts older than system-relevant thresholds are treated as stale.

**Decay tiers:**
| Age | Classification | Action |
|-----|----------------|--------|
| < 24h | Fresh | Use directly, no caveats |
| 1–7 days | Aging | Tag `[MEMORY_AGE: N days]` |
| 1–4 weeks | Stale | Re-verify before confident use |
| > 1 month | Historical | Only use with explicit `[VERIFY_AGAINST_CURRENT_CONTEXT]` tag |

**Stale info markers:**
- `created_at` field on every ArchivalMemory record
- `last_accessed` + `access_count` tracking — frequently accessed memories are considered more current
- `sessions.jsonl` records session context — old sessions are historical, not authoritative

**Auto-decay rules:**
- CoreMemory auto-trims to ~4000 chars (see `MAX_CHARS` in `tiers.py::CoreMemory`) — oldest/lowest-importance entries evicted first
- Importance < 0.85 → CoreMemory only (not archived for quick context)
- Importance ≥ 0.85 → promoted to CoreMemory key

**Implementation:**
- `ArchivalMemory` stores `created_at` and `last_accessed` on every record, indexed for time-based queries
- `CoreMemory._save()` enforces 4000 char cap by trimming oldest entries
- `auto_extract_and_save()` tags extracted facts with source + timestamp for future age judgment

**Rule:** When using information from ArchivalMemory, include the age: "User prefers X (archived 3 weeks ago — re-verify if critical)"

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