---
title: IKEA ASM (Assembly Simulation Model)
type: entity
status: active
tags: [popw, dataset, computer-vision, multi-task, pose-estimation, furniture-assembly]
created: 2026-04-13
updated: 2026-04-13
summary: IKEA ASM is a large-scale video dataset of people assembling IKEA furniture, used as a primary benchmark for POPW's multi-task learning architecture (detection + pose + activity recognition). It provides synchronized RGB frames, 2D/3D keypoints, and atomic action annotations across 40+ furniture types.
wikilinks:
  - [[projects/popw-research]]
  - [[entities/assembly101]]
  - [[entities/ego-exo4d]]
confidence: high
source: research
project: popw
---

# IKEA ASM (Assembly Simulation Model)

## TL;DR

IKEA ASM is a large-scale benchmark dataset for understanding furniture assembly from video — the primary validation environment for POPW's multi-task architecture. It provides synchronized RGB video, 2D/3D pose keypoints, object bounding boxes, and atomic action labels across 40 IKEA furniture types and 900+ assembly videos.

## Overview

IKEA ASM was developed to bridge the gap between static object recognition and complex human activity understanding in procedural tasks. Unlike action recognition datasets that label entire videos with a single class, IKEA ASM annotates at the **frame level** with:

- **17 COCO-style body keypoints** (per person per frame)
- **Object bounding boxes** (the furniture parts being manipulated)
- **Atomic action labels** from a 33-class taxonomy (rotate, attach, align, hold, reach, etc.)
- **Temporal boundaries** marking when each atomic action begins and ends
- **Assembly stage labels** (0–100% completion)

The dataset has ~900 videos across 40 furniture types, averaging 2–4 minutes each, with 9 actors performing multiple assembly sessions per item. Camera is static, positioned at ~45° viewing angle to capture both the worker's body and the parts being assembled.

## Why It Matters for POPW

POPW uses IKEA ASM as its **primary training and evaluation benchmark**. The dataset's value proposition:

1. **Multi-modal annotations** enable joint training of detection + pose + activity (the POPW three-head architecture)
2. **Procedural structure** means activity labels aren't ambiguous — a "rotate" action has unambiguous visual signatures in body pose and object displacement
3. **Egocentric-adjacent camera angle** bridges the gap between POPW's industrial head-mounted camera setup and the dataset's third-person captures

The 7 object classes in POPW (bottle, cap, screw, bracket, shelf, board, tool) are **not** from IKEA ASM directly — they're object categories that appear across multiple industrial assembly datasets including IKEA ASM, Assembly101, and custom industrial video.

## Key Statistics

| Metric | Value |
|--------|-------|
| Videos | 900+ assembly sessions |
| Furniture types | 40+ IKEA items |
| Duration | 2–4 min per video |
| Keypoint annotation | 17 COCO keypoints per person |
| Action taxonomy | 33 atomic actions |
| Camera angle | Fixed 45° workstation view |
| Actors | 9 unique performers |

## Integration with POPW

POPW's WorkerNet architecture trains on IKEA ASM as follows:

1. **Backbone**: ResNet-50 pretrained on ImageNet, frozen first 20 epochs
2. **Neck**: FPN (P3–P7 feature pyramids) for multi-scale detection
3. **Pose Head**: Predicts 17 COCO keypoints per frame
4. **Activity Head**: Predicts 33-class atomic action at video-fragment level
5. **Detection Head**: Predicts bounding boxes for 40 IKEA object part classes (later replaced by PDD)

Training showed:
- Pose PCK@0.5: 78.1% on IKEA ASM test set
- Activity Accuracy: 95.2% on 33-class atomic actions
- Detection IoU: 0.51 initially, later dropped (led to PDD pivot)

## Alternatives Considered

| Dataset | Strength | Weakness for POPW |
|---------|---------|-------------------|
| **Assembly101** | More object classes, 3D pose | Less pose annotation detail |
| **HA4M** | 4M samples, industrial setting | No public release |
| **IndustReal** | Real industrial parts | Limited activity labels |
| **Ego-Exo4D** | Egocentric video, large scale | Post-hoc pose annotation |
| **IKEA ASM** | Synchronized all modalities | Camera angle differs from head-mounted |

## Related

- [[projects/popw-research]]
- [[entities/assembly101]]
- [[entities/ha4m]]
- [[entities/industreal]]
- [[entities/ego-exo4d]]
