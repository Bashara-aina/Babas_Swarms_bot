---
title: Kendall Loss — Uncertainty-Weighted Multi-Task Learning
type: concept
status: active
tags: [popw, kendall, multi-task, loss-function, uncertainty-weighting]
created: 2026-04-13
updated: 2026-04-13
summary: Kendall Loss extends the negative log-likelihood of a Gaussian to weight multiple task losses by their learned uncertainty — tasks with high uncertainty receive lower weight, preventing noisy tasks from destabilizing training.
wikilinks:
  - [[concepts/wise-iou]]
  - [[concepts/multi-task-learning]]
  - [[projects/popw-research]]
confidence: high
source: research
project: popw
---

# Kendall Loss — Uncertainty-Weighted Multi-Task Learning

## TL;DR

Kendall Loss addresses the problem of balancing multiple task losses by learning per-task uncertainty σ. Rather than manual weight tuning, the model learns which tasks are reliable (low σ, high weight) and which are noisy (high σ, low weight) directly from data.

## The Gaussian Foundation

Starting from the Gaussian probability density function:

```
P(y|f(x), σ²) = (1/√(2πσ²)) × exp(-||y-f(x)||² / 2σ²)
```

Taking negative log-likelihood (to minimize instead of maximize):

```
-NLL = ||y-f(x)||²/(2σ²) + log(σ) + constant
```

## The Master Equation

```
L_total = (1/2σ²_det) × L_det + (1/2σ²_pose) × L_pose + (1/2σ²_act) × L_act
           + log(σ_det) + log(σ_pose) + log(σ_act)
```

Where:
- First term: **Weighted loss** — uncertainty acts as automatic task weight
- Second term: **Regularization** — prevents σ from growing unbounded

## How Uncertainty Adjusts Weights

| Task State | Loss Value | σ² | Weight (1/2σ²) | Effect |
|-----------|------------|-----|-----------------|--------|
| Reliable (detection good) | 0.293 | 0.606 | 0.826 | High weight, fast learning |
| Noisy (pose hard) | 8.17 | 3.32 | 0.150 | Low weight, slow learning |

### Example Calculation

```
L_det = 0.293 (good IoU)
→ s_det = ln(2 × 0.293) = ln(0.586) ≈ -0.53
→ σ²_det = e^(-0.53) = 0.606
→ w_det = e^0.53 = 1.70

L_pose = 8.17 (noisy keypoints)
→ s_pose = ln(2 × 8.17) = ln(16.34) ≈ 2.79
→ σ²_pose = e^2.79 = 3.32
→ w_pose = e^(-2.79) = 0.061
```

## Why Not Just Use Kendall?

Despite theoretical elegance, Kendall Loss was replaced with Wise-IoU because:

1. **Gradient Direction Problem**: Kendall scales gradient magnitude but not direction
2. **Shadow Contamination**: A high-loss "shadow on wall" sample gets low weight (0.5) but still pushes gradients toward detecting shadows
3. **Wise-IoU Fixes Direction**: Wise-IoU actively suppresses gradients from outliers rather than just scaling them

## The σ Update Rule

σ is learned via gradient descent alongside model parameters:

```
∂L/∂σ = -Loss/σ³ + 1/σ

If Loss is high → first term dominates → σ increases → task gets lower weight
If Loss is low → second term dominates → σ decreases → task gets higher weight
```

## Related

- [[concepts/wise-iou]]
- [[concepts/multi-task-learning]]
- [[projects/popw-research]]
