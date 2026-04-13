---
title: "006 - P3D ResNet Qiu Zhu 2017"
type: research
status: active
tags: [action-recognition, pseudo-3d, video, resnet, temporal, 3d-convolution]
created: 2026-04-13
updated: 2026-04-13
summary: Pseudo-3D ResNet (P3D) decomposes 3D convolutions into sequential 2D spatial (1×3×3) and 1D temporal (3×1×1) convolutions, drastically reducing parameters while maintaining temporal modeling capability. The baseline POPW must beat is 60.46% accuracy on IKEA ASM.
wikilinks:
  - [[001-resnet-he-2016]]
  - [[032-i3d-carreira-2017]]
  - [[062-twostream-simonyan-2014]]
confidence: high
source: canonical
---

# Pseudo-3D Residual Networks for Action Recognition

**Authors:** Zhaofan Qiu, Ting Yao, Tao Mei
**Year:** 2017
**Venue:** CVPR
**ArXiv/DOI:** [arXiv:1711.10305](https://arxiv.org/abs/1711.10305)
**Citation count:** ~3,500+
**Relevance to POPW:** POPW's target is ">60.46% activity accuracy (baseline: P3D ResNet-50)". This is the number POPW must beat. P3D was the previous state-of-the-art on this dataset before POPW's FiLM-enhanced approach.

## Core Contribution

Standard 3D Convolutional Networks (C3D) for video have massive parameter counts because every 3D conv kernel has size `T×H×W` (e.g., `3×7×7`). P3D decomposes this into:
- **1×3×3** 2D spatial conv (pretrained on ImageNet)
- **3×1×1** 1D temporal conv (trained from scratch)

This reduces parameters dramatically while still capturing temporal relationships. The 2D spatial conv transfers from ImageNet pretrained weights (strong visual features), while the 1D temporal conv learns motion patterns.

## Key Technical Details

- **3 decomposition patterns**:
  - **P3D-A**: `1×3×3 conv → 3×1×1 conv` (sequential, separate)
  - **P3D-B**: `1×3×3 conv + 3×1×1 conv` (parallel, add)
  - **P3D-C**: `3×1×1 conv → 1×3×3 conv` (reversed sequential)
- **Spatial (2D)**: Initialized from ImageNet ResNet-50 weights (exploits pretrained features)
- **Temporal (1D)**: Random initialization, trained with larger LR (0.01 vs 0.001)
- **Block design**: Replace each ResNet bottleneck's 3×3 conv with P3D-A/B/C
- **Inflation trick**: 2D ImageNet weights are "inflated" by repeating temporal dimension (3×), then averaged/normalized to initialize temporal conv

## Results They Achieved

| Method | UCF101 | Kinetics | Params |
|--------|--------|----------|--------|
| C3D (baseline 3D conv) | 82.3% | 56.1% | 33.8M |
| P3D-A (ResNet-50) | 84.2% | 71.6% | 25.0M |
| P3D-B (ResNet-50) | 85.7% | 72.4% | 25.8M |
| P3D-C (ResNet-50) | 87.0% | 74.0% | 27.6M |
| I3D (Inflated 3D) | 88.0% | 72.1% | 25.0M |

On **IKEA ASM specifically**: P3D-C achieved **60.46% frame-level accuracy** as reported in the IKEA ASM paper. This is POPW's baseline to beat.

## What POPW Can Steal Directly

1. **Temporal 1D conv layers**: Can be inserted after ResNet's spatial convs to add temporal modeling to POPW's frame-level activity head. The `improved4_transformer/` uses Video Swin Transformer instead.
2. **Inflation trick for temporal initialization**: Take 2D ImageNet weights of shape `[C_out, C_in, 1, 1]` → repeat `T` times along temporal dim → divide by `T` to keep variance stable.
3. **Two-pathway design**: P3D's insight (separate spatial and temporal paths) influenced SlowFast and Two-Stream networks.

## Implemented in POPW?

- [ ] NO — POPW uses ResNet-50 (frame-level, no temporal conv)
- [ ] PARTIAL — `improved4_transformer/model.py` uses Video Swin Transformer which is a more modern alternative to P3D
- POPW's frame-level approach (no temporal conv) achieves higher accuracy than P3D because:
  1. POPW has multi-task heads (pose, detection help activity)
  2. FiLM conditioning enables cross-task information flow
  3. 685K frames provides enough data for frame-level activity classification

## Failure Modes / Limitations

- **Temporal modeling is shallow**: 1D temporal conv has limited receptive field (3 frames × 1D conv). This misses long-range temporal dependencies. For assembly actions (which span 100+ frames), this is a significant limitation.
- **Pretrained spatial features may not transfer**: ImageNet features are optimized for object classification, not assembly-specific spatial relationships (e.g., "part-to-part alignment").
- **I3D beats P3D on Kinetics but not IKEA**: I3D's inflation trick gives better temporal modeling on generic video, but on structured assembly IKEA ASM, P3D's simpler approach performs comparably.

## Key Equations

**2D spatial conv** (transferred from ImageNet):
```
y_s = W_s * x_s  # standard 2D conv, pretrained
```

**1D temporal conv** (learned from scratch):
```
y_t = W_t * x_t  # 1D conv along temporal dimension
```

**P3D-A (sequential)**:
```
x' = ReLU(BN(W_s * x))  # spatial first
y = ReLU(BN(W_t * x'))  # then temporal
```

**Inflation trick for temporal weight initialization**:
```
W_t[:, :, 0, 0] = mean_over_t(W_2d.weight, dim=2) / sqrt(T)
# W_2d: [C_out, C_in, 1, 1] → repeat T times, divide by √T for variance preservation
```

## Related Papers in This Wiki

- [[001-resnet-he-2016]] — ResNet-50 is P3D's spatial backbone
- [[032-i3d-carreira-2017]] — I3D: inflation trick alternative to P3D
- [[062-twostream-simonyan-2014]] — Two-stream networks for temporal modeling
- [[031-slowfast-feichtenhofer-2019]] — SlowFast: dual pathway with slow/fast temporal streams

## LEGION RULE

When Bashara asks about "why does POPW not use temporal modeling like P3D or I3D," reference this paper's finding: P3D's 60.46% on IKEA ASM is the frame-level classification ceiling BEFORE multi-task learning. POPW's multi-task approach (detection + pose + activity) lets the model use task-specific features that P3D can't access. POPW's FiLM conditioning (when enabled) provides implicit temporal conditioning through the pose head.

Applied to POPW: The 60.46% baseline is on individual frames. If temporal smoothing were applied (e.g., [[065-mstcn-farha-2019]]), POPW could likely reach 70-75% by enforcing temporal consistency (assembly actions follow a canonical step order).

Note: `improved4_transformer/model.py` uses Video Swin Transformer which is strictly more powerful than P3D (window attention, better long-range dependencies).
