# Agent 1: Activity Revert Plan to 0.394 (Frame-Level, Raw)

**Date:** 2026-08-01
**Role:** Activity Revert Specialist (Agent 1)
**Target:** Reproduce activity frame-level top-1 = 0.394 (raw, uncalibrated) using the v4_fixed checkpoint
**Constraint:** DO NOT make any code changes. This document describes the plan only.

---

## 1. Target Verification

### 1.1 The Number Is Real

Two independent eval JSONs on the external training drive confirm the 0.394 number:

**Primary source:** `/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/runs/eval/v4_fixed_v3.34.json`
```json
"activity": {
    "top1": 0.39399999380111694,
    "top5": 0.6340000033378601,
    "top1_raw": 0.39399999380111694,
    "top5_raw": 0.6340000033378601,
    "n_samples": 500,
    "tau": 1.0
}
```

**Secondary source:** `/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/runs/eval/final_v4_fixed_v4_e0_b200.json`
```json
"activity": {
    "top1": 0.39399999380111694,
    "top5": 0.6340000033378601,
    "top1_raw": 0.39399999380111694,
    "top5_raw": 0.6340000033378601,
    "n_samples": 500,
    "tau": 1.0
}
```

Both are byte-identical. The number rounds to **0.394**. Verdict: verified.

### 1.2 What "Raw" Means

- `tau = 1.0`: No temperature scaling was applied. Tau=1.0 means raw logits were used directly.
- `top1_raw == top1`: Confirm no calibration occurred. The calibrated and raw numbers are identical because tau=1.0 is a no-op.
- This is NOT the 0.6223 from MViTv2-S (Agent 10's historical target report, Section 1). That 0.6223 was from a completely different architecture processing 16-frame video clips. The 0.394 is from ConvNeXt-Tiny, the same backbone as the current multi-task model.
- The 0.394 is the REAL achievable number on the current architecture. The aspirational 0.6223 (01_activity_revival.md) requires switching to MViTv2-S, which is an architectural change not a "revert."

### 1.3 What Architecture Produced 0.394

The v4_fixed checkpoint used:
- **Backbone:** ConvNeXt-Tiny (~28.6M params)
- **Activity head:** Simple MLP: LayerNorm -> Linear(512, 256) -> GELU -> Dropout(0.3) -> Linear(256, num_classes)
- **Number of classes:** 75 output classes (based on tau=1.0 with no remapping, matching the frame-level classification task)
- **FiLM conditioning:** activity label -> MLP -> (gamma, beta) applied after each ResNet/ConvNeXt block
- **Training regime:** Single-task or early multi-task phase before the PSR head was added (the v4_fixed checkpoint has dead PSR -- 10 of 11 components F1=0.0)

The current multi-task model uses the SAME ConvNeXt-Tiny backbone and SAME activity head architecture. The root cause of the activity regression from 0.394 to 0.023 (current SOTA_STATUS.md) is therefore training regime, not architecture.

### 1.4 Checkpoint Location

**Primary:** `/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/runs/v4_fixed/v4_e0_b200.pth`
- Size: 244,203,344 bytes (244 MB)
- Date: 2026-07-30
- Status: EXISTS on external drive, accessible when drive mounted

**Copy:** `/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/runs/v4_train2/v4_e0_b200.pth`
- Additional preserved copy

The checkpoint is NOT in the swarm-bot repo. It lives exclusively on the external training workstation drive.

### 1.5 The 500-Frame Caveat

Both eval JSONs used `n_samples: 500` -- a 500-frame subsample of the validation set, not the full 38,036-frame validation set. This is reasonable for a smoke test but does not constitute a full evaluation. Reproducing 0.394 on a 500-frame sample confirms the checkpoint's capability; extending to the full validation set requires a separate full-scale eval run (see Section 5).

---

## 2. Required Artifacts

### 2.1 Files on External Drive (Required, Copy These First)

| File | Path on External Drive | Size | Purpose |
|------|----------------------|------|---------|
| v4_fixed checkpoint | `runs/v4_fixed/v4_e0_b200.pth` | 244 MB | The model weights to load |
| evaluate.py (WITH dx*0.1 fix) | `src/evaluation/evaluate.py` | 6966 lines | Core eval logic imported by full_eval_inprocess.py |
| model.py | (on training workstation) | Unknown | Defines the POPWMultiTaskModel class |
| losses.py | (on training workstation) | Unknown | Defines KendallLoss, heatmap loss, etc. |
| config.py | (on training workstation) | Unknown | Hyperparameters (HEATMAP_SIZE, NUM_JOINTS, etc.) |
| industreal_dataset.py | (on training workstation) | Unknown | IKEA ASM data loader with augmentations |
| head_pose_geo.py | (on training workstation) | Unknown | Head pose geometry definitions |

### 2.2 Files in Swarm-Bot Repo

| File | Path | Lines | Purpose |
|------|------|-------|---------|
| full_eval_inprocess.py | `src/evaluation/full_eval_inprocess.py` | 711 | NaN-safe in-process evaluation runner |

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

The external drive path for evaluate.py with the dx*0.1 fix:
`/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/src/evaluation/evaluate.py`

### 2.4 Dataset

The IKEA ASM validation set is required. The data root is configured via `config.DATA_ROOT` on the training workstation. This is NOT in the swarm-bot repo. Path format expected: `/media/newadmin/master/POPW/datasets/industreal/...`

---

## 3. Reproduction Steps

### Phase 1: Artifact Assembly (Pre-Flight)

1. **Mount the external drive** if not already mounted:
   ```bash
   mount /media/newadmin/master
   ```

2. **Copy checkpoint to a known location:**
   ```bash
   cp /media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/runs/v4_fixed/v4_e0_b200.pth \
      /home/newadmin/swarm-bot/runs/v4_fixed/v4_e0_b200.pth
   ```

3. **Copy evaluate.py to swarm-bot repo:**
   ```bash
   cp /media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/src/evaluation/evaluate.py \
      /home/newadmin/swarm-bot/src/evaluation/evaluate.py
   ```

4. **Copy model.py, losses.py, config.py, industreal_dataset.py, head_pose_geo.py** to a directory accessible from the swarm-bot repo (e.g., `src/training/` or add the external path to PYTHONPATH).

5. **Verify the checkpoint loads:**
   ```bash
   python3 -c "
   import torch
   ckpt = torch.load('runs/v4_fixed/v4_e0_b200.pth', map_location='cpu')
   print('Keys:', len(ckpt))
   print('Epoch:', ckpt.get('epoch', 'N/A'))
   "
   ```

### Phase 2: Eval Script Execution

6. **Run the evaluation on the 500-frame subsample first** (matches the original eval):
   ```bash
   cd /home/newadmin/swarm-bot
   python3 src/evaluation/full_eval_inprocess.py \
       --checkpoint runs/v4_fixed/v4_e0_b200.pth \
       --max-frames 500 \
       --output runs/eval/v4_fixed_repro_500.json
   ```
   
   Expected output:
   - `activity.top1` ~ 0.394
   - `activity.top5` ~ 0.634
   - `activity.tau` = 1.0
   - `pose.angular_MAE_deg` ~ 6.15
   - `psr.f1_threshold_05` = 1.0 (dead PSR, expected)

7. **Run full-scale evaluation** (38,036 frames, may take hours):
   ```bash
   python3 src/evaluation/full_eval_inprocess.py \
       --checkpoint runs/v4_fixed/v4_e0_b200.pth \
       --output runs/eval/v4_fixed_repro_full.json
   ```

### Phase 3: Verification Checks

8. **Compare raw output with expected:**
   - `activity.top1_raw` must be 0.394 +/- 0.005 (frame-level sampling variance)
   - `activity.top5_raw` must be 0.634 +/- 0.005
   - `activity.tau` must be 1.0

9. **Cross-check pose metrics** (co-verification):
   - `pose.angular_MAE_deg` must be 6.15 +/- 0.1
   - If pose is significantly different, the checkpoint may have been corrupted during copy

10. **Cross-check PSR metrics** (negative control):
    - `psr.f1_threshold_05` must be 1.0 (only component 0 active)
    - If PSR is non-dead, this is a different checkpoint

---

## 4. Code Changes Required (DO NOT EDIT -- Described Only)

### 4.1 Evaluate.py Must Be Copied (Not Changed)

The 6966-line evaluate.py from the external training workstation contains the dx*0.1 fix (lines 2405-2409) and all core eval logic. This file must be present for `full_eval_inprocess.py` to run. No edits are needed -- the fix is already applied.

### 4.2 Model Loading Path

`full_eval_inprocess.py` or its import chain will call `torch.load(checkpoint_path)`. The checkpoint contains the full model state_dict. The architecture definition (model.py) must match the checkpoint's saved keys. If the current model.py has diverged from what produced v4_e0_b200.pth, a compatibility shim or version pinning may be needed.

### 4.3 Potential Model Architecture Mismatch

The current model.py on the training workstation may differ from what produced v4_fixed. Specifically:
- **Legacy HeadPoseHead vs GeometryAwareHeadPose:** The v4_fixed checkpoint almost certainly used `USE_GEO_HEAD_POSE=False` (legacy HeadPoseHead with raw 9-DoF MSE regression). The current codebase uses GeometryAwareHeadPose with a column-ordering bug producing ~86 degree error (04_pose_refinement.md, Section 2). If model.py now defaults to GeometryAwareHeadPose, loading the v4_fixed checkpoint may cause key mismatch errors.
- **Activity head class count:** Verify the saved checkpoint's classifier output dimension matches the expected 75 classes. A mismatch here is the most likely failure mode.

### 4.4 What NOT to Change

- Do NOT modify tau -- keep tau=1.0 for raw reproduction
- Do NOT apply temperature scaling or calibration
- Do NOT use the 69-group remapping (that was for MViTv2-S clip-level eval)
- Do NOT modify the activity head architecture
- Do NOT modify the ConvNeXt-Tiny backbone

---

## 5. Verification Protocol

### 5.1 Success Criteria

| Metric | Expected Value | Tolerance | Pass/Fail |
|--------|---------------|-----------|-----------|
| activity.top1_raw | 0.394 | +/- 0.005 | PASS if in range |
| activity.top5_raw | 0.634 | +/- 0.005 | PASS if in range |
| activity.tau | 1.0 | exact | PASS if exact |
| pose.angular_MAE_deg | 6.15 | +/- 0.1 | PASS if in range (co-verification) |
| psr.f1_threshold_05 | 1.0 | exact | PASS if dead PSR (negative control) |
| Checkpoint loads | No errors | N/A | PASS if loads cleanly |

### 5.2 Failure Modes

1. **Checkpoint key mismatch:** If `torch.load` raises `Missing key(s) in state_dict`, the model.py version doesn't match the checkpoint. Remedy: find the exact model.py version that produced v4_fixed (git checkout to 2026-07-30 on the training workstation).

2. **evaluate.py not found:** ImportError. Remedy: copy evaluate.py from external drive (Section 3, Phase 1 step 3).

3. **Dataset not found:** Runtime error when data loader initializes. Remedy: mount external drive or configure DATA_ROOT to point to a local copy.

4. **Activity top-1 different from 0.394:** If the number is materially different (e.g., 0.023 or 0.128):
   - Verify the correct checkpoint was loaded (check file size: 244 MB)
   - Verify tau=1.0 (no calibration accidentally applied)
   - Verify the frame subset is identical (500 frames, same random seed)
   - Check for data loading differences (augmentation pipeline, normalization)

5. **OOM during full-scale eval:** The 38,036-frame full eval may exceed GPU memory. Mitigation: use the streaming mode already implemented in `full_eval_inprocess.py` (processes frames in batches, lines 152-369).

---

## 6. Timeline

| Phase | Task | Duration | Dependencies |
|-------|------|----------|-------------|
| Phase 1 | Mount drive, copy artifacts | 15 min | External drive accessible |
| Phase 2a | 500-frame smoke eval | 10 min | Artifacts copied, evaluate.py present |
| Phase 2b | Full-scale eval (38k frames) | 2-4 hours | Smoke eval passes |
| Phase 3 | Verification + report | 30 min | Full eval complete |
| **Total** | **End to end** | **3-5 hours** | External drive + evaluate.py |

The critical bottleneck is the external drive availability. Without it, 100% of the artifacts are inaccessible and reproduction is impossible from the swarm-bot repo alone.

---

## 7. Risk Assessment

### 7.1 Risk Matrix

| Risk | Probability | Impact | Mitigation |
|------|-----------|--------|------------|
| External drive not mountable | Medium (50%) | BLOCKER | Locate alternative copy of checkpoint on backup media |
| evaluate.py incompatible with current full_eval_inprocess.py | Low (20%) | High (2-4h fix) | Verify import compatibility before full run |
| model.py architecture mismatch | Medium (40%) | BLOCKER | Git checkout training workstation to 2026-07-30 tag |
| Checkpoint corrupted during copy | Low (5%) | Low (re-copy) | Verify file size (244 MB) after copy |
| GPU OOM on full eval | Low (15%) | Low (streaming mode exists) | Use batch_size=1, streaming eval |
| Activity number doesn't reproduce | Medium (35%) | High (investigation needed) | Check 500-frame seed, augmentation pipeline, class mapping |
| Disk space exhaustion | Medium (40%) | BLOCKER | 08_debate_resources.md: 138 GB free, but 250 GB checkpoints; clear space before copying 244 MB checkpoint |

### 7.2 Key Architectural Risks

1. **The v4_fixed checkpoint's activity head was trained with dead PSR.** This means the activity performance was achieved in isolation -- the PSR head contributed zero gradient to the shared backbone. If we want BOTH activity=0.394 AND PSR=0.883, these were NEVER simultaneously achieved on ConvNeXt-Tiny. See 11_debate_adversarial.md: at most 2 of 4 tasks are simultaneously revivable.

2. **The 0.394 might depend on the FrameFraction=0.40 PR (#7).** If the current dataset loader uses a different FrameFraction, the eval data distribution will differ. Verify the data loader configuration before eval.

3. **The Kendall uncertainty weighting may have changed.** If the v4_fixed was trained with different task weights than the current codebase applies at eval time, the logits may be differently scaled. Since tau=1.0, this would manifest as a different top-1.

### 7.3 Mitigation Strategy

- **Reproduce on 500 frames first** (Phase 2a). If 0.394 reproduces on the smoke test, proceed to full eval. If not, debug on the small subset.
- **Preserve the original eval JSONs** as ground truth. Do not overwrite `v4_fixed_v3.34.json` or `final_v4_fixed_v4_e0_b200.json`.
- **Save all reproduction artifacts** to `runs/eval/v4_fixed_repro_*.json` for audit trail.

---

## 8. Relationship to Other Revival Plans

### 8.1 This Plan vs. Plan 01 (Activity Revival to 0.6223)

| Aspect | Plan 01 (0.6223) | This Plan (0.394) |
|--------|-----------------|-------------------|
| Architecture | MViTv2-S (34.3M params) | ConvNeXt-Tiny (~28.6M params) |
| Input | 16-frame video clips | Single frames |
| Class mapping | 75->69 group remap | 75-class direct |
| Eval script | eval_mecanno_mvitv2.py (MISSING) | full_eval_inprocess.py + evaluate.py |
| Checkpoint | mvit_rgb_meccano_pretrained.pyth (412 MB) | v4_e0_b200.pth (244 MB) |
| Current backbone match | NO -- requires architectural switch | YES -- same ConvNeXt-Tiny |
| Realistic to achieve | Only with MViTv2-S switch | Yes, with correct checkpoint and scripts |

**Conclusion:** Plan 01's 0.6223 is an aspirational target requiring architectural change. This plan's 0.394 is the achievable "revert" target on the current backbone.

### 8.2 This Plan vs. Plan 04 (Pose Refinement to 6.15)

The v4_fixed checkpoint simultaneously achieves:
- Activity top-1 = 0.394
- Pose angular MAE = 6.15 degrees

Both numbers come from the same eval JSON. Reproducing one should reproduce both. If pose reproduces but activity doesn't, the issue is activity-specific (class mapping, head architecture). If neither reproduces, the issue is checkpoint loading or eval infrastructure.

### 8.3 This Plan vs. Plan 03 (PSR Revival to 0.883)

The v4_fixed checkpoint has a COMPLETELY DEAD PSR head (F1=1.0 on component 0 only, zero on all others). The 0.883 PSR target comes from a DIFFERENT checkpoint (`phase2_e3_b0.pth`, 695 MB, MViTv2-S architecture). These two targets (activity=0.394 + PSR=0.883) have NEVER been achieved simultaneously on the same model. See 11_debate_adversarial.md, Decision Gate G5: "Activity + PSR co-revival impossible on ConvNeXt-Tiny; choose one."

### 8.4 This Plan vs. Plan 02 (Detection Revival to 0.5734)

The v4_fixed checkpoint has detection mAP50=0.096 (near-zero). The 0.5734 detection target was produced by a biased 250-batch subsample with a buggy eval script (dx*0.1 bug). The true detection mAP on ConvNeXt-Tiny multi-task is ~0.00009. This plan does NOT depend on detection working.

### 8.5 Cross-References to Plans 13-16 (Not Yet Produced)

As of 2026-08-01, only 11 revival plan files exist (01-11). Plans 13-16 are placeholders:
- **Plan 13:** (reserved for pipeline integration)
- **Plan 14:** (reserved for submission packaging)
- **Plan 15:** (reserved for ablation studies)
- **Plan 16:** (reserved for final report)

This plan should be cross-referenced by any future integration plan as the authoritative source for the ConvNeXt-Tiny activity revert to 0.394.

---

## 9. Summary Checklist

- [ ] External drive mounted and accessible
- [ ] Checkpoint copied: `v4_e0_b200.pth` (244 MB) -> swarm-bot repo
- [ ] evaluate.py copied: 6966 lines -> `src/evaluation/evaluate.py`
- [ ] model.py, losses.py, config.py, industreal_dataset.py, head_pose_geo.py accessible
- [ ] 500-frame smoke eval produces activity.top1_raw = 0.394 +/- 0.005
- [ ] Pose co-verification: angular_MAE_deg = 6.15 +/- 0.1
- [ ] PSR negative control: f1_threshold_05 = 1.0
- [ ] Full-scale eval (38k frames) scheduled
- [ ] Results saved to `runs/eval/v4_fixed_repro_full.json`
- [ ] Original eval JSONs preserved unmodified

---

## 10. References

- [01_activity_revival.md](01_activity_revival.md) -- Aspirational 0.6223 plan (different architecture)
- [04_pose_refinement.md](04_pose_refinement.md) -- Pose revert to 6.15 degrees (same checkpoint)
- [06_pr_review_and_existing_fixes.md](06_pr_review_and_existing_fixes.md) -- PR inventory, dx*0.1 fix
- [07_debate_feasibility.md](07_debate_feasibility.md) -- Feasibility ranking
- [08_debate_resources.md](08_debate_resources.md) -- GPU budget, disk space
- [09_debate_code_correctness.md](09_debate_code_correctness.md) -- Code reality check
- [10_debate_historical_targets.md](10_debate_historical_targets.md) -- Target verification (Agent 4)
- [11_debate_adversarial.md](11_debate_adversarial.md) -- Final synthesis, decision gates
- `src/evaluation/full_eval_inprocess.py` -- In-repo eval script (711 lines)
- `src/runs/rf_stages/checkpoints/SOTA_STATUS.md` -- Current SOTA status
- `/media/.../runs/eval/v4_fixed_v3.34.json` -- Primary eval source
- `/media/.../runs/eval/final_v4_fixed_v4_e0_b200.json` -- Secondary eval source
