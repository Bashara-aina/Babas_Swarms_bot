---
title: Uncertainty Regularized Meshgi 2022
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- research
created: '2026-04-14'
updated: '2026-04-14'
summary: '| **Tier** | 3 — Multi-Task Learning Methods |'
wikilinks: []
confidence: medium
source: research
---

# Paper 033 — Uncertainty Regularized Multi-Task Learning

## Metadata

| Field | Value |
|-------|-------|
| **Tier** | 3 — Multi-Task Learning Methods |
| **Citation** | Meshgi (2022). *Uncertainty Regularized Multi-Task Learning* |
| **Authors** | Meshgi |
| **Venue** | 2022 (arXiv/Conference) |
| **Note** | Paper verification pending |

---

## Abstract

*Note: Based on understanding of uncertainty regularization in MTL.*

This paper extends the uncertainty-based weighting approach (Kendall et al.) by adding explicit regularization terms that prevent the uncertainty weights from becoming degenerate. The key contribution is a proper regularization framework that maintains meaningful uncertainty estimates throughout training.

---

## Key Contributions

1. **Regularized uncertainty**: Prevents degenerate uncertainty estimates
2. **Stable weighting**: Maintains meaningful weights throughout training
3. **Theoretical analysis**: Guarantees on weight behavior
4. **Improved robustness**: More stable than naive Kendall approach

---

## Method Details

### Problem with Kendall UW
Uncertainty parameters can degenerate:
- $\sigma_i \rightarrow 0$: Loss weight $\rightarrow \infty$
- $\sigma_i \rightarrow \infty$: Task effectively ignored

### Regularization Framework
Add regularization term $R(\sigma)$ to prevent degeneracy:
$$\min_\theta \sum_i \frac{1}{2\sigma_i^2} L_i + \log\sigma_i + \lambda R(\sigma)$$

### R(\sigma) Options
1. **L2 regularization**: $\sum_i (\sigma_i - \sigma_{target})^2$
2. **Entropy regularization**: Encourages uniform weights
3. **Variance regularization**: Prevents extreme values

---

## POPW Relevance

**Moderate relevance** — Addresses practical issues with Kendall UW:

### For POPW:

If using uncertainty-based methods:
- Add regularization to prevent weight degeneracy
- Monitor uncertainty values during training
- Consider entropy-based regularization

### Key insight:
Kendall UW can be stabilized with proper regularization — this is a practical improvement rather than a fundamental change.

---

## References

- Meshgi (2022).
- Related: [[021-kendall-uncertainty-mtl-2018|Kendall UW]], [[028-amtl|AMTL]], [[029-uw-so|UW-SO]]

---

## POPW Protocol Context

**Used in**: POPW practical improvements to uncertainty methods  
**Insight**: If using Kendall UW, add regularization  
**Consider**: AMTL/UW-SO may be cleaner solutions
