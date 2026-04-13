---
title: POPW Research Meetings — Phase 1 (Nov–Dec 2025)
type: timeline
status: active
tags: [popw, research, meetings, sequential-training, yolov8, kendall-loss]
created: 2026-04-13
updated: 2026-04-13
summary: First phase of POPW weekly research meetings covering the transition from sequential single-task models to unified WorkerNet architecture, baseline establishment, and early multi-task loss experiments (Kendall uncertainty weighting).
wikilinks:
  - [[projects/popw-research]]
  - [[timelines/popw-meetings-jan-mar-2026]]
  - [[timelines/popw-meetings-mar-apr-2026]]
  - [[concepts/kendall-loss]]
confidence: high
source: research
project: popw
---

# POPW Research Meetings — Phase 1 (Nov–Dec 2025)

## TL;DR

Phase 1 of POPW research meetings established the foundational architecture: sequential training of detection, pose, and activity heads, then a pivot to unified WorkerNet with shared ResNet-50+FPN backbone. Early experiments used Kendall uncertainty weighting for multi-task loss balancing, achieving 96.77% PCK@0.1, 62.96% IoU, and 72.73% activity accuracy on baseline.

## 4th Meeting — November 11, 2025

**Architecture Decision**: Sequential → Unified WorkerNet

Initial experiments trained separate YOLOv8 models for detection (Bottle, Barcode, People) and pose keypoint models. Meeting 4 established the unified WorkerNet direction: a single model with shared backbone and three parallel heads.

Key decisions:
- Adopt ResNet-50+FPN backbone (ImageNet pretrained)
- 17 COCO keypoints: nose, eyes, ears, shoulders, elbows, wrists, hips, knees, ankles
- 7 object classes: bottle, cap, screw, bracket, shelf, board, tool
- Focus on finishing prototype for conference submission

Research goal clarified: count completed assembly cycles (Storing events) by verifying bottle + cap + correct pose sequence.

## 5th Meeting — November 25, 2025

**Progress**: WorkerNet base architecture implementation, data statistics analyzer, multi-scale pose head (P3 for face, P4 for body).

Clean dataset prepared: 485 train, 88 val, 90 test samples.

## 6th Meeting — December 2, 2025

**Training results**: Baseline model trained (300 epochs). Geometric loss removal discovered as key improvement — geometric loss terms were actually hurting performance.

4 configurations trained:
- ref_standard: baseline with geometric loss
- ablation_no_geom: without geometric loss
- curiosity_high_geom: with curiosity-driven geometry
- curiosity_high_pck: PCK-optimized variant

**Key finding**: Geometric loss removal improves performance by 9–11%. Geometric terms interfere with pose learning.

## 7th Meeting — December 9, 2025

**Late Fusion Architecture**: Established that activity head performs better with late fusion — pose features and visual features combined at the activity classification stage rather than shared earlier.

Late fusion enables pose features to directly inform activity classification without polluting the shared backbone.

## Research Arc: Phase 1

```
Nov 2025: Sequential models → Unified WorkerNet
Nov 2025: Baseline training 300 epochs
Dec 2025: Kendall uncertainty weighting for multi-task loss
Dec 2025: Geometric loss removal discovered as +9-11% improvement
Dec 2025: Late fusion architecture for pose-activity
```

## Key Findings from Phase 1

| Discovery | Impact |
|-----------|--------|
| Geometric loss hurts training | Remove → +9-11% accuracy |
| Late fusion > early fusion | Better pose-activity coupling |
| Kendall σ² balancing | Automatic task weighting, but gradient direction problem remains |
| Sequential → Unified pivot | Single backbone, 3 heads |

## Current Status (End of Phase 1)

WorkerNet baseline established with:
- Detection IoU: 62.96%
- Pose PCK@0.1: 96.77% (too high — likely overfitting on small dataset)
- Activity Accuracy: 72.73%

The architecture was functional but not yet optimized — Phase 2 focused on Wise-IoU, FiLM, and the detection degradation problem.

## Related

- [[projects/popw-research]]
- [[timelines/popw-meetings-jan-mar-2026]]
- [[timelines/popw-meetings-mar-apr-2026]]
- [[concepts/kendall-loss]]
- [[concepts/wise-iou]]
- [[concepts/multi-task-learning]]
