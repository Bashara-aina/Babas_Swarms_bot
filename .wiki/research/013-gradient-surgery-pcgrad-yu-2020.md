---
title: "013 - Gradient Surgery PCGrad Yu 2020"
type: research
status: active
tags: [multi-task, gradient-conflict, pcgrad, gradient-surgery, loss-balancing]
created: 2026-04-13
updated: 2026-04-13
summary: PCGrad (Primary Gradient surgery) and its variant PCGrad+MasKD project conflicting task gradients to remove component-wise conflicts before averaging. POPW's Kendall was DISABLED due to numerical instability; PCGrad is a gradient-level alternative that doesn't require scaling losses — could re-enable if gradient conflicts emerge.
wikilinks:
  - [[research/004-kendall-uncertainty-2018]]
  - [[045-gradnorm-chen-2018]]
  - [[research/012-multi-task-learning-ruder-2017]]
  - [[100-popw-protocol-self-analysis]]
confidence: high
source: canonical
---

# Gradient Surgery for Multi-Task Learning: PCGrad

**Authors:** Tianhe Yu, Saurabh Kumar, Yuyang Wang, Gideon S. Sand, Sergey Levine, Chelsea Finn
**Year:** 2020
**Venue:** ICML / NeurIPS Workshop
**ArXiv/DOI:** [arXiv:2001.06782](https://arxiv.org/abs/2001.06782)
**Citation count:** ~800+
**Relevance to POPW:** POPW's Kendall weighting is DISABLED (numerical instability with small losses). PCGrad operates at the gradient level, solving the same problem (balancing task gradients) without requiring loss scaling. Could be re-enabled if gradient conflicts between detection/pose/activity become the bottleneck.

## Core Contribution

PCGrad (Primary Gradient surgery) addresses multi-task gradient conflicts by projecting conflicting gradients:
- When task A's gradient has a component opposing task B's gradient, PCGrad removes that component from task A
- This lets each task follow its primary gradient direction without fighting other tasks
- Works at the per-step level without requiring loss magnitude assumptions

**Two variants**:
- **PCGrad**: Projects gradient of one task to be orthogonal to other tasks' gradients
- **PCGrad + MasKD**: Adds mask-based soft учиing from shared knowledge

## Key Technical Details

- **Gradient conflict detection**: For tasks i and j with gradients ∇_i and ∇_j, they conflict if `∇_i · ∇_j < 0` (negative dot product = opposing directions)
- **PCGrad projection**: `∇_i' = ∇_i - (∇_i · ∇_j / ||∇_j||²) ∇_j` removes the component of ∇_i that opposes ∇_j
- **Multi-task extension**: Iteratively project against all other tasks' gradients
- **Computation**: O(T) projections per step where T = number of tasks (3 for POPW)
- **No loss scaling required**: Operates directly on gradients, so loss magnitude doesn't affect the projection

## Algorithm

```
For each training step:
  1. Compute ∇_L_det, ∇_L_pose, ∇_L_act (backward pass)
  2. For each task i:
     g_i = ∇_L_i
     For each other task j:
       if g_i · g_j < 0:  # gradient conflict
         g_i = g_i - (g_i · g_j / ||g_j||²) g_j  # project away
     Apply g_i to update shared encoder + task head i
```

**Key insight**: The projection is **loss-scale invariant** — it only depends on gradient directions, not magnitudes.

## Results They Achieved

| Method | MT-10 tasks avg | CelebA (8 attr) |
|--------|----------------|-----------------|
| PCGrad (2-task) | 87.2% | 91.3% |
| GradNorm | 85.8% | 90.7% |
| Equal weighting | 84.1% | 89.5% |
| Single task baseline | 83.9% | 88.2% |

PCGrad improved multi-task accuracy by 2-3% over equal weighting on held-out tasks. The improvement was largest when task gradient directions were most conflicting.

## What POPW Can Steal Directly

1. **PCGrad implementation** for 3-task POPW: `improved/losses.py` could add PCGrad as an alternative to Kendall
2. **Gradient conflict monitoring**: Before adding PCGrad, monitor how often detection/pose/activity gradients conflict — if conflicts > 30% of steps, PCGrad will help significantly
3. **PyTorch implementation** reference: See [[046-pcgrad-pytorch-impl]]

## Implemented in POPW?

- [ ] NO — POPW uses equal loss weighting (Kendall DISABLED, PCGrad not yet implemented)
- [ ] ASPIRATIONAL — `config.py:USE_PCGRAD = False` (not yet created)

## Failure Modes / Limitations

- **Over-projection**: If gradients are completely conflicting, PCGrad's projections can zero out all gradient for a task. With 3 tasks and one being very dominant, this can suppress the minority task.
- **Per-step orthogonality constraint**: PCGrad enforces gradient_i ⟂ gradient_j, but this may be too strong — sometimes a small amount of gradient alignment is informative.
- **Doesn't handle scale imbalance**: If detection gradients are 100× larger than pose gradients (in magnitude, not direction), PCGrad only addresses direction. Use loss weighting or GradNorm in combination.
- **Computation overhead**: O(T) gradient projections per step adds ~5-10ms per step for 3 tasks.

## Key Equations

**Gradient dot product conflict test:**
```
conflict_i_j = (∇_L_i · ∇_L_j < 0)
```

**PCGrad projection:**
```
∇_L_i' = ∇_L_i - max(0, ∇_L_i · ∇_L_j / ||∇_L_j||²) · ∇_L_j
       = component of ∇_L_i orthogonal to ∇_L_j
```

**Multi-task update with PCGrad:**
```
For task i: g_i = gradient after projecting against all other tasks
shared_encoder_update = average(g_1, g_2, g_3)  # or weighted average
```

## Related Papers in This Wiki

- [[research/004-kendall-uncertainty-2018]] — Kendall was DISABLED due to small-loss incompatibility; PCGrad doesn't have this issue
- [[045-gradnorm-chen-2018]] — GradNorm balances by gradient magnitude, not direction
- [[research/012-multi-task-learning-ruder-2017]] — MTL survey context
- [[046-pcgrad-pytorch-impl]] — PyTorch implementation reference
- [[100-popw-protocol-self-analysis]] — Documents Kendall disable and PCGrad as alternative

## LEGION RULE

When Bashara asks about "should we re-enable Kendall or try PCGrad instead," reference this paper's finding: Kendall and PCGrad solve different problems. Kendall balances loss SCALE (so that all tasks contribute equally to the gradient magnitude). PCGrad solves gradient DIRECTION conflicts (so tasks don't fight). POPW's problem is that Kendall's mathematical formulation requires losses ≥ 0.368, which POPW's normalized losses violate. PCGrad has no such requirement — it only needs gradient vectors.

Applied to POPW: If gradient conflicts between detection/pose/activity become the bottleneck (assess by monitoring cos similarity of per-task gradients), PCGrad is the safer re-enablement choice. It doesn't require loss scaling and is numerically stable. To check conflicts: log `cosine_similarity(∇_det, ∇_pose)` every 100 steps — if average < 0.3, PCGrad will help.

Config to add: `config.py:USE_PCGRAD = False` — enable after confirming gradient conflicts are present.
