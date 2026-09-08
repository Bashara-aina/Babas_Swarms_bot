# Plan D: Final Unified Training -- MViTv2-S 4-Head Model

**Date:** 2026-08-01
**Role:** Agent 4 (Final Unified Training)
**Mission:** Train ONE MViTv2-S model from surgical transplant checkpoint to simultaneously achieve: PSR >= 0.75, ACT >= 0.30, DET >= 0.10, POSE <= 8.0 degrees.
**Constraint:** Plan document only. No code changes.
**Inputs:** Files 05 (integration synthesis), 12-16 (revert plans), 17 (weight merging), 23 (MTL architectures), 24 (long-tail training), 25 (9-channel backbones), 26 (final synthesis).

---

## 0. Executive Summary

**The core contradiction across the debate corpus is resolved.** File 17's `torch.load()` inspection proved both deployable checkpoints (v4_fixed at 233 MB and v3.41_safe at 664 MB) use the **same MViTv2-S backbone with 9-channel input** (`conv_proj` shape `[96, 9, 3, 7, 7]` in both, 544 shared state dict keys with identical shapes). Files 18-21 claiming ConvNeXt-Tiny for v4_fixed contain errata. Weight merging is architecturally viable. A single unified model is achievable.

**Strategy:** Surgical head transplant from v4_fixed (act=0.394, pose=6.15 deg) into v3.41_safe (psr=0.883, det=0.214) as base, followed by progressive joint fine-tuning with Kendall homoscedastic uncertainty weighting and PCGrad gradient conflict resolution.

**Realistic targets (12-day training campaign):**

| Head | Aspirational Target | Realistic Range | Proven Ceiling | Risk |
|------|-------------------|-----------------|----------------|------|
| PSR | 0.88 | **0.75 -- 0.85** | 0.883 (v3.41) | 4 dead components; multi-task interference may degrade |
| Activity | 0.30 | **0.28 -- 0.35** | 0.394 (v4_fixed, 500-frame) | Full 38k-frame may be lower; multi-task competition |
| Detection | 0.30 | **0.10 -- 0.20** | 0.214 (v3.41, honest full-eval) | 0.5734 withdrawn as biased subsample artifact; 0.30 is aspirational |
| Pose | 8.0 deg | **6.5 -- 7.5 deg** | 6.15 (v4_fixed, 500-frame) | Legacy HeadPoseHead is stable; multi-task may add 0.5-1.5 deg |

**The aspirational PSR=0.88 and DET=0.30 exceed the proven ceilings of the best individual checkpoints (0.883 and 0.214 respectively).** The training plan below describes the procedure to maximize all heads simultaneously, but the realistic ranges reflect what the evidence supports.

---

## 1. Architecture Decision

### 1.1 Backbone: MViTv2-S (Confirmed, Not Debated)

**Decision:** MViTv2-S (34.3M backbone parameters), 9-channel input, 16-frame 3D spatiotemporal clips.

**Proof:** Direct `torch.load()` inspection of BOTH checkpoints (File 17):

| Property | v4_fixed | v3.41_safe |
|----------|----------|------------|
| File size | 233 MB | 664 MB |
| Total keys | 639 | 578 |
| Backbone keys | 393 (MViTv2-S) | 393 (MViTv2-S) |
| conv_proj weight | `[96, 9, 3, 7, 7]` | `[96, 9, 3, 7, 7]` |
| Input channels | 9 | 9 |
| Shared key names + shapes | 544 | 544 |

**9-channel composition:** RGB(ch0-2) + VL(ch3) + StereoL(ch4-5) + Depth(ch6-8). The convolution projection layer was expanded from 3->9 channels (center-frame inflation for RGB pretrained weights, zero-init for extra 6 channels).

**Pretrained weights source:** `~/.cache/torch/hub/checkpoints/mvit_v2_s-ae3be167.pth` (torchvision, Kinetics-400 pretrained).

### 1.2 Why Not Alternatives

| Alternative | Rejection Reason |
|-------------|-----------------|
| ConvNeXt-Tiny | Linear probe: zero above-baseline activity signal (0.2169 < 0.2217). Detection collapses to 0.00009. PSR never exceeded 0.10. At most 2 of 4 tasks work. |
| MViTv2-S with 3-channel | Requires retraining conv_proj from scratch. Loses proven weights. 10+ days additional training. |
| MViTv2-B (52M) | Upgrade candidate but unproven. v3.41_safe was trained on MViTv2-S. Changing backbone resets all training progress. Defer to post-freeze. |
| Two separate models | Honest fallback but abandons the "one model" mandate. Only if Phase C/D training fails gate checks. |
| Training from scratch | 50 epochs at ~3hr/epoch. No guarantee all heads converge. Historical multi-task collapse happened during co-training. Surgical transplant starts from proven checkpoints. |

### 1.3 Head Architecture Specification

**Activity Head** (8 keys, transplanted from v4_fixed):
```
Input: FPN P5 features (768-dim)
Architecture: Linear(768, 512) -> LayerNorm -> Dropout -> ReLU -> Linear(512, 75)
Output: 75-class frame-level verb classification
Proven: 0.394 top-1 on v4_fixed (500-frame subsample)
```

**Pose Head** (4 keys, transplanted from v4_fixed, Legacy HeadPoseHead):
```
Input: GAP over C4(384ch) + C5(768ch) -> concat[1152]
Architecture: Linear(1152, 512) -> Linear(512, 256) -> Linear(256, 9)
Output: 9-DoF raw [forward_x, forward_y, forward_z, up_x, up_y, up_z, pos_x, pos_y, pos_z]
Proven: 6.15 deg forward_angular_MAE on v4_fixed (500-frame subsample)
CRITICAL: USE_GEO_HEAD_POSE=False -- GeometryAwareHeadPose has column-ordering bug (~86 deg error)
Note: No _init_weights method. Default PyTorch init (Xavier uniform) used. DO NOT add custom init.
```

**PSR Head** (Path A, from v3.41_safe base):
```
Base: Linear(768, 256) -> GRU(256) -> Linear(256, 11)
Predictor: 3-layer causal transformer (d_model=256, 4 heads, dim_feedforward=1024)
Heads: 11 per-component binary sigmoid heads (Linear(256, 64) -> SiLU -> Linear(64, 1))
Decoder: MonotonicDecoder with Q48 hysteresis (sustain_hi/sustain_lo)
Loss: Per-component focal BCE (gamma=2.0), class-specific alpha from training set prevalence
Proven: 0.883 F1 on v3.41_safe (canonical eval, 2000 frames)
Known issue: 4 of 11 components dead at F1=0.0 (comp4, comp7, comp8, comp9)
```

**Detection Head** (RetinaNet-style, from v3.41_safe base):
```
Neck: FPN (256ch, P2-P5/P3-P7)
Head: RetinaNet-style multi-scale detection
Anchors: 9 per spatial location x 24 object classes
Subnet: 4x Conv3x3(256) + batch_norm + ReLU for classification and box regression
Proven: 0.214 mAP50 on v3.41_safe (full eval, not subsample)
WITHDRAWN: 0.5734 mAP50_pc (biased 250-batch class-balanced subsample artifact, n_present=15)
```

### 1.4 Weight Transplant Map

From v4_fixed (source) into v3.41_safe (base), key prefix mapping verified by File 17:

```
Source (v4_fixed)                    Destination (v3.41_safe)
act_head.*                           act_head.*            (8 keys, identical names)
head_pose_head.* / pose_head.*       pose_head.*           (4 keys, verified matching)
backbone.*                           backbone.*            (393 keys, shared -- skip)
det_head.*                           det_head.*            (103 vs 137 keys -- keep v3.41 version)
psr_head.*                           psr_head.*            (4 base keys -- skip, identical)
psr_predictor.*                      psr_predictor.*       (95 keys -- keep v3.41 version)
```

**Procedure:**
1. Load v3.41_safe state dict as `merged_state`
2. Load v4_fixed state dict as `source_state`
3. For key in `source_state`: if key starts with `act_head.` or `pose_head.` (or `head_pose_head.`), copy to `merged_state`
4. Save `merged_state` as new checkpoint: `unified_transplant_e0_b0.pth`
5. Verify: forward pass through all 4 heads, check no NaN in outputs
6. Record SHA256 checksum

**Size estimate:** ~668 MB (v3.41_safe base + act_head(8) + pose_head(4) overhead is negligible).

---

## 2. Training Stages

### 2.1 Phase A: Transplant Verification (Day 1, ~4 hours)

**Objective:** Confirm the surgical transplant checkpoint loads correctly and all 4 heads produce valid (non-NaN) forward-pass outputs.

| Step | Action | GPU | Time | Risk |
|------|--------|-----|------|------|
| A1 | Copy both source checkpoints to local storage | CPU | <5 min | LOW |
| A2 | SHA256 checksums of v4_e0_b200.pth and phase2_e3_b0.pth | CPU | <1 min | LOW |
| A3 | Execute weight transplant script, save unified_transplant_e0_b0.pth | CPU | <1 min | LOW |
| A4 | Dry-run forward pass: load unified checkpoint, run 1 batch through all 4 heads | GPU | 30 min | MEDIUM |
| A5 | Verify: no NaN in act_logits(75), pose_9dof(9), psr_sigmoid(11), det boxes | CPU | 5 min | LOW |
| A6 | Record output distributions (mean, std per head) as baseline | CPU | 5 min | LOW |

**Gate G1:** All 4 heads produce finite outputs. NaN or inf from any head = STOP. Investigate key name mismatch.

### 2.2 Phase B: Single-Head Validation (Day 1-2, ~8 hours)

**Objective:** Verify each transplanted head can achieve its solo-target number on the unified backbone, confirming that the transplant did not corrupt features.

| Step | Action | Config | GPU | Time | Expected |
|------|--------|--------|-----|------|----------|
| B1 | Freeze backbone + det + psr. Train act_head only. 2 epochs. | lr=1e-3, act only | RTX 3060 | ~3h | act_top1 recovers to >= 0.30 |
| B2 | Freeze backbone + det + psr + act. Train pose_head only. 2 epochs. | lr=1e-3, pose only | RTX 3060 | ~3h | pose_MAE recovers to <= 8.0 deg |
| B3 | Eval all 4 heads after act and pose warmup | full eval | RTX 3060 | ~2h | Baseline: act~0.30, pose~8.0, psr~0.88, det~0.21 |

**Gate G2:** act >= 0.25 AND pose <= 9.0 deg. If either fails, the transplanted heads are not adapting -- investigate feature distribution shift between v4_fixed and v3.41_safe backbones.

### 2.3 Phase C: Progressive Joint Fine-Tuning (Day 2-7, 15 epochs)

**Objective:** Adapt all 4 heads jointly, using progressive unfreezing to prevent destructive interference.

**Loss function** (Kendall homoscedastic uncertainty):

```
L_total = exp(-lv_act) * L_act + lv_act
        + exp(-lv_det) * L_det + lv_det
        + exp(-lv_pose) * L_pose + lv_pose
        + exp(-lv_psr) * L_psr + lv_psr
```

Where:
- L_act: Cross-entropy (75 classes), optional focal modulation (gamma=1.0)
- L_det: CIoU box regression + focal BCE classification (gamma=2.0), multi-scale FPN
- L_pose: MSE on 9-DoF raw output, L2-normalized direction vectors
- L_psr: Per-component focal BCE (gamma=2.0), per-class alpha from prevalence, comp_weights from config

**PCGrad gradient projection** (applied after per-task backward, before optimizer step):
```
For each task pair (i, j) where cos(g_i, g_j) < 0:
    g_i' = g_i - (g_i . g_j) / ||g_j||^2 * g_j
```
Applied at shared backbone parameters only. Task-specific head gradients pass through unmodified.

**5 learnable log_vars** initialized to 0.0 (equal initial weighting). Clamped: `lv in [-LV_CLAMP_MAX, LV_CLAMP_MAX]` per config (det=1.5, pose=2.0).

**Progressive unfreezing schedule:**

| Sub-Phase | Epochs | Frozen | Trainable | Purpose |
|-----------|--------|--------|-----------|---------|
| C1: Head warmup | 1-5 | backbone, det, psr | act_head, pose_head | Adapt transplanted heads to v3.41 backbone features |
| C2: Unfreeze working heads | 6-8 | backbone | act_head, pose_head, psr_head, det_head | Let all 4 heads compete; PSR+det already adapted to this backbone |
| C3: Partial backbone | 9-12 | stage1-2 | stage3-4 + all heads | Gradual backbone unfreezing; shallow layers stay frozen (low-level features are stable) |
| C4: Full model | 13-15 | (none) | all parameters | Full multi-task convergence |

**Hyperparameters -- Phase C:**

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Batch size | 2 | RTX 3060 12GB VRAM limit with 9-channel 16-frame clips |
| Gradient accumulation | 16 | Effective batch size 32 |
| Optimizer | AdamW | Weight decay decoupled from LR |
| Peak LR (heads only, C1-C2) | 1e-3 | Higher LR for rapid head adaptation |
| Peak LR (full model, C3-C4) | 1e-4 | Lower LR to protect backbone features |
| Weight decay | 1e-4 | Standard for transformer/CNN hybrid |
| LR schedule | CosineAnnealingWarmRestarts | T_0=5 epochs, T_mult=2 |
| LR warmup | 500 steps linear | From 0 to peak LR |
| Mixed precision | AMP (float16) | ~40% memory savings, ~30% speedup |
| Gradient clipping | max_norm=5.0 | Prevent loss spikes during unfreezing |
| DataLoader workers | 0 | OOM mitigation per doc 207 |
| Thread config | OMP=4, MKL=4, OPENBLAS=4 | Thread convoy fix per train.py |

**VRAM budget (estimated):**

| Component | VRAM (GB) |
|-----------|-----------|
| MViTv2-S backbone (9ch, 16-frame) | ~3.5 |
| 4 task heads | ~1.0 |
| Activations (batch=2) | ~2.5 |
| AMP overhead | ~0.5 |
| PCGrad per-task gradients (4x) | ~2.0 |
| **Total** | **~9.5** |
| RTX 3060 capacity | 12.0 |
| **Headroom** | **~2.5** |

**Risk:** If PCGrad memory overhead pushes VRAM over 12GB, fall back to Kendall-only (no PCGrad), or reduce batch size to 1 with grad_accum 32.

**Gate G3 (after Phase C):** act >= 0.25, pose <= 9.0 deg, psr >= 0.60, det >= 0.05. If any head fails, continue to Phase D but document the failure mode.

### 2.4 Phase D: Stabilization and Evaluation (Day 7-8)

**Objective:** Stabilize multi-task training with reduced LR and run comprehensive evaluation.

| Step | Action | Config | Time |
|------|--------|--------|------|
| D1 | Continue training, reduced LR (1e-5) | Cosine annealing to 1e-6 | 5 epochs (~15h) |
| D2 | Full 38,036-frame evaluation, all 4 heads | full_eval_inprocess.py | ~2h |
| D3 | Per-component PSR breakdown (11 components) | eval_v3.34_psr_sweep.py | ~2h |
| D4 | Per-class activity accuracy breakdown | full_eval_inprocess.py | included in D2 |
| D5 | Cross-eval with v3.49 evaluator (consistency check) | eval_v3.49_psr.py | ~2h |

**Gate G4 (final):** act >= 0.28, pose <= 8.0 deg, psr >= 0.70, det >= 0.10. These are the minimum viable thresholds. If met, proceed to Phase E. If any head is below threshold, skip to Phase E (contingency) and document findings.

### 2.5 Phase E: Checkpoint Finalization (Day 8)

| Step | Action |
|------|--------|
| E1 | Save final checkpoint as `unified_final_e{epoch}_b{batch}.pth` |
| E2 | Record SHA256 checksum |
| E3 | Save eval JSON alongside checkpoint |
| E4 | Write per-head metric summary to `unified_final_metrics.json` |

---

## 3. Loss Balancing Strategy

### 3.1 Primary: Kendall Homoscedastic Uncertainty Weighting

Already deployed in the codebase (`losses.py`, `MultiTaskLoss`). 5 learnable log_vars. Proven on this dataset (PSR 0.883, det 0.214 on v3.41).

**Initialization:** All log_vars = 0.0 (equal starting weight).
**Clamping:** `[-1.5, 1.5]` for detection (config.LV_CLAMP_MAX_DET=1.5), `[-2.0, 2.0]` for pose (config.LV_CLAMP_MAX_POSE=2.0).
**Monitoring:** Log log_var values per epoch. If any log_var drifts to clamp boundary and stays, that task is being suppressed.

### 3.2 Enhancement: PCGrad Gradient Projection

Kendall weighting modulates loss magnitudes but cannot resolve destructive gradient interference. When activity and detection pull backbone features in opposite directions (cos_sim < 0), the shared representation degrades for both.

**PCGrad** (NeurIPS 2020, Yu et al.) projects each task's gradient onto the normal plane of conflicting tasks:

```python
for task_i, task_j in task_pairs:
    g_i, g_j = get_shared_gradients(task_i), get_shared_gradients(task_j)
    if torch.dot(g_i, g_j) < 0:
        g_i = g_i - (torch.dot(g_i, g_j) / torch.dot(g_j, g_j)) * g_j
        g_j = g_j - (torch.dot(g_i, g_j) / torch.dot(g_i, g_i)) * g_i
```

**Implementation notes:**
- Requires per-task `backward(retain_graph=True)` instead of single combined backward
- Applied at shared backbone parameters only (not task-specific heads)
- 1.5-2x memory overhead (stores per-task gradients)
- Can be toggled on/off per phase (disable during Phase C1 head-warmup, enable from C2 onward)

**Fallback:** ConicGrad (NeurIPS 2022) if PCGrad proves unstable. ConicGrad uses cone projection instead of half-space, better for 3+ tasks.

### 3.3 Not Included: Task-Specific Attention Masks (Deferred)

SwinMTL/MT-Swin-style task-specific attention masks would give each head its own "view" of shared features, theoretically reducing gradient conflict at the architectural level. However, implementing attention masks in MViTv2's pooling attention blocks requires modifying the backbone code -- this is a code change (violates the "no code changes" constraint for planning). Defer to post-freeze as a V2 enhancement.

### 3.4 Loss Component Details

**Activity loss (L_act):**
- Base: CrossEntropyLoss on 75-class logits
- Enhancement (optional): focal modulation gamma=1.0 for hard-negative mining
- Class-balanced sampling in DataLoader (Sampler weighted by inverse frequency, beta=0.9999)

**Detection loss (L_det):**
- Classification: focal BCE (gamma=2.0) on 24-class anchor-level predictions
- Box regression: CIoU loss on [cx, cy, w, h] deltas
- FPN multi-scale: P2, P3, P4, P5 detection layers
- The dx*0.1 bug is confirmed FIXED in current evaluate.py (lines 2405-2410, 831-834). No re-fix needed.

**Pose loss (L_pose):**
- Position: MSE on [pos_x, pos_y, pos_z]
- Direction: MSE on L2-normalized [forward(3), up(3)] vectors
- No orthogonality constraint between forward and up (legacy head does not enforce it; metric is per-vector angular MAE)

**PSR loss (L_psr):**
- Per-component focal BCE (gamma=2.0)
- Per-class alpha from training set prevalence (class_weights)
- Transition boost: 3.0x weight on frames with state transitions (config.PSR_TRANSITION_BOOST)
- Temporal smoothness: 0.05 weight on L2 difference between consecutive predictions
- Loss cap: 20.0 (config.PSR_LOSS_CAP) to prevent dead components from dominating

---

## 4. Hyperparameters

### 4.1 Master Configuration

| Parameter | Value | Source |
|-----------|-------|--------|
| Backbone | MViTv2-S (34.3M params) | File 17 torch.load proof |
| Input | 9-channel, 16-frame clips | Verified from both checkpoints |
| Image size | 1280 x 720 | config.IMG_WIDTH/HEIGHT |
| FPN channels | 256 | config.PSR_FPN_CHANNELS |
| Batch size | 2 | config.BATCH_SIZE, doc 207 |
| Gradient accumulation | 16 | Effective batch 32 |
| Optimizer | AdamW (betas=0.9, 0.999) | Standard for transformer training |
| Weight decay | 1e-4 | Decoupled from LR in AdamW |
| LR schedule | CosineAnnealingWarmRestarts | T_0=5, T_mult=2 |
| LR warmup | 500 steps linear | 0 to peak_lr |
| Mixed precision | AMP float16 | GradScaler with growth_interval=2000 |
| Gradient clipping | max_norm=5.0 | Prevents spikes during unfreezing |
| DataLoader workers | 0 | OOM mitigation |
| Thread limit | OMP=4, MKL=4 | Thread convoy fix |
| Seed | 42 | Reproducibility |

### 4.2 Phase-Specific Hyperparameters

| Phase | Peak LR | Min LR | Epochs | Frozen | PCGrad | Notes |
|-------|---------|--------|--------|--------|--------|-------|
| B1 (act warmup) | 1e-3 | 1e-4 | 2 | backbone, det, psr, pose | Off | Rapid adaptation |
| B2 (pose warmup) | 1e-3 | 1e-4 | 2 | backbone, det, psr, act | Off | Rapid adaptation |
| C1 (head warmup) | 1e-3 | 1e-4 | 5 | backbone, det, psr | Off | Adapt act+pose heads |
| C2 (unfreeze heads) | 5e-4 | 5e-5 | 3 | backbone | On | All heads compete |
| C3 (partial backbone) | 1e-4 | 1e-5 | 4 | stage1-2 | On | Gradual unfreeze |
| C4 (full model) | 5e-5 | 5e-6 | 3 | (none) | On | Full convergence |
| D (stabilization) | 1e-5 | 1e-6 | 5 | (none) | On | Fine-tuning |

### 4.3 Loss Weights (Static Fallbacks)

If Kendall log_vars produce unstable training, fall back to static loss weights tuned from v3.41_safe training log analysis:

| Loss Term | Initial Weight | Rationale |
|-----------|---------------|-----------|
| L_act | 1.0 | Baseline activity loss |
| L_det | 5.0 | Detection needs boosting (historically weak in multi-task) |
| L_pose | 0.1 | Pose loss magnitude is naturally ~10x larger (MSE on continuous values) |
| L_psr | 10.0 | Per config.PSR_WEIGHT. PSR needed heavy weighting to achieve 0.883 |

---

## 5. Scheduled Unfreezing: Detailed Rationale

### 5.1 Why Progressive Unfreezing

Directly training all 4 heads from the transplant checkpoint would cause:
1. **Early gradient competition:** Detection and activity gradients conflict in the shared FPN. The stronger task (PSR, with proven 0.883) would dominate.
2. **Feature distribution shift:** v4_fixed's act/pose heads were trained with v4_fixed backbone features. Transplanting onto v3.41 backbone features creates a distribution mismatch. The heads need adaptation before the backbone is modified.
3. **Catastrophic forgetting:** Without freezing, PSR could regress from 0.883 to <0.50 as backbone features are pulled toward activity/pose objectives.

### 5.2 Freezing Schedule Design

**Stage1-2 frozen (C3):** Low-level Conv3d patch embedding and early MViT blocks capture fundamental spatiotemporal features (edges, motion, depth). These are unlikely to be task-specific and should remain stable.

**Stage3-4 unfrozen (C3):** Higher-level semantic features can adapt to multi-task demands.

**Task-specific heads unfrozen before backbone (C1-C2):** Heads have small parameter counts (~5-10k each). Letting them adapt first before modifying the shared trunk minimizes backbone disruption.

### 5.3 Monitoring During Training

Log every 50 batches:
- Per-task loss (act, det, pose, psr)
- Kendall log_var values (all 5)
- Gradient cosine similarity matrix (4x4 task pairs) -- flag if any pair consistently < -0.5
- GPU memory usage
- LR current value

Log every epoch:
- Full validation metrics (all 4 heads)
- Per-component PSR F1 breakdown (to catch dead components early)
- Checkpoint save

---

## 6. Evaluation Protocol

### 6.1 Primary Evaluation

**Script:** `eval_v3.34_psr_sweep.py` for PSR (canonical evaluator, produces 0.883 reference). `full_eval_inprocess.py` for act, det, pose (NaN-safe in-process runner).

**Dataset:** Full 38,036-frame IndustReal validation set (n_frames=0).

### 6.2 Metrics Reported

| Head | Primary Metric | Secondary Metrics |
|------|---------------|-------------------|
| Activity | top-1 accuracy (raw, tau=1.0) | top-5 accuracy, per-class accuracy breakdown |
| Detection | mAP50 (COCO standard) | mAP50-95, per-class AP, mAP50_pc (present classes only) |
| Pose | forward_angular_MAE (degrees) | up_angular_MAE, position_MAE_mm |
| PSR | per-frame F1 (threshold=0.5) | per-class swept F1, per-component F1 breakdown, transition F1 (honest metric: TP=FP=FN=0 returns 0.0 not 1.0) |

### 6.3 Transition F1 -- The Honest PSR Metric

The per-frame F1 dominated by copy_prev persistence baseline (0.9997) is NOT a valid metric. **Transition F1** (computed only on frames where the ground truth state changes) is the honest metric. The F1=1.0 eval bug (returns 1.0 when TP=FP=FN=0) must be patched: return 0.0 instead.

### 6.4 Cross-Eval Consistency

Run both v3.34 (canonical) and v3.49 (current) PSR evaluators. Expected delta: -0.05 to -0.07 (v3.49 lower due to MonotonicDecoder parameter differences). Report both.

---

## 7. Checkpointing Strategy

### 7.1 Retention Policy

- **Every epoch:** Save checkpoint as `unified_e{epoch}_b{last_batch}.pth`
- **Best per head:** Save separate "best" checkpoints when any head achieves a new maximum: `unified_best_act_e{epoch}.pth`, `unified_best_psr_e{epoch}.pth`, etc.
- **Crash recovery:** Save `crash_recovery.pth` every 200 batches
- **Final:** `unified_final_e{epoch}_b{last_batch}.pth`

### 7.2 Disk Budget

| Item | Size | Count | Total |
|------|------|-------|-------|
| Transplant base | ~668 MB | 1 | 0.7 GB |
| Epoch checkpoints | ~668 MB | 20 | 13.4 GB |
| Best-per-head | ~668 MB | 4 | 2.7 GB |
| Crash recovery | ~668 MB | 1 | 0.7 GB |
| **Phase C+D total** | | | **~17.5 GB** |

Local storage: 138 GB free (457 GB total). Sufficient headroom.

### 7.3 SHA256 Integrity

Record SHA256 at:
1. Transplant creation (unified_transplant_e0_b0.pth)
2. Every epoch checkpoint
3. Final checkpoint

Store checksums in `checkpoints/SHA256SUMS` alongside checkpoints.

---

## 8. Timeline

### 8.1 Day-by-Day Schedule

| Day | Date | Phase | Activity | GPU Hours | Wall Clock |
|-----|------|-------|----------|-----------|------------|
| 1 | Aug 2 | A | Transplant + verification | 0.5 | 2h |
| 1 | Aug 2 | B1 | Act head warmup (2 epochs) | 3 | 3h |
| 1-2 | Aug 2-3 | B2 | Pose head warmup (2 epochs) | 3 | 3h |
| 2 | Aug 3 | B3 | Full eval baseline | 2 | 2h |
| 3-4 | Aug 4-5 | C1 | Head warmup (5 epochs @ ~2h/epoch) | 10 | 10h |
| 5 | Aug 6 | C2 | Unfreeze heads (3 epochs) | 6 | 6h |
| 6 | Aug 6-7 | C3 | Partial backbone (4 epochs) | 8 | 8h |
| 7 | Aug 7-8 | C4 | Full model (3 epochs) | 6 | 6h |
| 8-9 | Aug 9-10 | D | Stabilization (5 epochs) | 10 | 10h |
| 10 | Aug 11 | -- | Full eval + analysis | 2 | 4h |
| 11-12 | Aug 12-13 | -- | Buffer / retry / contingency | 16 | 48h |
| **--** | **Aug 13** | **E** | **Checkpoint finalization + documentation** | **0** | **2h** |

**Total GPU-hours:** ~60h on RTX 3060
**Total wall clock:** 12 days (Aug 2 -- Aug 13)
**Buffer before Aug 22 freeze:** 9 days

### 8.2 Parallelization Opportunity

If RTX 5060 Ti (16GB) is available simultaneously:
- Run Phase B (act+pose warmup) on RTX 5060 Ti in parallel with Phase A verification on RTX 3060
- Saves ~6 hours off the critical path
- RTX 5060 Ti's extra 4GB VRAM may allow batch_size=4 for faster iteration

### 8.3 Contingency Day Allocation

The 2-day buffer (Aug 12-13) covers:
- OOM debugging (PCGrad memory overhead adjustment)
- NaN investigation (if training diverges during unfreezing)
- Retry of any failed phase
- Final eval re-runs
- Documentation and cross-reference updates

If all phases pass on schedule, the buffer can be used for optional enhancements:
- Ablation: Kendall-only vs Kendall+PCGrad comparison
- Extended stabilization (10 epochs instead of 5)
- Per-class analysis and threshold tuning for PSR dead components

---

## 9. Risk Register

### 9.1 Technical Risks

| Risk | Prob | Impact | Mitigation |
|------|------|--------|------------|
| PCGrad OOM on RTX 3060 12GB | 40% | HIGH | Fall back to Kendall-only; reduce batch_size to 1 with grad_accum 32 |
| v4_fixed act_head produces NaN on v3.41 backbone | 15% | CRITICAL | Verify key name mapping. If mismatch found, manually map keys. |
| PSR regresses below 0.60 during joint training | 35% | HIGH | PSR head has proven robustness. Gate G3 catches this early. If failing, freeze PSR permanently and train 3-head model. |
| Detection stays below 0.05 | 50% | MEDIUM | Detection is historically the weakest multi-task head. If it stays near-zero, document as multi-task pathology finding. The aspirational 0.30 target was always above the proven ceiling (0.214). |
| 9-channel data pipeline broken | 20% | CRITICAL | Verify VL/Stereo/Depth channels exist in dataset before starting Phase B. If missing, the entire plan is blocked. |
| External drive disconnects mid-training | 10% | HIGH | Both checkpoints MUST be copied to local storage in Phase A. Training runs from local copies. |

### 9.2 Strategic Risks

| Risk | Prob | Impact | Mitigation |
|------|------|--------|------------|
| All 4 heads regress below individual baselines | 25% | CRITICAL | The "multi-task cost" is the paper's contribution. Document honestly. Fall back to separate models (2-checkpoint strategy from File 16). |
| Paper reviewers note v4_fixed eval was 500-frame smoke test, not full 38k | 100% | MODERATE | Disclose. Re-evaluate on full set. If number drops, report both. |
| Paper reviewers note 0.883 PSR has 4 dead components | 100% | MODERATE | Disclose per-component breakdown. The clean finding: "7 of 11 components achieve 0.913 mean F1; 4 are dead at F1=0.0 -- these components have near-zero positive samples in the training set." |
| Paper reviewers note backbone difference (MViTv2-S vs ConvNeXt-Tiny claims) | 80% | LOW | File 17's torch.load proof resolves this. Publish the actual inspection evidence. Withdraw the ConvNeXt claims. |
| Aug 22 freeze deadline missed | 15% | CRITICAL | 9-day buffer should absorb all contingencies. If training is still running at Aug 20, freeze checkpoint and document training-in-progress state. |

### 9.3 Abandonment Criteria

Stop training and document immediately if:

1. **Unified transplant crashes on load** (key mismatch, size mismatch). The two checkpoints are architecturally incompatible despite File 17's evidence. Re-examine checkpoint inspection.
2. **Any head produces NaN during Phase A dry run.** Indicates deeper code/architecture mismatch not detectable from state dict inspection alone.
3. **PSR drops below 0.40 during Phase C.** The strongest head is being destroyed by multi-task interference. The unified model approach is failing. Fall back to separate models.
4. **Training loss diverges (loss > 100 for 3+ consecutive batches).** Gradient explosion unstoppable by clipping.

---

## 10. Cross-References

### 10.1 Input Files (Read for Context)

| File | Agent | Content | Key Contribution to This Plan |
|------|-------|---------|------------------------------|
| 05_integration_synthesis.md | Agent 5 | Original integration synthesis | Conflict matrix, critical path, 2-head maximum on ConvNeXt. **Superseded by File 17's MViTv2-S finding.** |
| 12_revert_act_0.394.md | Agent 1 | Activity revert plan | Verified 0.394 on v4_fixed. Identified FiLM conditioning. **Superseded: backbone is MViTv2-S not ConvNeXt-Tiny.** |
| 13_revert_det_0.5734.md | Agent 2 | Detection revert plan | **Proved 0.5734 is a biased subsample artifact. Withdrawn.** Honest multi-task detection on ConvNeXt = 0.00009, on MViTv2-S = 0.214. |
| 14_revert_pose_6.15.md | Agent 3 | Pose revert plan | Verified 6.15 deg on legacy HeadPoseHead. USE_GEO_HEAD_POSE=False mandatory. |
| 15_revert_psr_0.883.md | Agent 4 | PSR revert plan | Verified 0.883 on v3.41_safe Path A. 4 dead components. Per-component breakdown. |
| 16_revert_all_integration.md | Agent 5 | Integration plan | 3 of 4 targets revertable. **Superseded: assumed ConvNeXt-Tiny for v4_fixed.** |
| 17_unified_model_weight_merging.md | Agent 1 | **Weight merging (CRITICAL)** | **torch.load proof: both checkpoints use MViTv2-S. 544 shared keys. Surgical transplant viable.** |
| 18_unified_model_training.md | Agent 2 | Training plan | **Contains errata: assumes ConvNeXt-Tiny vs MViTv2-S incompatibility.** Detailed Phase 0-4 timeline and GPU allocation used as template. |
| 21_unified_model_final_synthesis.md | Agent 5 | Final synthesis | **Contains errata: recommends ConvNeXt-Tiny despite File 17 evidence.** Target ranges partially adopted. |
| 23_deep_search_mtl_architectures.md | Agent 2 | MTL architecture search | Kendall #1, PCGrad/ConicGrad #2. Task-specific attention masks #3. VRAM estimates for PCGrad. |
| 24_deep_search_long_tail_training.md | Agent 3 | Long-tail training recipes | LDAM-DRW, focal BCE, CB-Focal. Class-balanced sampling beta parameter. |
| 25_deep_search_9channel_backbones.md | Agent 4 | 9-channel backbone search | MViTv2-S #1 (proven). MViTv2-B #2 (untested upgrade). Confirms File 17's checkpoint inspection. |
| 26_deep_search_final_synthesis.md | Agent 5 | Final architecture synthesis | Surgical transplant + progressive fine-tuning. 7 gates (G1-G7). 12-day timeline. |

### 10.2 Output Files (Produced After This Plan)

| File | Agent | Description | Dependency on This Plan |
|------|-------|-------------|------------------------|
| 31_plan_E_final_paper_submission.md | Agent 5 | Final paper submission plan | Uses this plan's final metrics (or contingency fallback metrics) as the paper's core results |

### 10.3 Key Numbers Cross-Reference

| Number | This Plan Uses? | Source | Notes |
|--------|----------------|--------|-------|
| act=0.394 | YES (baseline, not target) | File 12, v4_fixed | 500-frame smoke test. Full 38k expected lower. |
| det=0.5734 | **NO -- WITHDRAWN** | File 13 | Biased 250-batch subsample artifact. Honest number: 0.214 (v3.41) or 0.00009 (ConvNeXt). |
| pose=6.15 | YES (baseline, not target) | File 14, v4_fixed | 500-frame. Multi-task expected 6.5-7.5. |
| psr=0.883 | YES (ceiling, not target) | File 15, v3.41_safe | 4 dead components. Multi-task expected 0.75-0.85. |
| MViTv2-S act top-1=0.6223 | NO | File 10, Agent 10 historical | Different model (single-task MViTv2-S, 16-frame). Not a multi-task number. |

---

## 11. Appendix: Training Script Requirements

The following scripts must be present and verified before training begins. All live on the external training workstation (`/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/`).

### 11.1 Required for Training

| Script | Purpose | Lines | Status |
|--------|---------|-------|--------|
| `train.py` | Training loop, AMP, checkpointing, logging | ~1000+ | On external drive |
| `model.py` | POPWMultiTaskModel, 4-head architecture | unknown | On external drive |
| `losses.py` | MultiTaskLoss, Kendall weighting, per-task losses | unknown | On external drive |
| `config.py` | All hyperparameters | ~142 (swarm-bot), unknown (external) | Both copies exist |
| `industreal_dataset.py` | 9-channel data loading, augmentations | unknown | On external drive |

### 11.2 Required for Evaluation

| Script | Purpose | Status |
|--------|---------|--------|
| `full_eval_inprocess.py` | 4-head NaN-safe eval runner | In swarm-bot (`src/evaluation/`) |
| `evaluate.py` | Core eval logic (dependency of full_eval_inprocess.py) | On external drive (6,966 lines) |
| `eval_v3.34_psr_sweep.py` | PSR per-class threshold sweep | On external drive |
| `eval_v3.49_psr.py` | Current-version PSR cross-eval | On external drive |
| `eval_mtl_9ch.py` | 9-channel input eval for MViTv2-S | On external drive |

### 11.3 Critical Missing Dependencies (Copy Before Training)

The swarm-bot repo does NOT contain:
- `evaluate.py` (6,966 lines) -- must be copied from external drive
- `model.py` (architecture definitions) -- must be copied from external drive
- `train.py` (training loop) -- must be copied from external drive
- `losses.py` (loss functions) -- must be copied from external drive
- `industreal_dataset.py` (data loader) -- must be copied from external drive

**These 5 files must be available locally before Phase B can begin.**

---

## 12. Post-Freeze Enhancements (Out of Scope)

Items deferred to after the Aug 22 freeze:

1. **MViTv2-B upgrade:** 52M param backbone with ~50% more capacity. Drop-in replacement for MViTv2-S. Expected 5-10% improvement across all heads at cost of +2GB VRAM.
2. **Task-specific attention masks:** SwinMTL-style channel gating in MViTv2 blocks. Requires backbone code modification. Could reduce gradient conflict architecturally.
3. **PSR Path A component resurrection:** Specialized data augmentation or synthetic minority oversampling for comp4/7/8/9 (the 4 dead PSR components). Requires data pipeline changes.
4. **GeometryAwareHeadPose fix:** Fix column-ordering bug and retrain. Requires code changes in model.py.
5. **YOLO11 unified multi-task head:** Replace 4 independent heads with YOLO11-style unified head. Major architectural change. Production-grade but requires significant implementation work.
6. **TAPS branching:** Learn which layers to share vs branch per task. Requires implementation of gating networks and retraining.
