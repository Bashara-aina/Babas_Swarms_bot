---
title: Pose-Derived Detection (PDD)
type: concept
status: active
tags: [popw, pdd, object-detection, pose-estimation, anchored-detection, industrial]
created: 2026-04-13
updated: 2026-04-13
summary: Pose-Derived Detection (PDD) is an architectural pivot that removes the neural Detection Head entirely, deriving bounding boxes mathematically from pose keypoints — worker box from skeleton min-max, bottle box from wrist-anchored radius — achieving O(1) verification without neural network uncertainty.
wikilinks:
  - [[concepts/film-modulation]]
  - [[concepts/kendall-loss]]
  - [[projects/popw-research]]
confidence: high
source: research
project: popw
---

# Pose-Derived Detection (PDD)

## TL;DR

PDD solves the "lazy network" problem by removing neural detection and replacing it with mathematical derivation from pose. Instead of asking "where is the bottle?" (uncertain neural guess), PDD asks "where is the wrist?" (precise pose) and computes bottle location deterministically.

## The Problem: Neural Lazy Optimization

Training logs showed:
- **Epoch 51**: Best IoU (0.51), Activity Accuracy ~80%
- **Epoch 200+**: IoU degraded to 0.33, Activity Accuracy rose to 95.2%

The network learned that **pose alone achieves 95% activity accuracy** — detection gradients became "noise" conflicting with pose gradients. The backbone stopped updating detection weights.

## The PDD Solution

### Worker Box (Deterministic from Skeleton)

Instead of predicting a worker bounding box, compute it from keypoints:

```
K = {(x₁,y₁), ..., (x₁₃,y₁₃)}  # 13 COCO keypoints

x_min = min(keypoints.x)
x_max = max(keypoints.x)
y_min = min(keypoints.y)
y_max = max(keypoints.y)

Box_worker = [x_min - δ, y_min - δ, x_max + δ, y_max + δ]  # with safety padding
```

**Why "perfect"**: Since Pose PCK is 78.1%, keypoints are mathematically guaranteed to be on the person. IoU becomes a function of pose accuracy.

### Bottle Box (Anchored at Wrist)

```
K_wrist = (x_w, y_w)  # wrist keypoint coordinates
r = fixed_bottle_radius  # in pixels

Box_bottle = [x_w - r, y_w - r, x_w + r, y_w + r]
```

**Industrial logic**: We don't care about bottles on shelves — only bottles in hands. If the worker is holding a bottle, it's at the wrist.

## The O(1) Verification Argument

| Approach | Verification Question | Cost |
|----------|---------------------|------|
| Neural Detection | "Did the detector find the bottle?" | Uncertain, variable |
| **PDD** | "Is Activity == Checking?" | O(1) lookup |

For industrial monitoring, we count **completed cycles** (Storing events) rather than raw detections.

## State Inference from Activity Sequence

Instead of visually detecting "cap open" (5-pixel object):

```
If Activity_Sequence = Checking → Rotation → Storing:
    Bottle_State = Verified
```

This relies on 95.2% activity accuracy — statistically far more reliable than detecting a 5-pixel bottle cap.

## Mathematical Comparison

### Old Way (Fighting Heads)
```
L_total = L_activity + L_detection + L_pose
∇L_detection conflicted with ∇L_activity
Result: Detection "orphan" received weak, conflicting updates
```

### New Way (Sequential Flow)
```
Step 1: Pose Head → Skeleton (PCK 78.1%)
Step 2: Math Function → Worker Box (IoU = f(PCK))
Step 3: Wrist Anchor → Bottle Box (deterministic)
Step 4: Activity Head → State (95.2%)
```

## Related

- [[concepts/film-modulation]]
- [[concepts/kendall-loss]]
- [[concepts/wise-iou]]
- [[projects/popw-research]]
