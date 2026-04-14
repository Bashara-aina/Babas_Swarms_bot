---
title: "Just Add π: Discovering Motion Prior for Action Recognition"
created: 2026-04-14
modified: 2026-04-14
tags: [motion-prior, discovering, pose-prior, action-recognition, skeleton-prior, π-pi, pretraining, mtl]
authors: [Reilly et al.]
type: research
summary: "Just Add π (Reilly et al. WACV 2024) discovers motion priors from unlabeled skeleton data — a pretrained motion encoder that captures typical pose transition patterns. The π (psi) prior modulates skeleton features using learned motion patterns. For POPW, this provides a learned motion prior that can enhance PoseFiLM's pose-conditioned features."
wikilinks:
  - [[mmn]]
  - [[dmm-motion]]
  - [[pose-conditioned-temporal-modeling]]
  - [[projects/popw-multi-task-ikea]]
source: https://arxiv.org/abs/2311.18840
---

# Just Add π: Discovering Motion Prior for Action Recognition

## Paper Info
- **arXiv**: [2311.18840](https://arxiv.org/abs/2311.18840)
- **Authors**: Reilly et al.
- **Venue**: WACV 2024

## Core Contribution

"Just Add π" discovers **motion priors** from unlabeled skeleton data through self-supervised pretraining. The key insight: there are regular patterns in how poses transition during actions, and these can be learned without action labels.

**The π prior**: A learned embedding that captures typical pose transition patterns:
```
pose_t → π_encoder → π_t  # motion prior embedding
modulated = γ(π_t) ⊙ pose_features + β(π_t)
```

## Self-Supervised Motion Prior Learning

```
Unlabeled skeleton sequences:
  [pose_1, pose_2, ..., pose_T] ∈ R^[T, J, D]

Contrastive learning:
  Positive pairs: consecutive poses (should have similar π)
  Negative pairs: random non-consecutive poses

  π_t = MLP(pose_t)  # motion prior
  Loss = contrastive(π_t, π_{t+1})  # similar for consecutive
```

**What π learns**:
- Typical pose transitions for walking, reaching, grasping
- Common action patterns (sit → stand, reach → grasp)
- Natural human motion constraints

## π Modulation for Action Recognition

After pretraining π on unlabeled data:
```
Labeled skeleton sequence:
  pose_t → π_encoder → π_t (frozen)
  pose_t → task_encoder → pose_features

  # π modulates pose features:
  C5_mod = γ(π_t) ⊙ pose_features + β(π_t)

  → Activity Classification
```

**Why frozen π works**: The motion prior captures generic human motion patterns, not task-specific. Using frozen π provides regularization — prevents overfitting on small labeled datasets.

## Why π Matters for POPW

POPW's PoseFiLM learns pose→modulation mapping from scratch:
```
pose_flat → MLP → γ, β  # learned from 254 videos
```

"Just Add π" suggests **pretrained motion prior**:
```
pose_flat → pretrained π_encoder → π_t (frozen)
          → task MLP → γ, β (fine-tuned)

C5_mod = γ(π_t) ⊙ C5 + β(π_t)
```

**Benefits for POPW**:
1. π pretrained on large unlabeled skeleton datasets (NTU RGB+D has 56K videos)
2. π captures generic assembly-relevant motion patterns
3. POPW only needs to fine-tune γ, β — less overfitting on 254 videos

## Pretrained Motion Datasets for π

π can be pretrained on:
| Dataset | Videos | Actions | POPW Relevance |
|---------|--------|---------|---------------|
| NTU RGB+D 60 | 56K | 60 | Indoor activities |
| NTU RGB+D 120 | 114K | 120 | More activities |
| Kinetics-700 | 700K | 700 | General actions |
| assembly_evidence | ? | ? | Assembly-specific |

**For IKEA assembly**: Could pretrain π on:
1. Assembly-related YouTube videos (IKEA tutorials)
2. Ego-centric assembly datasets (Ego4D)
3. Hand-specific datasets (EgoHands)

## POPW Enhancement: Pretrained π

```
Pose encoder (pretrained on assembly videos):
  pose_flat → π_encoder → π_t ∈ R^64 (frozen)

PoseFiLM with π:
  pose_flat → MLP → γ_task, β_task
  π_t → γ_prior, β_prior (frozen from π)

  γ = γ_prior ⊙ γ_task
  β = γ_prior ⊙ β_task + β_prior

  C5_mod = γ ⊙ C5 + β
```

**Why multiplicative π modulation**:
- π_prior scales γ_task (activity-specific modulation scaled by general motion)
- π_prior shifts β_task (bias adjusted by general motion pattern)
- Result: modulation informed by both task-specific and general motion patterns

## Connection to Other Papers

| Paper | Motion Representation | POPW Connection |
|-------|----------------------|-----------------|
| Just Add π | Learned prior π | Pretrained motion encoder |
| MMN | Velocity + MSM/MTM | Bidirectional modulation |
| DMM | Vel + Acc + Jerk | Multi-scale motion |
| MANs/TARM | Velocity attention | Motion as attention |

## Future POPW v2 with Pretrained π

```
Pose encoder (frozen):
  keypoints → pretrained_π_encoder → π_t

PoseFiLM (fine-tuned on IKEA):
  pose_flat → MLP → γ_task, β_task
  π_t → γ_prior, β_prior (frozen)

  γ = γ_prior ⊙ γ_task
  β = γ_prior ⊙ β_task + β_prior

  C5_mod = γ ⊙ C5 + β

BiGRU + Classification:
  C5_mod[0:8] → BiGRU → activity prediction
```

**Expected benefit**: +2-4% accuracy from better pose representation (less overfitting on 254 videos).

## References

- Reilly et al. (2024). "Just Add π: Discovering Motion Prior for Action Recognition." WACV 2024. arXiv:2311.18840
