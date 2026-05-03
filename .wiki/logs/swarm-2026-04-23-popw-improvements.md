---
title: Swarm 2026 04 23 Popw Improvements
type: concept
status: active
tags: [/]
created: 2026-05-03
updated: 2026-05-03
---

# Swarm Run: POPW & IndustReal Model Improvements

**Date:** 2026-04-23
**Type:** FEATURE
**Agents used:** memory, explorer, worker (multiple), DiffAnalyzer (manual verification)

## Summary

Created two new improved model directories with architectural improvements targeting benchmark-beating performance on IKEA ASM and IndustReal datasets. All 14 contracts completed successfully.

## Contracts

| # | Priority | Title | Status | Files |
|---|----------|-------|--------|-------|
| 1 | HIGH | PopW folder structure | ✅ | 7 files in popw_main_improved/ |
| 2 | HIGH | ConvNeXt-Tiny backbone PopW | ✅ | model.py (40M params) |
| 3 | HIGH | OKS Loss PopW | ✅ | losses.py |
| 4 | HIGH | GCN Skeleton PopW | ✅ | model.py |
| 5 | HIGH | IndustReal folder structure | ✅ | 7 files in industreal_improved/ |
| 6 | HIGH | ConvNeXt-Tiny backbone IndustReal | ✅ | model.py (41.9M params) |
| 7 | HIGH | TMA Cell IndustReal | ✅ | model.py |
| 8 | HIGH | Temporal Bank IndustReal | ✅ | model.py |
| 9 | MEDIUM | Label Smoothing | ✅ | config.py, losses.py |
| 10 | MEDIUM | Temporal Augmentation | ✅ | ikea_dataset.py, config.py |
| 11 | MEDIUM | Spatial Augmentation | ✅ | ikea_dataset.py, *_dataset.py, config.py |
| 12 | MEDIUM | TTA horizontal flip | ✅ | evaluate.py, config.py |
| 13 | LOW | Cosine Annealing Warmup | ✅ | train.py (both), config.py (both) |
| 14 | LOW | ONNX Export | ✅ | export_onnx.py (both) |

## Files Created

### popw_main_improved/ (7 files)
- `model.py` — ConvNeXt-Tiny backbone, GCN skeleton module, updated FPN
- `losses.py` — OKS Loss (COCO 17-keypoint), ClassBalancedFocalLoss with label smoothing
- `config.py` — BACKBONE='convnext_tiny', USE_OKS_LOSS=True, USE_GCN_SKELETON=True, LABEL_SMOOTHING=0.1, TRAIN_FRAME_STRIDE_RANGE=[3,7], USE_SPATIAL_AUG=True, USE_TTA=False
- `train.py` — CosineAnnealingWarmRestarts scheduler with warmup
- `evaluate.py` — evaluate_with_tta() function
- `ikea_dataset.py` — apply_spatial_aug(), temporal augmentation
- `export_onnx.py` — ONNX export with GCN-aware fallback

### industreal_improved/ (7 files)
- `model.py` — ConvNeXt-Tiny backbone, TMACell, TemporalBankModule, updated FPN
- `losses.py` — Original losses
- `config.py` — BACKBONE='convnext_tiny', USE_TMA_CELL=True, USE_TEMPORAL_BANK=True, USE_SPATIAL_AUG=True
- `train.py` — CosineAnnealingWarmRestarts scheduler with warmup
- `evaluate.py` — Original evaluate
- `industreal_dataset.py` — apply_spatial_aug()
- `export_onnx.py` — ONNX export

## Key Architectural Changes

### ConvNeXt-Tiny Backbone
- Replaces ResNet-50 (~25M → 28.6M params)
- ImageNet-22k pretrained (fb_in22k_ft_in1k)
- Frozen BN, outputs C3(192ch), C4(384ch), C5(768ch)

### GCN Skeleton (PopW only)
- Manual sparse matmul (no torch_geometric dependency)
- 16 COCO skeleton edges with Laplacian normalization
- 2 GCN layers, hidden_dim=256

### TMACell (IndustReal only)
- GRU hidden_size=256, num_layers=1
- Masked self-attention (4 heads, causal/future masking)
- Probabilistic modeling (mean + logvar output)

### TemporalBankModule (IndustReal only)
- Dual-mode: batch Conv1D (training) + ring-buffer per-frame (evaluation)
- T=8 short-term + T=32 long-term
- Returns concatenated [B, 512] features

### OKS Loss (PopW only)
- COCO 17-keypoint OKS formula
- Per-keypoint k constants
- Replaces Wing Loss for scale-invariant pose regression

### Training Improvements
- Label smoothing: 0.1 for CrossEntropyLoss
- Temporal augmentation: random stride [3, 7] during training
- Spatial augmentation: horizontal flip (p=0.5) + random crop (scale [0.8, 1.0])
- CosineAnnealingWarmRestarts (T_0=10, T_mult=2) with linear warmup (5 epochs)

## Target Metrics

### PopW (IKEA ASM)
- Activity Top-1 > 64.15% (was I3D RGB+pose baseline)
- Activity mcAP (csv) > 84.47% (PTMA baseline)
- Pose PCK@10px > 64.3%
- Detection AP@0.5 > 85.3%

### IndustReal
- Activity Top-1 > 66.45% (MViTv2 Kinetics baseline)
- ASD mAP@0.5 > 83.8% (YOLOv8m baseline)
- PSR F1 > 0.901 (STORM-PSR baseline)

## Verification

All contracts verified via independent Python tests:
- ConvNeXt forward passes: ✅
- GCN output [B, 17, 256]: ✅
- TMACell output [B, 256]: ✅
- TemporalBankModule [B, 512]: ✅
- OKS Loss (no NaN): ✅
- Spatial augmentation (flip/crop): ✅
- Config flags: ✅
- ONNX exports: ✅
