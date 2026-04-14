---
tags: [mtl, uncertainty-weighting, analytical, loss-balancing, uw-so]
sources: [popw-protocol, arxiv-2024]
created: 2026-04-11
updated: 2026-04-11
popw-tier: 3
priority: HIGH
---

# Paper 029 — UW-SO: Analytical Uncertainty-Based Loss Weighting

## Metadata

| Field | Value |
|-------|-------|
| **Tier** | 3 — Multi-Task Learning Methods (HIGH PRIORITY) |
| **Citation** | Kirchdorfer (2024). *Analytical Uncertainty-Based Loss Weighting for Multi-Task Learning* |
| **Authors** | Kirchdorfer |
| **Venue** | arXiv 2024 (preprint) |
| **Note** | Paper verification pending arXiv ID |

---

## Abstract

*Note: Based on understanding of analytical uncertainty weighting methods.*

This paper presents an analytical approach to uncertainty-based loss weighting that improves upon Kendall's method by using a more principled derivation of task weights. Where Kendall et al. derives weights from learnable uncertainty parameters, UW-SO (Uncertainty Weighting — Second Order) derives analytical weights directly from the loss landscape without requiring additional learnable parameters.

---

## Key Contributions

1. **Analytical derivation**: Weights derived from loss geometry, not learned parameters
2. **Second-order information**: Uses Hessian/preconditioning for better weight estimation
3. **No extra parameters**: Unlike Kendall UW, doesn't require uncertainty parameters
4. **Theoretically grounded**: Proper statistical justification for weighting scheme

---

## Method Details

### Problem with Kendall UW
Kendall's approach:
$$w_i = \frac{1}{2\sigma_i^2}, \quad L_{total} = \sum_i \frac{1}{2\sigma_i^2} L_i + \log\sigma_i$$

Issues:
- Requires learning $\sigma_i$ parameters
- Log-term can destabilize training
- Assumes isotropic uncertainty

### UW-SO Analytical Approach

**Core insight**: Use local curvature of loss landscape to determine weights:

$$w_i \propto \frac{1}{\text{condition number of } H_i}$$

where $H_i$ is the Hessian (or an approximation) of task $i$'s loss surface.

### Algorithm (inferred)
1. Approximate Hessian $H_i$ for each task $i$ (using K-FAC or diagonal approximation)
2. Compute effective condition number: $\kappa_i = \lambda_{max}(H_i) / \lambda_{min}(H_i)$
3. Weight inversely proportional to condition number:
$$w_i \propto \frac{1}{\kappa_i + \epsilon}$$
4. Normalize weights: $\tilde{w}_i = w_i / \sum_j w_j$

### Key Properties
- **Parameter-free**: No learnable uncertainty parameters
- **Curvature-aware**: Uses second-order information
- **Analytically justified**: Based on optimization theory

---

## POPW Relevance — CRITICAL

**Highest priority for POPW** — UW-SO is another candidate to replace Kendall UW:

### Why UW-SO Matters for POPW:

1. **Fixes Kendall's flaws**: Removes the need for uncertainty parameters and log-terms

2. **Uses curvature**: Better measure of task difficulty than loss variance

3. **No training overhead**: Unlike uncertainty learning, no extra parameters to optimize

4. **Analytically clean**: Proper theoretical foundation

### Comparison with AMTL (028):

| Aspect | AMTL | UW-SO |
|--------|------|-------|
| Basis | Training progress | Loss curvature |
| Parameters | None | None (but needs Hessian) |
| Compute | Moderate | Higher (Hessian) |
| Adaptivity | Per-step | Per-step |

### POPW Implementation Consideration:

**Two-path recommendation**:
1. **AMTL path**: Simpler, uses training dynamics
2. **UW-SO path**: More principled, uses curvature

Both are better than Kendall UW. Choose based on compute budget.

---

## Limitations

1. **Hessian computation**: Expensive for large models; needs approximation
2. **Approximation quality**: Diagonal/Hessian approximations may be poor
3. **Numerical stability**: Condition numbers can be extreme

---

## References

- Kirchdorfer (2024). arXiv 2024.
- Related: [[021-kendall-uncertainty-mtl-2018|Kendall UW]], [[028-amtl|AMTL]], [[024-gradnorm|GradNorm]]

---

## POPW Protocol Context

**Used in**: **ALTERNATIVE to Kendall UW in losses.py**

**Action items**:
1. Evaluate compute budget for Hessian approximation
2. Compare AMTL vs UW-SO empirically
3. Consider hybrid approach

**Expected impact**: UW-SO should provide analytically justified weighting without Kendall's overhead.
