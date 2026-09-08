# Plan A: Reach Realistic Max with Current Architecture

**Date:** 2026-08-01
**Agent:** Agent 1 (Realistic Max Plan)
**Mission:** Build a concrete, executable plan to reach the REALISTIC MAXIMUM with the CURRENT ARCHITECTURE (MViTv2-S, 9-channel input, no new architecture needed).
**Priorities:** ACT > PSR > DET > Pose
**Constraint:** DO NOT make any code changes. This document is the plan only.
**Output:** This file only.

---

## 1. Current State Recap

### 1.1 Architecture

Both proven checkpoints use the **same MViTv2-S backbone** (file 17's definitive torch.load() inspection):

| Property | v4_fixed (`v4_e0_b200.pth`) | v3.41_safe (`phase2_e3_b0.pth`) |
|----------|------------------------------|----------------------------------|
| Backbone | MViTv2-S (393 keys) | MViTv2-S (393 keys) |
| conv_proj | `[96, 9, 3, 7, 7]` | `[96, 9, 3, 7, 7]` |
| Input | 9-channel (RGB+VL+StereoL+StereoR+Depth), 16-frame clips | Same |
| FPN | 32 keys, 256-channel | Same |
| Shared keys (identical names + shapes) | 544 | 544 |
| **Proven metrics** | act=0.394, pose=6.15 deg | psr=0.883, det=0.214 |

**The architecture is MViTv2-S with 9-channel input.** The ConvNeXt-Tiny claim in files 12, 14, 18-21 is incorrect. Weight merging via surgical transplant is architecturally viable.

### 1.2 Current Unified Model State (as reported by user)

| Task | Current Value | Target | Gap |
|------|--------------|--------|-----|
| **PSR (transition F1)** | 0.7999 | 0.883 | -0.083 |
| **Activity (top-1)** | 0.42% raw, 0.90% grouped | 0.20-0.30 (realistic), 0.394 (best-ever) | ~99% collapse |
| **Detection (mAP50)** | 0 matching keys | 0.21-0.30 | Architecture mismatch |
| **Pose (angular MAE)** | 11.75 degrees | 6.15-8.00 degrees | +3.75 to +5.60 degrees |

The current model appears to be a surgical transplant: v3.41_safe base + v4_fixed act_head + pose_head, following file 17's Strategy 4 Option A.

### 1.3 What "Realistic Max" Means

Based on file 26's synthesis, the realistic unified model performance ranges:

| Metric | Conservative | Expected | Optimistic | Best-Ever (Separate) |
|--------|-------------|----------|------------|----------------------|
| act top-1 | 0.28 | 0.34 | 0.38 | 0.394 (v4_fixed) |
| det mAP50 | 0.10 | 0.18 | 0.22 | 0.214 (v3.41_safe) |
| pose deg | 8.0 | 6.8 | 6.3 | 6.15 (v4_fixed) |
| psr f1 | 0.72 | 0.82 | 0.87 | 0.883 (v3.41_safe) |

**"Realistic Max" = reaching the Optimistic column for all 4 tasks.** This is ambitious but architecturally possible on MViTv2-S because:
1. The architecture is proven for all 4 tasks individually.
2. Weight sharing works (544 shared keys).
3. Progressive joint training has high probability of preserving individual-head quality.

---

## 2. PSR: 0.7999 to 0.883 Plan

### 2.1 Current Status

PSR at 0.7999 means it is running on Path A with 11 binary heads + MonotonicDecoder from v3.41_safe. The 0.083 gap to 0.883 has three likely causes:

1. **F1=1.0 bug still active**: 3 locations return F1=1.0 when both GT and pred have zero transitions. After fixing, the honest F1 for dead components drops to 0.0, lowering macro average by up to 0.05-0.09 (file 26 risk assessment: 80% probability).
2. **Kendall log_var suppression**: If KENDALL_FIXED_WEIGHTS is not set, the Kendall uncertainty weighting suppresses PSR loss (log_var learns to reduce the weight of high-magnitude PSR loss relative to lower-magnitude losses).
3. **Dead components (comp4, comp7, comp8, comp9)**: Even in v3.41_safe on MViTv2-S, these 4 of 11 components are dead at F1=0.0. Their prevalence may be near-zero in the 2000-frame eval subset.

### 2.2 Fix 1: F1=1.0 Bug (0 GPU, ~1 hour)

Three locations to fix:

**Location 1:** `psr_transition.py` lines 382-386 (`compute_transition_f1`):
```python
# Current (bug): total_f1 = 1.0 when all_tp==0 and all_fp==0 and all_fn==0
# Fix: total_f1 = 0.0
```

**Location 2:** `psr_transition.py` line 347 (per-component edge case):
```python
# Current (bug): comp_f1s[c] = 1.0
# Fix: comp_f1s[c] = 0.0
```

**Location 3:** `evaluate.py` line 1269 (`_event_f1`):
```python
# Current (bug): return 1.0 when not pred_tr.any() and not gt_tr.any()
# Fix: return 0.0
```

**Location 4:** `evaluate.py` lines 1412-1417 (`_decode_24class_psr_transitions`):
```python
# Current (bug): f1s.append(1.0), poss.append(1.0), edits.append(1.0)
# Fix: f1s.append(0.0), poss.append(0.0), edits.append(0.0)
```

**Expected effect:** Honest F1 drops 0.05-0.09 from 0.883, so real PSR may be ~0.79-0.83. The current 0.7999 may ALREADY be the honest number. If so, the gap is architectural, not bug-driven.

### 2.3 Fix 2: KENDALL_FIXED_WEIGHTS (Code flip, ~30 min)

Set `KENDALL_FIXED_WEIGHTS=True` in config or remove the log_var scaling in the loss computation. This prevents Kendall uncertainty from suppressing PSR loss:

```python
# When KENDALL_FIXED_WEIGHTS is True, task weights are fixed:
L_psr_weighted = PSR_WEIGHT * L_psr_raw  # instead of exp(-log_var_psr) * L_psr_raw + log_var_psr
```

**Expected effect:** PSR F1 +0.03 to +0.07 if log_var suppression was the cause. This is an ablation; the primary fix is architecture.

### 2.4 Fix 3: Resurrect Dead Components (Training, ~40 GPU-hours)

Components 4, 7, 8, 9 are dead even on v3.41_safe (F1=0.0). Two possible causes:

**Cause A: Zero prevalence in eval subset.** These components occur only in specific recordings not included in the 2000-frame eval sample. Mitigation: run eval on full 38k-frame dataset to check if they have any signal.

**Cause B: Architectural inability.** These components require features the backbone cannot produce. Mitigation:

1. **Per-component alpha boosting**: Increase focal loss alpha for dead components. Instead of computing alpha from prevalence, set alpha=2.0 for comp4/7/8/9 and alpha=0.5 for others.
2. **Selective head unfreezing**: Freeze all heads except comp4/7/8/9 component heads. Fine-tune only those 4 binary classifiers for 10 epochs at LR=1e-4.
3. **Data resampling**: Ensure training batches include frames where these components are active. If prevalence is <1%, use class-balanced sampling for PSR frames.

**Expected effect:** If Cause A (eval subset): +0.03-0.05 F1. If Cause B (architectural): +0.00-0.02 at best. Dead components may be genuinely dead.

### 2.5 PSR Training Configuration

If retraining is needed:

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| USE_PSR_PATH_A | True | 11-binary head (proven) |
| PSR_WEIGHT | 10.0 | Amplify PSR loss |
| Focal gamma | 2.0 | Standard focal |
| Per-component alpha | Prevalence-based, boosted for dead components | Address imbalance |
| Freeze strategy | Backbone + FPN frozen for first 5 epochs, then unfreeze FPN, then unfreeze all | Graduated unfreezing |
| Learning rate | 1e-4 with cosine to 1e-5 | Conservative for fine-tuning |
| Effective batch | 32 (batch_size=2, grad_accum=16) | RTX 3060 limit |
| Epochs | 15-25 | Sufficient for fine-tuning |
| PSR_TRANSITION flag | Verify enabled | Transition F1 vs per-frame F1 |

**Expected outcome:** PSR F1 = 0.83-0.87 after retraining. The 0.883 ceiling may be the theoretical maximum on this data distribution with 4 dead components.

### 2.6 PSR Decision Gates

| Gate | Condition | Action on Fail |
|------|-----------|----------------|
| G_PSR_1: Bug fix effect | F1 drops <0.10 after fixing F1=1.0 bug | Accept honest number as new baseline |
| G_PSR_2: Dead component check | comp4/7/8/9 have any signal on full 38k eval | If yes: eval subset issue. If no: architectural ceiling. |
| G_PSR_3: Retraining target | psr_f1 >= 0.83 after retraining | If <0.83: accept ceiling, document honestly. |

---

## 3. Activity: 0.42% to 0.20-0.30 Plan

### 3.1 Current Status

Activity at 0.42% raw / 0.90% grouped is effectively dead. This is a 99%+ collapse from the proven 0.394 on v4_fixed. The act_head from v4_fixed was transplanted onto the v3.41_safe backbone, but the feature distribution at the FPN output has shifted.

**Root cause:** Feature distribution shift between the v4_fixed backbone (epoch 0, batch 200) and the v3.41_safe backbone (phase 2, epoch 3). The act_head was trained to expect features from the early-training backbone; it receives different features from the later-training backbone.

### 3.2 Fix: Progressive Activity Head Fine-Tuning (~30 GPU-hours)

The activity head architecture is a simple MLP (8 keys: Linear->LayerNorm->Dropout->ReLU->Linear). It should adapt quickly with targeted fine-tuning.

**Step 1: Verify dataset label mapping (0 GPU, ~2 hours)**

The activity classification has 75 classes with a known off-by-one risk. Verify:
- The label mapping used by the current data loader matches what v4_fixed was trained with.
- No remapping (tau=1.0 in original eval, raw logits directly to class index).
- 75 output classes in the classifier head (check `act_head.fc2.weight` shape: should be `[75, 512]`).

**Step 2: Freeze backbone + FPN + PSR + pose + det, fine-tune act_head only (~10 GPU-hours)**

```
Phase 2a (epochs 1-10):
  Frozen: Backbone (393 keys), FPN (32 keys), PSR head, pose_head, det_head
  Training: act_head (8 keys) only
  Loss: Cross-entropy over 75 classes
  LR: 3e-4 with cosine to 3e-5
  Effective batch: 32
```

**Expected:** Activity should recover to 0.15-0.25 after head-only fine-tuning. The 8-key MLP head is small and should adapt quickly.

**Step 3: Class-Balanced Loss for Long-Tail Classes (~10 GPU-hours)**

The 75 activity classes have a severe long-tail distribution. If the majority of classes have zero signal (similar to ConvNeXt linear probe showing 41 dead classes):

```
Phase 2b (epochs 11-20):
  Frozen: Backbone + FPN + PSR head + pose_head + det_head
  Training: act_head (8 keys) only
  Loss: Class-balanced focal loss (gamma=1.0, beta=0.9999 for effective number)
       OR LDAM-DRW (Label-Distribution-Aware Margin loss with Deferred Re-weighting)
  LR: 1e-4 with cosine to 1e-5
```

**Expected:** Activity reaches 0.25-0.30 after class-balanced fine-tuning. The 0.394 ceiling from v4_fixed may not be reachable because the backbone features have shifted from PSR+det training.

**Step 4: Joint fine-tuning with low weight (~10 GPU-hours)**

```
Phase 2c (epochs 21-30):
  Frozen: Backbone (keep stable for other tasks)
  Training: act_head + FPN (unfreeze FPN to adapt feature distribution)
  Loss: Cross-entropy with class-balanced re-weighting
  LR: 5e-5 with cosine to 5e-6
```

**Expected:** Activity reaches 0.30-0.35. The FPN adaptation allows act-relevant features to emerge at the head input.

### 3.3 Activity Fallback Options

If activity stays below 0.15 after Phase 2a:
1. **HeadPoseFiLM check**: The pose column fix (04_pose_refinement.md) changes FiLM conditioning inputs to shared C5 features. This may contaminate activity features. Temporarily disable FiLM for activity, evaluate.
2. **Head fusion**: Run BOTH v4_fixed act_head AND v3.41 act_head at inference, ensemble their outputs. This guarantees the v4_fixed head's knowledge is preserved.
3. **Separate eval**: If all else fails, evaluate activity separately using the v4_fixed checkpoint directly. Accept that activity metrics come from a different training stage.

### 3.4 Activity Decision Gates

| Gate | Condition | Action on Fail |
|------|-----------|----------------|
| G_ACT_1: Label mapping | 75-class output confirmed, tau=1.0 | If wrong: fix mapping, re-eval |
| G_ACT_2: Head-only fine-tune | act >= 0.15 after 10 epochs | If <0.15: distribution shift too severe, try head fusion |
| G_ACT_3: Class-balanced fine-tune | act >= 0.25 after 20 epochs | If <0.25: accept 0.15-0.25 as realistic max |
| G_ACT_4: Joint fine-tune | act >= 0.30 after 30 epochs | If <0.30: accept best result, document honestly |

---

## 4. Detection: 0% to 0.21-0.30 Plan

### 4.1 Current Status

Detection has **0 matching keys** between the current model's detection head and the proven detection head from v3.41_safe (which achieves 0.214 mAP50). This is because:

1. The current model uses v4_fixed's detection head (103 keys, simpler architecture with fewer FPN scales).
2. v3.41_safe's detection head (137 keys, one additional FPN scale) is the one that achieved 0.214.
3. The 13 det_head keys from v4_fixed have a different architecture than v3.41_safe's 137 keys.

Additionally, the 0.5734 claim is a biased subsample artifact (250-batch class-balanced, only 15/24 classes present). The honest multi-task detection on MViTv2-S is 0.214 (v3.41_safe), not 0.5734 and not 0.00009 (ConvNeXt figure).

### 4.2 Primary Plan: Surgical Detection Head Transplant (~5 GPU-hours)

Since both checkpoints use MViTv2-S, transplant the full detection head from v3.41_safe (137 keys) into the current model.

**Step 1: Verify architecture compatibility (0 GPU, ~2 hours)**

The v3.41_safe detection head has one additional FPN scale (cv2.3/cv3.3 + input_adapter_p2) compared to v4_fixed. The model class must support this architecture. Verify:
- FPN outputs P2-P5 (4 scales)
- Detection head has cv2/cv3 modules for all 4 scales
- `use_p2=True` in config

If the current model class doesn't support 4-scale FPN, this requires adding the module definition (code change -- outside this plan's scope). In that case, fall back to the secondary plan.

**Step 2: Transplant and evaluate (0 GPU, ~1 hour)**

```python
# Load current model, copy v3.41_safe det_head keys
ckpt_v3 = torch.load('phase2_e3_b0.pth')
det_keys = {k: v for k, v in ckpt_v3['model_state_dict'].items() if k.startswith('m.det_head.')}
model.load_state_dict(det_keys, strict=False)
```

**Step 3: Quick eval on 500 frames**

Expected: mAP50 = 0.18-0.21 (near v3.41_safe's 0.214, minus minor degradation from different backbone training state).

**Step 4: Fine-tune detection head only (~5 GPU-hours)**

If transplant produces mAP50 < 0.10:
- Freeze backbone + FPN + all other heads
- Fine-tune det_head only for 5-10 epochs
- Use v3.41_safe's detection training config (CIoU + focal classification)

### 4.3 Secondary Plan: Pose-Derived Detection (PDD) (~10 GPU-hours)

If direct transplant fails (architecture mismatch in model class), use the Pose-Derived Detection approach:

**Rationale:** Pose estimates the operator's head position and orientation. From head pose, we can derive a bounding box around the operator's working area. This is NOT object detection but a geometric fallback.

**Implementation:**
1. From the 9-DoF pose output `[forward(3), up(3), position(3)]`, compute a bounding box around the estimated head position.
2. Use fixed-size box (e.g., 200x200 pixels centered on head position projection).
3. Calibrate against the ground truth detection boxes to find the best fixed box size.

**Limitations:**
- PDD produces ONE box per frame (the operator's working area).
- Cannot distinguish between 24 object classes.
- Useful for "presence detection" but not classification.
- Frame as "safety region detection" rather than object detection.

**Expected mAP50:** 0.05-0.10 (weak but non-zero, demonstrates the concept).

### 4.4 Tertiary Plan: Distillation from YOLOv8m (~20 GPU-hours)

If both transplant and PDD fail, distill detection from a single-task YOLOv8m model (0.995 mAP50 single-task).

**Approach:**
1. Run YOLOv8m on the full validation set to generate pseudo-labels (boxes + classes).
2. Train the multi-task model's detection head to predict these pseudo-labels.
3. This does NOT require the multi-task model to match YOLOv8m's 0.995 -- only to produce reasonable boxes.

**Expected mAP50:** 0.10-0.15 (distilled, lower than direct transplant). The student (multi-task model) has a weaker backbone than YOLOv8m's dedicated detection architecture.

### 4.5 Detection Decision Gates

| Gate | Condition | Action on Fail |
|------|-----------|----------------|
| G_DET_1: Transplant viable | Architecture supports 4-scale FPN detection head | If no: skip to PDD or distillation |
| G_DET_2: Transplant eval | mAP50 >= 0.10 after transplant | If <0.10: fine-tune det_head only |
| G_DET_3: Detection target | mAP50 >= 0.15 after fine-tuning | If <0.15: accept as weak head, frame as multi-task cost |

### 4.6 Detection Reality Check

Detection is the weakest head in any multi-task configuration. Even v3.41_safe's 0.214 is modest compared to YOLOv8m's 0.995 single-task. The realistic max for detection in a 4-head unified model is 0.15-0.21.

**Paper framing:** "Detection achieves 0.15-0.21 mAP50 in multi-task configuration vs 0.995 single-task YOLOv8m. This 79-85% cost quantifies the gradient conflict between detection and other tasks. In contrast, ConvNeXt-Tiny multi-task detection collapses to 0.00009 -- a 99.99% cost. The backbone architecture (spatiotemporal MViTv2-S vs per-frame ConvNeXt-Tiny) is the primary determinant of multi-task detection viability."

---

## 5. Pose: 11.75 degrees to 6.15-8.00 degrees Plan

### 5.1 Current Status

Pose at 11.75 degrees is significantly worse than the 6.15-degree proven target from v4_fixed. However, the pose_head (4 keys: `fc1.weight/bias`, `fc2.weight/bias`) WAS transplanted from v4_fixed. This means:

1. The pose_head weights are correct (proven 6.15).
2. The feature distribution at the pose_head input has shifted, degrading output.
3. **OR** the 11.75 number comes from a full 38k-frame eval while 6.15 comes from a 500-frame smoke test -- the difference may be statistical.

**Architecture confirmation:** Legacy HeadPoseHead (USE_GEO_HEAD_POSE=False):
- Input: GAP over C4+C5 feature concatenation (1152-dim)
- Architecture: Linear(1152, 512) -> Linear(512, 256) -> Linear(256, 9)
- Output: 9-DoF raw [forward(3), up(3), position(3)]

### 5.2 Fix 1: Verify Eval Consistency (~2 GPU-hours)

Before concluding pose has degraded, verify the eval methodology:

**Step 1:** Run pose eval on the transplanted model with the SAME 500-frame subset used for v4_fixed's original eval. If pose returns 6.15-7.00 on 500 frames but 11.75 on full 38k, the issue is statistical (500-frame sample was easy recordings).

**Step 2:** Run pose eval on v4_fixed checkpoint with the full 38k-frame dataset. If v4_fixed's full-eval pose is 8-10 degrees (not 6.15), then the 6.15 was optimistic due to the 500-frame subset.

**Expected:** The "true" full-dataset pose for v4_fixed is likely 8-10 degrees, not 6.15. The current 11.75 represents an additional 1.75-3.75 degrees of degradation from the transplant feature shift.

### 5.3 Fix 2: Progressive Pose Head Fine-Tuning (~10 GPU-hours)

The pose head is a 3-layer MLP (4 keys). It should adapt quickly.

```
Phase 5a (epochs 1-10):
  Frozen: Backbone + FPN + act_head + PSR head + det_head
  Training: pose_head (4 keys) only
  Loss: MSE over 9-DoF raw output
  LR: 3e-4 with cosine to 3e-5
  Effective batch: 32
```

**Expected:** Pose recovers to 6.5-8.0 degrees after head-only fine-tuning.

### 5.4 Fix 3: GeometryAwareHeadPose Check (0 GPU, ~1 hour)

Verify that `USE_GEO_HEAD_POSE=False` is enforced. The GeometryAwareHeadPose has a column-ordering bug producing ~86 degree error (file 14, Section 2). If accidentally enabled, pose will be catastrophically bad -- but 11.75 is not catastrophic, so this is likely already correct.

### 5.5 Fix 4: HeadPoseFiLM Contamination Check (0 GPU, ~1 hour)

The pose column fix changes FiLM conditioning inputs. Verify:
1. FiLM parameters for pose conditioning are not interfering with backbone features.
2. Run pose eval with FiLM temporarily disabled for pose-related conditioning.
3. If pose improves when FiLM is disabled, the FiLM contamination hypothesis is confirmed.

Mitigation if confirmed: Retrain FiLM parameters only (small number of params, ~5 epochs).

### 5.6 Pose Decision Gates

| Gate | Condition | Action on Fail |
|------|-----------|----------------|
| G_POSE_1: Eval consistency | 500-frame pose matches 6.15 +/- 1.0 deg | If yes: 11.75 is full-dataset reality, not degradation |
| G_POSE_2: Head fine-tune | pose <= 8.0 after 10 epochs | If >8.0: distribution shift too severe, retrain pose_head from scratch |
| G_POSE_3: FiLM check | FiLM contamination ruled out | If confirmed: retrain FiLM parameters |
| G_POSE_4: Final pose | pose <= 8.0 degrees | If >8.0: accept best result. 8-10 degrees is realistic for multi-task. |

---

## 6. Integrated Training Plan

### 6.1 Sequential Execution Order (Priority: ACT > PSR > DET > Pose)

Tasks are executed sequentially because they share the same GPU and the fixes build on each other.

| Phase | Days | GPU Hours | What | Freeze | Train |
|-------|------|-----------|------|--------|-------|
| **0: Verification** | 0-1 | 4 hr | Full re-eval of current model on 38k frames. Fix F1=1.0 bug. Verify label mappings. | -- | -- |
| **1: Activity** | 2-3 | 30 hr | act_head fine-tuning (Phases 2a-2c) | Backbone, FPN, PSR, det, pose | act_head + FPN (later) |
| **2: PSR** | 4-6 | 40 hr | PSR retraining with KENDALL_FIXED_WEIGHTS, dead component boosting | Backbone, act, det, pose | PSR head |
| **3: Detection** | 6-7 | 5-20 hr | det_head transplant or fine-tune | Backbone, FPN, act, PSR, pose | det_head |
| **4: Pose** | 8-9 | 12 hr | pose_head fine-tuning | Backbone, FPN, act, PSR, det | pose_head |
| **5: Joint Fine-Tuning** | 10-13 | 60 hr | Full model with Kendall weighting | -- | All parameters |
| **6: Final Evaluation** | 14 | 4 hr | Full 38k-frame eval, all metrics | -- | -- |
| **7: Buffer** | 15-17 | 20 hr | Retries, ablations, paper prep | -- | -- |
| **Total** | **17 days** | **~175 GPU-hours** | | | |

### 6.2 Why Sequential, Not Parallel

- Single RTX 3060 (12 GB) for training. Cannot run multiple training jobs simultaneously.
- Each fix builds on the previous: activity head must work before joint fine-tuning; PSR head must work before detection can be added.
- Phase 0 verification must complete before any training starts to establish honest baselines.
- Eval can run in parallel on CPU while GPU trains (threshold sweeps, per-recording breakdowns).

### 6.3 Full Model Joint Fine-Tuning (Phase 5)

After all 4 heads are independently working:

```
Phase 5 (epochs 1-20):
  Frozen: Nothing (full model unfrozen)
  Loss: Kendall homoscedastic uncertainty weighting:
    L_total = sum(exp(-log_var_i) * L_i + log_var_i for i in [act, det, pose, psr])
  LR: 5e-5 with cosine to 5e-6 (low, conservative)
  Effective batch: 32
  Mixed precision: AMP (autocast + GradScaler)

  Monitoring per epoch:
    - All 4 head metrics (act top-1, det mAP50, pose MAE, psr F1)
    - Log_var values (should converge to stable values)
    - Per-task loss magnitudes (watch for one task dominating)
    - Gradient norms per head (watch for gradient conflict)
```

**Alert thresholds:**
- Any head metric drops >10% from pre-joint baseline: increase that head's loss weight
- log_var for any task exceeds 5.0: that task is being suppressed, fix weight
- Gradient norm ratio between max and min head > 100: gradient conflict, consider Gradient Surgery (PCGrad)

---

## 7. Timeline and Resources

### 7.1 Wall Clock Schedule

| Date | Day | Phase | Milestone |
|------|-----|-------|-----------|
| Aug 1-2 | 0-1 | 0: Verification | Baselines established, bugs fixed |
| Aug 2-5 | 2-4 | 1: Activity | act >= 0.25 gate passed |
| Aug 5-8 | 5-7 | 2: PSR | psr >= 0.83 gate passed |
| Aug 8-9 | 7-8 | 3: Detection | det >= 0.15 gate passed |
| Aug 9-11 | 8-10 | 4: Pose | pose <= 8.0 gate passed |
| Aug 11-16 | 10-15 | 5: Joint Fine-Tuning | All heads stable |
| Aug 16-17 | 15-16 | 6: Final Evaluation | All metrics reported |
| Aug 17-20 | 16-19 | 7: Buffer + Paper | Ablations, retries |
| **Aug 22** | **21** | **FREEZE** | **Paper submission deadline** |

**Buffer:** 2-3 days before Aug 22 freeze. One full retry cycle possible if a gate fails.

### 7.2 GPU Resources

| Resource | Specification | Usage |
|----------|--------------|-------|
| Primary GPU | RTX 3060 (12 GB) | Training (175 hours) |
| Secondary GPU | RTX 5060 Ti (16 GB) | Available for parallel eval, not required |
| CPU | Any | Eval threshold sweeps, log analysis |

### 7.3 Disk Resources

| Item | Size | Notes |
|------|------|-------|
| Checkpoints (40 epochs) | ~28 GB | ~700 MB each with optimizer state |
| Eval cache | ~30 GB | Feature caching for threshold sweeps |
| Logs + metrics | ~2 GB | TensorBoard, JSON evals |
| Code artifacts | ~1 GB | evaluate.py, model.py copies |
| **Total required** | **~60 GB** | |
| **Currently free** | ~138 GB | Adequate |

### 7.4 Risk-Adjusted Timeline

| Risk | Probability | Impact on Timeline | Mitigated Duration |
|------|-----------|-------------------|-------------------|
| Activity fine-tuning needs backbone unfreeze | 30% | +3 days | 20 days total |
| PSR dead components cannot be resurrected | 50% | 0 days (accept ceiling) | No change |
| Detection transplant fails, need PDD/distillation | 40% | +3 days | 20 days total |
| Joint fine-tuning causes catastrophic forgetting | 25% | -6 days (skip Phase 5, use per-head best) | 11 days total |
| Disk full or OOM | 15% | +1 day | Checkpoint thinning |
| **Expected duration** | | | **14-20 days** |

---

## 8. Expected Final Metrics

### 8.1 Realistic Outcome (Gate-Passing Scenario)

| Task | Current | After Phase | Joint Fine-Tuning | Best-Ever |
|------|---------|-------------|-------------------|-----------|
| Activity (top-1) | 0.0042 | 0.28-0.32 | 0.30-0.35 | 0.394 |
| PSR (transition F1) | 0.7999 | 0.83-0.85 | 0.82-0.87 | 0.883 |
| Detection (mAP50) | 0.00 | 0.15-0.18 | 0.15-0.21 | 0.214 |
| Pose (angular MAE deg) | 11.75 | 7.0-8.0 | 6.5-7.5 | 6.15 |

### 8.2 What CANNOT Be Reached (Hard Ceilings)

| Ceiling | Reason |
|---------|--------|
| Activity = 0.394 | Requires v4_fixed backbone (epoch 0, batch 200). v3.41 backbone has different features. Best realistic: 0.30-0.35. |
| PSR = 0.883 | v3.41_safe eval was on 2000-frame subset. Full-dataset F1 is lower (0.82-0.85 cross-eval delta). Plus 4 dead components (comp4/7/8/9). Best realistic: 0.82-0.87. |
| Detection = 0.5734 | Number is fraudulent (biased 250-batch subsample). Honest target is v3.41_safe's 0.214. Best realistic: 0.15-0.21. |
| Pose = 6.15 | 500-frame smoke test number. Full-dataset pose for v4_fixed is likely 7-9 degrees. Plus transplant shift. Best realistic: 6.5-8.0. |

### 8.3 The ONE Number to Withdraw Immediately

**det_mAP50_pc = 0.5734** must be formally withdrawn. It is a biased 250-batch class-balanced subsample artifact with only 15 of 24 classes present (file 13). The true multi-task detection mAP50 on MViTv2-S ranges from 0.10 to 0.214. Any paper or claim including 0.5734 is factually incorrect.

---

## 9. Cross-References to Debate Files 28-31

### 9.1 Status of Files 28-31

As of 2026-08-01, debate files 28, 29, 30, and 31 do NOT exist in the `a_revival_plan/` directory. They are referenced in the task instructions as "Context -- read these first" but appear to be placeholder/still-being-written files.

### 9.2 Anticipated Cross-References

When files 28-31 are written, they should address:

**File 28 (likely: cross-task gradient analysis):**
- This plan assumes Kendall uncertainty weighting prevents gradient conflict. If file 28 shows that gradient surgery (PCGrad/GradNorm) is superior, Phase 5 should use that instead.
- Activity gradient conflict with PSR is the primary risk. File 28 should quantify the cosine similarity between act_head and PSR head gradients.

**File 29 (likely: per-component PSR diagnosis):**
- This plan's PSR section assumes comp4/7/8/9 are dead due to prevalence or architecture. File 29 should provide definitive diagnosis.
- If file 29 shows that a specific architectural fix (not just retraining) resurrects them, the PSR plan should incorporate that fix.

**File 30 (likely: detection architecture comparison):**
- This plan proposes surgical transplant of v3.41_safe's detection head. File 30 should compare the 103-key vs 137-key detection architectures in detail.
- If file 30 shows that the 4-scale FPN (P2-P5) is necessary and the current model doesn't support it, the secondary PDD/distillation plan becomes primary.

**File 31 (likely: final integration and paper strategy):**
- This plan's timeline targets Aug 22 freeze. File 31 should define the paper submission strategy and which metrics to report.
- If file 31 recommends a specific paper narrative (e.g., "multi-task cost as contribution"), this plan's monitoring and reporting should align with it.

### 9.3 How This Plan Adapts

This plan is designed to be modular. Each task's section (PSR, Activity, Detection, Pose) is self-contained and can be updated when files 28-31 provide new information. The gate structure allows any section to be replaced or modified without affecting others.

---

## 10. Rollback and Fallback Plan

### 10.1 Tiered Strategy

**Tier 1: All gates pass (40-50% probability)**
- Execute full plan. Accept metrics in the realistic range (Section 8.1).
- Paper contribution: "First 4-task MViTv2-S unified model for industrial assembly understanding."

**Tier 2: 3 of 4 heads succeed (30-40% probability)**
- Detection is the most likely to fail. Accept detection at 0.05-0.10 from PDD.
- Paper contribution: "Three-task model with PDD as safety-region detection."

**Tier 3: 2 of 4 heads succeed (15-20% probability)**
- Activity + PSR succeed, detection and pose partially work.
- Fall back to file 26's Tier 2: publish per-head bests, acknowledge multi-task cost.

**Tier 4: Complete failure (<5% probability)**
- File 26's Tier 4: "Transparent Pathology" paper.
- Two-column architecture comparison (ConvNeXt-Tiny vs MViTv2-S).
- Detection hierarchy: 0.995 (single-task) -> 0.214 (multi-task MViTv2-S) -> 0.00009 (multi-task ConvNeXt-Tiny).
- This is genuinely publishable as an architectural finding.

### 10.2 Abort Criteria

Training is aborted for a task if:
1. Metric doesn't improve for 5 consecutive epochs despite LR adjustments.
2. Training loss diverges (NaN or exponential growth).
3. Two consecutive gates fail for the same task.

**Failed tasks are NOT retried endlessly.** The time budget is fixed. If a task fails, accept the best-so-far metric and move to the next task.

### 10.3 Checkpoint Preservation

Before any training:
- SHA256 all current checkpoints (v4_e0_b200.pth, phase2_e3_b0.pth, current unified model).
- Copy to `/home/newadmin/swarm-bot/checkpoints/` as backup.
- Copy evaluate.py, model.py, losses.py, config.py from external drive.

---

## 11. Action Items (Ordered by Priority)

### Immediate (Today, No GPU)

1. [ ] Fix F1=1.0 bug in all 4 locations (psr_transition.py x2, evaluate.py x2). ~1 hour.
2. [ ] Set KENDALL_FIXED_WEIGHTS=True in config. ~5 min.
3. [ ] Verify activity label mapping: 75 classes, tau=1.0, no remapping. ~1 hour.
4. [ ] Verify USE_GEO_HEAD_POSE=False. ~5 min.
5. [ ] Copy evaluate.py, model.py, losses.py from external drive. ~30 min.
6. [ ] Free disk space by thinning old checkpoints. ~30 min.
7. [ ] SHA256 all critical checkpoints. ~10 min.

### Phase 0 (Day 0-1, 4 GPU-hours)

8. [ ] Full re-evaluation of current unified model on 38k-frame validation set. ~2 hours.
9. [ ] Full re-evaluation of v4_fixed checkpoint on 38k-frame validation set (establish honest full-dataset baselines). ~2 hours.
10. [ ] Run PSR eval with F1=1.0 bug fixed to get honest PSR baseline. ~30 min.
11. [ ] Run pose eval on 500-frame subset for direct comparison with v4_fixed's 6.15. ~30 min.

### Phase 1: Activity (Day 2-4, 30 GPU-hours)

12. [ ] Fine-tune act_head only (10 epochs, backbone frozen). Monitor G_ACT_2.
13. [ ] Class-balanced loss fine-tune (10 epochs). Monitor G_ACT_3.
14. [ ] Joint act_head + FPN fine-tune (10 epochs). Monitor G_ACT_4.

### Phase 2: PSR (Day 5-7, 40 GPU-hours)

15. [ ] Run PSR on full 38k-frame dataset to check dead components.
16. [ ] Boost per-component alpha for comp4/7/8/9.
17. [ ] Fine-tune PSR head (15-25 epochs with graduated unfreezing). Monitor G_PSR_3.

### Phase 3: Detection (Day 7-8, 5-20 GPU-hours)

18. [ ] Verify 4-scale FPN architecture support. Monitor G_DET_1.
19. [ ] Transplant v3.41_safe det_head or fine-tune. Monitor G_DET_2, G_DET_3.

### Phase 4: Pose (Day 9-10, 12 GPU-hours)

20. [ ] Run 500-frame pose eval for consistency check. Monitor G_POSE_1.
21. [ ] Fine-tune pose_head only. Monitor G_POSE_2.
22. [ ] FiLM contamination check. Monitor G_POSE_3.

### Phase 5: Joint Fine-Tuning (Day 10-15, 60 GPU-hours)

23. [ ] Full model unfreeze with Kendall weighting.
24. [ ] Monitor all 4 head metrics per epoch.
25. [ ] Alert if any head degrades >10%.

### Phase 6: Final Evaluation (Day 16, 4 GPU-hours)

26. [ ] Full 38k-frame eval with all bug fixes applied.
27. [ ] Per-component PSR threshold sweep.
28. [ ] Per-class activity accuracy breakdown.
29. [ ] Per-class detection AP breakdown.

### Phase 7: Buffer (Day 17-20)

30. [ ] Retry failed gates if time permits.
31. [ ] Prepare paper metrics table.
32. [ ] SHA256 final checkpoint.

---

## 12. Key References

| File | Content | Key Takeaway |
|------|---------|--------------|
| [17_unified_model_weight_merging.md](17_unified_model_weight_merging.md) | Checkpoint inspection proving both use MViTv2-S | 544 shared keys, weight merging viable |
| [26_deep_search_final_synthesis.md](26_deep_search_final_synthesis.md) | Architecture synthesis resolving ConvNeXt vs MViTv2 contradiction | MViTv2-S is the only viable backbone |
| [12_revert_act_0.394.md](12_revert_act_0.394.md) | Activity target verification | 0.394 from v4_fixed, 500-frame eval |
| [14_revert_pose_6.15.md](14_revert_pose_6.15.md) | Pose target verification | 6.15 degrees from v4_fixed, Legacy HeadPoseHead |
| [15_revert_psr_0.883.md](15_revert_psr_0.883.md) | PSR target verification | 0.883 from v3.41_safe, 4 dead components |
| [13_revert_det_0.5734.md](13_revert_det_0.5734.md) | Detection artifact exposure | 0.5734 withdrawn as biased subsample |
| [11_debate_adversarial.md](11_debate_adversarial.md) | Adversarial synthesis | Decision gates G1-G8, HeadPoseFiLM risk |
| [21_unified_model_final_synthesis.md](21_unified_model_final_synthesis.md) | Prior unified model plan | Outdated (assumed ConvNeXt-Tiny) but training schedule is useful |
| feedback_sota_history.md | Authoritative SOTA metrics | psr=0.883, act=0.394, pose=6.15, det=0.214 (all verified) |

---

**Agent 1 (Realistic Max Plan) signing off.** The architecture is proven (MViTv2-S, 9-channel, 544 shared keys). The path is surgical transplant + progressive fine-tuning with hard gates. Execute Phase 0 today to establish honest baselines.
