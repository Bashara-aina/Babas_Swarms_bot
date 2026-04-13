---
title: Multi-Task Learning — Shared Backbone Architecture
type: concept
status: active
tags: [popw, multi-task, shared-backbone, computer-vision, task-balancing]
created: 2026-04-13
updated: 2026-04-13
summary: Multi-task learning trains a single model to perform multiple tasks simultaneously by sharing a CNN backbone and attaching task-specific heads. The challenge is balancing task losses (task interference) and the "lazy optimization" problem where the network ignores tasks that conflict with the dominant gradient signal.
wikilinks:
  - [[concepts/kendall-loss]]
  - [[concepts/wise-iou]]
  - [[concepts/film-modulation]]
  - [[projects/popw-research]]
confidence: high
source: research
project: popw
---

# Multi-Task Learning — Shared Backbone Architecture

## TL;DR

Multi-task learning in WorkerNet shares a ResNet-50+FPN backbone across three heads (Detection, Pose, Activity), forcing the backbone to learn features useful for all tasks. The key challenges are task interference (conflicting gradient directions), gradient magnitude imbalance, and the "lazy optimization" problem where the network ignores tasks with weak gradient signals.

## Why Multi-Task for POPW?

| Single-Task | Limitation | Multi-Task Advantage |
|-------------|-----------|---------------------|
| Detection only | Knows parts, not actions | Share visual features |
| Pose only | Knows body, not objects | Joint pose-object reasoning |
| Activity only | Relies on visual bias | Use structured pose cues |

By sharing one backbone:
- **Feature efficiency**: One forward pass computes features for all tasks
- **Representation richness**: Pose features help activity recognition, detection provides spatial context
- **Interpretability**: Can inspect boxes and keypoints, not just class labels

## Architecture: YOLOv8 Backbone + FPN Neck

```
Input [B,3,480,640]
    ↓
CSPDarkNet-50 Backbone (ImageNet pretrained, BN frozen first 20 epochs)
    ↓
FPN Neck (P3, P4, P5, P6, P7 feature pyramids)
    ↓
    ├── Detection Head (YOLO-style box + class + objectness)
    ├── Pose Head (13 COCO keypoints × 2 coords + visibility)
    └── Activity Head (FiLM-modulated classification)
```

## The Task Interference Problem

### Gradient Direction Conflict

When the Activity Head learns that "raised wrist = checking":
1. Backbone features shift toward pose-relevant visual patterns
2. Detection Head receives **conflicting** gradient signals — the backbone optimized for pose, not boxes
3. Detection IoU degrades (0.51 → 0.33) even as Activity improves

### Task Magnitude Imbalance

| Task | Typical Loss | Gradient Magnitude |
|------|-------------|-------------------|
| Activity (CrossEntropy) | ~0.16 | Moderate, stable |
| Pose (Smooth L1) | ~8.17 | Large, noisy |
| Detection (Wise-IoU) | ~0.29 | Small, sparse |

Without balancing, pose gradients dominate and detection becomes an "orphan head."

## Solutions Explored

### 1. Kendall Uncertainty Weighting

Learns per-task σ to automatically adjust weights. Effective but doesn't fix gradient direction conflict.

### 2. Backbone Freezing (20 Epochs)

Freezes backbone for first 20 epochs, letting heads align before fine-tuning:
- Prevents "Gradient Shock" from random head weights destroying pretrained features
- Allows heads to learn meaningful representations before backbone adjusts

### 3. FiLM Modulation

Pose context directly modulates visual features, making pose information **architecture-encoded** rather than gradient-dependent.

### 4. PDD (Pose-Derived Detection)

Removes the detection head entirely, deriving boxes mathematically from pose — eliminates the conflict by making detection a function of pose.

## The Lazy Optimization Insight

The network is not broken — it's optimizing correctly for activity accuracy. The issue is that **high IoU boxes don't help activity recognition**:

- Epoch 51: Best IoU (0.51), Activity 80%
- Epoch 200+: IoU 0.33, Activity 95.2%

This proves that for activity recognition, pose alone is sufficient. PDD embraces this insight rather than fighting it.

## Related

- [[concepts/kendall-loss]]
- [[concepts/wise-iou]]
- [[concepts/film-modulation]]
- [[concepts/pose-derived-detection]]
- [[projects/popw-research]]
