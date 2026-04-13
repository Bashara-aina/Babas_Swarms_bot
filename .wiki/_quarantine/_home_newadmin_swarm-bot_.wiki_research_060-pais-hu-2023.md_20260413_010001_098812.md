---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/research/060-pais-hu-2023.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-13T01:00:01.098832"
}
---

---
tags: [semi-supervised, instance-segmentation, pseudo-label, alignment, iccv2023]
sources: [arxiv:2308.05359, openaccess:ICCV2023/Hu]
created: 2026-04-11
updated: 2026-04-11
paper_num: "060"
---

# PAIS: Pseudo-Label Alignment for Semi-Supervised Instance Segmentation

**Hu*, Yang*, Li*, et al. | ICCV 2023 | [arXiv:2308.05359](https://arxiv.org/abs/2308.05359)

## Overview

**PAIS** (Pseudo-label Alignment for Semi-supervised Instance Segmentation) addresses the challenge of utilizing unlabeled images for instance segmentation. The core insight is that pseudo-labels for instance segmentation must be aligned at both the pixel-level (mask quality) and instance-level (class consistency).

PAIS proposes a novel pseudo-label aligning framework that unleashes the potential of unlabeled data by considering both mask and class alignment for pixel-level instance predictions.

## Architecture

### Key Innovation: Dual-Level Alignment

1. **Pixel-Level Alignment**: Ensures mask boundaries are accurate by aligning pseudo-label masks with teacher's instance boundaries
2. **Instance-Level Alignment**: Ensures class predictions are consistent across different unlabeled images for the same object category

### Class-Specific Weighting Mechanism

- PAIS adjusts pseudo-label confidence using class-specific weights
- Different object categories may have different optimal confidence thresholds
- Handles the class imbalance issue common in COCO-style datasets

### Semi-Supervised Training Pipeline

1. Pre-train teacher on labeled data only
2. Generate pseudo-labels for unlabeled images
3. Apply dual-level alignment to filter/refine pseudo-labels
4. Train student on combined labeled + aligned unlabeled data
5. Update teacher via EMA

## Key Results

| Method | 1% Labeled | 5% Labeled | 10% Labeled |
|--------|------------|------------|-------------|
| PAIS | 17.2 mAP | 26.8 mAP | 31.4 mAP |
| Baseline (Cascade Mask R-CNN) | 12.1 mAP | 21.3 mAP | 27.5 mAP |

PAIS demonstrates particularly strong performance when labeled data is severely limited (1-5%).

## POPW Relevance

> [!IMPORTANT]
> PAIS's class-specific weighting mechanism is relevant for POPW furniture categories. Different furniture types (chairs, tables, shelves) may have different mask quality challenges. The dual-level alignment directly addresses mask + class consistency which is critical for multi-category pseudo-GT generation.

## Code Availability

- GitHub: https://github.com/hujiecpp/PAIS

## See Also

- [[064-better-pseudo-labels]] — Another SSIS approach focusing on confidence calibration
- [[065-pl-dc]] — PL-DC extends alignment with decoupling and correction
