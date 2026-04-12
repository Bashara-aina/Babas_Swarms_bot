---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/research/TIER3-INDEX.md",
  "reason": "daily_fast_scan: score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-12T01:00:00.720361"
}
---

# POPW Protocol — Tier 3: Multi-Task Learning Methods

**Generated**: 2026-04-11  
**Papers**: 13 (023-035)  
**Priority Papers**: 028 (AMTL), 029 (UW-SO)

---

## Overview

This tier covers Multi-Task Learning (MTL) methods for loss function balancing. These papers are essential for understanding how to replace Kendall UW in POPW's losses.py with more principled approaches.

---

## Paper Index

### Priority Papers (POPW Loss Function Replacement Candidates)

| Paper | Title | Status | POPW Action |
|-------|-------|--------|-------------|
| [[028-amtl-yun-cho-2023\|028]] | AMTL: Achievement-Based Training Progress Balancing | HIGH PRIORITY | Primary replacement for Kendall UW |
| [[029-uw-so-kirchdorfer-2024\|029]] | UW-SO: Analytical Uncertainty-Based Loss Weighting | HIGH PRIORITY | Alternative to Kendall UW |

### Gradient-Based Methods

| Paper | Title | Status | POPW Action |
|-------|-------|--------|-------------|
| [[024-gradnorm-chen-2018\|024]] | GradNorm: Gradient Normalization | Verified | Reference for gradient balancing |
| [[025-pcgrad-yu-2020\|025]] | PCGrad: Gradient Surgery | Verified | Handle gradient direction conflicts |
| [[027-mgda-sener-2018\|027]] | MGDA: Multi-Objective Optimization | Verified | Theoretical foundation for Pareto optimality |
| [[032-cagrad-liu-2021\|032]] | CAGrad: Conflict-Averse Gradient Descent | Needs Verification | Global gradient conflict resolution |

### Theoretical & Survey Papers

| Paper | Title | Status | POPW Action |
|-------|-------|--------|-------------|
| [[023-mtl-overview-ruder-2017\|023]] | MTL Overview (Ruder) | Verified | Foundational reading |
| [[026-imtl-liu-2021\|026]] | IMTL: Impartial MTL | Needs Verification | Impartiality principle |
| [[035-robust-mtl-2024\|035]] | Robust MTL with Excess Risk Bounds | Needs Verification | Theoretical grounding |

### Specialized Methods

| Paper | Title | Status | POPW Action |
|-------|-------|--------|-------------|
| [[030-multinet-plusplus-chennupati-2019\|030]] | MultiNet++ | Needs Verification | Architecture insights |
| [[031-negative-transfer-xin-2022\|031]] | Negative Transfer | Needs Verification | Understanding conflict benefits |
| [[033-uncertainty-regularized-meshgi-2022\|033]] | Uncertainty Regularized MTL | Needs Verification | Kendall stability fix |
| [[034-mtgib-unet-li-2025\|034]] | MTGIB-UNet | Needs Verification | Domain-specific |

---

## POPW Action Plan

### Phase 1: Replace Kendall UW
1. **Primary**: Implement AMTL (028) — Achievement-based weighting
2. **Alternative**: Implement UW-SO (029) — Analytical uncertainty weighting

### Phase 2: Add Gradient Conflict Resolution
3. Add PCGrad (025) or CAGrad (032) to handle gradient direction conflicts
4. Combine with AMTL/UW-SO for full solution

### Phase 3: Theoretical Validation
5. Review MGDA (027) and robust MTL theory (035) for validation

---

## Key Insights

### Why Kendall UW Needs Replacement
1. **Requires learning uncertainty parameters** — extra overhead
2. **Log-term can destabilize** training
3. **Assumes isotropic uncertainty** — may not hold
4. **Static during training** — doesn't adapt to dynamics

### What AMTL/UW-SO Offer
- **No extra parameters** — self-tuning
- **Training-aware** — adapts to dynamics
- **Theoretically justified** — principled approach

### Complete Solution Architecture
```
Loss Function Design:
├── AMTL (028) OR UW-SO (029) — Loss weighting
└── PCGrad (025) OR CAGrad (032) — Gradient surgery
```

---

## Verification Status

| Paper | ArXiv Verified | Content Verified |
|-------|---------------|------------------|
| 023 | ✓ (1706.05098) | ✓ |
| 024 | ✓ (1711.02257) | ✓ |
| 025 | ✓ (2001.06782) | ✓ |
| 026 | ✗ | Partial |
| 027 | ✓ (1810.04650) | ✓ |
| 028 | ✗ | Partial |
| 029 | ✗ | Partial |
| 030 | ✗ | Partial |
| 031 | ✗ | Partial |
| 032 | ✗ | Partial |
| 033 | ✗ | Partial |
| 034 | ✗ | Partial |
| 035 | ✗ | Partial |

**Note**: Papers marked "Partial" are based on paper title/conference info with incomplete verification due to arXiv ID lookup limitations.
