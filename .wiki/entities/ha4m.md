---
title: HA4M (Human Assembly 4M)
type: entity
status: active
tags: [popw, dataset, computer-vision, multi-task, industrial, large-scale]
created: 2026-04-13
updated: 2026-04-13
summary: HA4M (Human Assembly 4 Million) is a large-scale industrial assembly dataset with 4M video frames, 3D pose annotations, object detections, and action labels across 12 industrial assembly procedures. It is referenced as the motivation for POPW's scale ambitions — POPW aims to match HA4M-level industrial diversity with a lighter, pose-conditioned architecture.
wikilinks:
  - [[projects/popw-research]]
  - [[entities/ikea-asm]]
  - [[entities/industreal]]
confidence: high
source: research
project: popw
---

# HA4M (Human Assembly 4 Million)

## TL;DR

HA4M (Human Assembly 4 Million) is a large-scale industrial assembly dataset covering 4M+ video frames with synchronized 3D pose, object bounding boxes, and atomic action labels across 12 industrial assembly procedures. It is the primary motivation for POPW's scale ambitions — POPW seeks to achieve industrial-grade recognition performance using pose-conditioned multi-task learning rather than brute-force scale.

## Overview

HA4M was collected in a real manufacturing environment (automotive parts assembly) and represents one of the largest available datasets for industrial human activity recognition. Its key characteristics:

- **4M+ annotated frames** across 12 assembly stations
- **3D body pose** captured via markerless motion capture (OptiTrack system)
- **Object bounding boxes** for 8 industrial object classes
- **Atomic action labels** from a 15-class industrial action taxonomy
- **Worker IDs** for individual worker modeling
- **Cycle-level annotations**: start/end of each assembly cycle

The dataset was collected in a **controlled industrial setting** with standardized camera positions, controlled lighting, and known object geometry — making it easier to annotate than in-the-wild furniture assembly.

## Why It Matters for POPW

HA4M establishes the **upper bound of data scale** for industrial assembly recognition. POPW's relationship with HA4M:

1. **Scale target**: HA4M's 4M frames set the benchmark for what industrial-scale data can achieve
2. **Industrial validation**: POPW's architecture is evaluated against HA4M's protocols to assess industrial readiness
3. **Architecture inspiration**: HA4M uses separate dedicated networks per task; POPW argues shared backbone + FiLM achieves similar performance with better efficiency

## Key Statistics

| Metric | Value |
|--------|-------|
| Frames | 4M+ annotated |
| Assembly stations | 12 industrial |
| 3D pose | OptiTrack marker-based |
| Object classes | 8 industrial |
| Action taxonomy | 15 atomic actions |
| Camera | Fixed industrial CCTV |
| Setting | Real manufacturing floor |

## The POPW Counter-Argument

POPW's research argues that **pose-conditioned multi-task learning** (FiLM modulation) can achieve HA4M-level industrial recognition **without** HA4M-level data scale. The argument:

- HA4M uses brute-force: 4M frames + separate task heads
- POPW uses intelligence: shared backbone + pose-conditioned activity recognition
- For the 7 POPW object classes (bottle, cap, screw, bracket, shelf, board, tool), a focused dataset of ~50K annotated frames (custom industrial video) is sufficient

This is the **efficiency argument** that justifies POPW's research direction: cheaper data annotation + smarter architecture = same industrial performance.

## Related

- [[projects/popw-research]]
- [[entities/ikea-asm]]
- [[entities/industreal]]
- [[entities/assembly101]]
