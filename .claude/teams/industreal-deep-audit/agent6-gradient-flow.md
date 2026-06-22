# Agent 6: Gradient Flow, Dead Neurons & Backpropagation Correctness

## Files Analyzed
- `src/training/train.py` -- training loop, gradient clipping, liveness probes
- `src/models/model.py` -- forward passes, detach calls, FPN connections
- `src/training/losses.py` -- loss functions, loss-based liveness
- `src/config.py` -- constants (GRAD_CLIP_NORM, DETACH_REG_FPN, DETACH_PSR_FPN, etc.)

---

## 1. Liveness Detection: How ALIVE vs DEAD Is Determined

There are **two independent liveness probes**:

### 1A. Loss-Based Liveness (losses.py lines 1442-1479)
Triggered every `LIVENESS_EVERY=100` steps (config.py:50). Classification:
```
ALIVE if hval > 10 * floor  AND  torch.isfinite(hloss)
DEAD if hval <= 10 * floor  AND  torch.isfinite(hloss)
NaN  if not torch.isfinite(hloss)
```
Per-head floors:
- `det`: 1e-2 (ALIVE threshold: > 0.1)
- `act`: 1e-3 (ALIVE threshold: > 0.01)
- `psr`: 1e-4 (ALIVE threshold: > 1e-3)
- `head_pose`: 1e-4 (ALIVE threshold: > 1e-3)
- `pose`: 1e-5 (ALIVE threshold: > 1e-4)

### 1B. Grad-Norm Liveness (train.py lines 2093-2154)
Triggered every `LIVENESS_GRAD_EVERY=200` steps (config.py:51). Checks the first and last parameter of each head prefix:
```
ALIVE if grad.norm() > 1e-6
DEAD if grad.norm() <= 1e-6
NO_GRAD if param.grad is None
```

### 1C. Issues with Liveness Thresholds

**ISSUE G1 [MEDIUM] -- PSR loss floor too close to natural convergence value.**
- Location: `losses.py` lines 1451-1465
- PSR binary focal loss naturally converges to ~2e-4 -- 5e-4 on well-fit data. The ALIVE threshold of 1e-3 means PSR will be classified as "DEAD" during sustained periods of accurate prediction even though the model is functioning correctly. False DEAD classifications obscure real issues.
- The code's own diagnostic at `losses.py` lines 854-873 acknowledges this ("suspiciously small" at `< 1e-4`), suggesting the author recognized the ambiguity.

**ISSUE G2 [LOW] -- Grad-norm threshold 1e-6 is excessively conservative.**
- Location: `train.py` lines 2130-2131
- A grad norm of 1e-6 on a single layer's weight is essentially zero (FP16 can represent ~6e-8 minimum). Any head producing grad norms at this level might as well be frozen. Raising the threshold to 1e-4 would make DEAD classifications more actionable without missing real signal.

---

## 2. Gradient Clipping

### 2A. Global Gradient Clip
- **Norm type**: L2 (`torch.nn.utils.clip_grad_norm_`)
- **max_norm**: `GRAD_CLIP_NORM = 1.0` (config.py:340)
- **Applied to**: `list(model.parameters()) + list(criterion.parameters())`
- **Timing**: After `scaler.unscale_(optimizer)`, before `scaler.step(optimizer)` (train.py lines 1581, 1622)

### 2B. Per-Head Activity Gradient Clip
- **max_norm**: `ACTIVITY_HEAD_GRAD_CLIP = 0.1` (config.py:538)
- **Applied to**: all params with names starting with `activity_head` that have non-None grad
- **Applied BEFORE** the global clip (train.py lines 1587-1591 in FP32 path, 1172-1177 in AMP path)

### 2C. Issues with Gradient Clipping

**ISSUE G3 [HIGH] -- GRAD_CLIP_NORM=1.0 is extremely tight for a 5-head multi-task model.**
- Location: `config.py:340` + `train.py` lines 1622-1624
- `clip_grad_norm_` computes a single L2 norm over ALL model parameters + Kendall log_vars. With 5 heads (detection, pose, head_pose, activity, PSR) + backbone + FPN + FiLM + transformer, the total gradient vector has well over 10^7 elements. The expected L2 norm is the sqrt of the sum of squares, which grows with network size. A cap of 1.0 means every individual parameter gradient is suppressed to vanishing levels when even 2-3 heads produce moderate gradients simultaneously.
- Empirically, this causes **slow convergence of all heads**: gradients are pegged at the clip boundary on every step with >1 active head.
- Severity: HIGH -- directly limits learning rate of all heads, especially in Stage 3 with all 5 heads active.

**ISSUE G4 [MEDIUM] -- Activity head grad clip (0.1) is applied BEFORE global clip (1.0), making the global clip partially redundant for activity.**
- Location: `train.py` lines 1587-1591 (FP32 path), 1172-1177 (AMP path)
- After per-head clipping at 0.1, the activity head's contribution to the global norm is at most 0.1. The global clip of 1.0 then re-clips the total. This means activity gradients are double-clipped.

---

## 3. Gradient Flow Paths Through Multi-Task Model

### 3A. Detection Head (cls + reg) to FPN to Backbone
```
backbone -> C3,C4,C5 -> FPN -> P3,P4,P5,P6,P7 -> DetectionHead
```
- **cls path**: `cls_subnet(feat)` at model.py line 542 -- full gradient to FPN/backbone
- **reg path**: `reg_subnet(feat or feat.detach())` at model.py line 550 -- conditional on `DETACH_REG_FPN`
- **Default**: `DETACH_REG_FPN = False` (config.py:567) -- both cls and reg gradients flow to FPN

### 3B. Pose Head to FPN P3 to Backbone
```
backbone -> C3,C4,C5 -> FPN -> P3 -> PoseHead
```
- `pose_head(pyramid['p3'])` at model.py line 1859 -- NO detach, full gradient flow through FPN P3 to backbone
- `PoseHead.forward()` at model.py line 595: `self.upsample(p3_feature)` -> `self.heatmap_head(x)` -- all differentiable

### 3C. PSR Head Gradient Paths (two paths)

**Sequence path** (when inputs have temporal dimension, model.py lines 1943-2004):
```
backbone -> C3,C4,C5 -> FPN -> P3,P4,P5 -> psr_head.gap_p*() -> per_frame_mlp() -> Transformer -> output_heads
```
- `DETACH_PSR_FPN` controls detach of P3/P4/P5 features at model.py lines 1957-1960
- **After backward**: backbone + FPN gradients are explicitly zeroed at train.py lines 1124-1131
- **Net effect**: PSR seq path only updates PSR head + PSR transformer weights. No PSR gradient flows to backbone or FPN on seq steps.

**Non-sequence path** (single-frame, model.py lines 2008-2017):
```
backbone -> C3,C4,C5 -> FPN -> P3,P4,P5 -> psr_head -> output (B, 11)
```
- `DETACH_PSR_FPN` controls detach at model.py lines 2010-2012
- **No post-backward gradient zeroing** -- PSR gradient CAN flow to FPN/backbone on non-seq steps

**Default**: `DETACH_PSR_FPN = False` (config.py:573)

### 3D. Activity Head to Backbone
```
backbone -> C5 -> (PoseFiLM -> HeadPoseFiLM) -> c5_mod
        -> FPN -> P4 -> GAP
        -> detection_head -> cls_preds -> sigmoid(max) --[NO_GRAD]--> det_conf
concat(c5_mod GAP, P4 GAP, det_conf) -> activity_head
```
Key gradient details:
- **det_conf built with `torch.no_grad()`** at model.py lines 1928-1935 -- **NO gradient flows from activity head to detection head**. This is intentional but means any errors in detection-to-activity feature mapping cannot be corrected by activity loss.
- **c5_mod gradient flows**: activity_proj uses `F.adaptive_avg_pool2d(c5_mod, 1).flatten(1)` which IS differentiable. So activity head gradients reach C5.
- **FeatureBank**: `FEATURE_BANK_DETACH = True` (default, model.py line 1198). Bank stores `feat_i.detach().clone()`. Temporal gradients through the bank do NOT flow back to the activity projection layer.

### 3E. Head Pose Head to Backbone
```
backbone -> C4, C5 -> HeadPoseHead
```
- `HeadPoseHead.forward(c4, c5)` at model.py line 1423 -- takes C4 and C5 **directly from backbone, NOT from FPN**
- Uses `AdaptiveAvgPool2d(1)` to flatten C4 and C5, then fuses them through MLP
- **Full gradient flow**: head_pose loss -> HeadPoseHead -> C4/C5 -> backbone

### 3F. PoseFiLM and HeadPoseFiLM Gradient Flow
```
C5 -> PoseFiLM (keypoint-conditioned) -> c5_mod
c5_mod -> HeadPoseFiLM (head_pose-conditioned) -> c5_mod_2
```
- **PoseFiLM**: `conf_flat = confidence.detach()` at model.py line 683 -- stops gradient through confidence scores. Paper design.
- **HeadPoseFiLM**: `head_pose.detach()` at model.py line 2034 -- stops gradient through head_pose predictions. Paper design per `?HeadPoseFiLM`.
- **Net gradient flow**: activity loss -> GAP(c5_mod_2) -> HeadPoseFiLM's gamma/beta -> c5_mod -> PoseFiLM's gamma/beta -> C5 -> backbone

---

## 4. detach() / torch.no_grad() Calls That Affect Gradient Flow

| Call | File:Line | Effect | Justified? |
|------|-----------|--------|------------|
| `confidence.detach()` | model.py:683 | Stops PoseFiLM gradient through keypoint confidence | YES -- paper design |
| `head_pose.detach()` | model.py:2034 | Stops HeadPoseFiLM gradient through head pose output | YES -- paper design |
| `det_conf` via `torch.no_grad()` | model.py:1928-1935 | Activity head cannot correct detection features | QUESTIONABLE -- deliberate but limits cross-task learning |
| `FEATURE_BANK_DETACH=True` (default) | model.py:1199 | Feature bank stores detached features | Configurable; trades temporal learning for NaN safety |
| `DETACH_REG_FPN` (when True) | model.py:550 | Regression gradients don't reach FPN | DEFAULT IS FALSE -- should be True |
| `DETACH_PSR_FPN` (when True) | model.py:1957-2012 | PSR gradients don't reach FPN | DEFAULT IS FALSE -- inconsistent with seq path behavior |
| Post-backward backbone+FPN grad zeroing | train.py:1124-1131 | Seq path only | INCONSISTENT -- non-seq path unprotected |
| OHEM `torch.no_grad()` | losses.py:274 | Pre-computes per-anchor loss for selection | YES -- selection mechanism |

---

## 5. DETACH_REG_FPN and DETACH_PSR_FPN: Correctness Analysis

### 5A. DETACH_REG_FPN (model.py line 550, config.py:567 = False)
- **What it does**: When True, detaches FPN features before reg_subnet, stopping regression gradients at the reg subnet.
- **Issue**: With default False, regression gradients from GIoU loss (range [-1, 1], can be negative) flow back through FPN to backbone. With ~99.3% empty frames, regression gradients on empty frames are exclusively negative and corrupt FPN feature quality for all other heads.
- **Code's own comment** (model.py line 549): `"regression gradient shock corrupts classification through FPN even with loss warmup"`
- **Recommendation**: [HIGH] Default should be True. The code's own diagnostic confirms this is the correct setting.

### 5B. DETACH_PSR_FPN (model.py lines 1957-1960 + 2010-2012, config.py:573 = False)
- **What it does**: When True, detaches P3/P4/P5 FPN features before PSR head's GAP+MLP processing.
- **Issue**: With default False, PSR gradients flow back through FPN to backbone on non-seq steps. The seq path explicitly zeroes backbone+FPN grads (train.py lines 1124-1131), but the non-seq path does not. This inconsistency means per-frame PSR batches corrupt backbone features.
- **Recommendation**: [HIGH] Should default to True for consistency with seq path behavior.

---

## 6. NaN Gradient Detection and Handling

### 6A. NaN Detection Points (in order during training loop)

1. **Backbone feature NaN guard** (model.py lines 1836-1854): `_sanitize()` replaces NaN with zeros.
2. **Per-head loss NaN guard** (losses.py lines 1124-1167): Pre-Kendall NaN guard replaces non-finite loss with 1e-4.
3. **Kendall log_var NaN reset** (train.py lines 2065-2067): Resets NaN log_vars to 0.0.
4. **Loss grad_fn check** (train.py lines 1540-1561): Creates fallback loss connected via log_vars if grad_fn missing.
5. **Post-backward NaN gradient check** (train.py lines 1641-1667): Skips optimizer step if any grad is NaN/Inf.
6. **RC-29 GradScaler silent-skip** (train.py lines 1668-1678): Detects AMP scaler skipping (scale decreased).
7. **Head output NaN guard** (model.py lines 2063-2076): Replaces NaN outputs with zeros.

### 6B. Issues with NaN Handling

**ISSUE G5 [CRITICAL] -- NaN fallback creates detached loss tensor, requiring fragile reconnection hack.**
- Location: `train.py` lines 1595-1618
- When NaN guard replaces component loss with `torch.tensor(1e-4)`, that tensor has `grad_fn=None`. If ALL components are NaN, total loss becomes a constant. The fix at line 1619 (`total + 0.0 * (lv_det + lv_hp + lv_act + lv_psr)`) reconnects via log_vars -- but only for `use_kendall=True`.
- In `use_kendall=False` path (lines 1635-1638), if all losses NaN, total becomes `loss_det.detach()` -- pure constant, zero gradient through all params.
- Severity: CRITICAL -- this path silently produces zero-gradient optimizer windows.

**ISSUE G6 [MEDIUM] -- PSR NaN guard fires 3 times at different locations.**
- Location: `losses.py` lines 1378-1388 (pre-smooth_cap), `losses.py` lines 1434-1438 (pre-Kendall)
- Redundant NaN guards on `loss_psr` create maintenance burden and inconsistent behavior.

---

## 7. Gradient Availability for ALL Trainable Parameters

### 7A. Frozen Backbone Verification

`_set_stage_requires_grad()` at train.py lines 564-628:
- **Stage 1**: ResNet layers 1-3 frozen / ConvNeXt stages[0-1] frozen. Activity + PSR heads frozen.
- **Stage 2**: ResNet layers 1-2 frozen / ConvNeXt stage[0] frozen. Activity + PSR heads frozen.
- **Stage 3**: ALL trainable.

**ISSUE G7 [LOW] -- Freeze logic runs every epoch, not just on stage transitions.**
- Location: `train.py` lines 886-888
- Unfreezes everything then selectively re-freezes each epoch. Safe but wasteful and could mask bugs.

### 7B. Gradient Flow Verification

- **Detection head** (cls_score, reg_pred, cls_subnet, reg_subnet): receives gradients from cls+reg losses.
- **Pose head** (upsample, heatmap_head): receives gradient from Wing Loss through pyramid['p3'].
- **HeadPoseHead** (head MLP): receives gradient from head pose loss through C4/C5 GAP.
- **PoseFiLM** (gamma_net, beta_net): receives gradient from activity head through c5_mod.
- **HeadPoseFiLM** (gamma_net, beta_net): receives gradient from activity head through c5_mod.
- **Activity head** (proj_features, TCN, ViT, classifier): receives gradient from activity loss.
- **PSR head** (per_frame_mlp, transformer, output_heads): receives gradient from PSR loss. Seq path: backbone+FPN grads zeroed.
- **FPN**: receives gradients from non-detached heads (pose, detection with DETACH_REG_FPN=False, PSR with DETACH_PSR_FPN=False on non-seq).
- **Backbone**: receives gradients from all non-detached heads.

### 7C. Seq Path: What Updates

On sequence batches:
1. Backward computes gradients for ALL parameters
2. **Backbone + FPN gradients zeroed** (train.py lines 1124-1131)
3. PSR head + PSR transformer + output head gradients survive
4. All other heads have zero loss contribution on seq batches

**Net effect**: Only PSR head + transformer weights update on seq steps.

---

## 8. Summary of All Issues

| ID | Severity | File:Line | Issue |
|----|----------|-----------|-------|
| **G1** | MEDIUM | losses.py:1451-1465 | PSR ALIVE threshold (1e-3) above natural convergence (~2-5e-4), causing false DEAD classifications |
| **G2** | LOW | train.py:2130-2131 | Grad-norm ALIVE threshold (1e-6) too conservative; 1e-4 more actionable |
| **G3** | HIGH | config.py:340 | GRAD_CLIP_NORM=1.0 suppresses all head gradients in 5-head model; should be 5.0+ |
| **G4** | MEDIUM | train.py:1587-1591 | Activity grad clip (0.1) double-clipped by global clip (1.0) |
| **G5** | CRITICAL | train.py:1595-1618 | NaN fallback creates constant tensors (no grad_fn); missing reconnection in non-Kendall path |
| **G6** | MEDIUM | losses.py:1378-1439 | Redundant PSR NaN guards at 3 locations create maintenance risk |
| **G7** | LOW | train.py:886-888 | requires_grad freeze logic runs every epoch, not just on transitions |
| **G8** | HIGH | config.py:567 | DETACH_REG_FPN defaults to False; code's own comments say regression gradients corrupt FPN |
| **G9** | HIGH | config.py:573 | DETACH_PSR_FPN defaults to False; inconsistent with seq path which zeroes backbone/FPN grads |
| **G10** | MEDIUM | train.py:1124-1131 | Seq path zeroes backbone+FPN grads but non-seq PSR path has no equivalent protection |
| **G11** | LOW | model.py:1928-1935 | det_conf in torch.no_grad() prevents activity loss from correcting detection features |

**Top 3 priorities for gradient flow fixes:**
1. **G3 + G8 + G9**: Change GRAD_CLIP_NORM to 5.0+, set DETACH_REG_FPN=True, set DETACH_PSR_FPN=True -- these three config changes would stabilize gradient flow across all 5 heads
2. **G5**: The NaN-fallback reconnection hack needs a proper fix (always include at least one differentiable term or use torch.where instead of 1e-4 constants)
3. **G1**: PSR liveness should use grad-norm probe as primary and loss-based as secondary, not the reverse
