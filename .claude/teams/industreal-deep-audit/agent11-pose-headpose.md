# Agent 11: Pose Estimation & Head Pose Estimation Audit

## Executive Summary

The body pose head is a **heatmap-based keypoint estimator** using soft-argmax with Wing Loss, but operates **without real keypoint annotations** (no COCO-style labels in IndustReal). The head pose head uses either a **raw 9-DoF MSE regression** (`HeadPoseHead`) or a **6D rotation representation** (`GeometryAwareHeadPose`). Both share FPN features with detection, but head pose suffers from **60+ degree angular MAE** -- barely better than chance. The NO_GRAD liveness warnings for `pose_head` and `head_pose_head` during RF1 are **expected** due to staged training (Stage 1 freezes pose + head_pose), but the `pose_head` is architecturally **vestigial** in IndustReal.

---

## 1. Pose Head: Heatmap-Based (Correct Architecture)

**File:** `src/models/model.py` line 561

```
class PoseHead(nn.Module):
    # ConvTranspose2d(k=4, s=2, p=1) -> GroupNorm(32) + ReLU
    # -> Conv1x1 -> heatmaps [B, 17, H, W]
    # -> Soft-argmax -> keypoints [B, 17, 2] + confidence [B, 17]
```

**Architecture is correct:**
- Takes FPN P3 (256ch, stride 8), upsamples 2x to stride 4 (180x160 at 1280x720 input).
- Produces 17 heatmaps (COCO-style keypoints) via 1x1 conv.
- **Soft-argmax** (line 88-128): differentiable extraction via softmax-weighted spatial summation. Temperature=0.07.
- Confidence: sigmoid(max-heatmap-value) per keypoint.
- Uses **Wing Loss** (omega=0.05, epsilon=0.005) for keypoint regression.

**Critical finding -- NO REAL KEYPOINT ANNOTATIONS:**
- IndustReal has no COCO keypoint labels. Line 1865: when `not self.train_pose`, generates **pseudo-keypoints** from the highest-confidence detection box.
- The Wing Loss block for body keypoints only fires when `train_pose=True` AND keypoints exist in targets. IndustReal never satisfies this.
- `pose` in the liveness log refers to body pose (Wing Loss), which should always be DEAD/zero.

**Verdict: `PoseHead` is architecturally correct but functionally vestigial.** It produces heatmaps and pseudo-keypoints that feed `PoseFiLM`, but its own loss is always zero.

---

## 2. Head Pose Head: Dual Architecture

### 2a. `HeadPoseHead` (Legacy) -- Model.py line 1392

```
class HeadPoseHead(nn.Module):
    # GAP(C4, 384ch) + GAP(C5, 768ch) -> concat [1152]
    # MLP: 1152 -> 512 -> 256 -> 9 (raw 9-DoF)
```

- **Regression-based**: predicts 9 raw numbers (forward[3] + position[3] + up[3]).
- **Loss**: `head_pose_loss_split` (losses.py line 880-904) -- two-term:
  - Position MSE (raw values, O(1) after HEAD_POSE_POS_SCALE=100)
  - Direction MSE on L2-normalized forward/up vectors (scale-invariant)
- No orthogonality constraint. The network treats forward/up as independent scalars.

### 2b. `GeometryAwareHeadPose` (Current) -- `head_pose_geo.py`

```
class GeometryAwareHeadPose(nn.Module):
    # GAP(C4, 384ch) + GAP(C5, 768ch) -> concat [1152]
    # Rotation net: 1152 -> 512 -> 256 -> 6 (6D continuous rep)
    # Position net: 1152 -> 512 -> 256 -> 3 (tanh-normalized)
    # Gram-Schmidt orthonormalization -> [B, 3, 3] rotation matrix
```

- **Regression with structural prior**: 6D continuous rotation (Zhou et al., CVPR 2019), converted to SO(3) via Gram-Schmidt.
- **Loss** (lines 177-210):
  - `geodesic_loss`: acos((tr(R_pred^T R_true) - 1) / 2) in radians.
  - `cosine_rotation_loss`: 1 - (1/3) * sum of column dot products.
  - `position_loss`: MSE on tanh-normalized [-1, 1] position.
  - Combined: `rotation_weight * (geo + 0.5*cos) + position_weight * pos` (default 1.0/0.1).
- Init bias to identity: rotation_net last layer bias set to a1=[1,0,0], a2=[0,1,0].

**Verdict: Neither is classification -- both are regression.** GeometryAware is strictly better (6D + orthogonality + geodesic loss).

---

## 3. NO_GRAD for pose_head / head_pose_head During Stage 1 -- EXPECTED

From `_set_stage_requires_grad` (train.py line 564-628):

- Stage 1 (epochs 1-5): Detection-only. Freezes activity_head, psr_head. **Does NOT freeze pose_head or head_pose_head.**
- However, Kendall weighting zeros `prec_hp * 0` in Stage 1 (losses.py line 1527-1528) -- head pose contribution to total loss is zeroed.
- Body pose loss is always zero in IndustReal (no keypoint annotations).

**During RF1:** The liveness log showing `pose=0.00e+00 DEAD` and `head_pose=0.00e+00 DEAD` in Stage 1 is **intended behavior**. Stage 1 only trains detection. These heads are not supposed to be alive until Stage 2 (epoch 6+).

---

## 4. Pose Loss = 0.0000010: CORRECT

The `pose` value in training output refers to **body keypoint Wing Loss**, which is always ~0 because IndustReal has no real keypoint annotations. The `PoseLoss` block requires `'keypoints' in targets` (losses.py line 1190), which is never true. `loss_pose = zero` (line 1198).

**The head pose loss** appears under the `head_pose` key in the loss dict, NOT under `pose`. The training log (train.py line 1533-1534) shows both separately.

---

## 5. head_pose_angular_MAE_deg = 61.1: PROBLEMATIC

**61.1 degrees is barely above chance (~57 deg for random unit vectors on S^2).**

Root causes in the code:

### 5a. Coordinate system ambiguity
The angular MAE (evaluate.py lines 1711-1717) uses arccos(dot product) between pred/GT forward and up vectors. Valid ONLY when both are unit vectors. The fallback (lines 1704-1709) checks `norm > 0.5` -- the 61.1 deg value means evaluation determined norms are unit, but the angle is wrong.

### 5b. Legacy head limitation
This 61.1 was under `HeadPoseHead` (legacy 9-DoF MSE), before `USE_GEO_HEAD_POSE=True`. The legacy head predicts 9 raw numbers with no orthogonality constraint. GeometryAware was expected to drop to 10-25 degrees (head_pose_geo.py docstring line 14-16) but this **has not been validated** on test data yet.

### 5c. Position MAE in mm is unreliable
Evaluate.py line 1729-1737: `pos_err_m * 1000.0` assumes CSV values are metres. Code itself says "The unit is UNVERIFIED -- possibly decimetres, 0.1m-normalized or dataset-specific." The `HEAD_POSE_POS_SCALE=100` division further confuses the chain. **Do not use position_MAE_mm for reporting.**

---

## 6. Gradient Flow: Shared FPN Features with Detection

**Yes, pose and head_pose heads share FPN features with detection.**

Architecture flow:
```
Backbone -> C3, C4, C5
                  |
                FPN
                  |
           P3   P4+P5  P6+P7
           |      |      |
       PoseHead  ...  DetHead
           |
       PoseFiLM
           |
       C5_mod -> HeadPoseFiLM -> C5_mod2 -> ActivityHead
           |
       HeadPoseHead (from C4 + C5 directly)
```

**Key observations:**
- `PoseHead` takes FPN P3 (shares C3 backbone with detection).
- `HeadPoseHead` takes backbone C4/C5 directly (bypasses FPN).
- `HeadPoseFiLM` applies `head_pose.detach()` (model.py line 2034) -- stop_grad prevents circular dependency. Head pose gradients do NOT flow through HeadPoseFiLM.
- `PoseFiLM` DOES propagate gradients: `loss_headpose -> rotation_net -> C5_mod -> PoseFiLM -> C5 -> backbone`. Head pose gradients reach the backbone.

**No direct gradient conflict** between head pose and detection FPN features, because head pose bypasses FPN (uses backbone C4/C5 directly).

---

## 7. Loss Weighting: Pose Tasks vs Detection

### Kendall log_var initialization (losses.py):
```
log_var_det = 0   (precision=1.0)
log_var_pose = 0  (precision=1.0, was -1 but changed to 0 to prevent negative Kendall terms)
```

### Stage-aware weighting:
- Stage 1: `prec_hp = 0` (head pose zeroed)
- Stage 2: Head pose active at full precision
- Stage 3: All tasks active

### Key finding: `POSE_LOSS_WEIGHT=0.01` is irrelevant
Body keypoint Wing Loss weight is applied to an always-zero loss. Has zero effect.

### Shared `log_var_pose` for body + head pose:
Intentional per paper spec (both are pose tasks). Body pose loss~0 barely affects the sum. Minor issue: the shared log_var theoretically adjusts for two tasks but body pose contributes nothing.

---

## 8. Keypoint/Pose Coordinate System

### Pose.csv format (dataset line 535):
```
frame.jpg, forward_x, forward_y, forward_z, position_x, position_y, position_z, up_x, up_y, up_z
```

### Sanity checks (dataset lines 566-580):
- Warns if forward mean norm not in [0.5, 1.5].
- Warns if position max abs > 5 after HEAD_POSE_POS_SCALE=100 division.

### Column ordering concern in GeometryAware:
The rotation matrix is `[b1, b2, b3]` where b1=right, b2=up, b3=forward (head_pose_geo.py line 47). The 9-DoF reconstruction uses column 0 as forward and column 2 as up (model.py lines 2030-2032). However, `legacy_9dof_to_6d_rotation` (head_pose_geo.py line 227) also uses `R = stack([right, up, forward])` with columns as [right, up, forward]. **Need to verify this matches pose.csv axis semantics.**

---

## 9. Numerical Issues

### Head pose loss (`head_pose_loss_split`):
- Position: MSE on O(1)-scaled values -- safe.
- Direction: L2-normalization before MSE -- gradient-safe with eps=1e-6.
- No internal NaN guards -- relies on outer Kendall NaN guard (losses.py line 1429-1440).

### Known gradient overflow:
- train.py line 1583: "geo head pose geodesic loss gradient ~2200 near identity can overflow" -- large gradient at small rotation angles due to `acos` derivative.
- Mitigated by AMP gradient scaling (`scaler.scale(loss).backward()`) + global grad clipping.

### NaN guards (losses.py):
- Pre-Kendall guard replaces non-finite losses with 1e-4 (line 1429).
- Smooth cap on each loss (differentiable, preserves gradient above threshold).
- Liveness diagnostic every 200 steps isolates failing heads.

---

## 10. Recommendations

1. **Validate `GeometryAwareHeadPose` angular MAE** on test set immediately. If 10-25 degrees reported, the 61.1 baseline from legacy head is confirmed broken.

2. **Verify rotation matrix column ordering** against actual pose.csv axis conventions. Column swap would produce systematically wrong angular MAE.

3. **Fix position_MAE_mm reporting** -- the metre->mm *1000 assumption is explicitly acknowledged as unreliable. Document actual units or remove.

4. **Remove or disable `PoseHead` / `PoseLoss`** for IndustReal. No real keypoint annotations exist. Preserve pseudo-keypoint generation for PoseFiLM.

5. **Confirm `USE_GEO_HEAD_POSE=True`** in active config -- the 61.1 MAE was from legacy head; fix was recently enabled.

6. **Add round-trip test for `legacy_9dof_to_6d_rotation`** -- verify 9dof -> 6d -> rotation_matrix -> 9dof preserves angular error.

7. **Log forward_angular_MAE_deg + up_angular_MAE_deg separately** in training logs (already in evaluate.py output), and include head_pose_status flag (unit_vectors_ok vs non_unit_vectors).
