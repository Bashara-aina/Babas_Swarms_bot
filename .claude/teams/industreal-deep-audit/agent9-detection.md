# Agent 9: Detection Head Audit

## Files Audited
- `/media/newadmin/master/POPW/working/code/industreal_improved/src/models/model.py` — DetectionHead (L488-555), AnchorGenerator (L434-482), cls_score init (L527-534)
- `/media/newadmin/master/POPW/working/code/industreal_improved/src/training/losses.py` — FocalLoss (L74-352), anchor matching (L91-132), empty-frame path (L224-239)
- `/media/newadmin/master/POPW/working/code/industreal_improved/src/training/train.py` — get_stage (L538-561), detach-reg-fpn arg (L4346-4355), reinit-heads wiring (L4387-4393)
- `/media/newadmin/master/POPW/working/code/industreal_improved/src/evaluation/evaluate.py` — compute_detection_map (L157-273), compute_det_metrics_extended (L1547-1598), mAP all-frames (L1480-1544), eval loop (L3628-3703)
- `/media/newadmin/master/POPW/working/code/industreal_improved/src/config.py` — FOCAL_ALPHA=0.90, FOCAL_GAMMA=2.0, DET_OHEM_*, DET_EMPTY_*, DET_GT_FRAME_FRACTION, DETACH_REG_FPN

---

## 1. RetinaNet-Style Architecture Correctness

**Finding: Architecturally correct RetinaNet with modifications for extreme imbalance.**

The DetectionHead (model.py:488-555) follows the standard RetinaNet pattern: shared cls/reg subnets across P3-P7, 4 conv layers each, followed by task-specific output convs. Key differences from canonical RetinaNet:

| Feature | Standard RetinaNet | This Implementation |
|---------|-------------------|-------------------|
| Subnet activation | ReLU (no norm) | ReLU + GroupNorm(8) |
| Cls output | 9 x num_classes | 9 x 24 |
| Reg output | 9 x 4 | 9 x 4 |
| Subnet depth | 4 convs | 4 convs |
| Grad isolation | None | detach_reg_fpn option |

**GroupNorm instead of BN**: The original RetinaNet paper uses no normalization in subnets. This implementation adds GroupNorm(8) per conv layer. This is plausible for small-batch training (batch=2) where BN statistics are poor, but it increases per-anchor computation approximately 2x in the subnets (GN overhead). No correctness issue.

**detach_reg_fpn** (model.py:550): When enabled, `reg_feat = feat.detach()` prevents regression gradients from flowing back into shared FPN features. This is a training stability hack for --reinit-heads -- it prevents freshly initialized regression weights from corrupting FPN via gradient shock. Downside: the regression head can never learn to modulate FPN features, capping regressor performance. Confirmed safe because this is only enabled during RF1 recovery stages.

---

## 2. Anchor Box Generation and Matching

**AnchorGenerator** (model.py:434-482):
- 3 ratios x 3 scales = 9 anchors per FPN location
- 173,088 total anchors at 1280x720
- Anchor sizes: (96, 160, 256, 384, 512) -- calibrated via k-means on GT boxes (Doc 01 B.3)
- Comment in config (L268-271): k-means on 14,122 boxes gave (195,335,375,445,578) but these were too large, missing small GT (h_p10=156px). Current guess-based sizes were chosen empirically.

**Matching** (losses.py:91-132):
- CRITICAL BUG FIX (L95-99): Both anchors and GT boxes are now normalized to [0,1] before IoU matching. The original code skipped normalization, producing max IoU of 0.0001 << 0.5 threshold, causing zero positive matches and no learning.
- IoU thresholds: positive >= 0.5, negative < 0.4, ignore in [0.4, 0.5)
- GT guarantee (L129-130): for each GT box, the anchor with max IoU is forced to positive regardless of threshold.
- Empty GT (L104-106): returns all anchors as -2 (background) with zero boxes.

**Finding: Anchor sizes are not yet optimal.** The comment itself states the calibrated k-means sizes were too large and the current sizes were guess-based, giving only 0.0172 mAP. The extreme imbalance (99.3% empty frames) compounds this.

---

## 3. FocalLoss Integration -- Alpha/Gamma/Pi

### FOCAL_ALPHA = 0.90 (config.py:419)
The docstring in losses.py says alpha=0.25 (standard RetinaNet), but actual instantiation uses C.FOCAL_ALPHA=0.90. At the standard 0.25 positive weight, the 173K:1 neg/pos ratio produced net-negative gradient even with focal loss, causing cls_mean collapse to approximately -16 over ~850 steps. Alpha=0.90 ensures net-positive gradient.

### FOCAL_GAMMA = 2.0 (config.py:420) -- Modified by asymmetric gamma.

### Asymmetric Gamma (config.py:438-440, losses.py:302-310)
```
DET_ASYMMETRIC_GAMMA = True
DET_GAMMA_POS = 0.0   # No focal suppression on positives
DET_GAMMA_NEG = 2.0   # Standard focal suppression on negatives
```
Effect: positives get full CE gradient (gamma=0), negatives get standard gamma=2 suppression. At symmetric gamma=2, well-classified positives (p approximately 0.9) have near-zero gradient [(1-0.9)^2 * CE = 0.001 per anchor], allowing cumulative negative gradient to dominate. Gamma_pos=0 gives 75x more positive gradient.

### cls_score Bias Initialization (model.py:527-534)
```
pi = 0.03
nn.init.constant_(self.cls_score.bias, -math.log((1 - pi) / pi))
```
Math: `-log((1-0.03)/0.03)` = `-log(32.33)` = approximately -3.48
Standard RetinaNet uses pi=0.01 giving bias = -4.60. The 0.03 is intentionally "less aggressive".

**Stale docstring**: Class docstring L490-493 references "pi=0.01 bias init" but code uses pi=0.03. Documentation inconsistency, not a bug.

### Alpha Weight in Main Path (losses.py:309)
```
alpha_t = self.alpha * cls_target + (1 - self.alpha) * (1 - cls_target)
alpha = 0.90:
  - target=1 (foreground): alpha_t = 0.90
  - target=0 (background): alpha_t = 0.10
```
Correct per standard focal loss formulation.

---

## 4. Empty Frame Handling (the (1-alpha) Question)

**Finding: The (1-alpha) multiply on line 233 is mathematically correct for the empty-frame path.**

Code (losses.py:224-238):
```python
bg_p = torch.sigmoid(bg_cls).clamp(1e-7, 1.0 - 1e-7)
bg_ce = F.binary_cross_entropy_with_logits(bg_cls, bg_target, reduction='none')
bg_p_t = bg_p * bg_target + (1 - bg_p) * (1 - bg_target)
bg_focal = (1 - self.alpha) * (1 - bg_p_t).pow(self.gamma) * bg_ce
bg_loss = bg_focal.sum() * C.DET_EMPTY_BG_SCALE
```

Verification: Standard focal loss for background (target=0):
```
FL = -alpha_t * (1-p_t)^gamma * log(p_t)
where alpha_t = (1-alpha) for background, and p_t = (1-p) for target=0
```

The code computes `bg_p_t = (1-bg_p)` (since bg_target=0), then `bg_focal = (1-alpha) * (1-bg_p_t)^gamma * bg_ce`. Since bg_ce = -log(bg_p_t) = -log(1-bg_p), this is exactly standard background focal loss.

**The (1-alpha) = 0.10 scalar is correct for an all-background batch.**

### Empty-Frame vs Main-Path Background
Main path uses per-element `alpha_t` while empty path uses scalar `(1-alpha)`. Since all empty-frame targets are background, `alpha_t` would be uniform (0.10) for every anchor, making the scalar equivalent. **No correctness issue.**

### DET_EMPTY_SAMPLE and DET_EMPTY_BG_SCALE Tuning
The empty-frame loss went through three iterations:
1. **RC-28 original (skip)**: `continue` on empty frames -- eliminated the giant 130-200 negative gradient from 173K anchors, but left detection head with gradient on only ~0.7% of batches, causing weight drift.
2. **First fix (512 samples, 0.01 scale)**: Grad norm still decayed to 0.0049 (DEAD).
3. **Current (2048 samples, 0.05 scale)**: Produces ~0.005-0.9 loss per empty frame, keeping gradients alive.

---

## 5. Extreme Imbalance (99.3% Empty Frames) -- Is Focal Loss Handling It Correctly?

**Finding: Focal loss alone cannot handle this imbalance. The system uses a multi-layered defense:**

| Defense Layer | Mechanism | Status |
|--------------|-----------|--------|
| DET_GT_FRAME_FRACTION | Absolute per-batch GT fraction (0.9 = 90% GT-bearing) | Root fix, but defaults to 0.0 (OFF) |
| DET_EMPTY_SAMPLE | Subsampled background loss on empty frames (2048/173K anchors) | Active |
| DET_EMPTY_BG_SCALE | Scales empty-frame loss (0.05) | Active |
| Asymmetric Gamma | No focal suppression on positives | Active |
| alpha=0.90 | 9x foreground weight | Active |
| OHEM | Hard-negative mining (1:1 ratio, min 16 neg) | Active |
| TASK_AWARE_DET_BOOST | 2x sampling weight for GT frames | Active |
| Synthetic pretrain | 20 epochs of synthetic detection pretraining | Active when PRETRAIN_DET_ON_SYNTH=True |

**Critical gap**: `DET_GT_FRAME_FRACTION = 0.0` by default (config.py:531). This means the absolute GT-frame target is disabled unless explicitly set via env var or preset. Standard training without --preset gets 0.0 (off). Without it, the activity-balanced sampler draws GT-bearing frames at natural density (~0.7%), so ~99.3% of training steps see zero GT boxes.

---

## 6. Regression Loss (GIoU)

**Finding: GIoU replaces Smooth L1 with proper numerical guards.**

Key guards:
1. **Zero-area boxes**: Predicted boxes clamped to [0, IMG], enforced x2 >= x1 + 1.0, y2 >= y1 + 1.0
2. **NaN guard**: `torch.where(torch.isfinite(giou_loss), giou_loss, 0.0)`
3. **Zero-floor**: `loss_det = torch.where(loss_det < 0, 0.0, loss_det)` -- GIoU can be negative (range [-1, 1])
4. **Smooth cap**: `_smooth_cap(loss_det, cap=50.0)` -- preserves gradient above cap via `cap*(1+log(x/cap))`

**GIOU_WEIGHT = 2.0**: Regression weighted 2x vs classification.

**Reinit regression warmup**: When --reinit-heads active, reg_loss ramps from 0.01 to 1.0 over 1000 steps to prevent gradient shock.

---

## 7. Gradient Patterns

### OHEM Behavior
- `DET_OHEM_RATIO = 1.0`: Keeps 1 negative per positive (floor 16 negatives)
- With ~20 positives per GT-bearing image: keeps ~20 negatives total
- Extremely aggressive -- standard RetinaNet uses 3:1
- Without OHEM: cumulative gradient from 173K negatives collapses cls logits to -16 over ~850 steps

### Empty-Frame Gradient
- 2048 subsampled anchors x 0.05 scale = ~0.005-0.9 loss per empty frame
- Divided by `max(n_img_with_gt, 1)` -- all-empty batches divide by 1 (preserves gradient)
- With ~24% GT-bearing batches: detector sees positive signal on ~24% of steps

### detach_reg_fpn Gradient Isolation
- Reg subnet receives `feat.detach()` -- no reg gradients through FPN to backbone
- Cls subnet still gets gradients through FPN
- Prevents regression gradient shock from corrupting FPN
- Only for RF1 recovery stages

---

## 8. mAP Calculation Correctness

**Finding: mAP computation is correct with COCO-style protocol and per-class-present variant.**

- COCO 101-point interpolation across 11 IoU thresholds (0.5:0.05:1.0)
- Per-class 0.5-IoU NMS, max 300 detections
- Returns both COCO-style mAP@50 and mAP@50:95
- Per-class-present variant (`det_mAP50_pc`) excludes zero-GT classes from mean
- `DET_METRICS_EVERY_N` skips full mAP on non-metric epochs (performance optimization)

**Concern**: `score_thresh=0.5` in compute_detection_map is high for early training. Most scores below 0.5 produce zero predictions and mAP=0. Config.py L310 comments acknowledge this but the eval threshold remains 0.5.

---

## 9. NMS and Post-Processing

- **NMS**: `torchvision.ops.nms` per class -- standard
- **Score filter**: > 0.5 (high threshold)
- **Max detections**: 1000 per image in top-k, then NMS to top_k (default 10 in ROIDetector)

---

## 10. Findings Summary

### Verified Correct
- Anchor matching normalization bug fix (pixel-to-unit IoU)
- Empty-frame (1-alpha) multiplication is mathematically correct
- Asymmetric gamma formulation is correct
- GIoU regression with all numerical guards
- mAP computation with COCO protocol and per-class-present variant
- OHEM correctly subsamples negatives by hardest loss

### Issues Found

| # | Severity | Issue | Location |
|---|----------|-------|----------|
| 1 | MEDIUM | DET_GT_FRAME_FRACTION defaults to 0.0 -- the root fix for 99.3% empty frame imbalance is OFF by default | config.py:531 |
| 2 | LOW | cls_score bias docstring says pi=0.01 but code uses pi=0.03; stale docstring | model.py:490 vs 527 |
| 3 | MEDIUM | DET_EVAL_SCORE_THRESH=0.5 is too high for early training -- filters out most predictions, producing spurious mAP=0 | evaluate.py:162, config.py:310 |
| 4 | LOW | Anchor sizes are guess-based, not properly k-means calibrated for current data distribution | config.py:268-271 |
| 5 | INFO | Empty-frame loss denominator `max(n_img_with_gt, 1)` makes loss scale batch-composition-dependent | losses.py:352 |

### Recommendations
1. **Enable DET_GT_FRAME_FRACTION by default** at 0.4 in standard config, not just via --preset. Without it, the detector sees positive gradient on <1% of steps.
2. **Lower eval score_thresh** to 0.05 for early-training mAP, with 0.5 as a separate high-precision metric.
3. **Re-run anchor k-means calibration** on the full training set now that the loss functions are stable, and document the process.
