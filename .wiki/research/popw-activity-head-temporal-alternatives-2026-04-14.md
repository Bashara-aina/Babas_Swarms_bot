---
title: POPW Activity Head Temporal Alternatives (TSM vs BiGRU and Beyond)
type: concept
status: active
tags: [popw, temporal-modeling, activity-head, tsm, bigru, posefilm, architecture]
created: 2026-04-14
updated: 2026-04-14
summary: POPW temporal modeling options were compared across six approaches with implementation cost, VRAM, dataset requirements, and novelty. The core result is that both TSM and BiGRU require multi-frame dataset changes, but BiGRU preserves multi-task head isolation and aligns better with PoseFiLM. Recommendation: choose BiGRU + feature bank for stronger paper novelty, or TSM for fastest implementation.
wikilinks:
  - [[research/069-tsm-lin-2019]]
  - [[research/071-slowfast-feichtenhofer-2019]]
  - [[research/097-attention-vaswani-2017]]
  - [[research/temporal-attention-alternatives]]
  - [[INDEX]]
confidence: high
source: research
---

# POPW Activity Head Temporal Alternatives — Research Summary

TSM is a zero-parameter temporal operator that shifts feature channels across adjacent frames, while BiGRU is an explicit sequence model that learns temporal memory after feature extraction. Both approaches require changing POPW from single-frame loading to clip-based loading with $T$ consecutive frames. For POPW’s multi-task architecture, the decisive factor is not only accuracy or compute, but whether temporal improvements remain isolated to the activity head or interfere with shared backbone learning.

## How TSM Works (Precise)

Input tensor is arranged as `[B, T, C, H, W]`. Let `fold = C // 8` (default: 1/8 channels per direction).

```python
out[:, :-1, :fold]       = x[:, 1:, :fold]          # shift LEFT  (future)
out[:, 1:, fold:2*fold]  = x[:, :-1, fold:2*fold]   # shift RIGHT (past)
out[:, :, 2*fold:]       = x[:, :, 2*fold:]         # no shift
```

For ResNet-50 `layer4` (`C=2048`): `256` channels shift left, `256` shift right, and `1536` stay. This adds no MACs and no trainable parameters.

## 6-Way Comparison

| Method | Params added | FLOPs added | VRAM (RTX 3060) | Dataset change? | Kinetics-400 Top-1 | Paper novelty | POPW fit | Impl difficulty |
|---|---:|---:|---|---|---|---|---|---|
| TSM | 0 | 0 | No change | YES (stack T frames) | 74.1% (8f, R50) | Medium (2019) | Good | Low |
| BiGRU + FeatureBank | +2.1M | +0.04 GFLOPs | Minimal | YES (clip-level feature bank) | N/A (assembly-focused) | High | Best | Medium |
| Transformer | +1.2M | +0.02 GFLOPs | Minimal | YES (clip sampling) | ~78% (ViT-B) | Medium | Good | Medium |
| TokenLearner | +0.1M | Low | Minimal | YES (clip sampling) | ~75% | High | Medium | High |
| SlowFast | +Slow path | ~2× total | ~9–10GB | YES (dual stream) | ~79% | Medium | Poor | High |
| X3D / MoViNet | Backbone swap | Full replace | ~6–8GB | YES (new video backbone) | ~74% | Medium | Poor | Very High |

## Critical Finding: TSM and BiGRU Both Require Dataset Refactor

Neither method is compatible with strict single-frame training. Both require clip sampling, but differ architecturally:

| Aspect | TSM | BiGRU |
|---|---|---|
| Use of T frames | Parallel (reshape into batch dimension) | Sequential (hidden state flows over time) |
| Backbone impact | Modified in-place | Unchanged |
| Temporal modeling location | Inside shared visual backbone | Post-backbone activity path |
| Paper narrative | “Zero-cost temporal backbone” | “Assembly-aware temporal memory head” |

## Exact POPW TSM Integration Pattern

```python
from temporal_shift import make_temporal_shift
make_temporal_shift(self.backbone, n_segment=8, n_div=8, place='blockres')
```

Data flow change:
1. Old loader: single frame/sample
2. New loader: `T=8` consecutive frames/sample
3. Forward: `[B, T, C, H, W] -> [B*T, C, H, W]` for backbone
4. Post-backbone: reshape to `[B, T, 2048, H, W]`, temporal average, then activity head

## What BiGRU Gives That TSM Does Not

- **PoseFiLM synergy:** BiGRU can consume `C5_mod` (already pose-conditioned), preserving the chain `Pose -> FiLM(C5) -> BiGRU(C5_mod)`.
- **Head isolation:** BiGRU stays in the activity head, reducing cross-task interference with detection and pose optimization.
- **Interpretability:** GRU hidden state can be analyzed as latent assembly-state progression.
- **Novelty leverage:** Feature-bank + post-FiLM recurrent modeling is less saturated than pure TSM in assembly recognition literature.

## Recommendation (Research-Grade)

Use **BiGRU + feature bank** if objective is strongest paper contribution and clean multi-task ablations. This aligns with POPW’s architectural story: perception (pose) conditions semantics (FiLM), then temporal memory models assembly evolution.

Use **TSM** if objective is fastest implementation with established public benchmarks and minimal parameter overhead.

## Decision Matrix

| Priority | Choose |
|---|---|
| Stronger paper story + PoseFiLM synergy | BiGRU |
| Fastest implementation + known benchmarks | TSM |
| Maximum novelty | BiGRU + feature bank |
| Minimal code changes | TSM (with shared-backbone tradeoff) |

## Current Status

- Summary captured in wiki for POPW temporal design decisions.
- No training run or ablation was executed in this note; this is architecture-level synthesis for implementation planning.
- Next implementation checkpoint: decide `T` (e.g., 8 vs 16) and finalize dataset clip sampler API before coding activity-head temporal module.
