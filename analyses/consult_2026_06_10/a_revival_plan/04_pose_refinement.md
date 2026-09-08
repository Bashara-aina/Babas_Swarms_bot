# Agent 4: Pose Refinement Plan -- forward_angular_MAE to Below 6.15 Degrees

**Date:** 2026-08-01
**Role:** Pose Refinement Specialist (Agent 4 of 5-agent debate team)
**Target:** Push head pose `forward_angular_MAE` below 6.15 degrees (v4_fixed benchmark) from current best of 7.83 degrees (rf_stages validation). Fix the 86-degree random error observed in the current Geometry-Aware configuration.
**Codebase reference:** `/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/` (external drive; source files listed below)
**Primary sources:** SOTA history (`feedback_sota_history.md`), audit files (Agent 4 model audit, Agent 11 pose audit), eval script (`full_eval_inprocess.py`), gradient balancing action plan (`133_GRADIENT_BALANCING_ACTION_PLAN.md`)

---

## 1. Historical Evidence

### 1.1 Recorded head pose metrics across all checkpoint lineages

Data from `feedback_sota_history.md` (authoritative, 2026-08-01):

| Checkpoint / Eval | forward_angular_MAE (deg) | Notes |
|---|---|---|
| **v4_fixed** | **6.15** | Truthful per SOTA audit. Legacy `HeadPoseHead` (USE_GEO_HEAD_POSE=False). |
| rf_stages val | 7.83 | Current best on the multi-task ConvNeXt. Train-time val from `logs/metrics.jsonl`. |
| v3.41 eval | 7.94 | Earlier architecture. Close to rf_stages. |
| v4_smoke_500 | 9.14 | After normalization fix (per Agent 5 synthesis, Section 8.1). |
| best train-time val | 8.12 | From training logs across all runs. |
| full_multi_task_tma_tbank_benchmark saved eval | 9.94 | Old architecture (69 activity classes, 670MB checkpoint). |
| **test_gradfix_20260801** | **position_MAE_mm = 42.15** (model random) | Current-architecture compatible. Position MAE after grad fix -- forward angular not reported in this eval. |
| **Current GeometryAware run** | **~86** | Random-level error. See Section 2 root cause. |

**Key observation:** The v4_fixed checkpoint at 6.15 degrees is the only number independently verified as truthful by the SOTA audit. All other numbers are reported with varying degress of validation rigor. The 6.15 value was achieved with the legacy `HeadPoseHead` (raw 9-DoF MSE regression, no orthogonality constraint). It was NOT achieved with `GeometryAwareHeadPose`.

### 1.2 Which checkpoint produced 6.15 degrees

The v4_fixed checkpoint is located on the external drive:
- **Path:** `/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/src/runs/v4_fixed/checkpoints/`
- **Eval file:** `final_v4_fixed_v4_e0_b200.json` (referenced but not present in swarm-bot repo; resides on external drive)
- **Config state:** Almost certainly had `USE_GEO_HEAD_POSE=False` (using legacy `HeadPoseHead`), based on the following evidence:
  1. The archive naming pattern `v4_fixed` predates the `GeometryAwareHeadPose` implementation
  2. The 6.15 degree result is achievable with raw 9-DoF regression (no orthogonality needed for single-vector angular accuracy)
  3. The current 86-degree error is specific to GeometryAware's column ordering mismatch (Section 2)

### 1.3 Which eval script was used

The eval script is `src/evaluation/full_eval_inprocess.py` (539 lines, in-repo at `/home/newadmin/swarm-bot/src/evaluation/full_eval_inprocess.py`). This is THE authoritative eval script. Key excerpt (lines 248-254):

```python
hp_pred = outputs["head_pose"]  # [B, 9]
if hp_pred is not None and hp_gt is not None:
    fwd_mae = angular_mae(hp_pred[:, :3], hp_gt[:, :3]) * hp_pred.shape[0]
    up_mae = angular_mae(hp_pred[:, 3:6], hp_gt[:, 3:6]) * hp_pred.shape[0]
```

The eval assumes the 9-DoF output format is: **[forward(3), up(3), position(3)]**.
- Columns 0-2: Forward direction vector (unit-normalized before angular comparison)
- Columns 3-5: Up direction vector (unit-normalized before angular comparison)
- Columns 6-8: Position (used for position MAE, NOT angular comparison)

The `angular_mae` function (lines 134-139) uses L2 normalization before computing arccos of the dot product -- so even if non-unit vectors are passed, they are normalized first. This makes the metric robust to scale errors but extremely sensitive to direction errors.

### 1.4 What head pose architecture was used in v4_fixed

The legacy `HeadPoseHead` (`src/models/model.py`, line 1392):

```
GAP(C4, 384ch) + GAP(C5, 768ch) -> concat [1152]
MLP: 1152 -> 512 -> 256 -> 9 (raw 9-DoF output)
LayerNorm + GELU + Dropout(0.15/0.1) intermediate layers
No output activation (unbounded raw prediction)
```

**Critically, this head has NO `_init_weights` method** (Agent 4 audit, HIGH severity finding). All 5 Linear layers use PyTorch default Kaiming-uniform initialization. Despite this, v4_fixed achieved 6.15 degrees -- the legacy head's simple architecture avoids the column-ordering bug that plagues `GeometryAwareHeadPose`.

### 1.5 Coordinate convention

**Dataset (pose.csv):**
```
frame.jpg, forward_x, forward_y, forward_z, position_x, position_y, position_z, up_x, up_y, up_z
```
Format: [forward(3), position(3), up(3)] (per Agent 11 audit, line 167)

**Legacy HeadPoseHead output (documented):**
Format: [forward(3), position(3), up(3)] (per Agent 4 audit, line 97)

**Legacy HeadPoseHead output (effective, inferred from 6.15 deg result):**
Format: [forward(3), up(3), position(3)] -- MUST be this format, because the eval script slices columns 3-5 as "up", and if those were actually position coordinates (3D spatial coordinates in mm/dm), the angular MAE after L2 normalization would be random (~57 degrees mean on S^2), not 6.15.

**Resolution of this contradiction:** The documentation at model.py line 97 says `[forward(3), position(3), up(3)]` but the actual output order is `[forward(3), up(3), position(3)]`. This is confirmed by the v4_fixed result of 6.15 degrees -- if position values were being compared as up-vectors, the error would be ~57 degrees (random unit vectors on S^2). The 6.15 result proves the eval's column slicing matches the actual output format.

**GeometryAwareHeadPose `to_legacy_9dof` output (from audit):**
The rotation matrix is `[b1, b2, b3]` where:
- b1 = right (column 0, the x-axis of the head coordinate frame)
- b2 = up (column 1, the y-axis)
- b3 = forward (column 2, the z-axis)

`to_legacy_9dof` at head_pose_geo.py lines 215-221:
- forward direction is column 2 (the z-axis of the rotation matrix)
- up is column 1 (the y-axis of the rotation matrix)

**GeometryAwareHeadPose output as consumed by model.py (lines 2030-2032):**
- "uses column 0 as forward and column 2 as up" (Agent 11 audit, line 175)
- This means: column 0 (= right vector) is passed as forward, and column 2 (= forward vector) is passed as up

**Eval script expectation:**
- Columns 0-2 = forward
- Columns 3-5 = up
- Columns 6-8 = position

---

## 2. Root Cause Analysis

### 2.1 Why the current run shows 86 degrees (random)

There are TWO independent column-ordering mismatches that compound to produce 86 degrees:

#### Mismatch 1: GeometryAware Rotation Matrix Column Convention vs. Eval Convention

The `GeometryAwareHeadPose` produces a 3x3 rotation matrix `R = [right, up, forward]` (columns in that order). The eval script expects the 9-DoF output to be `[forward, up, position]`. But the `to_legacy_9dof` function constructs the 9-DoF output from the rotation matrix columns in an order that does NOT match eval expectations.

Specifically, from Agent 11 audit line 175:
> "The 9-DoF reconstruction uses column 0 as forward and column 2 as up (model.py lines 2030-2032)"

This means:
- Eval slices columns 0-2 as "forward" -> Gets R[:, 0] which is actually the **right** vector, not forward
- Eval slices columns 3-5 as "up" -> Gets R[:, 2] which is actually the **forward** vector, not up
- Eval slices columns 6-8 as "position" -> Gets the position prediction (from the separate position_net), this is correct

The right vector and forward vector of a head coordinate frame are approximately perpendicular (90 degrees on S^2). Therefore, comparing the "right" vector against the GT "forward" vector yields ~86 degrees (close to the expected 90 degrees for orthogonal unit vectors, with the 4-degree deviation coming from the fact that head poses are not perfectly axis-aligned and the network may partially learn to compensate).

#### Mismatch 2: `to_legacy_9dof` vs. model.py column handling conflict

There is an internal contradiction between two code paths:
1. `to_legacy_9dof` (head_pose_geo.py lines 215-221): forward=col2, up=col1 (CORRECT)
2. model.py lines 2030-2032: forward=col0, up=col2 (INCORRECT)

If `to_legacy_9dof` is called and produces output `[right(3), up(3), forward(3)]` concatenated with position, and then model.py re-interprets this as `[forward(3), up(3), right(3)]`, the column indices are scrambled twice. Or, alternatively, if model.py's `to_legacy_9dof` output is passed directly as the `head_pose` tensor without re-indexing, but model.py's downstream code at line 2030 applies a different column mapping, the HeadPoseFiLM receives the wrong vectors.

**The exact mapping depends on which of these two interpretations is actually in effect. Without reading the external-drive source file directly, the precise 9-DoF layout cannot be confirmed. However, the 86-degree result is consistent with orthogonal vector comparison and therefore with a column-mapping error.**

### 2.2 Why v4_fixed achieved 6.15 degrees (truthful result)

v4_fixed used the legacy `HeadPoseHead` with `USE_GEO_HEAD_POSE=False`. The legacy head:
1. Outputs raw 9 numbers in the format `[forward(3), up(3), position(3)]` (effective format, confirmed by eval result)
2. Has NO orthogonality constraint -- each of the 9 numbers is an independent scalar prediction
3. Uses simple MSE loss (`head_pose_loss_split`): position MSE + direction MSE on L2-normalized vectors
4. The L2-normalization in the loss implicitly handles the unit-vector requirement for angular accuracy

Because the legacy head's output format matches the eval's expected format, the angular MAE computation is correct. The 6.15 degree result represents the genuine forward-vector angular error of a raw 9-DoF regression head on ConvNeXt-Tiny features.

### 2.3 The position MAE reliability problem

The `position_MAE_mm` metric is unreliable. Agent 11 audit (line 108):
> "Evaluate.py line 1729-1737: `pos_err_m * 1000.0` assumes CSV values are metres. Code itself says 'The unit is UNVERIFIED -- possibly decimetres, 0.1m-normalized or dataset-specific.' The `HEAD_POSE_POS_SCALE=100` division further confuses the chain."

Therefore, the position MAE numbers (42.15 mm from test_gradfix, 103.7 mm from benchmark) should NOT be used for reporting or comparison. Only angular MAE metrics (forward and up) are reliable.

### 2.4 Summary of root cause

| Component | Format | Columns 0-2 | Columns 3-5 | Columns 6-8 |
|---|---|---|---|---|
| pose.csv (GT) | Dataset | forward | position | up |
| Eval script expectation | Evaluator | **forward** | **up** | position |
| Legacy HeadPoseHead (effective) | Model | **forward** | **up** | position |
| GeometryAware `to_legacy_9dof` (likely) | Model | right | up | forward |
| GeometryAware as interpreted by model.py:2030 | Model | right (= "forward" in code) | forward (= "up" in code) | position |

**Primary bug:** The GeometryAwareHeadPose rotates the column semantics of the 9-DoF output relative to what the eval script expects. The eval compares the right-vector against the forward-vector GT, producing ~86 degrees (close to the 90-degree expected for orthogonal vectors).

**Secondary bug:** The internal code paths for column handling (`to_legacy_9dof` vs model.py line 2030) may contradict each other, creating a double-mapping error.

---

## 3. Solution Strategy

### 3.1 Strategy A: Fix the column ordering (PRIMARY, 2 hours)

**This is a zero-training-cost fix. No GPU required.**

The eval script (`full_eval_inprocess.py`) expects the 9-DoF output format: `[forward(3), up(3), position(3)]`. The fix must ensure that `GeometryAwareHeadPose.to_legacy_9dof()` and/or the model's `head_pose` tensor construction outputs exactly this format.

**Specific changes (in execution order):**

#### Step A1: Audit the actual 9-DoF layout (30 minutes)

Before writing any code, determine the exact output by instrumenting with a debug unit test:

```python
# Pseudocode for verification (run on CPU, 30 seconds)
import torch
# Instantiate GeometryAwareHeadPose
geo_head = GeometryAwareHeadPose(in_channels=1152)
# Pass a known input
x = torch.randn(1, 1152)
# Get rotation matrix (deterministic from 6D representation)
R = geo_head.rotation_6d_to_matrix(x)  # [1, 3, 3]
# Get 9-DoF output
output_9dof = geo_head.to_legacy_9dof(R, geo_head.position_net(x))
# Print column slices
print("Cols 0-2:", output_9dof[0, :3])   # What IS this?
print("Cols 3-5:", output_9dof[0, 3:6])  # What IS this?
print("Cols 6-8:", output_9dof[0, 6:9])  # What IS this?
# Compare against R columns
print("R col 0 (right):", R[0, :, 0])
print("R col 1 (up):", R[0, :, 1])
print("R col 2 (forward):", R[0, :, 2])
```

This immediately identifies which rotation matrix columns map to which 9-DoF output positions.

#### Step A2: Apply the fix (1 hour)

**Case 1: If `to_legacy_9dof` correctly outputs `[right, up, forward]` or `[forward, up, right]` but eval expects `[forward, up, position]`:**

Fix `to_legacy_9dof` to output:
```python
def to_legacy_9dof(self, R, position):
    """
    Convert 3x3 rotation matrix + position to legacy 9-DoF format.
    
    Expected format: [forward(3), up(3), position(3)]
    - R[:, :, 0] = right
    - R[:, :, 1] = up
    - R[:, :, 2] = forward
    
    Returns: [B, 9] tensor
    """
    forward = R[:, :, 2]   # column 2 is forward (z-axis)
    up = R[:, :, 1]        # column 1 is up (y-axis)
    pos = torch.tanh(position)  # from position_net, normalized
    return torch.cat([forward, up, pos], dim=1)  # [B, 9]
```

**Case 2: If `to_legacy_9dof` is correct but model.py re-interprets columns:**

Fix model.py line 2030-2032 to use the correct columns:
```python
# BEFORE (broken):
# Uses column 0 as forward, column 2 as up
forward = head_pose[:, :3]    # actually right
up = head_pose[:, 6:9]        # actually forward

# AFTER (fixed):
# head_pose from to_legacy_9dof is [forward(3), up(3), position(3)]
forward = head_pose[:, :3]    # really forward
up = head_pose[:, 3:6]        # really up
position = head_pose[:, 6:9]  # really position
```

**Case 3: If there is NO `to_legacy_9dof` call and the 9-DoF is constructed directly in model.py:**

Fix the construction at model.py lines 2030-2032 to use rotation matrix columns correctly:
```python
# R is [B, 3, 3] with columns = [right, up, forward]
forward = R[:, :, 2]   # column 2 is forward
up = R[:, :, 1]        # column 1 is up
position = position_net_output  # from position_net
head_pose_9dof = torch.cat([forward, up, position], dim=1)  # [B, 9]
```

#### Step A3: Add round-trip unit test (30 minutes)

Add to `tests/test_head_pose_geo.py` (new file):

```python
def test_9dof_roundtrip():
    """Verify 9-DoF output format matches eval expectations."""
    import torch
    from src.models.head_pose_geo import GeometryAwareHeadPose
    
    model = GeometryAwareHeadPose()
    model.eval()
    
    # Create a known rotation: identity matrix (forward = [0,0,1])
    R = torch.eye(3).unsqueeze(0)  # [1, 3, 3]
    pos = torch.tensor([[0.1, 0.2, 0.3]])  # [1, 3]
    
    output = model.to_legacy_9dof(R, pos)  # [1, 9]
    
    # Eval slices: cols 0-2 = forward, cols 3-5 = up, cols 6-8 = position
    fwd_pred = output[0, :3]
    up_pred = output[0, 3:6]
    pos_pred = output[0, 6:9]
    
    # For identity rotation: forward = [0, 0, 1], up = [0, 1, 0]
    assert torch.allclose(fwd_pred, torch.tensor([0., 0., 1.]), atol=1e-5), \
        f"Forward should be [0,0,1], got {fwd_pred}"
    assert torch.allclose(up_pred, torch.tensor([0., 1., 0.]), atol=1e-5), \
        f"Up should be [0,1,0], got {up_pred}"
    assert torch.allclose(pos_pred, pos[0], atol=1e-5), \
        f"Position should be {pos[0]}, got {pos_pred}"
    
    # Now test eval's angular_mae with known vectors
    from src.evaluation.full_eval_inprocess import angular_mae
    
    # Forward: predicted = GT = [0,0,1] -> angle = 0
    fwd_err = angular_mae(fwd_pred.unsqueeze(0), torch.tensor([[0., 0., 1.]]))
    assert fwd_err < 0.01, f"Forward angular error should be ~0, got {fwd_err}"
    
    # Up: predicted = GT = [0,1,0] -> angle = 0
    up_err = angular_mae(up_pred.unsqueeze(0), torch.tensor([[0., 1., 0.]]))
    assert up_err < 0.01, f"Up angular error should be ~0, got {up_err}"
    
    # Regression test: predicted forward = right [1,0,0], GT forward = [0,0,1] -> angle = 90
    wrong_fwd = torch.tensor([[1., 0., 0.]])  # right vector
    wrong_err = angular_mae(wrong_fwd, torch.tensor([[0., 0., 1.]]))  # forward GT
    assert 85.0 < wrong_err < 95.0, \
        f"Right vs Forward should be ~90 deg, got {wrong_err}"
    
    print("PASSED: 9-DoF roundtrip + eval slicing verified")
```

The last assertion (`85.0 < wrong_err < 95.0`) is the regression test that catches the column swap: if `to_legacy_9dof` ever outputs the right vector where the eval expects forward, this test fails.

### 3.2 Strategy B: Revert to legacy HeadPoseHead with proper init (FALLBACK, 1 day)

If Strategy A fails (unexpected interactions with HeadPoseFiLM or downstream consumers), revert to the legacy `HeadPoseHead` but with:

1. **Add `_init_weights` method** (the HIGH-severity finding from Agent 4 audit):
   ```python
   class HeadPoseHead(nn.Module):
       def _init_weights(self):
           for m in self.modules():
               if isinstance(m, nn.Linear):
                   nn.init.normal_(m.weight, std=0.01)
                   if m.bias is not None:
                       nn.init.zeros_(m.bias)
   ```

2. **Add output activation** to prevent unbounded head pose values from propagating NaN through HeadPoseFiLM (Agent 17 numerical stability audit finding):
   ```python
   def forward(self, c4, c5):
       x = torch.cat([c4_pooled, c5_pooled], dim=1)
       x = self.mlp(x)  # raw 9-DoF [forward(3), up(3), position(3)]
       # Clamp direction vectors to reasonable range
       direction = torch.tanh(x[:, :6])  # forward + up in [-1, 1]
       position = x[:, 6:9]  # unbounded position
       return torch.cat([direction, position], dim=1)
   ```

3. **Set `USE_GEO_HEAD_POSE=False`** in config.

Expected outcome: forward_angular_MAE <= 7 degrees (matching v4_fixed's 6.15, within noise). This is a regression to the working configuration but with the init and NaN-safety fixes applied.

### 3.3 Strategy C: Hybrid approach -- fix column ordering AND keep GeometryAware (RECOMMENDED, 2 hours + 2 days validation)

Run Strategy A (fix column ordering) and validate with these checks:

1. **Immediate sanity check (5 minutes):** Run `full_eval_inprocess.py` on the fixed checkpoint with `--max-batches 10`. If forward_angular_MAE drops from ~86 to < 20 degrees, the fix is correct.

2. **Full validation eval (2 hours):** Run full 38,036-frame eval. Expected result: forward_angular_MAE in the 6-12 degree range (depends on training state of the checkpoint; a model trained with broken column ordering may not learn accurate head pose, in which case the result will be better than 86 degrees but may still be worse than 7.83).

3. **If validation shows > 15 degrees after fix:** The model was trained with broken gradients through HeadPoseFiLM (the head pose tensor feeds into FiLM which modulates C5 features). Training with wrong head pose vectors corrupted the backbone features that head pose depends on. In this case, resume training from the checkpoint with the column fix applied -- 2-3 days for head pose to converge from partially-corrupted features.

### 3.4 Strategy D: New training with column fix from scratch (LAST RESORT, 5-7 days)

If the fixed checkpoint still produces > 15 degrees after 2 days of resume training, launch a new training run with the column fix applied from epoch 0. Use `USE_GEO_HEAD_POSE=True` with corrected column ordering.

---

## 4. Training Configuration

### 4.1 Current baseline configuration

| Parameter | Value | File | Notes |
|---|---|---|---|
| `BATCH_SIZE` | 2 | config.py | RTX 3060 VRAM limit (12 GB) |
| `GRAD_ACCUM` | 16 | config.py | Effective batch = 32 |
| `USE_GEO_HEAD_POSE` | True (current run) | config.py | Geometry-Aware active, column ordering broken |
| `TRAIN_HEAD_POSE` | True | config.py | Active after stage 1 (epoch 5+) |
| `HEAD_POSE_POS_SCALE` | 100 | config.py | Applied to GT position at load time. Unit chain: raw CSV value / 100 |
| `Kendall log_var_pose` | 0.0 init | losses.py | Shared for body pose + head pose |
| HeadPoseFiLM | `head_pose.detach()` | model.py:2034 | Stop-grad per paper spec |
| Head pose loss (legacy) | Position MSE + Direction MSE | losses.py:880-904 | Two-term; no orthogonality constraint |
| Head pose loss (GeometryAware) | `geodesic + 0.5*cosine + 0.1*position` | head_pose_geo.py:177-210 | Rotation weights = 1.0, position weight = 0.1 |
| AMP gradient scaling | `scaler.scale(loss).backward()` | train.py | Mitigates geodesic loss gradient overflow (grad ~2200 near identity) |

### 4.2 Configuration changes for revival training

Apply these changes in config.py or as environment overrides:

```python
# --- Head pose architecture ---
USE_GEO_HEAD_POSE: bool = True      # Keep GeometryAware (with column fix from Strategy A)

# --- Head pose loss weights ---
# GeometryAware default: rotation_weight=1.0, position_weight=0.1
# Consider reducing rotation_weight to 0.5 if geodesic loss dominates
HP_ROTATION_WEIGHT: float = 0.5      # was 1.0 -- reduce to prevent geodesic gradient dominance
HP_POSITION_WEIGHT: float = 0.1      # unchanged

# --- Gradient safety ---
# Geodesic loss gradient ~2200 near identity. AMP handles this with scaling,
# but explicit clamping adds safety.
HP_GRAD_CLIP: float = 10.0           # per-parameter gradient clipping for head pose

# --- Kendall weighting ---
# Head pose uses shared log_var_pose with body pose (which is always zero in IndustReal).
# This is actually beneficial: no competing task dilutes head pose precision.
# Keep log_var_pose init at 0 (precision = 1.0).
KENDALL_LOG_VAR_MIN_POSE: float = -1.0  # Allow head pose precision up to exp(1)=2.72

# --- Training schedule ---
# Head pose is active from epoch 6+ in staged mode.
# For head-pose-focused revival, consider making it active from epoch 0:
STAGE_1_EPOCHS: int = 3              # was 5 -- shorter detection-only phase
# Head pose becomes active at epoch 4 (was epoch 6)
```

### 4.3 Loss function configuration for head-pose-only revival

If training a head-pose-only or head-pose+detection run (not all 5 heads):

```python
# --- Multi-task loss config (abbreviated) ---
# In losses.py MultiTaskLoss.forward:
# Stage 1 (epochs 0-3): detection only
# Stage 2 (epochs 4+): detection + head pose (PSR, activity, body pose disabled)

TRAIN_ACT: bool = False     # Disable activity (confirmed zero backbone signal)
TRAIN_PSR: bool = False     # Disable PSR (separate head repair in progress)
TRAIN_POSE: bool = False    # Disable body pose (always zero in IndustReal)
TRAIN_DET: bool = True      # Detection active
TRAIN_HEAD_POSE: bool = True  # Head pose active -- THIS IS THE TARGET
```

This reduces the multi-task conflict from 5 heads to 2 heads (detection + head pose), which eliminates the gradient starvation issues identified in Strategy 1 of the gradient balancing plan.

### 4.4 Expected training time

| Phase | Duration | GPU | Notes |
|---|---|---|---|
| Column fix implementation + unit test | 2 hours | None (CPU) | Strategy A Steps 1-3 |
| Sanity eval (10 batches) | 5 minutes | RTX 3060 | Verify fix drops 86 -> < 20 degrees |
| Full eval (38,036 frames) | 2 hours | RTX 3060 | Forward + up angular MAE on full val set |
| IF resume training needed | 2-3 days | RTX 3060 | Resume from fixed checkpoint, head pose adapts |
| IF new training needed (Strategy D) | 5-7 days | RTX 3060 | Fresh training with column fix from epoch 0 |
| Final full eval + metrics commit | 2 hours | RTX 3060 | Freeze checkpoint SHA256 + metrics.json |

---

## 5. Timeline & Verification

### 5.1 Execution timeline (aligned with Agent 5 integration synthesis)

```
Aug 1-2 (TODAY + 1):
  [1 hour]   Read the external-drive source files (head_pose_geo.py, model.py:2020-2040)
  [30 min]   Run debug unit test to determine exact 9-DoF layout
  [1 hour]   Implement column fix (Strategy A)
  [30 min]   Add round-trip unit test (Strategy A3)
  [5 min]    Sanity eval: 10 batches on RTX 3060
  [1 hour]   Document findings + file this plan

Aug 2-3:
  [2 hours]  Full evaluation on RTX 3060 (38,036 frames)
  Decision gate: If forward_angular_MAE < 15 degrees, proceed.
                 If 15-30 degrees, resume training (2-3 days).
                 If > 30 degrees, implement Strategy B (revert to legacy head).

Aug 3-7 (IF resume training):
  [3-4 days] Resume training from fixed checkpoint on RTX 3060
  [2 hours]  Full evaluation on final checkpoint

Aug 7-12 (IF new training needed -- Strategy D):
  [5-7 days] Fresh training with column fix on RTX 3060
  [2 hours]  Full evaluation on final checkpoint

Aug 12-18 (concurrent with freeze deadline Aug 22):
  [1 day]    Per-recording up-vector breakdown (Agent 5 requirement, Section 9 checklist)
  [1 day]    Document position_MAE unreliability + insert disclaimer into paper
  [2 days]   Fill honest disclosure D7 (up-vector MAE unstable) + D8 (position units unverified)
```

**Target freeze date: August 22, 2026** (per Agent 5 integration synthesis, Section 8.2).

### 5.2 Verification protocol

#### V1: Unit tests (pre-merge)

- [ ] `test_9dof_roundtrip()` passes: identity rotation matrix maps to correct forward/up/position vectors
- [ ] `test_right_vs_forward_90deg()` passes: right vector compared against forward GT gives ~90 degrees
- [ ] `test_legacy_9dof_preserves_orthogonality()` passes: Gram-Schmidt output is orthonormal within 1e-5 tolerance
- [ ] `test_to_legacy_9dof_and_eval_slicing_match()` passes: `to_legacy_9dof` output sliced per eval convention matches expected vectors

#### V2: Sanity eval (post-fix, pre-full-eval)

```bash
python src/evaluation/full_eval_inprocess.py \
    --ckpt /path/to/fixed/checkpoint.pth \
    --max-batches 10 \
    --save-dir /tmp/pose_fix_sanity
```

Expected: `forward_angular_MAE_deg` drops from ~86 to < 20 degrees (proving the column fix works). If > 20 degrees, STOP and investigate -- the fix did not address the correct column mapping.

#### V3: Full evaluation (post-fix)

```bash
python src/evaluation/full_eval_inprocess.py \
    --ckpt /path/to/fixed/checkpoint.pth \
    --max-batches 0 \
    --save-dir src/runs/pose_refinement/full_eval
```

Check the output `metrics.json`:
- `forward_angular_MAE_deg`: expected < 12 degrees (ideally < 7 to approach 6.15 target)
- `up_angular_MAE_deg`: expected < 12 degrees (ideally < 8)
- `head_pose_n`: must equal 38,036 (full val set)

#### V4: Per-recording breakdown (post-full-eval)

Required by Agent 5's verification checklist (Section 9). Run a modified eval that tracks `forward_angular_MAE` per recording:

```python
# Pseudocode for per-recording breakdown
per_rec = defaultdict(lambda: {"fwd_sum": 0.0, "up_sum": 0.0, "n": 0})
for bi, (images, targets) in enumerate(val_loader):
    ...
    for i in range(B):
        rec_id = targets["metadata"][i]["recording_id"]
        fwd_err = angular_mae(hp_pred[i:i+1, :3], hp_gt[i:i+1, :3])
        up_err = angular_mae(hp_pred[i:i+1, 3:6], hp_gt[i:i+1, 3:6])
        per_rec[rec_id]["fwd_sum"] += fwd_err
        per_rec[rec_id]["up_sum"] += up_err
        per_rec[rec_id]["n"] += 1

# Print median + IQR per recording
for rec_id, stats in sorted(per_rec.items()):
    fwd_mean = stats["fwd_sum"] / stats["n"]
    up_mean = stats["up_sum"] / stats["n"]
    print(f"  {rec_id}: forward={fwd_mean:.2f}deg  up={up_mean:.2f}deg  n={stats['n']}")
```

This identifies whether specific recordings have systematically higher head pose error (e.g., recordings with fast motions, occlusions, or lighting changes).

#### V5: Regression test against known good checkpoint

Re-run full eval on the v4_fixed checkpoint (if accessible on external drive) to re-confirm the 6.15 degree number with the CURRENT eval script. This proves the eval script itself is not the source of the discrepancy:

```bash
python src/evaluation/full_eval_inprocess.py \
    --ckpt /media/newadmin/master/.../v4_fixed/checkpoints/best.pth \
    --max-batches 0 \
    --save-dir src/runs/v4_fixed_re_eval
```

Expected: `forward_angular_MAE_deg` = 6.15 +/- 0.1 (reproducible within noise).

#### V6: Position MAE disclaimer

The position_MAE_mm metric is structurally unreliable. Insert the following disclaimer into any paper or report that references head pose:

> "Position MAE (mm) is computed as `L2_norm(pred - GT) * 1000`, assuming the GT position values are in metres. However, the original IndustReal `pose.csv` unit is unverified and may be expressed in decimetres, 0.1m-normalized units, or dataset-specific conventions. The `HEAD_POSE_POS_SCALE=100` division at data load time further compounds this uncertainty. Therefore, position MAE numbers should be treated as relative (for comparing checkpoints within the same codebase) but not absolute (for comparison against external baselines). Only forward/up angular MAE (degrees) is reliable for cross-work comparison."

### 5.3 Success criteria

| Tier | Criterion | Metric | Threshold | Notes |
|---|---|---|---|---|
| Minimum viable | Column fix verified | Unit test pass + sanity eval < 20 deg | Must-pass | Proves the 86-degree bug is fixed |
| Target | Match v4_fixed | forward_angular_MAE <= 6.15 deg | Ideal | Would be a SOTA-equivalent result |
| Acceptable | Improve on rf_stages | forward_angular_MAE < 7.83 deg | Satisfactory | Beats current best on the ConvNeXt backbone |
| Fallback | Revert to legacy head | forward_angular_MAE < 8.5 deg | Adequate | With init fix + NaN guard |
| Failure | No improvement | forward_angular_MAE > 8.5 deg | Abandon | Publish as characterized limitation |

---

## 6. Cross-References & Challenges

### 6.1 Dependencies on other agents

| Agent | Dependency | Status |
|---|---|---|
| Agent 1 (PSR) | None. Head pose fix is independent. Can run in parallel on RTX 3060 with PSR repair on same GPU. | Parallel |
| Agent 2 (Detection) | None. Head pose architecture is separate from detection. | Independent |
| Agent 3 (Activity) | None. Activity head is architecturally isolated from head pose. | Independent |
| Agent 5 (Integration) | Per-recording up-vector breakdown (Section 9 checklist item). Position MAE disclaimer (D8 honest disclosure). Head pose forward/up numbers for freeze (D7). | **Required by Agent 5** |

### 6.2 Dependencies on external resources

| Resource | Status | Action |
|---|---|---|
| `head_pose_geo.py` (252 lines) | External drive only | Must be read before implementing column fix. Cannot be accessed through swarm-bot filesystem MCP. |
| `model.py` (2191 lines, lines 2020-2040) | External drive only | Must be read to verify column handling at HeadPoseFiLM injection point. |
| v4_fixed checkpoint | External drive only | Re-eval needed to confirm 6.15 with current eval script (Verification V5). |
| RTX 3060 GPU (12 GB) | Currently running PSR repair (epoch 24+/100) | Head pose fix does NOT require training immediately (column fix is code-only). Sanity eval uses < 1 GB VRAM for 10 batches. Full eval uses ~4 GB. Can share GPU with PSR repair (eval mode). |

### 6.3 Challenges from Agent 5 (Integration Synthesis, Section 7.4)

Agent 5 has NOT formally challenged Agent 4 in the integration synthesis (Section 7 challenges are directed at Agents 1-3; Agent 4 is treated as "Integrity/Diagnostic Specialist"). This is a gap: Agent 4 (Pose Refinement) was not represented in the original debate. However, the following challenges from Agent 5's general framework apply:

#### Challenge 1: The freeze deadline is tight

Agent 5's integration synthesis imposes a freeze date of **August 22, 2026**. The pose refinement fix is a code-only change (2 hours) plus eval (2 hours), which comfortably meets this deadline. However, if resume training or new training is needed (Strategies C or D), the timeline extends to August 12-18, which leaves only 4-10 days of buffer before the freeze.

**Mitigation:** Implement the column fix immediately (Aug 1-2). Evaluate on Aug 2-3. Decide on training by Aug 3.

#### Challenge 2: The honest disclosure D7 (up-vector MAE unstable) must be filled

Agent 5's Section 9 checklist requires "Per-recording up-vector breakdown available." The per-recording breakdown (Verification V4) must be completed and committed.

**Status:** Pending. To be run with the column-fixed eval.

#### Challenge 3: The honest disclosure D8 (position units unverified) must be filled

Agent 5's checklist requires all 8 disclosure placeholders filled. D8 specifically concerns position MAE unverified units. The disclaimer in Verification V6 addresses this.

**Status:** Ready. Disclaimer written in Section 5.2 (V6). Insert into paper when writing begins.

### 6.4 Challenges to other agents (from Pose perspective)

#### Challenge to Agent 1 (PSR Specialist):

Your PSR repair training runs on the same RTX 3060 GPU that head pose eval requires. The head pose fix is a **2-hour eval** that can run while PSR training is paused or between epochs. Coordinate: I need 2 hours of RTX 3060 time on Aug 2 for the post-fix full eval. Impact on your timeline: negligible.

#### Challenge to Agent 5 (Integration):

Your synthesis claims "Head pose works" (Section 8.1, point 1) and cites forward=9.14, up=7.78. These numbers come from the **legacy head** (USE_GEO_HEAD_POSE=False) after a normalization fix. The GeometryAware head (current architecture) produces 86 degrees due to the column ordering bug documented here. Your synthesis should distinguish between "legacy head pose works on ConvNeXt features" and "current GeometryAware head has a column-ordering bug that must be fixed before it can produce meaningful results."

#### Challenge to the results freeze protocol:

The SOTA history document (`feedback_sota_history.md`) correctly flags 6.15 as "truthful" and the PSR 1.0 as "FAKE." However, the history does not distinguish between head pose results from the legacy head (v4_fixed, rf_stages, v3.41) and from the GeometryAware head. After the column fix, all new head pose results must be tagged with the architecture flag (USE_GEO_HEAD_POSE=True/False) in the SOTA history.

### 6.5 Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Column fix doesn't drop error below 86 degrees | 10% | HIGH -- root cause misidentified | Run the debug unit test (Step A1) BEFORE implementing the fix. The test will confirm the exact column mapping. |
| Fixed checkpoint produces 20-30 degrees (model trained with broken columns) | 40% | MEDIUM -- requires resume training | Strategy C: resume training for 2-3 days. Acceptable within timeline. |
| GeometryAware geodesic loss gradient overflow after fix | 15% | MEDIUM -- training instability | AMP scaling handles this. Reduce HP_ROTATION_WEIGHT from 1.0 to 0.5 as a safeguard. |
| v4_fixed checkpoint not accessible for re-eval | 60% | LOW -- external drive may be disconnected | Trust the SOTA history (6.15 verified truthful). Re-eval is a "nice to have" but not required for the fix. |
| Position MAE remains unreliable | 100% | LOW -- already acknowledged | Insert disclaimer (Verification V6). Do not use position MAE for headline claims. |
| RTX 3060 unavailable (PSR repair occupies it) | 0% | LOW | Eval uses eval mode (< 4 GB VRAM). Can run between PSR training epochs. |

### 6.6 What this plan does NOT address

1. **Improving beyond 6.15 degrees.** The v4_fixed result is the theoretical ceiling for raw 9-DoF regression on ConvNeXt-Tiny features. GeometryAware (6D rotation + orthogonality) COULD improve on this (by enforcing geometric consistency), but only AFTER the column fix makes it functional. The 6.15 target is a restoration goal, not an improvement goal.

2. **Position MAE.** The metric is structurally unreliable (unverified units, scale division chain). Fixing the metric pipeline is out of scope -- the disclaimer suffices for the freeze deadline.

3. **Body pose (PoseHead).** This head is vestigial in IndustReal (no real keypoint annotations). No revival planned.

4. **HeadPoseFiLM gradient interaction.** The head_pose tensor feeds into HeadPoseFiLM (with `.detach()`), which modulates C5 backbone features. If the column fix changes the vectors flowing through HeadPoseFiLM, the C5 features that detection and activity depend on will change. This is a second-order effect -- run the full 5-head eval after the fix to measure impact on detection mAP and other metrics.

5. **Training from scratch with GeometryAware.** If resume training (Strategy C) fails to reach < 8 degrees, launching a new training run (Strategy D) requires 5-7 days of RTX 3060 compute. This may conflict with the August 22 freeze deadline. Decision gate: Aug 3.

---

## Appendix A: Files Referenced

| File | Location | Lines | Content |
|---|---|---|---|
| `full_eval_inprocess.py` | `/home/newadmin/swarm-bot/src/evaluation/full_eval_inprocess.py` | 539 | Eval script (in-repo, verified) |
| `model.py` | External drive: `/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/src/models/model.py` | 2191 | Model architecture (external, Agent 4 audit is source) |
| `head_pose_geo.py` | External drive: `/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/src/models/head_pose_geo.py` | 252 | GeometryAwareHeadPose (external, Agent 4+11 audits are sources) |
| `losses.py` | External drive (same path, `src/training/losses.py`) | ~1600 | Kendall weighting, head pose loss functions |
| `config.py` | External drive (same path, `src/config.py`) | ~600 | USE_GEO_HEAD_POSE flag, HEAD_POSE_POS_SCALE |
| `train.py` | External drive (same path, `src/training/train.py`) | ~3500 | Staged training schedule, --reinit-heads |
| `feedback_sota_history.md` | `/home/newadmin/.claude/projects/-home-newadmin-swarm-bot/memory/feedback_sota_history.md` | 79 | Authoritative SOTA numbers |
| Agent 4 audit | `/home/newadmin/swarm-bot/.claude/teams/industreal-deep-audit/agent4-model.md` | 294 | Model architecture audit |
| Agent 11 audit | `/home/newadmin/swarm-bot/.claude/teams/industreal-deep-audit/agent11-pose-headpose.md` | 212 | Head pose architecture audit |
| Agent 17 audit | `/home/newadmin/swarm-bot/.claude/teams/industreal-deep-audit/agent17-numerical-stability.md` | ~350 | Numerical stability audit |
| Gradient balancing plan | `/home/newadmin/swarm-bot/analyses/consult_2026_06_10/AAIML/133_GRADIENT_BALANCING_ACTION_PLAN.md` | 894 | Strategy 1 (Kendall fix, stop-grad) |
| Integration synthesis | `/home/newadmin/swarm-bot/analyses/consult_2026_06_10/a_revival_plan/05_integration_synthesis.md` | 426 | Agent 5's synthesis |

## Appendix B: Code Changes Summary (NOT executed -- plan only)

Per the task directive, NO code changes are made. The following summarizes what would be changed:

1. **`head_pose_geo.py` line 215-221** (`to_legacy_9dof`): Reorder columns to `[forward, up, position]` matching eval expectations.
2. **`model.py` line 2030-2032**: Fix column indexing to match rotation matrix semantics (col0=right, col1=up, col2=forward).
3. **`model.py` line 1392-1427** (`HeadPoseHead`): Add `_init_weights` method (HIGH severity finding from Agent 4 audit).
4. **`model.py` line 1427** (`HeadPoseHead.forward`): Add `torch.tanh` on direction output to prevent NaN propagation through HeadPoseFiLM.
5. **New file: `tests/test_head_pose_geo.py`**: Round-trip unit test + regression test for column ordering.
6. **`config.py`**: Reduce `HP_ROTATION_WEIGHT` from 1.0 to 0.5 (optional safeguard against geodesic gradient dominance).
