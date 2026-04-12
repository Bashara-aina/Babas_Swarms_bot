---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/research/065-pl-dc-lin-2025.md",
  "reason": "daily_fast_scan: score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-12T01:00:00.788840"
}
---

---
tags: [semi-supervised, instance-segmentation, pseudo-label, decoupling, correction, 2025]
sources: [arxiv:2505.11075]
created: 2026-04-11
updated: 2026-04-11
paper_num: "065"
---

# PL-DC: Pseudo-Label Quality Decoupling and Correction

**Lin*, et al. | 2025 | [arXiv:2505.11075](https://arxiv.org/abs/2505.11075)

## Overview

**PL-DC** (Pseudo-Label Quality Decoupling and Correction) is a state-of-the-art framework for Semi-Supervised Instance Segmentation (SSIS) that explicitly decouples and corrects different aspects of pseudo-label quality.

The key innovation is recognizing that pseudo-label quality is multi-dimensional — class prediction quality and mask quality are not necessarily correlated — and handling them separately leads to better overall performance.

## Architecture

### Instance-Level Decoupled Dual-Threshold Mechanism

1. **Class Quality Pathway**
   - Dedicated threshold for class assignment confidence
   - Handles category-level prediction separately from mask quality
   - Independent filtering criteria for classification vs segmentation

2. **Mask Quality Pathway**
   - Dedicated evaluation of boundary accuracy, shape consistency
   - Mask-specific confidence scoring
   - Separate refinement for mask predictions

### Two-Stage Correction Pipeline

**Stage 1: Decoupling**
- Split pseudo-label evaluation into class and mask components
- Apply independent confidence thresholds to each
- Generate class-qualified and mask-qualified pseudo-labels

**Stage 2: Correction**
- Refine class predictions using mask quality signals
- Improve mask boundaries using class consistency
- Iterative cross-refinement between pathways

### Design Rationale

High class confidence ≠ High mask quality:
- A pseudo-label might correctly classify "chair" but have poor boundary
- Another might have good mask but wrong category
- Decoupling allows independent optimization of each aspect

## Key Results

| Method | 1% Labeled | 5% Labeled | 10% Labeled |
|--------|------------|------------|-------------|
| PL-DC | 23.8 mAP | 31.2 mAP | 35.3 mAP |
| Better Pseudo-Labels | 19.8 mAP | 28.9 mAP | 33.2 mAP |
| S⁴M (ICCV 2025) | 22.3 mAP | 30.1 mAP | 34.8 mAP |

PL-DC achieves +11.7 mAP improvement with 1% labeled data vs baseline.

## POPW Relevance

> [!CRITICAL]
> PL-DC's decoupling mechanism is directly applicable to POPW pseudo-GT generation. Currently, POPW likely uses a single confidence threshold for all pseudo-GT aspects. PL-DC shows that separately handling class vs mask quality leads to significant improvements (+11.6 mAP at 1% COCO). For furniture assembly pseudo-GT, this means separate quality gates for: (1) furniture category classification, (2) mask boundary accuracy.

## Code Availability

- GitHub: (referenced in paper, check arXiv page)

## See Also

- [[064-better-pseudo-labels]] — Confidence calibration approach
- [[062-s4m]] — SAM-augmented SSIS
- [[060-pais]] — Pseudo-label alignment for SSIS
