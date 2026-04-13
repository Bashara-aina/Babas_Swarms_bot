---
title: FiLM Modulation — Feature-wise Linear Modulation
type: concept
status: active
tags: [popw, film, feature-modulation, computer-vision, pose-conditioning]
created: 2026-04-13
updated: 2026-04-13
summary: FiLM (Feature-wise Linear Modulation) is a pose-conditioned feature modulation technique where pose keypoints generate affine parameters (γ, β) that dynamically rescale and shift CNN feature channels, enabling skeletal structure to attentionivate visual features without attention computational overhead.
wikilinks:
  - [[concepts/pose-derived-detection]]
  - [[concepts/multi-task-learning]]
  - [[projects/popw-research]]
confidence: high
source: research
project: popw
---

# FiLM Modulation — Feature-wise Linear Modulation

## TL;DR

FiLM modulates CNN features by generating scale (γ) and shift (β) parameters from pose keypoints. Unlike attention mechanisms, FiLM has zero additional computational cost — it simply rescales feature channels, yet achieves SOTA activity recognition by forcing the model to "look where the skeleton points."

## The Core Equation

```
F'_channel = γ_channel × F_old + β_channel
```

Where:
- `F_old` = original CNN feature at a spatial location
- `γ(z)` = learned scale factor from pose context z (range 0.0–5.0)
- `β(z)` = learned bias from pose context z

## Why It Works

### The "Spotlight" Metaphor

When the Pose Encoder detects a "raised right wrist" pose:
1. It generates γ_hand_channel = 2.5 (amplify hand-related features)
2. It generates β_hand_channel = 0.8 (boost baseline signal)
3. The CNN's hand-detecting feature channels become 3x brighter numerically
4. The Activity Head effectively sees a "spotlight" on where the action is

Instead of the neural network having to *learn* that hands are important, **mathematics forces the connection**.

### Comparison with Attention

| Mechanism | Operation | Compute Cost | Effect |
|----------|-----------|-------------|--------|
| Self-Attention | Query×Key×Value matrix mult | O(n²d) | Content-based selection |
| FiLM | γ×F + β (per channel) | O(d) | Feature recalibration |
| **FiLM advantage** | | **100x cheaper** | **Pose-guided focus** |

## Implementation in WorkerNet

### Pose Encoder (MLP)
```python
# Input: 13 joints × 3 coords (x, y, visibility) = 39 values
# Stage 1: Expansion 39 → 128
# Stage 2: Compression 128 → 64 (pose context z)
z_pose = MLP(keypoints)  # → R^64
```

### FiLM Generator
```python
# From 64-dim pose context, generate γ and β for each of 256 FPN channels
γ, β = FiLM_generator(z_pose)  # γ, β ∈ R^256
```

### Modulation
```python
# Apply to P3 feature map (256 × H × W)
F_modulated = γ.unsqueeze(-1) × F_p3 + β.unsqueeze(-1)
```

## Results

FiLM + Kendall Loss (vs baseline Kendall without FiLM):
- **Activity Accuracy**: 91% → 95.2% (+4.2%)
- **Pose PCK**: 75% → 78.1% (+3.1%)
- **Detection IoU**: 0.27 → 0.51 initially, later dropped to 0.33 (leading to PDD pivot)

## The γ-only vs β-only Question

Ablation question: Is scale (γ) or shift (β) more important?
- γ controls **amplitude** — how strong a feature channel fires
- β controls **baseline** — the default activation level

Planned ablation study to determine which component carries the pose-conditioning signal.

## Related

- [[concepts/pose-derived-detection]]
- [[concepts/multi-task-learning]]
- [[projects/popw-research]]
