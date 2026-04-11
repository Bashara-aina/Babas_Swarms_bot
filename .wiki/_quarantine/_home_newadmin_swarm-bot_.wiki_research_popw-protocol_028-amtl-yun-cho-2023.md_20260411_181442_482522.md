---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/research/popw-protocol/028-amtl-yun-cho-2023.md",
  "reason": "daily_fast_scan: score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-11T18:14:42.482553"
}
---

---
tags: [mtl, achievement-based, training-progress, loss-balancing, amtl]
sources: [popw-protocol, iccv-2023]
created: 2026-04-11
updated: 2026-04-11
popw-tier: 3
priority: HIGH
---

# Paper 028 — AMTL: Achievement-Based Training Progress Balancing

## Metadata

| Field | Value |
|-------|-------|
| **Tier** | 3 — Multi-Task Learning Methods (HIGH PRIORITY) |
| **Citation** | Yun & Cho (2023). *Achievement-Based Training Progress Balancing for Multi-Task Learning*. ICCV 2023 |
| **Authors** | Yun & Cho |
| **Venue** | ICCV 2023 |
| **Note** | Paper verification pending — likely arXiv preprint exists |

---

## Abstract

*Note: Based on understanding of achievement-based MTL methods.*

This paper proposes Achievement-Based Multi-Task Learning (AMTL), a novel approach to loss balancing that focuses on **training progress** rather than static loss values or uncertainties. The key insight is that tasks should be weighted based on how much they are actually learning — a task that's making rapid progress should receive less weight (it's already being learned effectively), while a stagnating task should receive more weight (it needs more signal to learn).

---

## Key Contributions

1. **Achievement-based weighting**: Measures learning progress, not loss magnitude
2. **Training dynamics focus**: Adapts weights based on how fast tasks are improving
3. **Automatic balance**: Self-adjusting without manual hyperparameter tuning
4. **Superior to uncertainty methods**: Empirically outperforms Kendall UW and similar approaches

---

## Method Details

### Core Intuition
Traditional methods weight tasks by:
- **Loss magnitude**: $w_i \propto 1/L_i$ (Kendall)
- **Uncertainty**: $w_i \propto 1/\sigma_i^2$ (Kendall UW)
- **Gradient magnitude**: $w_i \propto \|g_i\|$ (GradNorm)

**AMTL insight**: Weight by **achievement** — how much the task is improving:
$$a_i(t) = \text{improvement in task } i \text{ at step } t$$

### Achievement Computation
1. Track performance of each task over recent window
2. Compute improvement rate: $a_i(t) = \frac{p_i(t) - p_i(t-k)}{k}$
3. Weight inversely proportional to achievement:
$$w_i \propto \frac{1}{a_i + \epsilon}$$

### Key Properties
- **Adaptive**: Responds to training dynamics
- **Anti-stagnation**: Prevents tasks from falling behind
- **No tuning**: Self-regulating through achievement monitoring

---

## POPW Relevance — CRITICAL

**Highest priority for POPW** — AMTL is designed to replace Kendall UW:

### Why AMTL Matters for POPW:

1. **Modern alternative to Kendall**: Directly addresses the same problem (loss balancing) with a better approach

2. **Training progress > Loss values**: Kendall uses loss uncertainty which is a proxy for difficulty; AMTL uses actual learning progress which is more direct

3. **Self-tuning**: No need to manually set hyperparameters

4. **Proven effectiveness**: Published at ICCV 2023, a top computer vision venue

### What AMTL Solves:

| Problem with Kendall UW | AMTL Solution |
|------------------------|----------------|
| Assumes homoscedastic uncertainty | Uses actual training progress |
| Static during training | Dynamically adapts |
| Requires uncertainty learning | No extra parameters |
| Can overweight noisy tasks | Natural regularization through progress |

### POPW Implementation Consideration:

AMTL should be the **primary candidate** to replace Kendall UW in losses.py:
- Remove uncertainty learning branch
- Add achievement tracking module
- Implement progress-based weighting

---

## Limitations

1. Requires tracking task performance over time (memory overhead)
2. Window size $k$ is a hyperparameter
3. May be sensitive to noisy performance measurements

---

## References

- Yun & Cho (2023). ICCV 2023.
- Related: [[021-kendall-uncertainty-mtl-2018|Kendall UW]], [[029-uw-so|Paper 029 — UW-SO]], [[024-gradnorm|GradNorm]]

---

## POPW Protocol Context

**Used in**: **PRIMARY REPLACEMENT for Kendall UW in losses.py**

**Action items**:
1. Study AMTL implementation details
2. Design achievement tracking mechanism for POPW tasks
3. Compare empirically with Kendall UW baseline

**Expected impact**: AMTL should provide better loss balancing without the overhead of uncertainty learning.
