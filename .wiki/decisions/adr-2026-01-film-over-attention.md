---
title: "ADR-2026-01: FiLM Modulation Over Attention"
type: decision
status: active
tags: [popw, film, attention, architecture, pose-conditioning, feature-modulation]
created: 2026-04-13
updated: 2026-04-13
summary: Architectural decision to use FiLM (Feature-wise Linear Modulation) instead of attention mechanisms for pose-conditioned activity recognition. FiLM achieves pose-guided feature attention at O(d) computational cost vs attention's O(n²d), with results showing +4.2% activity accuracy improvement.
wikilinks:
  - [[projects/popw-research]]
  - [[concepts/film-modulation]]
  - [[concepts/multi-task-learning]]
confidence: high
source: research
project: popw
---

# ADR-2026-01: FiLM Modulation Over Attention

## Status

Accepted: January 2026
Reviewed: April 2026 (still valid post-PDD pivot)

## Context

POPW's activity head must recognize 33 atomic assembly actions. Visual features alone are ambiguous — raised wrist could mean "checking bottle" or "adjusting grip." Pose context provides the disambiguation: raised right wrist + bottle nearby = checking.

The question: **how to inject pose context into the activity classifier?**

Options considered:
1. **Attention mechanism**: Query-key-value modulation of visual features by pose
2. **FiLM modulation**: Affine rescaling of visual feature channels by pose-generated parameters
3. **Feature concatenation**: Append pose features to visual features before classification

## Decision

**Use FiLM (Feature-wise Linear Modulation) for pose-conditioned activity recognition.**

### FiLM Mechanism

```
F'_channel = γ_channel(z_pose) × F_old + β_channel(z_pose)
```

Where:
- `F_old` = original CNN feature at a spatial location
- `z_pose` = 64-dimensional pose context from MLP encoder
- `γ(z), β(z)` = learned affine parameters ∈ R^256

Implementation:
```python
# Pose encoder: 13 joints × 3 coords = 39 → 128 → 64
z_pose = MLP(keypoints)  # R^64

# FiLM generator: 64 → (γ, β) ∈ R^256
γ, β = FiLM_generator(z_pose)

# Modulation: per-channel affine transform on P3 features
F_modulated = γ.unsqueeze(-1) × F_p3 + β.unsqueeze(-1)
```

## Why Not Attention?

| Mechanism | Operation | Compute | POPW Use Case |
|-----------|-----------|---------|---------------|
| Self-Attention | Q×K^T×V matrix mult | O(n²d) | Content-based selection |
| FiLM | γ×F + β (per channel) | O(d) | Feature recalibration |

Attention's strengths (content-based selection, variable sequence length) are unnecessary for POSITION-FIXED spatial features. The skeleton "spotlight" metaphor: we want to amplify hand-related feature channels, not select which spatial locations to attend to.

## Consequences

### Positive
- **Zero attention overhead**: Only O(d) multiply-add per channel vs O(n²d)
- **Pose-encoded structurally**: γ, β are deterministic functions of keypoints — no learned attention weights needed
- **Interpretable**: γ amplitude = channel importance; β baseline = default activation
- **Works with FPN**: Modulates any feature pyramid level without architectural change

### Negative
- **No spatial attention**: FiLM is channel-wise only — doesn't select which spatial locations to attend to
- **Requires meaningful channel structure**: Benefits from CNN channels that already encode semantically meaningful features

## Results

FiLM + Kendall (vs baseline Kendall without FiLM):
- **Activity Accuracy**: 91% → 95.2% (+4.2%)
- **Pose PCK**: 75% → 78.1% (+3.1%)
- **Detection IoU**: 0.27 → 0.51 initially (later dropped due to lazy optimization)

## Alternatives Considered

| Alternative | Why Rejected |
|-----------|-------------|
| Self-Attention QKV | O(n²d) overhead; n is spatial pixels (thousands) |
| Cross-attention pose→visual | Same overhead; pose has only 13×3=39 dims |
| Feature concatenation | Requires larger classification head; pose/visual not interactively modulated |
| **FiLM (chosen)** | Minimal compute, structured pose injection |

## Related

- [[concepts/film-modulation]]
- [[concepts/multi-task-learning]]
- [[projects/popw-research]]
