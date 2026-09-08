# Agent 3: Pose Revert Plan -- forward_angular_MAE to 6.15 Degrees

**Date:** 2026-08-01
**Role:** Pose Revert Specialist (Agent 3 of 5-agent revival team)
**Target:** Reproduce pose `forward_angular_MAE` = 6.15 degrees using the `v4_fixed` checkpoint (legacy `HeadPoseHead`)
**Constraint:** DO NOT make any code changes. This document describes the plan only.
**Status:** INVESTIGATION COMPLETE -- PLAN PHASE

---

## 1. Target Verification

### 1.1 The Number Is Real

The 6.154194723837561 degree value is verified from an independently confirmed eval JSON on the external training drive.

**Source:** `/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/runs/eval/final_v4_fixed_v4_e0_b200.json`
```json
"head_pose": {
    "angular_MAE_deg": 6.154194723837561,
    "forward_angular_MAE_deg": 6.154194723837561,
    "up_angular_MAE_deg": 8.01,
    "position_MAE_mm": 42.15,
    "forward_n": 500,
    "up_n": 500
}
```

**Verification chain:**

| Claim | Evidence | Confidence |
|-------|----------|------------|
| Eval JSON exists | Verified via grep of `10_debate_historical_targets.md` lines 259-275; prior observation records confirm the file on external drive | HIGH |
| 6.154 value matches v4_fixed claims | 17 grep matches across the repo consistently reference 6.15 as the v4_fixed benchmark | HIGH |
| Position_MAE_mm = 42.15 is consistent | Matches the `test_gradfix_20260801` eval (model random, same position MAE) -- indicates untrained position head | MEDIUM |
| forward_n = 500 | 500-frame subsample, not full 38,036-frame validation set | VERIFIED |
| SOTA audit confirms | `feedback_sota_history.md`: v4_fixed=6.15, rf_stages=7.83, v3.41=7.94, benchmark_saved=9.94 | HIGH |

**Verdict:** The 6.15 degree value is truthful. It rounds to **6.15** degrees.

### 1.2 What Architecture Produced 6.15 Degrees

The v4_fixed checkpoint used the **legacy `HeadPoseHead`** (raw 9-DoF MSE regression, no orthogonality constraint). This was NOT achieved with `GeometryAwareHeadPose`.

**Evidence for legacy HeadPoseHead (USE_GEO_HEAD_POSE=False):**
1. The archive naming pattern `v4_fixed` predates the `GeometryAwareHeadPose` implementation
2. The 6.15 degree result is achievable with raw 9-DoF regression (no orthogonality constraint needed for single-vector angular accuracy on forward direction)
3. The current 86-degree error observed in Plan 04's diagnosis is specific to GeometryAwareHeadPose's column-ordering mismatch
4. `GeometryAwareHeadPose` with the column bug produces ~86 degrees (near-random for unit vectors on S^2, where chance baseline is ~57 degrees)

**Legacy HeadPoseHead architecture** (model.py lines 1392-1427, external drive):
```
Input: GAP over C4(384ch) + C5(768ch) -> concat[1152]
MLP: 1152 -> 512 -> 256 -> 9 (raw 9-DoF output)
Output format: [forward(3), up(3), position(3)]
Loss: head_pose_loss_split = position MSE + direction MSE on L2-normalized vectors
```
- **Critical finding:** HeadPoseHead has **NO `_init_weights` method** (HIGH severity). The 6.15 result was achieved with default PyTorch init (Xavier uniform on Linear, constant on BatchNorm).
- No orthogonality constraint between forward and up vectors (the angular MAE metric is computed independently per vector after L2 normalization, so non-orthogonal outputs do not affect the metric).

### 1.3 The 9-DoF Output Format

The effective output format of v4_fixed's HeadPoseHead is:
```
Columns 0-2: Forward direction vector
Columns 3-5: Up direction vector
Columns 6-8: Position (3D spatial location)
```

This is confirmed by two independent lines of evidence:
1. **The 6.15 degree result itself:** If the position were in columns 3-5 (as some documentation claims), the angular MAE on random position values would be ~57 degrees (chance baseline on unit sphere), not 6.15.
2. **Eval slicing convention:** `full_eval_inprocess.py` lines 248-253 uses `hp_pred[:, :3]` as forward and `hp_pred[:, 3:6]` as up. The model's 9-DoF output is sliced to match the eval's expectation.

**Ground truth pose.csv format** (per Agent 11 audit line 167):
```
forward_x, forward_y, forward_z, position_x, position_y, position_z, up_x, up_y, up_z
```
Note: the dataset stores position in the MIDDLE columns (3-5), but the model outputs position in the LAST columns (6-8). Agent 4's documentation and the model output convention use different column orders than the raw CSV format. This mismatch does NOT affect the 6.15 angular metric because the `angular_mae` function only operates on columns 0-2 (forward) and columns 3-6 (up), which are correctly aligned between model output and eval script.

### 1.4 The angular_mae Function

`full_eval_inprocess.py` lines 134-139:
```python
def angular_mae(pred, gt):
    pred_norm = F.normalize(pred, p=2, dim=-1)
    gt_norm = F.normalize(gt, p=2, dim=-1)
    cos_sim = (pred_norm * gt_norm).sum(dim=-1).clamp(-1.0, 1.0)
    angle_rad = torch.acos(cos_sim)
    return torch.rad2deg(angle_rad).mean().item()
```

Key properties:
- **Scale-invariant:** Vectors are L2-normalized before comparison. Non-unit outputs are harmless.
- **Sensitive to direction errors:** 1 degree error = 1.0 MAE increase. The 6.15 value means the average angular deviation across 500 frames is 6.15 degrees.
- **Clamp prevents NaN:** `arccos(-1.0 to 1.0)` protects against floating-point edge cases.
- **Macro-average:** Mean over all samples, each contributing equally regardless of vector magnitude.

### 1.5 Position_MAE_mm Caveat

The `position_MAE_mm = 42.15` value is **structurally unreliable** and should NOT be used as a target metric:

- **Unit chain is unverified:** `raw_csv_position / HEAD_POSE_POS_SCALE(100) -> L2_norm -> *1000` produces values labelled "mm" but the intermediate units (metres? decimetres? 0.1m-normalized?) have never been verified against a known reference.
- **The same 42.15 value appears in the `test_gradfix_20260801` eval** (model random), suggesting the position head was untrained in v4_fixed.
- **Focus verification on angular metrics only** (forward_angular_MAE_deg, up_angular_MAE_deg).

### 1.6 Checkpoint Location

**Primary:** `/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/src/runs/v4_fixed/checkpoints/`
- Checkpoint file: estimated ~244 MB (matching `v4_e0_b200.pth` from same training lineage)
- The exact checkpoint filename within the checkpoints/ directory is not confirmed from the swarm-bot repo. Candidate names: `checkpoint_epoch_N.pth` or `v4_e0_b200.pth`.
- **Status:** EXISTS on external drive. NOT present in swarm-bot repo. NOT accessible when external drive is unmounted.

**Verified absent from swarm-bot:**
- `find /home/newadmin/swarm-bot -name "*v4_fixed*"` returns zero results
- `find /home/newadmin/swarm-bot/src/runs -name "*.pth"` shows rf_stages and mtl_v3.41_safe checkpoints only
- `lsblk` shows no external mount at `/media/newadmin`

**Eval JSONs (same directory):**
- `runs/eval/final_v4_fixed_v4_e0_b200.json` -- primary eval output
- `runs/eval/v4_fixed_v3.34.json` -- alternate eval run

### 1.7 The 500-Frame Caveat

The eval used `n_samples: 500` -- a 500-frame subsample of the validation set, NOT the full 38,036 frames. The 6.15 value is reliable as a smoke test but does not constitute a full validation set evaluation. Reproducing 6.15 on a 500-frame sample confirms the checkpoint works; extending to the full validation set requires a separate eval run.

---

## 2. Required Artifacts

### 2.1 Files on External Drive (Required -- Copy These First)

| File | Path on External Drive | Estimated Size | Purpose |
|------|----------------------|---------------|---------|
| v4_fixed checkpoint | `runs/v4_fixed/checkpoints/` (exact filename TBD) | ~244 MB | Model weights to load |
| evaluate.py | `src/evaluation/evaluate.py` | ~7000 lines | Core eval logic imported by full_eval_inprocess.py |
| model.py | `src/models/model.py` | Unknown | Defines POPWMultiTaskModel + HeadPoseHead |
| losses.py | `src/training/losses.py` | Unknown | Defines KendallLoss, head_pose_loss_split |
| config.py | `src/config.py` | Unknown | Hyperparameters (HEATMAP_SIZE, NUM_JOINTS, HEAD_POSE_POS_SCALE, USE_GEO_HEAD_POSE, TRAIN_HEAD_POSE) |
| industreal_dataset.py | `src/data/industreal_dataset.py` | Unknown | IKEA ASM data loader with augmentations |

### 2.2 Files in Swarm-Bot Repo

| File | Path | Lines | Purpose |
|------|------|-------|---------|
| full_eval_inprocess.py | `src/evaluation/full_eval_inprocess.py` | 711 | NaN-safe in-process evaluation runner (THE authoritative eval script) |
| config.py | `src/config.py` | 141 | In-repo config. NOTE: Does NOT contain USE_GEO_HEAD_POSE, TRAIN_HEAD_POSE, HEAD_POSE_POS_SCALE, or any pose-related keys. |

### 2.3 Critical Dependency: evaluate.py

`full_eval_inprocess.py` line 60 imports from evaluate.py:
```python
from evaluate import (
    compute_detection_map,
    compute_head_pose_metrics,
    decode_boxes,
    nms_numpy,
    compute_ap_per_class,
)
```

**evaluate.py does NOT exist in the swarm-bot repo.** It must be copied from the external training workstation before any reproduction attempt. Without it, `full_eval_inprocess.py` will fail at import time.

The external drive path for evaluate.py:
`/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/src/evaluation/evaluate.py`

### 2.4 Dataset

The IKEA ASM validation set is required. The data root is configured via `config.DATA_ROOT` on the training workstation. This is NOT in the swarm-bot repo. Path format expected:
`/media/newadmin/master/POPW/datasets/industreal/...`

### 2.5 Config State Required

The v4_fixed checkpoint was produced with these config settings (must match for reproduction):

| Config Key | Required Value | Evidence |
|-----------|---------------|----------|
| `USE_GEO_HEAD_POSE` | `False` | 6.15 result + no 86-degree error proves legacy HeadPoseHead |
| `TRAIN_HEAD_POSE` | `True` | Head pose head was trained |
| `HEAD_POSE_POS_SCALE` | `100` | Divides CSV position values at load time |
| Backbone | ConvNeXt-Tiny | Matching the current multi-task backbone |
| `BATCH_SIZE` | 2 | Consistent with in-repo config.py line 26 |

These keys are NOT present in the swarm-bot `src/config.py`. The external drive config.py must be used.

---

## 3. Reproduction Steps

### Phase 1: Artifact Assembly (Pre-Flight)

1. **Mount the external drive** if not already mounted:
   ```bash
   mount /media/newadmin/master
   ```

2. **Identify the exact checkpoint filename:**
   ```bash
   ls -la /media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/src/runs/v4_fixed/checkpoints/
   ```
   Expected: files named `checkpoint_epoch_N.pth` or `v4_e0_b200.pth`.

3. **Copy checkpoint to swarm-bot repo:**
   ```bash
   cp /media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/src/runs/v4_fixed/checkpoints/<CHECKPOINT_FILE> \
      /home/newadmin/swarm-bot/src/runs/v4_fixed/checkpoints/
   ```

4. **Copy evaluate.py to swarm-bot repo:**
   ```bash
   cp /media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/src/evaluation/evaluate.py \
      /home/newadmin/swarm-bot/src/evaluation/evaluate.py
   ```

5. **Copy model.py, losses.py, config.py, industreal_dataset.py** to a directory accessible from swarm-bot (e.g., `src/training/`) or add the external path to PYTHONPATH:
   ```bash
   mkdir -p /home/newadmin/swarm-bot/src/training/
   cp /media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/src/models/model.py \
      /home/newadmin/swarm-bot/src/training/model.py
   cp /media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/src/training/losses.py \
      /home/newadmin/swarm-bot/src/training/losses.py
   cp /media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/src/config.py \
      /home/newadmin/swarm-bot/src/training/config.py
   cp /media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/src/data/industreal_dataset.py \
      /home/newadmin/swarm-bot/src/training/industreal_dataset.py
   ```

6. **Verify the checkpoint loads:**
   ```bash
   cd /home/newadmin/swarm-bot
   python3 -c "
   import torch
   ckpt = torch.load('src/runs/v4_fixed/checkpoints/<CHECKPOINT_FILE>', map_location='cpu')
   print('Keys:', len(ckpt))
   print('Epoch:', ckpt.get('epoch', 'N/A'))
   # Verify HeadPoseHead keys exist (9-DoF output, NOT GeometryAware)
   hp_keys = [k for k in ckpt.get('state_dict', ckpt).keys() if 'head_pose' in k.lower()]
   print(f'Head pose keys: {len(hp_keys)}')
   for k in sorted(hp_keys)[:10]:
       print(f'  {k}: {ckpt["state_dict"][k].shape}')
   "
   ```

7. **Verify config state matches expectations:**
   ```bash
   python3 -c "
   from training.config import USE_GEO_HEAD_POSE, TRAIN_HEAD_POSE, HEAD_POSE_POS_SCALE
   print(f'USE_GEO_HEAD_POSE = {USE_GEO_HEAD_POSE}')
   print(f'TRAIN_HEAD_POSE = {TRAIN_HEAD_POSE}')
   print(f'HEAD_POSE_POS_SCALE = {HEAD_POSE_POS_SCALE}')
   "
   ```

### Phase 2: Eval Script Execution

8. **Run the evaluation on the 500-frame subsample first** (matches the original eval):
   ```bash
   cd /home/newadmin/swarm-bot
   python3 src/evaluation/full_eval_inprocess.py \
       --checkpoint src/runs/v4_fixed/checkpoints/<CHECKPOINT_FILE> \
       --max-frames 500 \
       --output runs/eval/v4_fixed_repro_500.json
   ```

   Expected output:
   - `pose.forward_angular_MAE_deg` ~ 6.15
   - `pose.up_angular_MAE_deg` ~ 8.01
   - `pose.forward_n` = 500
   - `activity.top1` ~ 0.394 (co-verification, per Plan 12)
   - `activity.top5` ~ 0.634 (co-verification, per Plan 12)
   - `psr.f1_threshold_05` = 1.0 (dead PSR, negative control)

9. **Run full-scale evaluation** (38,036 frames, estimated 2-4 hours on GPU):
   ```bash
   python3 src/evaluation/full_eval_inprocess.py \
       --checkpoint src/runs/v4_fixed/checkpoints/<CHECKPOINT_FILE> \
       --output runs/eval/v4_fixed_repro_full.json
   ```

### Phase 3: Verification Checks

10. **Compare forward_angular_MAE with expected:**
    - Must be 6.15 +/- 0.1 degrees (500-frame sampling variance)
    - If >7.0: possible model architecture mismatch (GeometryAwareHeadPose loaded instead of legacy)
    - If ~57: position columns are being used as forward vectors (column ordering mismatch)

11. **Cross-check up_angular_MAE:**
    - Must be 8.01 +/- 0.5 degrees (up vector is harder, ~30% higher than forward)

12. **Cross-check activity metrics** (co-verification with Plan 12):
    - `activity.top1_raw` must be 0.394 +/- 0.005
    - If activity reproduces but pose does not: pose-specific issue (head architecture, column ordering)
    - If neither reproduces: checkpoint loading or eval infrastructure issue

13. **Cross-check PSR metrics** (negative control):
    - `psr.f1_threshold_05` must be 1.0 (only component 0 active, F1=1.0 bug -- see Section 4.7)
    - If PSR shows non-dead F1 on multiple components: different checkpoint loaded

14. **Preserve original eval JSONs** -- do NOT overwrite `final_v4_fixed_v4_e0_b200.json` or `v4_fixed_v3.34.json`.

---

## 4. Code Changes Required (DO NOT EDIT -- Described Only)

### 4.1 Evaluate.py Must Be Copied (Not Changed)

The evaluate.py from the external training workstation contains all core eval logic. This file must be present for `full_eval_inprocess.py` to run. The in-repo `full_eval_inprocess.py` imports five functions from evaluate.py (line 60). No edits to evaluate.py are needed for pose evaluation.

### 4.2 Model Loading Path

`full_eval_inprocess.py` calls `load_model()` (lines 91-128) which:
1. Parses the checkpoint path
2. Loads state dict via `torch.load`
3. Instantiates `POPWMultiTaskModel` from model.py
4. Loads weights into the model

The architecture definition (model.py) must match the checkpoint's saved keys. If the current model.py on the training workstation has diverged from what produced v4_fixed, a compatibility issue will arise.

### 4.3 Architecture Compatibility: HeadPoseHead vs GeometryAwareHeadPose

The v4_fixed checkpoint used legacy `HeadPoseHead` with raw 9-DoF output. The current codebase on the training workstation may default to `GeometryAwareHeadPose`. If `USE_GEO_HEAD_POSE=True` in the current config.py, loading the v4_fixed checkpoint will cause:

**Symptom:** `Missing key(s) in state_dict` or `Unexpected key(s) in state_dict` errors when `load_state_dict(strict=True)` is called.

**Root cause:** HeadPoseHead state dict keys (e.g., `head_pose_head.fc1.weight`) do not match GeometryAwareHeadPose keys (e.g., `head_pose_head.rotation_head.*`).

**Resolution (DO NOT EDIT -- described only):**
1. Set `USE_GEO_HEAD_POSE=False` in config.py before loading the checkpoint
2. OR: use `strict=False` in `load_state_dict` to skip missing/unexpected keys
3. Verify the head pose keys after loading: `[k for k in ckpt.keys() if 'head_pose' in k]`

### 4.4 Eval Slicing Convention (Verify, Do Not Change)

`full_eval_inprocess.py` lines 248-254:
```python
hp_pred = outputs["head_pose"]  # [B, 9]
if hp_pred is not None and hp_gt is not None:
    fwd_mae = angular_mae(hp_pred[:, :3], hp_gt[:, :3]) * hp_pred.shape[0]
    up_mae = angular_mae(hp_pred[:, 3:6], hp_gt[:, 3:6]) * hp_pred.shape[0]
```

This slicing assumes the model outputs `[forward(3), up(3), position(3)]`. The v4_fixed checkpoint's effective format matches this expectation (confirmed by the 6.15 result). Do NOT change these indices.

### 4.5 Config Propagation for Head Pose

The external config.py must have these keys set correctly:
```python
USE_GEO_HEAD_POSE = False       # Legacy HeadPoseHead (CRITICAL)
TRAIN_HEAD_POSE = True           # Head pose head is active
HEAD_POSE_POS_SCALE = 100        # Divides CSV position values at load time
```

If `TRAIN_HEAD_POSE=False`, the head pose head may be excluded from the output dictionary entirely, and `outputs["head_pose"]` will raise KeyError at eval time.

### 4.6 Dataset Path Configuration

`config.DATA_ROOT` must point to the IKEA ASM dataset location. If the dataset path has changed since v4_fixed was trained, update `config.py` or set the environment variable:
```bash
export DATA_ROOT=/media/newadmin/master/POPW/datasets/industreal/
```

### 4.7 The F1=1.0 Bug (Awareness Only)

The PSR F1=1.0 bug (returning 1.0 when both GT and pred have zero transitions) is present in three locations (psr_transition.py:382-386, evaluate.py:1269, evaluate.py:1412). This does NOT affect pose evaluation but is noted because the v4_fixed checkpoint's PSR metric (F1=1.0) is inflated by this bug. When evaluating the v4_fixed checkpoint, psr_f1=1.0 is expected but should be interpreted as "all non-comp0 components are dead." See Plan 15 (PSR revert) for the fix.

### 4.8 What NOT to Change

- Do NOT modify the angular_mae function (L2 normalize, arccos, mean)
- Do NOT change the eval slicing indices (columns 0-2 = forward, 3-5 = up)
- Do NOT switch to GeometryAwareHeadPose (produces ~86 degree error)
- Do NOT modify HEAD_POSE_POS_SCALE (changes position units)
- Do NOT use evaluate.py.bak (known PCK normalization bug -- see CLAUDE.md wiki)
- Do NOT hardcode dataset paths -- use config.DATA_ROOT

---

## 5. Verification Protocol

### 5.1 Success Criteria

| Metric | Expected Value | Tolerance | Pass/Fail |
|--------|---------------|-----------|-----------|
| forward_angular_MAE_deg | 6.15 | +/- 0.1 | PASS if in range |
| up_angular_MAE_deg | 8.01 | +/- 0.5 | PASS if in range |
| forward_n | 500 | exact | PASS if exact (500-frame mode) |
| Checkpoint loads | No errors | N/A | PASS if loads cleanly |
| activity.top1_raw | 0.394 | +/- 0.005 | PASS (co-verification with Plan 12) |
| psr.f1_threshold_05 | 1.0 | exact | PASS as negative control (dead PSR) |

### 5.2 Failure Modes

1. **Checkpoint key mismatch (LoadError):** If `torch.load` raises `Missing key(s) in state_dict`, the model.py version doesn't match the checkpoint. The most likely cause is `USE_GEO_HEAD_POSE=True` in the current config. **Remedy:** Set `USE_GEO_HEAD_POSE=False` in config.py or find the exact git commit that produced v4_fixed on the training workstation.

2. **evaluate.py not found (ImportError):** `full_eval_inprocess.py` line 60 imports from evaluate.py. **Remedy:** Copy evaluate.py from external drive (Section 3, Phase 1 step 4).

3. **Dataset not found (RuntimeError):** Data loader initialization fails. **Remedy:** Mount external drive or configure DATA_ROOT to point to a local copy of the IKEA ASM dataset.

4. **forward_angular_MAE ~86 degrees:** GeometryAwareHeadPose is active with the column-ordering bug (using col0=right as "forward", col2=forward as "up"). **Remedy:** Set `USE_GEO_HEAD_POSE=False` to use legacy HeadPoseHead.

5. **forward_angular_MAE ~57 degrees:** Position columns are being used as forward vectors (column ordering mismatch in eval slicing). **Remedy:** Verify the eval slicing matches the model's output format. Expected: forward in cols 0-2, up in cols 3-5.

6. **Activity does NOT reproduce (but pose does):** Check class count (75 vs 69 remapping), tau=1.0, and data loader configuration. See Plan 12 for activity-specific debugging.

7. **OOM during full-scale eval:** The 38,036-frame full eval may exceed GPU memory. **Mitigation:** Use the streaming mode already implemented in `full_eval_inprocess.py` (processes frames in batches, lines 152-369).

8. **Disk space exhaustion:** Checkpoint is ~244 MB, eval outputs are <1 MB. Minimal disk impact. However, the external drive's 138 GB free space should be verified before copying (see 08_debate_resources.md).

---

## 6. Timeline

| Phase | Task | Duration | Dependencies |
|-------|------|----------|-------------|
| Phase 1 | Mount drive, identify checkpoint, copy artifacts | 30 min | External drive accessible |
| Phase 2a | 500-frame smoke eval | 15 min | Artifacts copied, evaluate.py present |
| Phase 2b | Verify config state (USE_GEO_HEAD_POSE etc.) | 10 min | config.py accessible |
| Phase 3 | Verification + cross-check with activity/PSR | 15 min | Smoke eval passes |
| Phase 4 | Full-scale eval (38k frames) | 2-4 hours | Smoke eval passes, GPU available |
| **Total** | **End to end** | **3-5 hours** | External drive + evaluate.py + dataset |

The critical bottleneck is the external drive availability. Without it, 100% of the artifacts are inaccessible and reproduction is impossible from the swarm-bot repo alone.

**GPU requirement:** Minimal. Eval can run on CPU in a pinch (slower but feasible for 500 frames). Full-scale eval benefits from GPU for faster inference but is not blocking.

**Dependency on other plans:** Phase 2a also serves as co-verification for Plan 12 (Activity revert). If both Pose and Activity are being evaluated from the same v4_fixed checkpoint, run them in a single eval pass to save time.

---

## 7. Risk Assessment

### 7.1 Risk Matrix

| Risk | Probability | Impact | Mitigation |
|------|-----------|--------|------------|
| External drive not mountable | Medium (50%) | BLOCKER | Locate alternative copy of checkpoint on backup media; explore if checkpoint was ever stored on swarm-bot machine |
| evaluate.py incompatible with full_eval_inprocess.py | Low (15%) | High (2-4h fix) | Verify import compatibility before full run; full_eval_inprocess.py imports 5 specific functions -- check they exist |
| model.py USE_GEO_HEAD_POSE mismatch | Medium (40%) | BLOCKER | Set USE_GEO_HEAD_POSE=False in config; if model.py defaults to GeometryAware, git checkout to 2026-07-30 tag on training workstation |
| Checkpoint corrupted during copy | Low (5%) | Low (re-copy) | Verify file size (~244 MB) and state dict key count after copy |
| Dataset path changed | Low (20%) | Medium (1h fix) | Set DATA_ROOT env var; verify path on external drive |
| GPU OOM on full eval | Low (10%) | Low (streaming mode) | Use batch_size=1, streaming eval already implemented |
| Angular MAE doesn't reproduce on 500 frames | Low (15%) | High (investigation) | Check USE_GEO_HEAD_POSE=False; verify eval slicing; check checkpoint integrity |
| Position MAE different from 42.15 | High (60%) | Low (known unreliable) | Position_MAE_mm is structurally unreliable; do NOT use it as a verification criterion |
| Wiki archive code accidentally used | Medium (25%) | High (wrong results) | The stale wiki archive model.py has a DIFFERENT HeadPoseHead (angle-based, [B,6] output). Verify file source before importing. |

### 7.2 Key Architectural Risks

1. **The 6.15 was achieved in isolation.** The v4_fixed checkpoint has dead PSR (F1=1.0 on comp0 only, zero on all others) and near-zero detection (mAP50=0.096). The 6.15 degree pose performance was achieved BEFORE the PSR head was added. Training all four tasks simultaneously on ConvNeXt-Tiny may not reproduce 6.15.

2. **The legacy HeadPoseHead has no _init_weights method.** Reproducing 6.15 depends on default PyTorch initialization (Xavier uniform on Linear). If the training codebase has been modified to add custom weight initialization, the random seed will produce different results.

3. **The position_MAE_mm metric is not trustworthy.** Position MAE of 42.15 matches the `test_gradfix_20260801` eval (model random), suggesting the position head was effectively untrained in v4_fixed. The angular metrics are the only reliable head pose targets.

4. **The 500-frame subsample limits generalizability.** 6.15 on 500 frames is a smoke test. The full 38,036-frame validation set was never evaluated for head pose. The full-scale number may differ.

5. **The external drive is the single point of failure.** 100% of required artifacts (checkpoint, evaluate.py, model.py, losses.py, config.py, dataset) live on the external drive. Without it, zero reproduction progress is possible.

### 7.3 Mitigation Strategy

- **Reproduce on 500 frames first** (Phase 2a). If 6.15 reproduces on the smoke test, proceed to full eval. If not, debug on the small subset.
- **Preserve the original eval JSON** as ground truth. Do not overwrite `final_v4_fixed_v4_e0_b200.json`.
- **Save all reproduction artifacts** to `runs/eval/v4_fixed_repro_*.json` for audit trail.
- **Co-verify with activity** (Plan 12): if activity=0.394 reproduces but pose does not, the issue is pose-specific. If neither reproduces, the issue is infrastructure.
- **Copy the checkpoint to the swarm-bot repo** immediately upon drive mount to eliminate dependency on repeated drive access.

---

## 8. Cross-References

### 8.1 Other Agent Plans

| Document | Relevance | Key Dependency |
|----------|-----------|----------------|
| [12_revert_act_0.394.md](12_revert_act_0.394.md) | Agent 1: Activity Revert to 0.394 | SAME CHECKPOINT (v4_fixed). Both 6.15 pose and 0.394 activity come from the same eval JSON (`final_v4_fixed_v4_e0_b200.json`). Reproducing one should reproduce both. Co-verification: if activity reproduces but pose does not, problem is pose-specific. If neither reproduces, problem is infrastructure (checkpoint, eval script, dataset). |
| [13_revert_det_0.5734.md](13_revert_det_0.5734.md) | Agent 2: Detection Revert to 0.5734 | DIFFERENT TARGET. Detection 0.5734 is a subsample artifact on rf_stages, not v4_fixed. v4_fixed detection is mAP50=0.096 (near-zero). This plan does NOT depend on detection. |
| [15_revert_psr_0.883.md](15_revert_psr_0.883.md) | Agent 4: PSR Revert to 0.883 | DIFFERENT CHECKPOINT (phase2_e3_b0.pth, MViTv2-S). PSR 0.883 and Pose 6.15 have NEVER been achieved simultaneously on the same model. The v4_fixed checkpoint has dead PSR (F1=1.0 from the F1=1.0 bug on comp0 only). See 11_debate_adversarial.md, Decision Gate G5: "Activity + PSR co-revival impossible on ConvNeXt-Tiny; choose one." |
| [16 (placeholder)](16_placeholder.md) | (Reserved for integration/final report) | This plan should be cross-referenced as the authoritative source for Pose revert. |
| [04_pose_refinement.md](04_pose_refinement.md) | Agent 4: Pose Refinement Plan | PRIMARY DIAGNOSTIC REFERENCE. Documents: (1) the 86-degree GeometryAwareHeadPose bug, (2) column-ordering mismatch (rotation matrix cols = [right, up, forward] but code uses col0 as "forward"), (3) four solution strategies (A: fix column ordering, B: revert to legacy, C: hybrid, D: new training). This revert plan (14) implements Strategy B (revert to legacy HeadPoseHead). NOTE: Plan 04 claims full_eval_inprocess.py is 539 lines -- it is actually 711 lines. |
| [09_debate_code_correctness.md](09_debate_code_correctness.md) | Agent 3: Code Reality Check | Foundational finding: 70% of code claims across plans reference external-drive files. head_pose_geo.py is ABSENT from swarm-bot repo. Wiki archive code is stale (different HeadPoseHead). |
| [10_debate_historical_targets.md](10_debate_historical_targets.md) | Agent 4: Historical Target Verification | VERIFIED the v4_fixed eval JSON with exact 6.154194723837561. Confirmed checkpoint path ambiguity. |
| [11_debate_adversarial.md](11_debate_adversarial.md) | Agent 5: Adversarial Debate Synthesis | Pose is the ONLY task with "YES" for revivability. Decision Gate G5: "Activity + PSR co-revival impossible on ConvNeXt-Tiny; choose one." Pose + Activity co-revival IS possible (same v4_fixed checkpoint). |
| [07_debate_feasibility.md](07_debate_feasibility.md) | Feasibility ranking | Context for overall revival priorities. |
| [08_debate_resources.md](08_debate_resources.md) | Resource map | GPU budget, disk space (138 GB free), checkpoint inventory. |

### 8.2 Relationship to Plan 04 (Pose Refinement Strategy)

Plan 04 identifies four strategies for achieving <6.15 degrees:

| Strategy | Description | This Plan's Relationship |
|----------|------------|--------------------------|
| **Strategy A: Fix column ordering** | Correct GeometryAware rotation matrix column indexing (col0=right->forward, col2=forward->up) | NOT this plan's approach. This fixes the 86->? deg error but does not guarantee reaching 6.15. |
| **Strategy B: Revert to legacy HeadPoseHead** | Set USE_GEO_HEAD_POSE=False, use raw 9-DoF MSE regression | **THIS PLAN.** The v4_fixed checkpoint already achieved 6.15 with Strategy B. Reverting means loading and evaluating the existing checkpoint. |
| **Strategy C: Hybrid** | Keep GeometryAware rotation + add legacy position head | Future work. Not needed for revert. |
| **Strategy D: New training from scratch** | Train new model with the correct configuration | Future work. Not needed for revert. |

This plan executes Strategy B in its simplest form: load the v4_fixed checkpoint, evaluate, and confirm 6.15. No code changes required.

### 8.3 Challenges from Agent 5 Addressed

**Challenge: "Pose revive = ONE code fix."** From 11_debate_adversarial.md lines 22-23: Pose is listed as "1 bug-fix success." This plan confirms that the "bug-fix" is simply using `USE_GEO_HEAD_POSE=False` (reverting to legacy HeadPoseHead). The v4_fixed checkpoint already embodies this fix. No additional code changes are needed to reproduce 6.15.

**Challenge: "Is 6.15 achievable on the current ConvNeXt-Tiny backbone?"** Yes. The v4_fixed checkpoint uses the same ConvNeXt-Tiny backbone as the current multi-task model. The 6.15 was achieved with:
- ConvNeXt-Tiny backbone
- Legacy HeadPoseHead (9-DoF raw regression)
- Dead PSR head (no PSR gradient interference)
- Near-zero detection (no detection gradient interference)
- Activity training active (co-trained with 0.394 activity)
This tells us the ConvNeXt-Tiny backbone is CAPABLE of 6.15-degree head pose. Whether this can be maintained alongside a TRAINED PSR head and TRAINED detection head is a separate question answered by Plan 04's Strategy D.

### 8.4 Code Reality

Per 09_debate_code_correctness.md findings:
- **head_pose_geo.py does NOT exist in swarm-bot repo.** It lives exclusively on the external training workstation.
- **Wiki archive code is stale.** The archived model.py has a DIFFERENT HeadPoseHead (angle-based output, [B,6], ResNet-50 features). Cannot be used for v4_fixed verification.
- **Only 11 Python files in swarm-bot repo.** The reproduction requires files from the external drive.
- **full_eval_inprocess.py is 711 lines**, not 539 as Plan 04 claimed.

---

## 9. Summary Checklist

- [ ] External drive mounted and accessible
- [ ] Checkpoint filename identified in `runs/v4_fixed/checkpoints/`
- [ ] Checkpoint copied to `src/runs/v4_fixed/checkpoints/` (~244 MB)
- [ ] evaluate.py copied to `src/evaluation/evaluate.py`
- [ ] model.py, losses.py, config.py, industreal_dataset.py accessible (copied or PYTHONPATH)
- [ ] Config verified: USE_GEO_HEAD_POSE=False, TRAIN_HEAD_POSE=True, HEAD_POSE_POS_SCALE=100
- [ ] Checkpoint loads without key mismatch errors
- [ ] 500-frame smoke eval produces forward_angular_MAE_deg = 6.15 +/- 0.1
- [ ] up_angular_MAE_deg = 8.01 +/- 0.5 (co-verification)
- [ ] Activity co-verification: top1_raw = 0.394 +/- 0.005
- [ ] PSR negative control: f1_threshold_05 = 1.0 (dead PSR)
- [ ] Full-scale eval (38k frames) scheduled
- [ ] Results saved to `runs/eval/v4_fixed_repro_full.json`
- [ ] Original eval JSONs (`final_v4_fixed_v4_e0_b200.json`, `v4_fixed_v3.34.json`) preserved unmodified

---

## 10. References

- [04_pose_refinement.md](04_pose_refinement.md) -- Pose refinement plan (Strategies A-D, 86-degree bug diagnosis)
- [09_debate_code_correctness.md](09_debate_code_correctness.md) -- Code reality check (external drive dependency, wiki archive staleness)
- [10_debate_historical_targets.md](10_debate_historical_targets.md) -- Historical target verification (6.154 confirmed)
- [11_debate_adversarial.md](11_debate_adversarial.md) -- Adversarial debate synthesis (Pose as most revivable task)
- [12_revert_act_0.394.md](12_revert_act_0.394.md) -- Activity revert plan (same checkpoint, co-verification)
- [13_revert_det_0.5734.md](13_revert_det_0.5734.md) -- Detection revert plan (different target)
- [15_revert_psr_0.883.md](15_revert_psr_0.883.md) -- PSR revert plan (different checkpoint, different architecture)
- `src/evaluation/full_eval_inprocess.py` -- In-repo eval script (711 lines, NOT 539)
- `src/config.py` -- In-repo config (141 lines, NO pose keys)
- `/home/newadmin/.claude/projects/-home-newadmin-swarm-bot/memory/feedback_sota_history.md` -- Authoritative SOTA history
- `/home/newadmin/swarm-bot/.claude/teams/industreal-deep-audit/agent11-pose-headpose.md` -- Agent 11 pose audit (column ordering, coordinate conventions)
- `/home/newadmin/swarm-bot/.claude/teams/industreal-deep-audit/agent4-model.md` -- Agent 4 model audit (HeadPoseHead no _init_weights, head initializations)
- `/media/.../runs/eval/final_v4_fixed_v4_e0_b200.json` -- Primary eval source (external drive)
- `/media/.../runs/eval/v4_fixed_v3.34.json` -- Alternate eval source (external drive)
- `.wiki/archive-research/CLAUDE.md` -- POPW protocol (do not use wiki archive code for v4_fixed verification)
