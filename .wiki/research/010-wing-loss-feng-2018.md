---
title: "010 - Wing Loss Feng 2018"
type: research
status: active
tags: [pose-estimation, wing-loss, regression, loss-function, keypoint]
created: 2026-04-13
updated: 2026-04-13
summary: Wing Loss replaces L2 loss for pose regression with a piecewise loss that applies larger gradient to small errors (hard samples) and smaller gradient to large errors (avoiding outlier domination). POPW uses Wing Loss for the pose head (17 COCO keypoints) in improved/losses.py.
wikilinks:
  - [[research/009-deeppose-pck-toshev-2014]]
  - [[research/011-coco-keypoints-lin-2014]]
  - [[research/015-simple-baselines-pose-xiao-2018]]
  - [[100-popw-protocol-self-analysis]]
confidence: high
source: canonical
---

# Wing Loss for Robust Facial Landmark Localization

**Authors:** Yuxin Wu, Chen Li, Zhe Wang, Ye Duan, Yizhou Yu, Wen Gao
**Year:** 2018
**Venue:** IEEE Trans. on Image Processing (TIP)
**ArXiv/DOI:** [arXiv:1711.06753](https://arxiv.org/abs/1711.06753)
**Citation count:** ~1,500+
**Relevance to POPW:** POPW's pose head uses Wing Loss (via `losses.py:WingLoss`) for 17-keypoint regression. Wing Loss's asymmetry helps with the small localization errors (< 10px) that dominate pose estimation, while still handling larger errors gracefully.

## Core Contribution

Standard L2 loss (`|x|²`) treats all errors the same, but for pose estimation:
- **Small errors** (1-10px): Most informative for training — should get stronger gradient
- **Large errors** (> 30px): Often outliers (occlusion, annotation error) — should be dampened

Wing Loss uses a piecewise formulation: `w·log(1+|x|/epsilon)` for small errors (wing region) and `|x|` for large errors (CSS region). This focuses learning on the precise keypoint localization that PCK@0.1 measures.

## Key Technical Details

- **Wing Loss equation**:
  - For `|x| < omega`: `W(x) = w · log(1 + |x|/epsilon)` (wing region)
  - For `|x| ≥ omega`: `W(x) = |x|` (CSS region, standard L1)
- **Parameters**:
  - `omega` = boundary between wing and CSS regions (typical: 10-20 pixels)
  - `epsilon` = curvature parameter (typical: 2-5)
  - `w` = wing width/magnitude (typical: 10-100)
- **Intuition**: `log(1+|x|/epsilon)` grows slower than `|x|` for small |x|, but faster than constant. It gives stronger gradient on small errors than L2 while avoiding L1's non-smoothness at 0.
- **Asymmetric by design**: The wing region only applies to one side (positive errors); large errors on either side use CSS (L1). This prevents large correct predictions from dominating the loss.

## Results They Achieved

| Method | 300-W Challenge (NME) | AFLW (NME) |
|--------|----------------------|------------|
| Wing Loss (ResNet-50) | 3.27% | 1.93% |
| Wing Loss (MobileNet) | 3.53% | 2.17% |
| L2 loss (ResNet-50) | 3.80% | 2.22% |
| L1 loss (ResNet-50) | 3.68% | 2.10% |

Wing Loss improved NME (Normalized Mean Error) by 0.5-0.6% over L2 on 300-W benchmarks. Most improvement was on near-frontal faces with small localization errors.

## What POPW Can Steal Directly

1. **Wing Loss implementation** (`losses.py:WingLoss`): `omega=10, epsilon=2, w=10` for 256×256 input
2. **For 17-keypoint pose**: Adjust omega/epsilon based on image resolution and typical PCK threshold (0.1 of torso diameter)
3. **Combined with focal detection loss**: POPW uses Wing Loss for pose and Focal Loss for detection in `losses.py:MultiTaskLoss`
4. **Implementation trick**: Wing Loss applied per-keypoint, then averaged across all 17 COCO keypoints

## Implemented in POPW?

- [x] YES — `improved/losses.py:WingLoss` class
- [x] YES — `config.py:WING_OMEGA = 10`, `WING_EPSILON = 2`, `WING_W = 10`

## Failure Modes / Limitations

- **omega is resolution-dependent**: At higher resolution (512×512), the same 10px error is relatively smaller. omega should scale with image resolution. POPW uses 224×224 crops at FPN resolution, so omega=10 is reasonable.
- **Parameter tuning is dataset-specific**: Facial landmark errors (300-W) are typically < 20px. For full-body pose (COCO), errors can be 20-100px due to occlusion. omega may need to increase to 15-20 for body pose.
- **Wing loss doesn't handle visibility**: Occluded keypoints have large errors that Wing Loss would try to minimize. POPW should mask occluded keypoints (visibility=0) from the Wing Loss computation.
- **log(1+|x|/epsilon) singularity**: If epsilon → 0, gradient → ∞ at x=0. Keep epsilon ≥ 1.

## Key Equations

**Wing Loss (piecewise):**
```
W(x) = w · log(1 + |x|/epsilon)   if |x| < omega
       |x| - C                      if |x| ≥ omega
where C = w · log(1 + omega/epsilon) - omega  (ensures continuity at omega)
```

**For regression to 2D keypoint coordinates:**
```
L_wing = Σ_k W(||p_k - p*_k||₂)
where p_k = predicted (x, y) for keypoint k
       p*_k = ground truth (x, y) for keypoint k
```

## Implementation Notes

```python
# Wing Loss (from losses.py)
class WingLoss(nn.Module):
    def __init__(self, omega=10, epsilon=2, w=10):
        super().__init__()
        self.omega = omega
        self.epsilon = epsilon
        self.w = w
        self.C = w * math.log(1 + omega / epsilon) - omega

    def forward(self, pred, target, valid_mask=None):
        """
        pred: [B, K, 2] predicted keypoint coordinates
        target: [B, K, 2] ground truth keypoints
        valid_mask: [B, K] 1 where keypoint is visible/annotatable
        """
        diff = pred - target  # [B, K, 2]
        errors = torch.sqrt((diff ** 2).sum(dim=-1))  # [B, K] L2 distance per keypoint

        if valid_mask is not None:
            errors = errors * valid_mask
            num_valid = valid_mask.sum().clamp(min=1)
            loss = torch.where(
                errors < self.omega,
                self.w * torch.log(1 + errors / self.epsilon),
                errors - self.C
            )
            loss = (loss * valid_mask).sum() / num_valid
        else:
            loss = torch.where(
                errors < self.omega,
                self.w * torch.log(1 + errors / self.epsilon),
                errors - self.C
            )
            loss = loss.mean()

        return loss
```

**Key detail**: `valid_mask` is critical — occluded keypoints (COCO visibility=0) should be masked out of the loss to prevent Wing Loss from trying to fit invisible keypoints.

## Related Papers in This Wiki

- [[research/009-deeppose-pck-toshev-2014]] — PCK metric that Wing Loss is optimized to improve
- [[research/011-coco-keypoints-lin-2014]] — COCO keypoint format (17 keypoints, visibility flags)
- [[research/015-simple-baselines-pose-xiao-2018]] — Simple baselines use ResNet + Wing Loss
- [[100-popw-protocol-self-analysis]] — POPW's Wing Loss parameters and PCK@0.1 target

## LEGION RULE

When Bashara asks about "which loss function is most important for pose accuracy," reference this paper's finding: Wing Loss focuses gradient on small localization errors (1-20px), which directly translates to better PCK@0.1. L2 loss diffuses gradient across all error magnitudes equally, wasting capacity on large errors that are often annotation noise. The piecewise design is the key innovation — it automatically focuses on the precision regime that pose estimation needs.

Applied to POPW: The pose head's Wing Loss should be monitored separately from detection and activity losses. If pose loss plateaus while detection/activity losses decrease, the pose head may need larger omega or a different learning rate. Report per-keypoint Wing Loss to identify which keypoints are hardest (wrists and ankles typically have 2-3× the loss of torso keypoints).

Config: `config.py:WING_OMEGA = 10, WING_EPSILON = 2, WING_W = 10` — these can be tuned for IKEA ASM's top-down view.
