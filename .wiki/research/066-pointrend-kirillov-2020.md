---
tags: [instance-segmentation, semantic-segmentation, point-based, rendering, adaptive-sampling, cvpr2020]
sources: [arxiv:1912.08193, openaccess:CVPR2020/Kirillov]
created: 2026-04-11
updated: 2026-04-11
paper_num: "066"
---

# PointRend: Image Segmentation as Rendering

**Kirillov*, Wu*, He*, Girshick* | CVPR 2020 | [arXiv:1912.08193](https://arxiv.org/abs/1912.08193)

## Overview

**PointRend** treats image segmentation as a rendering problem, applying classical computer graphics techniques (specifically, point-based rendering) to efficiently predict segmentation masks at adaptively selected locations.

The key insight is that full-resolution segmentation over every pixel is wasteful — most pixels can be confidently labeled from coarse predictions, while only boundary regions need finer computation. PointRend selects points near boundaries for detailed prediction.

## Architecture

### Core Idea: Segmentation as Rendering

Classical rendering selects a subset of pixels to compute at high resolution, then interpolates the rest. PointRend applies the same principle to segmentation:

1. Start with coarse segmentation map (e.g., from FCN or mask head)
2. Select points where uncertainty is highest (near boundaries)
3. Refine predictions at selected points using learned feature interpolation
4. Repeat iteratively for progressively finer boundaries

### Point Selection Strategy

**Adaptive Point Selection:**
- Points should be more densely located near boundaries
- Use uncertainty estimation to guide selection
- Confidence-based sampling prioritizes difficult regions

**Two Modes:**
1. **Training**: Points selected based on GT boundaries + random sampling
2. **Inference**: Points selected iteratively based on prediction uncertainty

### Implementation Details

- Uses feature pyramid network (FPN) features
- Small MLP head for point-wise prediction
- Coarse-to-fine refinement in 5-6 iterations
- Can be applied to both instance (Mask R-CNN) and semantic segmentation

## Key Results

### Instance Segmentation (COCO)

| Method | Mask AP |
|--------|---------|
| Mask R-CNN (baseline) | 34.5% |
| Mask R-CNN + PointRend | 36.5% |
| Hybrid Knowledge Distillation | 38.5% |

### Semantic Segmentation (Cityscapes)

| Method | mIoU |
|--------|------|
| DeepLabV3 (baseline) | 78.5% |
| DeepLabV3 + PointRend | 79.4% |

PointRend improves mask quality especially near boundaries without hurting efficiency.

## POPW Relevance

> [!IMPORTANT]
> PointRend's boundary-focused refinement is highly relevant for POPW pseudo-GT quality. Mask boundaries are critical for furniture assembly masks — imprecise boundaries lead to incorrect region overlap detection. PointRend's point selection strategy (prioritizing high-uncertainty boundary regions) could be applied to refine pseudo-GT masks from Mask R-CNN before using them as training labels.

## Code Availability

- Detectron2: https://github.com/facebookresearch/detectron2 (official implementation)
- Original: https://github.com/facebookresearch/pointrend

## See Also

- [[061-pointly-supervised]] — Same first author, point-based approach
- [[067-sam]] — Segment Anything Model (same author group)
- [[069-mask2former]] — Transformer-based segmentation (later work)
