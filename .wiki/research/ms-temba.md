---
title: Ms Temba
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- research
created: '2026-04-14'
updated: '2026-04-14'
summary: '- **arXiv**: [2501.06138](https://arxiv.org/abs/2501.06138)'
wikilinks: []
confidence: medium
source: research
---

# MS-Temba: Multi-Scale Temporal Action Detection

## Paper Info
- **arXiv**: [2501.06138](https://arxiv.org/abs/2501.06138)
- **Authors**: Sinha et al.
- **Venue**: arXiv Jan 2025

## Core Contribution

MS-Temba addresses **temporal action detection** (TAD) in untrimmed videos — localizing and classifying actions within long videos. The key insight: **different actions have different optimal temporal scales**:

- Short actions (hammer strike): 0.5-2 seconds → fine-grained temporal resolution
- Medium actions (screw a bolt): 5-15 seconds → standard temporal resolution
- Long phases (align furniture legs): 30-60 seconds → coarse temporal resolution

MS-Temba uses **multi-scale SSM branches** to capture actions at all temporal granularities simultaneously.

## Architecture

```
Untrimmed Video [T_max frames]
  → Frame Sampling at Multiple Scales
       ├── Scale 1: every frame → [T/1, C]     (fine)
       ├── Scale 2: every 4th frame → [T/4, C]  (medium)
       └── Scale 3: every 16th frame → [T/16, C] (coarse)
              ↓
       SSM Branch (per scale) → temporal features
              ↓
       Scale Fusion → Multi-scale temporal context
              ↓
       Action Classifier + Temporal Boundary Predictor
```

**Scale Fusion**: Combines outputs from all SSM branches using learned scale weights:
```
W_fused = softmax([w1, w2, w3])  # scale importance
F_fused = w1·F_fine + w2·F_med + w3·F_coarse
```

## Why MS-Temba Matters for POPW

IKEA assembly involves **multi-scale temporal structure**:

| Assembly Phase | Duration | Temporal Scale |
|---------------|----------|---------------|
| Pick up tool | 0.5-2s | Fine (Scale 1) |
| Position part | 2-5s | Medium (Scale 2) |
| Align with reference | 5-15s | Medium (Scale 2) |
| Secure connection | 2-10s | Medium (Scale 2) |
| Full assembly phase | 30-120s | Coarse (Scale 3) |

POPW's BiGRU with T=8 window captures ~267ms at 30fps — fine for per-frame actions but misses longer phase context.

## MS-Temba Scale Selection for POPW

Replacing POPW's single-scale BiGRU with MS-Temba-style multi-scale SSM:

```
Feature Bank (T=8 frames, 30fps) → C5_mod ∈ R^2304
  ├── Scale 1: direct → Mamba_S1 → [T, 512] (fine: 267ms windows)
  ├── Scale 2: pool(2) → Mamba_S2 → [T/2, 512] (medium: 533ms windows)
  └── Scale 3: pool(4) → Mamba_S3 → [T/4, 512] (coarse: 1.07s windows)

Scale Fusion → Multi-scale H_t ∈ R^512
  → Activity Classifier (33-class)
```

**Benefit**: Activity recognition at IKEA assemble level can leverage both:
- Fine scale: exact hand pose and tool use
- Coarse scale: overall assembly progress (which part of instruction video)

## MS-Temba on IKEA ASM Dataset

MS-Temba's multi-scale approach is well-suited for **IKEA ASM** (Assembly Model) videos:

1. **Instruction Following**: Multiple sequential phases (unpack → sort → assemble → verify)
2. **Tool Use**: Fast actions within longer tool-handling phases
3. **Error Detection**: Multi-scale helps detect when assembly deviates from expected phases

MS-Temba achieves state-of-the-art on:
- GTVI (GuitarTeach video instructions)
- IKEA ASM (assembly instructions)
- Breakfast (cooking actions)
- 50 Salads (multi-person activities)

## Comparison with POPW's Current Temporal Modeling

| Aspect | POPW BiGRU (current) | MS-Temba Multi-Scale SSM |
|--------|----------------------|--------------------------|
| Temporal scales | Single (T=8 window) | Multiple (fine/med/coarse) |
| Long-range | Limited to T=8 | Scalable to full video |
| Action localization | Video-level only | Temporal boundaries |
| Phase awareness | No | Yes (coarse scale) |
| Complexity | O(T) | O(T) × n_scales |

## Future POPW Extension: MS-Temba Temporal Head

```
C5_mod_t → Project(2304→512)

Branch 1 (fine):    Mamba_S1(concat of past 8 frames)
Branch 2 (medium):  Mamba_S2(pool(concat of past 8 frames, k=2))
Branch 3 (coarse):  Mamba_S3(pool(concat of past 8 frames, k=4))

Scale Weights → softmax-learned per frame
Fused = w1·h1 + w2·h2 + w3·h3

→ Activity Classifier (33-class IKEA assembly actions)
→ Phase Predictor (which instruction step)
→ Progress Tracker (assembly completion %)
```

## References

- Sinha et al. (2025). "MS-Temba: Multi-Scale Temporal Modeling with State Space Models for Action Detection." arXiv:2501.06138
