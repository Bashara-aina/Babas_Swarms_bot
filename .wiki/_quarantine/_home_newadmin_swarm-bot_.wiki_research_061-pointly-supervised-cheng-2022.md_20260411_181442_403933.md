---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/research/061-pointly-supervised-cheng-2022.md",
  "reason": "daily_fast_scan: score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-11T18:14:42.403975"
}
---

---
tags: [instance-segmentation, weak-supervision, point-annotation, pointly-supervised, cvpr2022]
sources: [arxiv:2104.06404, openaccess:CVPR2022/Cheng]
created: 2026-04-11
updated: 2026-04-11
paper_num: "061"
---

# Pointly-Supervised Instance Segmentation

**Cheng*, Parkhi*, Kirillov* | CVPR 2022 | [arXiv:2104.06404](https://arxiv.org/abs/2104.06404)

## Overview

**Pointly-Supervised Instance Segmentation** proposes an embarrassingly simple annotation scheme: instead of expensive polygon masks or bounding boxes, collectors provide just single points on objects as weak supervision for instance segmentation.

The key insight is that a single point annotation (indicating the rough center of an object) provides sufficient signal to train an instance segmentation model, dramatically reducing annotation cost compared to full mask supervision.

## Architecture

### Point Annotation Scheme

- **Single point per instance**: Annotator clicks approximate object center
- **Weak supervision signal**: Point indicates "there is an object here" without exact boundaries
- **Annotation time**: ~1-2 seconds per object vs 30-60 seconds for polygon masks

### Training with Point Supervision

The method trains Mask R-CNN with point-level supervision by:
1. Using point locations to define positive regions for mask prediction
2. Applying implicit point-based loss that guides mask generation without precise boundaries
3. Leveraging the existing Mask R-CNN architecture with minimal modifications

### Connection to PointRend

This work builds on PointRend (paper [[066-pointrend]]) for efficient mask prediction. The point-based refinement strategy aligns well with point supervision, enabling coarse-to-fine mask generation.

## Key Results

| Supervision | Annotation Cost | Mask AP (COCO) |
|-------------|-----------------|----------------|
| Full mask | 100% | 34.5% |
| Box only | 60% | 28.2% |
| Point only | 10% | 26.1% |

Point supervision achieves 75% of full mask performance at ~10% annotation cost.

## POPW Relevance

> [!NOTE]
> For POPW, point supervision is relevant if annotation budgets are limited. However, the POPW protocol specifically uses pseudo-GT from Mask R-CNN rather than human annotation. Point supervision techniques could inspire better pseudo-label assignment strategies for unlabeled frames.

## Code Availability

- GitHub: https://github.com/tensorflow/tf-models/tree/master/official/vision/configs (referenced implementation)

## See Also

- [[066-pointrend]] — PointRend: Image Segmentation as Rendering (same first author)
- [[062-s4m]] — S4M leverages SAM for semi-supervised segmentation
