---
title: Worker Net Architecture Diagram
type: architecture
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- architecture
created: '2026-04-14'
updated: '2026-04-14'
summary: This document references the Draw.io mxGraphModel XML diagram for the POPW
  (Pose-guided Object Detection with Pose) architecture with temporal modeling support.
wikilinks: []
confidence: medium
source: research
---
# POPW Worker Net Architecture Diagram

## Overview
This document references the Draw.io mxGraphModel XML diagram for the POPW (Pose-guided Object Detection with Pose) architecture with temporal modeling support.

## Diagram Files

| File | Description |
|------|-------------|
| `POPW_ARCHITECTURE_TEMPORAL.xml` | Full architecture with temporal path (Clip Sampler, Feature Bank, BiGRU) |

## Architecture Components

### Input Pipeline
- **Video Input**: Raw video stream
- **Clip Sampler**: Samples T=8 frames per clip for temporal processing

### Backbone
- **ResNet-50**: Feature extraction backbone
- **FPN**: Feature Pyramid Network for multi-scale features

### Heads
| Head | Color | Purpose |
|------|-------|---------|
| Pose Head | Purple `#8e44ad` | 2D/3D pose estimation |
| Detection Head | Red `#e74c3c` | Object detection |
| Activity Head | Various | Human activity classification |

### Temporal Modeling (NEW)
| Component | Color | Description |
|-----------|-------|-------------|
| Feature Bank | Pink `#ff69b4` | Stores temporal features across frames |
| BiGRU | Crimson `#dc143c` | Bidirectional GRU with 256 hidden units |

### PoseFiLM
Pose-guided Feature-wise Linear Modulation conditions feature extraction on pose estimation output.

## Flow Diagram

```
Video → Clip Sampler (T=8) → ResNet-50 → FPN
                                     ├──→ Pose Head → PoseFiLM → C5_mod
                                     │                              ↓
                                     │                      Feature Bank ↔ BiGRU
                                     │                              ↓
                                     ├──→ Detection Head            FC → Classification
```

## Legend Colors
- Green `#27ae60`: Backbone components
- Purple `#8e44ad`: Pose estimation
- Teal `#16a085`: PoseFiLM
- Pink `#ff69b4`: Feature Bank (temporal storage) — NEW
- Crimson `#dc143c`: BiGRU (temporal modeling) — NEW

## Usage
Open `POPW_ARCHITECTURE_TEMPORAL.xml` in [Draw.io](https://app.diagrams.net/) to view and edit the architecture diagram.

## References
- Original POPW architecture research
- BiGRU temporal modeling approach for activity recognition