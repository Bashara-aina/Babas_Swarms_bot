---
title: POPW Research Meetings — Phase 2 (Jan–Mar 2026)
type: timeline
status: active
tags: [popw, research, meetings, wise-iou, film-modulation, detection-degradation]
created: 2026-04-13
updated: 2026-04-13
summary: Second phase covering Wise-IoU replacement for Kendall loss, FiLM modulation experiments, and the critical "lazy optimization" discovery — detection IoU degrading from 0.51 to 0.33 as activity accuracy rose to 95.2%, leading to the PDD pivot decision.
wikilinks:
  - [[projects/popw-research]]
  - [[timelines/popw-meetings-nov-dec-2025]]
  - [[timelines/popw-meetings-mar-apr-2026]]
  - [[concepts/wise-iou]]
  - [[concepts/film-modulation]]
confidence: high
source: research
project: popw
---

# POPW Research Meetings — Phase 2 (Jan–Mar 2026)

## TL;DR

Phase 2 was the most intellectually productive: Wise-IoU replaced Kendall for detection, FiLM modulation boosted activity from 91% to 95.2%, and the "lazy optimization" problem was discovered — the network prioritizes activity over detection because pose alone achieves 95% accuracy. This led directly to the PDD (Pose-Derived Detection) architectural pivot.

## 8th–9th Meetings — December 16–23, 2025

**Wise-IoU Experiments Begin**

Wise-IoU v3 was introduced to replace Kendall loss for bounding box regression. The key insight: Kendall scales gradient magnitude but not direction, meaning outlier samples still push gradients toward wrong solutions. Wise-IoU actively suppresses gradients from anomalous samples using the outlierness metric β = L_IoU/L_IoU_mean.

Results:
- Detection IoU improved: 0.27 (Kendall) → 0.51 (Wise-IoU)
- Activity accuracy held at ~91%

## 10th Meeting — January 13, 2026

**FiLM Modulation Integration**

Pose-conditioned feature modulation (FiLM) was added to the architecture:
- Pose encoder (MLP: 39→128→64 dims) generates γ, β parameters
- γ, β modulate 256 FPN channels via F' = γ×F + β
- No attention computational overhead — O(d) vs attention's O(n²d)

FiLM results:
- Activity Accuracy: 91% → 95.2% (+4.2%)
- Pose PCK: 75% → 78.1% (+3.1%)
- Detection IoU: 0.27 → 0.51 initially, later dropped to 0.33

## 11th Meeting — January 27, 2026

**Late Fusion Architecture Finalized**

Stable late fusion pipeline established:
1. Backbone + FPN: Extract multi-scale visual features
2. Pose Head: 17 COCO keypoints → pose context z (64-dim)
3. FiLM modulation: γ, β from z rescale FPN channels
4. Activity Head: GAP over modulated features → 33-class classification

**Geometric Analysis**: Bottle position derived from wrist keypoint:

```
μ = (1/N) × Σᵢ [(xbottle − xwrist), (ybottle − ywrist)] / Ltorso
Bbottle = wrist_anchor ± W/2, H/2 (based on μ and checking_left/storing flags)
```

## 12th Meeting — March 15, 2026

**The "Lazy Optimization" Discovery**

After ~200 epochs of training with FiLM + Wise-IoU:
- Epoch 51: Best IoU (0.51), Activity 80%
- Epoch 200+: IoU degraded to 0.33, Activity rose to 95.2%

The network had **correctly** learned that pose alone achieves 95% activity accuracy. High-IoU boxes were not helping activity recognition — they were redundant with pose features. The backbone stopped updating detection weights.

**Critical insight**: Detection head became an "orphan" — receiving weak, conflicting gradients as activity head dominated.

## 13th Meeting — March 25, 2026

**Simultaneous Hypothesis + Class Imbalance**

Key observations:
- Some activities look visually similar without temporal or pose context
- Class imbalance: real industrial distribution (similar to HA4M findings)
- Proposed solution: "simultaneous hypothesis" — force activity head to consume both visual AND pose inputs, reducing reliance on ambiguous visual cues alone

The "1/3 power" comment in meeting notes: the model uses only 1/3 of its capacity because pose features carry most of the activity signal, making visual detection redundant.

## Research Arc: Phase 2

```
Jan 2026: Wise-IoU replaces Kendall for detection
Jan 2026: FiLM modulation added (+4.2% activity)
Jan 2026: Late fusion finalized (pose + visual)
Mar 2026: Lazy optimization discovered (IoU 0.51→0.33)
Mar 2026: PDD pivot conceived — remove detection head
```

## Key Findings from Phase 2

| Discovery | Impact |
|-----------|--------|
| Wise-IoU > Kendall for detection | 0.27 → 0.51 IoU |
| FiLM boosts activity | 91% → 95.2% |
| Lazy optimization | Detection orphaned by activity gradient |
| Pose alone = 95% activity | Detection is redundant |
| Class imbalance in activities | Need temporal/context cues |

## Current Status (End of Phase 2)

FiLM + Wise-IoU architecture achieved 95.2% activity accuracy, but detection was degrading. The architecture was working too well — the network had discovered that pose alone solves activity, making detection unnecessary. This created the intellectual opening for PDD.

## Related

- [[projects/popw-research]]
- [[timelines/popw-meetings-nov-dec-2025]]
- [[timelines/popw-meetings-mar-apr-2026]]
- [[concepts/wise-iou]]
- [[concepts/film-modulation]]
- [[concepts/pose-derived-detection]]
