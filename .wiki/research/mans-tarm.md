---
title: "MANs & TARM: Motion Attention Networks and Temporal Attention Recurrent Module"
created: 2026-04-14
modified: 2026-04-14
tags: [motion-attention, tarm, temporal-attention, skeleton-action, pose-activity, attention-mechanism, recurrent]
authors: [Xie et al.]
type: research
summary: "MANs (Motion Attention Networks) and TARM (Temporal Attention Recurrent Module) by Xie et al. use motion-based attention for skeleton action recognition. Motion attention computes attention weights based on pose velocity — relevant frames get high attention. TARM combines this with recurrent modules for temporal modeling. Foundation for MMN's motion-guided approach."
wikilinks:
  - [[mmn]]
  - [[bigru-temporal-action-recognition]]
  - [[pose-conditioned-temporal-modeling]]
  - [[projects/popw-multi-task-ikea]]
source: https://arxiv.org/abs/1804.08254
---

# MANs & TARM: Motion Attention for Skeleton Action Recognition

## Paper Info
- **arXiv**: [1804.08254](https://arxiv.org/abs/1804.08254)
- **Authors**: Xie et al.
- **Venue**: Pattern Recognition (PR) 2018

## Core Contribution

MANs (Motion Attention Networks) introduce **motion-based attention** for skeleton action recognition. The key insight: relevant frames for action classification are not uniformly distributed — frames with high motion (action transitions) deserve more attention than frames with static pose.

TARM (Temporal Attention Recurrent Module) combines motion attention with recurrent temporal modeling — foundational work that MMN later builds upon.

## Motion Attention Mechanism

```
Skeleton sequence: S = [s_1, s_2, ..., s_T] ∈ R^[T, J, D]
  # J = 17 joints (COCO format), D = 3 (x, y, confidence)

Motion representation:
  m_t = ||s_{t+1} - s_{t-1}||  # motion magnitude at frame t
  # Captures how much the pose is changing

Motion attention weights:
  α_t = softmax(MLP(m_t))  # attention weight for frame t
  # High α = significant motion = important for action
```

**Temporal aggregation with attention**:
```
h_temporal = Σ_t α_t · s_t  # weighted sum of skeleton frames
```

## TARM: Temporal Attention Recurrent Module

TARM extends motion attention with recurrent temporal modeling:

```
Frame t:
  s_t → Motion Encoder → m_t (motion features)
  α_t = softmax(Linear(m_t))  # motion attention

  h_t = GRU(s_t, h_{t-1})  # standard recurrent update

Temporal aggregation:
  H = Σ_t α_t · h_t  # attention-weighted hidden states

  → FC → Activity Classification
```

**Key difference from POPW**:
- POPW uses uniform attention pooling over BiGRU hidden states
- TARM uses motion-based attention weights to weight each hidden state

## Why This Matters for POPW

POPW's BiGRU processes pose-conditioned features uniformly:
```
C5_mod[0:8] → BiGRU → [h_0, h_1, ..., h_7]
  → AttentionPool → activity prediction
```

TARM suggests **motion-weighted attention**:
```
velocity_t = keypoints[t+1] - keypoints[t]
motion_weight_t = softmax(MLP(velocity_t))

H_weighted = Σ_t motion_weight_t · h_t
  → activity prediction
```

**Benefit**: During fast actions (hammer strike), motion weights concentrate on the transition frames. During stable assembly (holding parts), motion weights are more uniform.

## Motion Attention for POPW Enhancement

POPW can adopt motion attention to weight BiGRU outputs:

```
Current POPW:
  H_attention = AttentionPool([h_0, h_1, ..., h_7])
  # Uniform attention over 8 frames

With Motion Attention:
  velocity_t = ||keypoints[t+1] - keypoints[t-1]||  # 17 keypoints
  motion_weight_t = softmax(MLP(velocity_t))
  H_motion = Σ_t motion_weight_t · h_t
  # High weight → frames with significant pose changes
```

## Connection to MMN

MANs/TARM established:
1. Motion can serve as attention weights ✓
2. Motion-guided temporal aggregation ✓
3. Recurrent + attention combination ✓

MMN (Gu et al. 2025) extended this to:
1. Motion-guided feature **modulation** (MSM) not just attention
2. Motion-guided **temporal gating** (MTM) not just aggregation
3. Bidirectional pose↔activity communication

## POPW Ablation Opportunity

A POPW ablation study could test motion attention:

| Variant | Temporal Aggregation | Expected Impact |
|---------|---------------------|-----------------|
| POPW baseline | Uniform attention pool | 73.1% (current) |
| + Motion attention | Motion-weighted pool | +1-2% |
| + MSM (MMN) | Motion-modulated features | +2-3% |
| + MTM (MMN) | Motion-gated temporal | +1-2% |

## References

- Xie et al. (2018). "Motion Attention Networks for Skeleton-based Action Recognition." Pattern Recognition. arXiv:1804.08254
