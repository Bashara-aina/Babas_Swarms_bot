---
title: POPW Research — Point-of-Work Protocol
type: project
status: active
tags: [popw, computer-vision, multi-task-learning, pose-estimation, action-recognition, master's-thesis]
created: 2026-04-13
updated: 2026-04-13
summary: POPW (Point-of-Work Protocol) is a multi-task computer vision system for furniture assembly recognition, detecting 7 object classes, estimating 17 keypoints, and classifying 33 atomic actions from RGB frames using FiLM-modulated pose-conditioned architecture.
wikilinks:
  - [[concepts/multi-task-learning]]
  - [[concepts/film-modulation]]
  - [[concepts/pose-derived-detection]]
  - [[concepts/kendall-loss]]
  - [[concepts/wise-iou]]
  - [[projects/legion-bot]]
confidence: high
source: research
project: popw
---

# POPW Research — Point-of-Work Protocol

## TL;DR

POPW is Bashara's Master's research project developing a multi-task computer vision system for furniture assembly recognition. The system simultaneously performs object detection (7 furniture parts), pose estimation (17 COCO keypoints), and activity classification (33 atomic actions) from single RGB frames, using a novel FiLM-modulated pose-conditioned architecture with Pose-Derived Detection (PDD).

## Research Problem

### Industrial Monitoring Need

The system enables real-time worker assistance, quality control, and process analytics in furniture assembly lines via CCTV:

- **Worker Assistance**: Verify correct assembly steps, proper posture, skill assessment
- **Quality Control**: Detect incorrect assembly steps early, monitor unsafe postures
- **Process Analytics**: Measure step durations, identify bottlenecks
- **Robotics Foundation**: Provide supervision for human-robot collaboration

### Why Multi-Task Learning

| Approach | Limitation |
|----------|-----------|
| Detection only | Knows parts present, not what worker is doing |
| Pose only | Knows body config, not which object is manipulated |
| Action only (raw image) | Relies on misleading visual cues, lacks interpretability |
| **Multi-task (ours)** | Shares backbone, uses pose/parts as structured cues for action |

## Technical Architecture

### Task Definitions

1. **Object Detection**: 7 furniture part classes (table top, leg, shelf, side panel, etc.)
2. **Pose Estimation**: 17 COCO keypoints (nose, eyes, shoulders, elbows, wrists, hips, knees, ankles)
3. **Activity Classification**: 33 atomic actions from IKEA ASM dataset ("pick up leg", "attach shelf", "screw side panel", etc.)

### Core Innovation: FiLM Modulation

```
Feature_new = γ(z_pose) ⊙ Feature_old + β(z_pose)
```

The Pose Encoder (MLP on 13×3 keypoint coordinates → 64-dim context vector) generates γ and β parameters that modulate CNN features, letting skeletal structure dynamically attentionivate visual features.

### Architecture Evolution

| Model | Architecture | Loss | Detection IoU | Pose PCK@0.1 | Activity Acc |
|-------|-------------|------|--------------|--------------|-------------|
| Sequential | YOLOv8→ResNet | CIoU+MSE | xx | xx | xx |
| Unified V1 | Concatenation | Kendall | 0.27 (stuck) | 75% | 91% |
| Unified V2 | FiLM+Sampling | Kendall | 0.51→0.33 | 78.1% | 95.2% |
| **PDD (Ours)** | Pose-Derived | Wise-IoU | Math-guaranteed | 78.1% | 95.2% |

### The PDD Pivot

**Problem**: Neural network "laziness" — model ignored detection gradients to optimize activity accuracy (detection IoU degraded from 0.51→0.33 while activity rose to 95.2%).

**Solution**: Remove Detection Head entirely. Derive boxes mathematically:
- **Worker Box**: Min-max of skeleton keypoints (mathematically guaranteed to contain person)
- **Bottle Box**: Fixed-radius box anchored at wrist keypoint location

**Result**: O(1) verification — instead of uncertain neural detection, verify by activity state lookup.

## Key Findings

1. **Geometric Loss Hurts**: Removing geometric guidance improved activity accuracy by 8% (72.73%→80.68%)
2. **Backbone Freezing Critical**: Frozen first 20 epochs prevents "Gradient Shock" from destroying pretrained features
3. **Multi-Scale Pose Essential**: P3 (stride-8) for face, P4 (stride-16) for body — boosts face PCK from 64.2%→89.1%
4. **Temporal Attention Planned**: Next implementation phase (April 2026)

## Conference Targets

| Conference | Location | Deadline | Focus |
|-----------|----------|----------|-------|
| IEEE FG 2026 | Kyoto, Japan | Jan 15, 2026 | FiLM novelty (CV) |
| IEEE ISIE 2026 | Nagoya, Japan | Jan 31, 2026 | Industrial application |
| IEEE CASE 2026 | Shenyang, China | TBD | System engineering |

## Current Status (April 2026)

- **Architecture**: Complete (WorkerNet with FiLM + PDD)
- **Training**: Ablation studies done, exploring temporal attention
- **Dataset**: IKEA ASM primary, evaluating Assembly101/HA4M/IndustReal alternatives
- **Paper**: Delayed from January target, now targeting mid-2026 venues
- **Next Milestone**: Implement temporal attention, complete ablation training (FiLM vs no-FiLM)

## Related

- [[concepts/multi-task-learning]]
- [[concepts/film-modulation]]
- [[concepts/pose-derived-detection]]
- [[decisions/popw-conference-strategy]]
- [[decisions/popw-pdd-pivot]]
