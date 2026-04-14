---
title: Mgda Sener 2018
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

# Paper 027 — MGDA: Multi-Task Learning as Multi-Objective Optimization

## Metadata

| Field | Value |
|-------|-------|
| **Tier** | 3 — Multi-Task Learning Methods |
| **Citation** | Sener & Koltun (2018). *Multi-Task Learning as Multi-Objective Optimization*. NeurIPS 2018, arXiv:1810.04650 |
| **Authors** | Ozan Sener, Vladlen Koltun (Intel Labs) |
| **Venue** | NeurIPS 2018 |
| **Code** | https://github.com/intel-derivative/mtl |
| **Related** | See also: PCGrad (Paper 025), CAGrad (Paper 032) |

---

## Abstract

In multi-task learning, multiple tasks are solved jointly, sharing inductive bias between them. Multi-task learning is inherently a multi-objective problem because different tasks may conflict, necessitating a trade-off. A common compromise is to optimize a proxy objective that minimizes a weighted linear combination of per-task losses. However, this workaround is only valid when the tasks do not compete, which is rarely the case. In this paper, we explicitly cast multi-task learning as multi-objective optimization, with the overall objective of finding a Pareto optimal solution. To this end, we use algorithms developed in the gradient-based multi-objective optimization literature. These algorithms are not directly applicable to large-scale learning problems since they scale poorly with the dimensionality of the gradients and the number of tasks. We therefore propose an upper bound for the multi-objective loss and show that it can be optimized efficiently. We further prove that optimizing this upper bound yields a Pareto optimal solution under realistic assumptions.

---

## Key Contributions

1. **Pareto optimality framework**: Formulates MTL explicitly as finding Pareto optimal solutions
2. **Gradient-based multi-objective optimizer**: Adapts algorithms from multi-objective optimization literature
3. **Scalable upper bound**: Proposes an efficiently optimizable upper bound on multi-objective loss
4. **Theoretical guarantees**: Proves Pareto optimality under reasonable assumptions

---

## Method Details

### Multi-Objective Formulation
Find weights $w_i$ such that:
- $w_i \geq 0$
- $\sum_i w_i = 1$
- Optimize: $\min_\theta \sum_i w_i L_i(\theta)$

### Pareto Optimality
A solution $\theta^*$ is Pareto optimal if no other solution $\theta$ can improve one task's loss without worsening another's.

### MGDA Algorithm
1. Compute per-task gradients: $g_i = \nabla_\theta L_i$
2. Find solution to: $\min_w \| \sum_i w_i g_i \|$ subject to $w_i \geq 0$, $\sum w_i = 1$
3. If $\| \sum_i w_i^* g_i \| = 0$, tasks are non-conflicting; update with any positive $w$
4. Otherwise, update in direction of $\sum_i w_i^* g_i$

### Scalable Upper Bound
Instead of solving the full quadratic program, use:
$$g_{mgda} = \frac{1}{N} \sum_i g_i - \frac{1}{N} \sum_i \|g_i\| \cdot \frac{g_i}{\|g_i\|}$$

This is an upper bound that's efficiently computable.

---

## POPW Relevance

**High relevance** — MGDA provides theoretical grounding for POPW's loss weighting:

**Why it matters for POPW:**
1. **Pareto optimality**: MGDA guarantees finding Pareto optimal solutions; POPW should aim for this
2. **Beyond weighted sum**: Shows why simple weighted sum (Kendall) fails — only works when tasks don't conflict
3. **Gradient-based**: Uses gradient information for decision-making (like GradNorm, PCGrad)

**Connection to other papers:**
- **vs Kendall UW**: MGDA theoretically justifies why we need principled weighting
- **vs GradNorm**: Both use gradient magnitude, but MGDA has stronger theoretical grounding
- **vs PCGrad**: Both address gradient conflicts, but MGDA uses a different optimization approach

**Key insight for POPW**: Finding Pareto optimal solutions is more principled than trying to balance losses arbitrarily.

---

## Limitations

1. **Upper bound is conservative**: May not find the exact Pareto front
2. **Assumes continuous gradients**: Performance with discrete or highly non-convex losses unclear
3. **Compute intensive**: Requires solving optimization problem per step
4. **Implementation complexity**: More involved than simpler methods like GradNorm

---

## References

- Sener & Koltun (2018). [arXiv:1810.04650](https://arxiv.org/abs/1810.04650)
- Related: [[021-kendall-uncertainty-mtl-2018|Kendall]], [[024-gradnorm|GradNorm]], [[025-pcgrad|PCGrad]], [[032-cagrad|CAGrad]]

---

## POPW Protocol Context

**Used in**: POPW theoretical foundations for multi-objective optimization  
**Key insight**: Pareto optimality should be the goal, not arbitrary loss balancing  
**Recommendation**: Combine MGDA's theory with AMTL/UW-SO's practical weighting
