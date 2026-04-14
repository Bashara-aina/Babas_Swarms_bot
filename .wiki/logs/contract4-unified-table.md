---
title: Contract4 Unified Table
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- logs
created: '2026-04-14'
updated: '2026-04-14'
summary: '- contract1-architecture-fit.md: architecture fit scores'
wikilinks: []
confidence: medium
source: research
---
# Contract 4: Unified Comparison Table — POPW BiGRU Alternatives

## Source Documents
- contract1-architecture-fit.md: architecture fit scores
- contract2-novelty-assessment.md: novelty scores
- contract3-rtx3060-analysis.md: RTX 3060 feasibility

---

## Unified Comparison Matrix

| Method | Arch Fit (1-5) | Novelty (1-5) | RTX 3060 | Params/Memory | GFLOPs | Integration | Paper Value | Recommended Role |
|--------|---------------|---------------|----------|---------------|--------|-------------|-------------|------------------|
| **MMN** | 5/5 | 5/5 | ✅ Feasible | ~512 KB | ~5 | Medium-High | Strongest | Pose↔Activity bidirectional |
| **Mamba** | 4/5 | 4/5 | ✅ Feasible | ~16 KB | ~2 | Low | Strong | Activity head replacement |
| **MS-TCN++** | 4/5 | 3/5 | ✅ Feasible | ~2 MB | ~5 | Medium | Moderate | Activity head pre-MLP |
| **S4** | 3/5 | 3/5 | ✅ Feasible | ~16 KB | ~2 | Medium | Moderate | Long-sequence option |
| **ToTMNet** | 3/5 | 2/5 | ✅ Feasible | ~16 KB | ~1 | Low | Weak | Pose head lightweight |
| **ATSS** | 3/5 | 3/5 | ⚠️ Borderline | ~4-5 MB | ~15 | High | Moderate | Not recommended |
| **BiGRU (baseline)** | 3/5 | 1/5 | ✅ Feasible | ~32 MB | ~4 | Low | Baseline | Current implementation |

---

## Ranked Recommendations

### Tier 1: Strongest Contribution (Recommended Primary)

**1. MMN (Motion Modulation Network)**
- Architecture Fit: 5/5 — Best fit for POPW's pose↔activity communication
- Novelty: 5/5 — Extends FiLM into bidirectional modulation, novel for assembly
- RTX 3060: ✅ Feasible — 512 KB, ~5 GFLOPs, ~3-4ms inference
- Integration: Medium-High — dual-stream (MSM+MTM) with consistency loss
- Paper Value: Strongest — directly addresses multi-task coordination challenge
- Recommended Role: Replace BiGRU for pose↔activity bidirectional communication

**2. Mamba (Selective SSM)**
- Architecture Fit: 4/5 — Selection mechanism aligns with FiLM conditioning
- Novelty: 4/5 — Novel in assembly context, 1000× memory reduction
- RTX 3060: ✅ Feasible — 16 KB, ~2 GFLOPs, ~2ms inference
- Integration: Low — replaces BiGRU, no backbone modification
- Paper Value: Strong — efficient temporal modeling with content selectivity
- Recommended Role: Activity head temporal modeling (if MMN complexity too high)

### Tier 2: Good Alternatives (Secondary Options)

**3. MS-TCN++**
- Architecture Fit: 4/5 — Multi-stage refinement aligns with FiLM cascade concept
- Novelty: 3/5 — Well-established in action segmentation
- RTX 3060: ✅ Feasible — 2 MB, ~5 GFLOPs, ~3ms inference
- Integration: Medium — adds 4 stages before MLP
- Paper Value: Moderate — proven for action segmentation, direct application
- Recommended Role: Pre-MLP temporal enhancement for activity head

**4. S4**
- Architecture Fit: 3/5 — Data-independent matrices limit FiLM flexibility
- Novelty: 3/5 — Overshadowed by Mamba's selective mechanism
- RTX 3060: ✅ Feasible — 16 KB, ~2 GFLOPs, ~2ms inference
- Integration: Medium — HiPPO initialization required
- Paper Value: Moderate — stable long-range modeling
- Recommended Role: Long-sequence option (if T increases beyond 16)

### Tier 3: Niche Options (Situational Use)

**5. ToTMNet**
- Architecture Fit: 3/5 — Generic temporal mixer, no pose-specific optimization
- Novelty: 2/5 — Preprint without GitHub, implementation risk
- RTX 3060: ✅ Feasible — 16 KB, ~1 GFLOPs, ~1-2ms inference
- Integration: Low — replaces BiGRU
- Paper Value: Weak — low contribution to paper narrative
- Recommended Role: Pose head lightweight option (only if MMN/Mamba unavailable)

**6. ATSS**
- Architecture Fit: 3/5 — Cross-modal but domain-mismatched (video anomaly)
- Novelty: 3/5 — Bidirectional but not assembly-specific
- RTX 3060: ⚠️ Borderline — 4-5 MB, ~15 GFLOPs, ~8-10ms inference
- Integration: High — full cross-attention O(T²)
- Paper Value: Moderate — cross-attention could inspire pose-activity alignment
- Recommended Role: NOT RECOMMENDED — exceeds 33ms inference budget

---

## Recommendation Summary

| Priority | Choose | Rationale |
|----------|--------|-----------|
| Strongest paper contribution | MMN | Bidirectional pose↔activity modulation extends FiLM story |
| Fastest implementation | Mamba | Replaces BiGRU, 1000× memory reduction, well-maintained |
| Balanced (tradeoff) | MS-TCN++ | Proven for action segmentation, stable, moderate novelty |
| Long sequences (T>16) | S4 | Stable HiPPO initialization for very long sequences |
| Ultra-lightweight | ToTMNet | Lowest compute but implementation risk (no GitHub) |
| AVOID | ATSS | Exceeds 33ms inference budget, domain mismatch |

---

## POPW-Specific Decision Matrix

| POPW Priority | Recommended Method | Alternative |
|---------------|-------------------|-------------|
| Research novelty (paper contribution) | MMN | Mamba |
| Implementation speed | Mamba | MS-TCN++ |
| Pose↔Activity bidirectional communication | MMN | ATSS (not recommended) |
| RTX 3060 real-time inference | ToTMNet (lightest) / Mamba | MS-TCN++ |
| Training stability | MS-TCN++ | S4 |
| Assembly-specific applicability | MMN | MS-TCN++ |
| Backward compatibility (minimal changes) | Mamba | S4 |

---

## Integration Complexity Breakdown

| Method | Backbone Change | Head Modification | Data Loader Change | PoseFiLM Compatible | Overall |
|--------|-----------------|-----------------|-------------------|-------------------|---------|
| MMN | None | Pose + Activity streams | Clip-level (same as BiGRU) | Yes (dual-stream) | Medium-High |
| Mamba | None | Replace BiGRU | Clip-level | Yes (selective) | Low |
| MS-TCN++ | None | Add before MLP | Clip-level | Yes (per-stage) | Medium |
| S4 | None | Replace BiGRU | Clip-level | Limited | Medium |
| ToTMNet | None | Replace BiGRU | Clip-level | Limited | Low |
| ATSS | None | Replace BiGRU | Clip-level | Yes | High |

---

## Key Insights from Unified Analysis

1. **MMN dominates for paper contribution** but requires dual-stream integration.
   The bidirectional pose↔activity communication directly addresses POPW's multi-task challenge.

2. **Mamba is the safest implementation choice** — lowest risk, good novelty, minimal changes.
   1000× memory reduction frees significant VRAM for larger batches.

3. **MS-TCN++ is the稳健 choice** for activity head — proven technique, stable training,
   moderate novelty, good integration with POPW's architecture.

4. **All methods require clip-level data loading** — no single-frame shortcut exists.
   This is a fundamental change to the data pipeline regardless of method choice.

5. **ATSS is the only method that fails the inference budget** (33ms at 30fps).
   Not recommended despite having good novelty and bidirectional communication.

6. **S4 is dominated by Mamba** — same memory/compute profile but less selective.
   Choose S4 only if you need HiPPO's long-range stability and Mamba's selective mechanism is problematic.