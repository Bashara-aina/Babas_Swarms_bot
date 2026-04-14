---
title: Better Pseudo Labels Porcher 2024
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
summary: '**Porcher*, Couprie*, Szafraniec*, Verbeek* | 2024 | [arXiv:2403.11675](https://arxiv.org/abs/2403.11675)'
wikilinks: []
confidence: medium
source: research
---

# Better (Pseudo-)Labels for Semi-Supervised Instance Segmentation

**Porcher*, Couprie*, Szafraniec*, Verbeek* | 2024 | [arXiv:2403.11675](https://arxiv.org/abs/2403.11675)

## Overview

**Better Pseudo-Labels** addresses the miscalibration of confidence scores in semi-supervised instance segmentation (SSIS). The core insight is that confidence scores from standard teacher-student models do not reliably indicate pseudo-label quality — a high-confidence prediction may still have poor mask boundaries.

The paper proposes techniques to obtain more useful pseudo-labels by explicitly modeling the relationship between confidence and mask quality.

## Architecture

### Key Problem: Confidence Miscalibration

In standard SSIS:
- Teacher confidence scores correlate poorly with actual mask IoU
- High-confidence masks may have blurry boundaries
- Low-confidence masks may have sharp boundaries but lower overall quality

### Proposed Solutions

1. **Quality-Aware Thresholding**
   - Separate thresholds for classification confidence vs mask quality
   - Use IoU-based quality estimation instead of pure confidence
   - Dynamic threshold adaptation per instance

2. **Mask Quality Regression**
   - Train auxiliary predictor for mask quality
   - Features: boundary sharpness, shape regularity, area consistency
   - Use quality predictor to filter/refine pseudo-labels

3. **Class-Balanced Sampling**
   - Address class imbalance in pseudo-label selection
   - Ensure rare classes get appropriate representation
   - Maintain training diversity

### Training Pipeline

1. Pre-train teacher on labeled data
2. Generate initial pseudo-labels with quality scores
3. Apply quality-aware filtering (not just confidence threshold)
4. Train student with high-quality pseudo-labels
5. Iterative refinement of quality predictor

## Key Results

| Method | 1% Labeled | 5% Labeled | 10% Labeled |
|--------|------------|------------|-------------|
| Better Pseudo-Labels | 19.8 mAP | 28.9 mAP | 33.2 mAP |
| Vanilla SSIS | 12.1 mAP | 21.3 mAP | 27.5 mAP |
| PAIS | 17.2 mAP | 26.8 mAP | 31.4 mAP |

Better Pseudo-Labels achieves +2.6 mAP over PAIS at 5% labeled data through improved filtering.

## POPW Relevance

> [!IMPORTANT]
> For POPW pseudo-GT generation, the confidence calibration issue is critical. Mask R-CNN produces confidence scores that don't always correlate with actual mask quality. Implementing quality-aware thresholding (as in Better Pseudo-Labels) could significantly improve POPW pseudo-GT by filtering out high-confidence but poor-quality masks before using them as training labels.

## Code Availability

- GitHub: https://github.com/facebookresearch/better-pseudo-labels-ssis (referenced)

## See Also

- [[060-pais]] — PAIS pseudo-label alignment approach
- [[065-pl-dc]] — PL-DC extends with decoupling and correction
- [[062-s4m]] — S4M uses SAM for quality improvement
