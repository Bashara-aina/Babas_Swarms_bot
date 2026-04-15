---
title: Video Mamba
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
summary: '**arXiv**: [2403.06977](https://arxiv.org/abs/2403.06977)'
wikilinks: []
confidence: medium
source: research
---

# VideoMamba & Video Mamba Suite

## Two Papers

### Paper A: VideoMamba (Li et al.)
**arXiv**: [2403.06977](https://arxiv.org/abs/2403.06977)
**Authors**: Kunchang Li, Xinhao Li, Yi Wang, Yinan He, Yali Wang, Limin Wang, Yu Qiao
**Venue**: Shanghai AI Lab / CUHK | arXiv Mar 2024

**Core Contribution**: Direct adaptation of Mamba to video domain. Addresses local redundancy (adjacent frames similar) and global dependencies (far frames informative). Linear-complexity operator for efficient long-range temporal modeling. Four abilities:
1. Scalable self-distillation for vision domain (train without large-scale pretraining)
2. Short-term action sensitivity (adjacent frame changes)
3. Long-range video understanding (full video context)
4. Multi-modal fusion capability

**Architecture**: 3D video tokens → temporal Mamba blocks with frame-level scanning. Each Mamba block processes a sequence of frame-level features.

### Paper B: Video Mamba Suite (Chen et al.)
**arXiv**: [2403.09626](https://arxiv.org/abs/2403.09626)
**Authors**: Guo Chen, Yifei Huang, Jilan Xu, Baoqi Pei, Zhe Chen, Zhiqi Li, Jiahao Wang
**Venue**: Nankai Univ. / OPPO | arXiv Mar 2024

**Core Contribution**: Comprehensive benchmarking — categorizes Mamba into **4 roles** for video modeling:
1. **Temporal Modeler**: SSM replaces temporal attention — processes pre-extracted frame features
2. **Spatio-Temporal Modeler**: SSM processes spatial AND temporal tokens jointly
3. **Backbone**: SSM replaces ViT encoder (pure SSM vision backbone)
4. **Memory Modeler**: SSM as memory component in hybrid architectures (e.g., memory bank between pose encoder and activity classifier)

14 model variants derived from these 4 roles, evaluated on 12 video understanding tasks.

## The 4 Roles — Relevance to POPW

| Role | POPW Application | Fit |
|------|-----------------|-----|
| Temporal Modeler | BiGRU replaced by Mamba for temporal aggregation | High — replaces BiGRU with linear-complexity SSM |
| Spatio-Temporal Modeler | Joint pose spatial + temporal reasoning | Medium — for integrated pose+activity modeling |
| Backbone | Replace ResNet-50-FPN with SSM backbone | Medium — Vision Mamba does this |
| **Memory Modeler** | **Mamba as pose-activity memory buffer** | **Highest — enables bidirectional pose↔activity** |

### Role 4 Detail: Memory Modeler for Bidirectional Communication

In the Memory Modeler role, Mamba maintains a **pose context buffer** that:
1. **Receives** current frame pose features (from pose head) → updates hidden state
2. **Is modulated by** recognized activity state (from activity head) → gates what pose information is retained
3. **Provides** rich temporal context for activity recognition at each frame

This creates a natural bidirectional loop:

```
Pose Head → pose_feature_t → Mamba Memory → context_for_activity_t
Activity Head → activity_state_t → Mamba Memory (gating)
Mamba Memory → modulated_hidden_state → Activity Head (activity prediction)
```

The Mamba's selective mechanism determines what pose information to keep vs. discard based on current activity context — enabling **activity→pose feedback** that POPW's current architecture lacks.

## Why VideoMamba > BiGRU for POPW v2

| Aspect | BiGRU (POPW current) | VideoMamba (POPW v2) |
|--------|----------------------|---------------------|
| Temporal complexity | O(T) linear | O(T) linear |
| Parameters | ~1.18M | Similar |
| Selective focus | No (uniform GRU) | Yes (selective SSM) |
| Long-range modeling | Limited to T=8 window | Scalable to full video |
| GPU memory | 1.18M params | Similar, but no attention quadratic |
| Backbone integration | Post-backbone only | Can integrate with backbone |
| Multimodal fusion | No native support | Built-in (ability 4) |

## Dataset Coverage

Both papers validate on:
- Kinetics-400/600 (large-scale action recognition)
- Something-Something v1/v2 (motion-heavy actions)
- Charades (multi-label activity)
- AVA (spatio-temporal action detection)

For POPW: VideoMamba's multi-modal fusion (ability 4) is most relevant — could fuse pose features with RGB frames for improved assembly activity recognition.

## Key Architectural Idea: Temporal Mamba Block

```
Frame_features [T, C] → LayerNorm
                    → Mamba (selective SSM)
                    → [T, C] output (same sequence length)
                    → Residual connection

Mamba internal:
  Δ = σ(Linear(x))         # gate modulation
  B = Linear(x)             # input transform
  C = Linear(x)             # output transform
  A = learned (not input-dependent)
  h' = A⊙h + B⊙x          # selective recurrence
  y = C⊙h                  # output
```

The Δ (step size) controls how fast the hidden state evolves — large Δ = fast changes (action transitions), small Δ = slow evolution (stable assembly phases).

## Future POPW Architecture: Mamba as Memory Modeler

```
Input frame
  → Vim backbone (per-frame spatial encoding)
  → Pose Head (keypoints)
  → PoseFiLM → C5_mod (pose-conditioned features)
  → GAP + Concat(P4) → f_t ∈ R^2304

Feature Bank (deque of T-1 past f's)
  → Mamba Memory Modeler (bidirectional SSM)
      ← activity_state from previous frame (feedback signal)
  → temporal_context ∈ R^512
  → Activity Classifier
```

Mamba acts as the memory buffer between pose-conditioned features and activity predictions, with activity state feeding back to gate which pose information is propagated.

## References

- Li et al. (2024). "VideoMamba: State Space Model for Efficient Video Understanding." arXiv:2403.06977
- Chen et al. (2024). "Video Mamba Suite: State Space Model as a Versatile Alternative for Video Understanding." arXiv:2403.09626