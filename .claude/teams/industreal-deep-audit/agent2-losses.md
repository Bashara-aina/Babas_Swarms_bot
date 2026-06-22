# Agent 2: Loss Functions — Deep Audit Findings

**Files analyzed:**
- `/media/newadmin/master/POPW/working/code/industreal_improved/src/training/losses.py` (1684 lines)
- `/media/newadmin/master/POPW/working/code/industreal_improved/src/training/train.py` (key sections)
- `/media/newadmin/master/POPW/working/code/industreal_improved/src/config.py` (loss hyperparameters)

---

## HIGH Severity

### H1. GIoU `reduction='sum'` with per-image normalization vs global mean [losses.py:338, 346, 352]

The GIoU loss uses `reduction='sum'` at line 338, then divides by `num_pos` at line 346. Each image's GIoU is normalized by its own positive count. Then `total_reg` is divided by `n_img_with_gt` at line 352. This gives:

```
final_reg_loss = (1/N) * sum_over_images(giou_sum_i / num_pos_i)
```

where `N = n_img_with_gt`. This means images with FEW positives get the SAME weight in the final average as images with MANY positives. A frame with 2 positive anchors contributes the same as a frame with 50. The regression gradient from dense-positive frames is diluted by sparse-positive frames.

**Fix:** Accumulate `giou_loss_sum` and `pos_count_sum` separately, then divide once at the end.

### H2. PSR BCE fallback path silently ignores -1 targets [losses.py:1000, 1328]

When `USE_PSR_FOCAL` is False (i.e., `PSR_FOCAL_GAMMA = 0`), the loss falls back to:
```python
self.psr_loss_fn = nn.BCEWithLogitsLoss(reduction='mean')
```
Called at line 1328: `loss_psr = self.psr_loss_fn(outputs['psr_logits'], _psr_targets)`.

The `binary_focal_loss` function at lines 804-827 carefully masks -1 ignore labels. But the BCE fallback path has NO such masking. BCEWithLogitsLoss with target=-1 produces: `loss = -(-1)*log(p) - (1-(-1))*log(1-p) = log(p) - 2*log(1-p)`, which is completely wrong. This corrupts the loss on any batch containing error-state frames.

### H3. Kendall NaN guard disconnects computation graph [losses.py:1429-1439, 1619]

The `_safe()` lambda at line 1429 creates a new `torch.tensor(1e-4, ...)` when a loss is non-finite. This tensor has NO gradient connection to the model. The reconnection at line 1619 (`total = total + 0.0 * (lv_det + lv_hp + lv_act + lv_psr)`) adds zero-weighted log_vars but the actual loss values still have zero gradient. The backward pass trains only Kendall log_vars and wastes the batch.

---

## MEDIUM Severity

### M1. Double activity ramp when STAGED_TRAINING=True [losses.py:1250-1252, 1520-1532]

Activity loss is ramped TWICE when staged training is enabled:

1. **Line 1250-1252**: `loss_act = loss_act * act_ramp` -- multiplies raw activity loss by the ramp.
2. **Lines 1520-1524 + 1532/1537**: `prec_act = prec_act * act_ramp` -- multiplies Kendall precision by the ramp again.

The effective activity contribution is `ramp^2`. At epoch 0 (ramp=0.2): effective = 0.04x instead of 0.2x.

Currently latent because `STAGED_TRAINING = False` in config.py:472.

### M2. Head pose loss dropped when train_act=False [losses.py:1561-1569]

The condition at line 1561 uses `self.train_act` to gate head pose inclusion:
```python
if self.train_pose or self.train_act:
    ...
    elif self.train_pose:
        pose_contribution = prec_hp * loss_pose + lv_hp  # NO HEAD POSE!
```
When `train_pose=True, train_act=False` the `elif` branch excludes `loss_head_pose`. The `train_act` flag is an incorrect proxy. Latent in current config (`TRAIN_ACT=True`).

### M3. Classification loss in all-GT-free batches scales with batch size [losses.py:234, 352]

When ALL images have no GT boxes, `n_img_with_gt=0` and the return divides by `max(0,1)=1`. The `total_cls` is SUM of background focal losses over all empty images. A batch with 8 empty frames produces ~8x more loss than 1 empty frame, so the loss magnitude bounces depending on empty-frame density.

### M4. LDAM s*x_m clamp at +/-50 kills gradient for high-margin classes [losses.py:611]

```python
logits_safe = (self.s * x_m).clamp(-50.0, 50.0)
```

With `s=30` and `x_m` at extreme values (high-margin rare classes), the product exceeds +/-50, and the gradient through clamp is zero. The model cannot reduce extreme logits for rare classes.

### M5. PSR binary_focal_loss logit clamp at +/-8 may be too aggressive [losses.py:798]

Sigmoid is already fully saturated at +/-8 (p=0.9997 / p=0.0003), and gradient at those limits is near zero. Well-tuned for stability (multiple historical fixes), but prevents the model from achieving very high confidence.

---

## LOW Severity

### L1. Inconsistent epsilon bounds [losses.py:297 vs 830]
Detection path uses `1e-7`, PSR path uses `1e-6`. Minor inconsistency, both prevent log(0).

### L2. PSR temporal smoothing uses mean-of-all-components [losses.py:1360-1366]
Averaging 11 components into a scalar before comparison means a single-component transition is diluted to ~0.09. If the model misses the only meaningful transition, the smooth loss is near zero.

### L3. PSR seq batch logging always shows zero [train.py:1090-1092]
The scaled `loss_dict_seq['psr']` is overwritten by line 1092's dict clear. Backward gets the correct scaled loss, but logging shows `psr=0.000` for all sequence batches.

### L4. getattr fallback pattern [config.py:489, losses.py:1196]
`float(getattr(C, 'POSE_LOSS_WEIGHT', 0.02))` silently reverts to fallback if key is renamed/removed. This fragile pattern appears at ~10+ locations in losses.py.

### L5. Duplicate Kendall clamp [losses.py:1490-1493, train.py:992]
In-forward `.clamp()` (+reduntant) duplicates in-parameter `clamp_()` at train.py:992. Harmless but wastes compute.

---

## Correctness Verifications (No issues found)

- **FocalLoss alpha=0.90**: Empty-frame path uses `(1-self.alpha) = 0.10`, consistent with line 309's `alpha_t = 1-alpha` for background. Positives correctly get 9x weight. Verified.
- **pi=0.01 bias init**: Target `sigmoid~0.01` corresponds to `logit~-4.6`, which matches `b = -log((1-pi)/pi) = -log(99)`. Verified correct.
- **OHEM**: Correctly keeps all positives + top-K hardest negatives using `ce_pre.sum(dim=1)` as per-anchor hardness metric. `num_pos` floor prevents div-by-zero. Verified.
- **Empty-frame subsampling (RC-28)**: Uses `torch.randperm` for unbiased 2048-anchor subsampling. Loss scaled by `DET_EMPTY_BG_SCALE=0.05`. Verified.
- **GIoU NaN guard**: `torch.where(isfinite, loss, 0.0)` preserves gradient graph structure. Verified.
- **Kendall graph reconnection**: `0.0 * log_vars` correctly keeps graph alive without training log_vars from NaN fallback. Verified.

## Config Values (at audit time)
| Param | Value | Param | Value |
|-------|-------|-------|-------|
| FOCAL_ALPHA | 0.90 | FOCAL_GAMMA | 2.0 |
| GIOU_WEIGHT | 2.0 | DET_OHEM_RATIO | 1.0 |
| DET_GAMMA_POS | 0.0 | DET_GAMMA_NEG | 2.0 |
| PSR_FOCAL_ALPHA | 0.25 | PSR_FOCAL_GAMMA | 1.0 |
| USE_LDAM_DRW | False | CB_GAMMA | 1.0 |
| ACTIVITY_LOSS_WEIGHT | 0.2 | PSR_WEIGHT | 20.0 |
| POSE_LOSS_WEIGHT | 0.01 | STAGED_TRAINING | False |
| KENDALL_LOG_VAR_MIN_ACT | -0.5 | KENDALL_LOG_VAR_MAX_PSR | 0.0 |
| KENDALL_LOG_VAR_MAX_POSE | 3.0 | PSR_SENSITIVITY_WEIGHT | 0.01 |
