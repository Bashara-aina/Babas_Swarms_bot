---
title: "ADR-2026-03: PDD Pivot — Remove Neural Detection Head"
type: decision
status: active
tags: [popw, pdd, architecture, detection, pose-derived, pivot]
created: 2026-04-13
updated: 2026-04-13
summary: Architectural decision to remove the neural Detection Head from WorkerNet and replace it with Pose-Derived Detection (PDD) — mathematically computing bounding boxes from skeleton keypoints. This eliminates the "lazy optimization" problem where the network ignored detection gradients in favor of activity gradients.
wikilinks:
  - [[projects/popw-research]]
  - [[concepts/pose-derived-detection]]
  - [[concepts/wise-iou]]
  - [[concepts/multi-task-learning]]
confidence: high
source: research
project: popw
---

# ADR-2026-03: PDD Pivot — Remove Neural Detection Head

## Status

Accepted: March–April 2026
Supersedes: Earlier decision to use Wise-IoU for neural detection

## Context

After training WorkerNet with FiLM + Wise-IoU for 200+ epochs, training logs revealed a critical pattern:

| Epoch | Detection IoU | Activity Accuracy | Observation |
|-------|-------------|-----------------|-------------|
| 51 | **0.51** | ~80% | Peak detection performance |
| 200+ | 0.33 | **95.2%** | Detection degraded, activity dominated |

The network had discovered that **pose alone achieves 95% activity accuracy** — high-IoU bounding boxes were not helping activity recognition. The backbone stopped updating detection weights, treating the detection head as an "orphan" receiving weak, conflicting gradients.

The root cause: **gradient direction conflict**. Activity gradients and detection gradients pushed the backbone in different directions. Since activity was easier to learn (pose features carry most of the signal), the network optimized for activity and ignored detection.

## Decision

**Remove the neural Detection Head entirely. Derive bounding boxes mathematically from pose keypoints.**

### Worker Box (PDD)

Instead of predicting a worker bounding box, compute it from 17 COCO keypoints:

```
x_min = min(keypoints.x) − δ
x_max = max(keypoints.x) + δ
y_min = min(keypoints.y) − δ
y_max = max(keypoints.y) + δ

Box_worker = [x_min, y_min, x_max, y_max]  # with safety padding δ
```

Since Pose PCK is 78.1%, keypoints are mathematically guaranteed to be on the person. IoU becomes a function of pose accuracy.

### Bottle Box (PDD)

```
K_wrist = (x_w, y_w)  # wrist keypoint
r = fixed_bottle_radius  # in pixels (industrial calibration)

Box_bottle = [x_w − r, y_w − r, x_w + r, y_w + r]
```

**Industrial logic**: We only care about bottles in hands, not bottles on shelves. If holding a bottle, it's at the wrist.

## Consequences

### Positive
- **O(1) verification**: No neural network uncertainty in detection — math is deterministic
- **Eliminates gradient conflict**: Detection is now a function of pose, not a competing head
- **Interpretable**: Box = keypoint math, not black-box prediction
- **Faster training**: One less head to train
- **Better activity accuracy**: Backbone freed from conflicting detection gradients

### Negative
- **No novel object detection**: PDD only detects pose-anchored objects (wrist)
- **Fixed bottle radius**: Requires industrial calibration per object class
- **Pose accuracy = detection accuracy**: If pose fails, detection fails

## Alternatives Considered

| Alternative | Why Rejected |
|-----------|-------------|
| Keep Wise-IoU detection, tune harder | Lazy optimization persists — network still ignores detection |
| Separate detection backbone | Defeats multi-task efficiency goal |
| Attention mechanism for detection | Computational overhead; pose still sufficient for activity |
| **PDD (chosen)** | Mathematically sound for wrist-anchored industrial objects |

## Related

- [[concepts/pose-derived-detection]]
- [[concepts/wise-iou]]
- [[concepts/multi-task-learning]]
- [[projects/popw-research]]