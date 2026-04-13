---
title: Assembly101
type: entity
status: active
tags: [popw, dataset, computer-vision, multi-task, action-recognition, 3d-pose]
created: 2026-04-13
updated: 2026-04-13
summary: Assembly101 is a large-scale video dataset for human assembly activity understanding with 3D pose annotations, 51 object classes, and 133 atomic action classes. It covers 14 unique assembly procedures from a variety of construction toys and household items.
wikilinks:
  - [[projects/popw-research]]
  - [[entities/ikea-asm]]
  - [[entities/ha4m]]
confidence: high
source: research
project: popw
---

# Assembly101

## TL;DR

Assembly101 is a large-scale video dataset for assembly activity understanding, featuring synchronized multi-view RGB, 3D body pose (25 SMPL joints), 51 object classes, and 133 atomic action classes across 14 assembly procedures. It is used as a complementary benchmark to IKEA ASM for POPW multi-task learning validation.

## Overview

Assembly101 was created to address the need for **fine-grained, temporally precise** activity recognition in assembly contexts. Unlike older datasets that label entire videos, Assembly101 provides:

- **Frame-level atomic action labels** (133 classes): "rotate-left", "insert-peg", "align-edge", etc.
- **3D body pose** via SMPL model fitting (25 joints per frame)
- **Multi-object tracking** with 51 distinct object classes
- **14 assembly procedures**: LEGO Technic, Playmobil, IKEA furniture, household items
- **Multi-view capture**: 4 GoPro cameras at different angles plus RGB-D

The 14 assembly procedures each have 20–30 videos, with 2–5 actors per procedure. Total duration: ~120 hours of annotated video.

## Comparison with IKEA ASM

| Feature | Assembly101 | IKEA ASM |
|---------|-------------|----------|
| 3D pose | SMPL 25-joint | 3D direct (but fewer joints) |
| Object classes | 51 | 40 (part-level) |
| Action classes | 133 | 33 |
| Camera views | Multi-view (4 GoPros) | Fixed single |
| Assembly procedures | 14 diverse | 40 IKEA items |
| Temporal precision | Frame-level | Segment-level |

## Why It Matters for POPW

Assembly101 provides POPW with:

1. **3D pose validation**: POPW's 2D pose predictions can be validated against Assembly101's 3D SMPL annotations
2. **Larger action taxonomy**: 133 atomic actions vs IKEA ASM's 33 — tests whether POPW's activity head generalizes
3. **Multi-view training**: Enables studying view invariance for POPW's head-mounted camera setup
4. **Object diversity**: 51 classes vs 40 — POPW's 7-class subset is trivially covered

## Key Statistics

| Metric | Value |
|--------|-------|
| Videos | ~1,800 assembly sessions |
| Procedures | 14 assembly types |
| Duration | ~120 hours total |
| 3D pose | 25 SMPL joints per frame |
| Object classes | 51 tracked objects |
| Action taxonomy | 133 atomic actions |
| Camera | 4-view GoPro + RGB-D |

## POPW Usage

POPW's training pipeline uses Assembly101 as:
- **Secondary benchmark** (IKEA ASM is primary)
- **3D pose evaluation** — compare 2D keypoint predictions against projected 3D
- **Cross-dataset generalization test** — train on IKEA ASM, evaluate on Assembly101 to check domain shift sensitivity

## Related

- [[projects/popw-research]]
- [[entities/ikea-asm]]
- [[entities/ha4m]]
- [[entities/industreal]]
