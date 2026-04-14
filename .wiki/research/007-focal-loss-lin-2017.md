---
title: "007 - Focal Loss Lin Goyal Girshick 2017"
type: research
status: active
tags: [focal-loss, object-detection, class-imbalance, retinaNet, detection]
created: 2026-04-13
updated: 2026-04-13
summary: Focal Loss adds a modulating factor (1-pt)^γ to standard cross-entropy, focusing training on hard negative examples rather than easy background. Lin 2017 shows that for class-imbalanced detection, focal loss significantly outperforms balanced sampling. POPW uses Focal Loss for its detection head.
wikilinks:
  - [[research/002-fpn-lin-2017]]
  - [[research/008-class-balanced-loss-cui-2019]]
  - [[024-yolo-decoupled-head-2023]]
  - [[049-generalized-focal-loss-li-2020]]
  - [[100-popw-protocol-self-analysis]]
confidence: high
source: canonical
---

# Focal Loss for Dense Object Detection (RetinaNet)

**Authors:** Tsung-Yi Lin, Priya Goyal, Ross Girshick, Kaiming He, Piotr Dollár
**Year:** 2017
**Venue:** ICCV (Best Paper Honorable Mention)
**ArXiv/DOI:** [arXiv:1708.02002](https://arxiv.org/abs/1708.02002)
**Citation count:** ~25,000+
**Relevance to POPW:** POPW's detection head uses Focal Loss for the 7-class furniture part detection. The extreme class imbalance (many more background anchors than part anchors) is exactly what focal loss addresses. Implemented in `losses.py:FocalLoss`.

## Core Contribution

Standard cross-entropy loss for detection is dominated by easy negatives (background anchors). Even though each negative has low loss, there are so many that they overwhelm the gradient. Focal loss down-weights easy examples by adding a modulating factor `(1 - p_t)^γ`, focusing training on hard examples.

## Key Technical Details

- **Focal Loss equation**: `FL(p_t) = -α_t (1 - p_t)^γ log(p_t)`
  - `p_t` = predicted probability for the ground truth class
  - `γ` (gamma) = focusing parameter (default: 2.0)
  - `α_t` = class-balanced weighting (default: α=0.25 for foreground, 0.75 for background or per-class)
- **γ = 0**: Equivalent to cross-entropy
- **γ = 2**: Standard focal loss (used in RetinaNet)
- **When γ increases**: Easy examples contribute less, hard examples contribute more
- **Class imbalance fix**: With γ=2, even well-classified negatives (p_t ≈ 1) contribute `(1-0.99)^2 ≈ 0.0001` instead of `0.01` in CE — 100× reduction

## Results They Achieved

| Method | Backbone | COCO mAP |
|--------|----------|----------|
| RetinaNet (ResNet-50) + Focal Loss | ResNet-50 | 39.1% |
| RetinaNet (ResNet-101) + Focal Loss | ResNet-101 | 41.1% |
| RetinaNet (ResNet-101) + OHEM | ResNet-101 | 38.4% |
| YOLOv2 (anchor-based) | DarkNet-19 | 21.6% |
| SSD513 | ResNet-101 | 31.2% |
| R-FCN (ResNet-101) | ResNet-101 | 39.9% |

With **class-balanced focal loss** (α-tuning per class): COCO mAP improved by ~2-3%.

## What POPW Can Steal Directly

1. **Focal Loss implementation** (`losses.py:FocalLoss`): Uses α=0.25, γ=2.0 as defaults
2. **Anchor assignment thresholds**: `pos_iou_thresh=0.5`, `neg_iou_thresh=0.4` for matching anchors to GT boxes
3. **Hard negative mining implicit in focal loss**: No need for explicit OHEM (Online Hard Example Mining) — focal loss automatically down-weights easy negatives
4. **Multi-class focal loss**: For 7 classes, use sigmoid BCE (not softmax CE) per class

## Implemented in POPW?

- [x] YES — `improved/losses.py:FocalLoss` class
- [x] YES — Uses `alpha=0.25`, `gamma=2.0` from `config.py:FOCAL_ALPHA`, `FOCAL_GAMMA`
- [x] YES — Anchor matching with `pos_iou_thresh=0.5`, `neg_iou_thresh=0.4`
- [x] YES — `BCEWithLogitsLoss` (sigmoid, not softmax) for multi-class

## Failure Modes / Limitations

- **γ tuning is dataset-specific**: γ=2 works for COCO's ~1:1000 negative:positive ratio. For POPW's furniture parts (less extreme imbalance), γ=1.5 or γ=1.0 might work better.
- **α/γ interaction**: The best α depends on γ. γ=2 needs α=0.25; γ=1 might need different α. Grid search both on validation set.
- **Focal loss + Kendall conflict**: When combining focal loss (per-sample) with Kendall weighting (per-task), the loss scale differences become worse. This is part of why Kendall was disabled in POPW.

## Key Equations

**Standard Cross-Entropy:**
```
CE(p_t) = -log(p_t)
```

**Focal Loss:**
```
FL(p_t) = -(1 - p_t)^γ · log(p_t)
```

**Class-Balanced Focal Loss:**
```
FL(p_t) = -α_t (1 - p_t)^γ · log(p_t)
where α_t ∈ {α, 1-α} for {foreground, background}
```

**Probability modulation:**
```
p_t = p if y=1 (foreground), else p_t = 1-p
(1 - p_t) → 1 for wrong predictions (p≈0)
(1 - p_t) → 0 for easy correct predictions (p≈1)
```

## Implementation Notes

```python
# Focal Loss implementation (from losses.py)
class FocalLoss(nn.Module):
    def __init__(self, alpha=0.25, gamma=2.0, pos_iou_thresh=0.5, neg_iou_thresh=0.4):
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.pos_iou_thresh = pos_iou_thresh
        self.neg_iou_thresh = neg_iou_thresh

    def forward(self, cls_preds, reg_preds, anchors, targets):
        # cls_preds: [B, num_anchors, num_classes] raw logits
        # targets: list of dicts with 'boxes' and 'labels'
        B = cls_preds.shape[0]
        device = cls_preds.device
        total_cls = torch.tensor(0.0, device=device)

        for i in range(B):
            gt_boxes = targets[i]['boxes'].to(device)
            gt_labels = targets[i]['labels'].to(device)
            matched_labels = self._match_anchors(anchors, gt_boxes, gt_labels)
            pos_mask = matched_labels >= 0
            neg_mask = matched_labels == -2
            valid_mask = pos_mask | neg_mask
            num_pos = max(pos_mask.sum().item(), 1)

            # Build target tensor
            cls_pred = cls_preds[i][valid_mask]
            cls_target = torch.zeros_like(cls_pred)
            if pos_mask.sum() > 0:
                pos_in_valid = pos_mask[valid_mask]
                cls_target[pos_in_valid, matched_labels[valid_mask][pos_in_valid]] = 1.0

            # Focal loss
            p = torch.sigmoid(cls_pred)
            ce = F.binary_cross_entropy_with_logits(cls_pred, cls_target, reduction='none')
            p_t = p * cls_target + (1 - p) * (1 - cls_target)  # probability of correct class
            focal_weight = (1 - p_t) ** self.gamma
            alpha_t = self.alpha * cls_target + (1 - self.alpha) * (1 - cls_target)
            total_cls = total_cls + (alpha_t * focal_weight * ce).sum() / num_pos

        return total_cls / B, total_reg / B  # cls_loss, reg_loss
```

## Related Papers in This Wiki

- [[research/002-fpn-lin-2017]] — FPN + RetinaNet = focal loss was the original application
- [[research/008-class-balanced-loss-cui-2019]] — CB Focal combines class-balanced + focal loss (POPW uses this for activity)
- [[024-yolo-decoupled-head-2023]] — YOLOv8 uses focal loss with decoupled classification/regression heads
- [[049-generalized-focal-loss-li-2020]] — GFL extends focal loss to bbox regression (QFL + DFL)

## LEGION RULE

When Bashara asks about "why focal loss for detection but CB Focal for activity," reference this paper's finding: Focal loss solves the foreground-background imbalance in detection (90%+ of anchors are background). Activity classification (33 classes) has different imbalance — intra-class imbalance (some actions are 100× rarer than others). CB Focal combines both: focal focuses on hard vs easy, class-balanced focuses on rare vs common.

Applied to POPW: For the 7 detection classes, all parts are roughly equally common (leg appears as often as shelf). So plain focal (α=0.25, γ=2.0) is sufficient. For 33 activity classes, class-balanced (effective number) is more important. The combined CB Focal in `improved/losses.py` is the right choice for activity.

Config: `config.py:FOCAL_ALPHA = 0.25`, `FOCAL_GAMMA = 2.0` — these can be tuned via ablation experiments.
