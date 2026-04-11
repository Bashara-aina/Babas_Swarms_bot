---
tags: [semi-supervised, object-detection, pseudo-label, bias, teacher-student, iclr2021]
sources: [arxiv:2102.09480, openreview:MJIve1zgR]
created: 2026-04-11
updated: 2026-04-11
paper_num: "063"
---

# Unbiased Teacher for Semi-Supervised Object Detection

**Liu*, Ma*, He*, Kuo*, et al. | ICLR 2021 | [arXiv:2102.09480](https://arxiv.org/abs/2102.09480)

## Overview

**Unbiased Teacher** addresses the pseudo-labeling bias issue in Semi-Supervised Object Detection (SS-OD). The core problem is that as the teacher improves, it tends to favor high-confidence predictions and neglect harder examples, leading to confirmation bias where the student only learns easy cases.

The solution is a simple yet effective teacher-student joint training framework where the teacher gradually progresses and maintains balanced learning for all object categories.

## Architecture

### Key Innovation: Pseudo-Label Bias Identification

The paper identifies that standard SS-OD methods suffer from:
1. **Class imbalance**: Teacher focuses on common classes, ignores rare classes
2. **Difficulty bias**: Teacher gravitates toward easy detections, avoids hard ones
3. **Feedback loop**: Student reinforce teacher's biases over training iterations

### Teacher-Student Joint Training

1. **Initial Phase**: Train student on labeled data only
2. **Joint Training Phase**: 
   - Teacher generates pseudo-labels for unlabeled images
   - Student trains on labeled + pseudo-labeled data
   - Teacher weights updated via EMA from student
3. **Progressive Unfreezing**: Gradually increase pseudo-label contribution

### Balanced Training Strategy

- Uses class-aware thresholding instead of global threshold
- Applies data augmentation equally to all categories
- Prevents the teacher from ignoring low-frequency classes

## Key Results

| Method | 5% Labeled | 10% Labeled | 100% Labeled |
|--------|------------|-------------|--------------|
| Unbiased Teacher | 25.1 mAP | 28.3 mAP | 39.2 mAP |
| STAC | 22.4 mAP | 25.8 mAP | 39.2 mAP |
| Supervised only | 18.2 mAP | 21.5 mAP | 39.2 mAP |

Unbiased Teacher achieves 72% of fully supervised performance with 5% labeled data.

## POPW Relevance

> [!IMPORTANT]
> The pseudo-label bias issue identified in Unbiased Teacher directly applies to POPW pseudo-GT generation. When generating pseudo-GT from Mask R-CNN, the model will naturally favor common furniture types and easy poses. Unbiased Teacher's class-aware thresholding and balanced training strategies could improve pseudo-GT quality across all furniture categories.

## Code Availability

- GitHub: https://github.com/facebookresearch/unbiased-teacher

## See Also

- [[059-soft-teacher]] — Soft Teacher for end-to-end SS-OD
- [[064-better-pseudo-labels]] — Addresses confidence calibration for SSIS
