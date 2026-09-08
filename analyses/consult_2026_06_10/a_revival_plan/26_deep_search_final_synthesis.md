# Agent 5: Final Architecture Synthesis -- ONE Model, All 4 Tasks

**Date:** 2026-08-01
**Agent:** Agent 5 (Final Architecture Synthesist)
**Mission:** Synthesize all agent plans into ONE concrete architecture + training plan achieving act=0.394, det=0.21+, pose=6.15 degrees, psr=0.883 in ONE model.
**Inputs:** Revert plans 12-16, unified model plans 17-20, adversarial debates 11/20, SOTA history, prior synthesis 21
**Note:** Background agents for deep-search plans 22-25 are still running. This synthesis uses the available unified-model analyses (17-20) as proxy material. Their paper citations will be incorporated if/when those files are completed.
**Constraint:** This file only. No code changes.

---

## 0. Executive Summary: The Contradiction Resolved

A critical contradiction exists across the analysis files:

- **Files 18, 19, 20, 21** all assert v4_fixed uses ConvNeXt-Tiny (3-channel RGB) and v3.41_safe uses MViTv2-S (9-channel). They conclude weight merging is impossible and at most 2 of 4 tasks are revivable.
- **File 17** performed actual `torch.load()` checkpoint inspection and found BOTH checkpoints use MViTv2-S with 9-channel input. `conv_proj` shape `[96, 9, 3, 7, 7]` in both. 544 shared keys with identical shapes. Weight merging is architecturally viable.

**File 17 was written last (21:37 vs 21:32-21:33 for files 18-20) and contains the only empirical checkpoint inspection evidence.** Files 18-20 were written before this evidence was available and based their conclusions on documentation claims rather than on-disk inspection.

**Verdict: Both checkpoints use MViTv2-S. Weight merging is viable. A single model IS architecturally possible.**

This changes the entire feasibility landscape. Activity=0.394 and pose=6.15 were achieved on MViTv2-S, not ConvNeXt-Tiny. The "ConvNeXt dead-end" argument is moot. The linear probe showing zero activity signal was performed on ConvNeXt features -- MViTv2-S's spatiotemporal features are a different story.

---

## 1. Architecture Decision

### 1.1 Decision: MViTv2-S with 9-Channel Input + 4 Specialized Heads

**Backbone:** MViTv2-S (34.3M params), 9-channel input (RGB + VL + StereoL + StereoR + Depth), 16-frame 3D spatiotemporal clips.

**Rationale:** This is the architecture both proven checkpoints use. No other backbone has demonstrated multi-task convergence at any level.

### 1.2 Checkpoint Evidence

| Property | v4_fixed (`v4_e0_b200.pth`, 233 MB) | v3.41_safe (`phase2_e3_b0.pth`, 664 MB) |
|----------|--------------------------------------|------------------------------------------|
| Total keys | 639 | 578 |
| Backbone keys | 393 (MViTv2-S) | 393 (MViTv2-S) |
| conv_proj shape | `[96, 9, 3, 7, 7]` | `[96, 9, 3, 7, 7]` |
| Input channels | 9 | 9 |
| Shared keys (identical names + shapes) | 544 | 544 |
| act_head keys | 8 | 8 |
| pose_head keys | 4 | 4 |
| psr_head base keys | 4 | 4 |
| PSR predictor keys | 95 (Path A: transformer + 11 transition_heads) | 0 (absent -- Path B only) |
| Detection head keys | 103 | 137 (one additional FPN scale) |
| **Proven metrics** | act=0.394, pose=6.15 deg | psr=0.883, det=0.214 |

### 1.3 Head Architecture Specification

**Activity Head** (8 keys, shared between checkpoints):
- Input: FPN P5 features (768-dim)
- Architecture: `Linear(768, 512) -> LayerNorm -> Dropout -> ReLU -> Linear(512, 75)`
- Proven: 0.394 top-1 on v4_fixed

**Pose Head** (4 keys, Legacy HeadPoseHead):
- Input: GAP over C4+C5 feature concatenation
- Architecture: `Linear(1152, 512) -> Linear(512, 256) -> Linear(256, 9)`
- Output: 9-DoF raw [forward(3), up(3), position(3)]
- Proven: 6.15 degrees angular MAE on v4_fixed
- **CRITICAL:** `USE_GEO_HEAD_POSE=False` mandatory. GeometryAwareHeadPose has column-ordering bug producing ~86 degree error.

**PSR Head** (Path A, from v3.41_safe):
- Base: `Linear(768, 256) -> GRU(256) -> Linear(256, 11)`
- Predictor: 3-layer causal transformer (d_model=256, 4 heads) + 11 per-component binary sigmoid heads
- Decoder: MonotonicDecoder with Q48 hysteresis (sustain_hi/sustain_lo)
- Loss: Per-component focal BCE (gamma=2.0, per-class alpha from prevalence)
- Proven: 0.883 F1 on v3.41_safe
- **Note:** v4_fixed checkpoint has PSR Path A predictor keys (95) but they produce dead output because training was stopped at epoch 0 batch 200. The Path A architecture was present but barely trained.

**Detection Head** (from v3.41_safe):
- FPN-based multi-scale detection (P2-P5)
- 137 keys in v3.41_safe (one additional scale vs v4_fixed's 103)
- Proven: 0.214 mAP50 on full eval (v3.41_safe) -- NOT collapsed
- **Note:** 0.5734 det_mAP50_pc is a biased 250-batch class-balanced subsample artifact (n_present=15 of 24 classes). Honest multi-task detection is ~0.21, not 0.57 and not 0.00009. The 0.00009 number is from ConvNeXt-Tiny, not MViTv2-S.

### 1.4 Why Not Alternatives

| Alternative | Why Rejected |
|-------------|--------------|
| **ConvNeXt-Tiny** | Linear probe proves zero activity signal (0.2169 < 0.2217 baseline). Detection collapses to 0.00009 (99.99% cost). Never achieved PSR > 0.10. At most 2 of 4 tasks work. |
| **MViTv2-S with 3-channel** | Requires retraining conv_proj from 9-channel to 3-channel. Loses the proven checkpoint weights. 10+ days training from scratch. |
| **Two separate models** | Honest but abandons the "ONE model" goal. Better as fallback, not as primary plan. |
| **Distillation across backbones** | No precedent for distilling across different input modalities (9-channel spatiotemporal -> 3-channel per-frame). Requires 9-channel pipeline anyway. |
| **Training from scratch** | 30-50 epochs at ~3 hr/epoch. No guarantee all heads converge. Historical multi-task collapse (detection 0.00009) happened during co-training. |

---

## 2. Training Recipe

### 2.1 Strategy: Surgical Head Transplant + Progressive Joint Fine-Tuning

This strategy combines file 17's Strategy 4 Option A (surgical head copy) with progressive training to adapt transplanted heads.

**Phase approach:**
1. **Base model:** v3.41_safe checkpoint (proven PSR=0.883, det=0.214)
2. **Transplant:** act_head + pose_head from v4_fixed (proven 0.394, 6.15 deg)
3. **Freeze PSR+det:** Lock the heads that already work
4. **Fine-tune act+pose:** Adapt transplanted heads to v3.41's backbone feature distribution
5. **Unfreeze and joint-tune:** Once all heads are independently working, unfreeze for full multi-task convergence

### 2.2 Loss Function

**Total loss with Kendall homoscedastic uncertainty weighting:**

```
L_total = exp(-log_var_act) * L_act + log_var_act
        + exp(-log_var_det) * L_det + log_var_det
        + exp(-log_var_pose) * L_pose + log_var_pose
        + exp(-log_var_psr) * L_psr + log_var_psr
```

Where:
- **L_act:** Cross-entropy over 75 classes (verb_group classification)
- **L_det:** CIoU box regression + focal classification loss (YOLOv8-style, multi-scale FPN)
- **L_pose:** MSE over 9-DoF raw output [forward(3), up(3), position(3)]
- **L_psr:** Per-component focal BCE (gamma=2.0) with class-specific alpha from training set prevalence

**Initial log_var values** (from v4_fixed and v3.41_safe training logs):
- log_var_act: ~0.0 (act loss ~1.0-2.0 range)
- log_var_det: ~3.0 (det loss ~5-15 range, higher magnitude)
- log_var_pose: ~2.0 (pose loss ~10-50 range)
- log_var_psr: ~0.0 (PSR BCE loss ~0.3-0.7 range)

### 2.3 Training Schedule

**Phase A: Preservation and Verification (Day 0, ~4 GPU-hours)**

| Step | Action | GPU | Time |
|------|--------|-----|------|
| A1 | Copy both checkpoints to local safe storage with SHA256 | None | 5 min |
| A2 | Copy evaluate.py, model.py, losses.py, train.py from external drive | None | 10 min |
| A3 | Re-evaluate v4_fixed on full 38k-frame validation set (not 500-frame smoke test) | RTX 3060 | 2 hr |
| A4 | Re-evaluate v3.41_safe on full validation set | RTX 3060 | 2 hr |
| A5 | Fix F1=1.0 bug in all 4 locations (psr_transition.py:382-386, :347, evaluate.py:1269, :1412) | None | 1 hr |
| A6 | Free disk space (thin det_fixed_v1 checkpoints, remove incomplete MTL runs) | None | 1 hr |

**Gate A:** If act != 0.394 +/- 0.02 OR pose != 6.15 +/- 0.5 deg OR psr_f1 < 0.80 (with F1=1.0 bug fixed), STOP. Checkpoints are corrupted or metrics were inflated. Revert to two-model fallback.

**Phase B: Surgical Head Transplant (Day 1, ~2 GPU-hours)**

| Step | Action | GPU | Time |
|------|--------|-----|------|
| B1 | Implement selective checkpoint loader: load v3.41_safe as base, replace act_head + pose_head with v4_fixed weights | None | 2 hr |
| B2 | Verify forward pass produces correct outputs for all 4 heads (no NaN, no shape mismatch) | RTX 3060 | 30 min |
| B3 | Quick eval (500 frames) to verify act ~0.39, pose ~6.15, psr ~0.88, det ~0.21 | RTX 3060 | 1 hr |

**Gate B:** If act < 0.25 OR pose > 15 deg after transplant, feature distribution shift is too severe. The v4_fixed heads are incompatible with v3.41's backbone features. Proceed to Phase C (fine-tuning required) rather than expecting zero-shot transfer.

**Phase C: Progressive Head Adaptation (Days 2-7, ~120 GPU-hours)**

| Epochs | What's Frozen | What's Training | Learning Rate | Goal |
|--------|---------------|-----------------|---------------|------|
| 1-10 | Backbone + FPN + PSR head + Det head | act_head + pose_head only | 3e-4 with cosine to 1e-5 | Adapt transplanted heads to v3.41 backbone features |
| 11-15 | Backbone + FPN | All 4 heads (Kendall weighting) | 1e-4 with cosine to 1e-5 | Joint convergence, monitor for task interference |
| 16-25 | Nothing (full model) | All parameters | 5e-5 with cosine to 5e-6 | Full multi-task fine-tuning |
| 26-40 | Nothing | All parameters | 1e-5 constant | Stabilization |

**Learning rate rationale:**
- Phase C epochs 1-10: Higher LR for head adaptation. Heads start from different feature distribution.
- Phase C epochs 11-15: Medium LR for joint tuning. Kendall weights prevent one task from dominating.
- Phase C epochs 16-25: Lower LR. Backbone features are close to optimal from v3.41.
- Phase C epochs 26-40: Minimal LR for fine stabilization.

**Batch configuration:**
- Batch size: 2 (RTX 3060, 12 GB VRAM limitation with 9-channel 16-frame clips)
- Gradient accumulation: 16 steps (effective batch = 32)
- Mixed precision: AMP (autocast + GradScaler)

**Data pipeline:** 9-channel input (RGB+VL+StereoL+StereoR+Depth). The 9-channel dataset pipeline must be functional since both checkpoints were trained with it. Verify loading code at Phase A.

### 2.4 Monitoring and Gates

**Per-epoch metrics to track:**
- Activity: top-1 accuracy, macro F1, per-class accuracy on rare classes (41 classes with zero signal on ConvNeXt)
- Pose: forward_angular_MAE, up_angular_MAE, position_MAE_mm
- PSR: per-frame state accuracy, transition F1 (with F1=1.0 bug fixed), per-component F1 (watch for dead components)
- Detection: mAP50, mAP50-95, per-class AP

**Critical gates:**

| Gate | When | Condition | Action on Fail |
|------|------|-----------|----------------|
| G1: Transplant viability | Phase B | act >= 0.25 AND pose <= 15 deg | Proceed to fine-tuning (Phase C) |
| G2: PSR preservation | Phase C epoch 2 | psr_f1 >= 0.70 (no catastrophic forgetting) | Increase PSR loss weight, freeze act/pose LR |
| G3: Activity convergence | Phase C epoch 10 | act >= 0.30 (trending up) | Increase act loss weight, check for FiLM contamination |
| G4: Pose convergence | Phase C epoch 10 | pose <= 8.0 deg (trending down) | Verify USE_GEO_HEAD_POSE=False, check FiLM params |
| G5: Detection non-collapse | Phase C epoch 5 | det_mAP50 >= 0.10 (not collapsed to zero) | Accept detection as weak head, do not increase weight |
| G6: Multi-task stability | Phase C epoch 15 | ALL heads improving or stable (no head declining > 10%) | Stop training, checkpoint best-so-far |
| G7: Final evaluation | Phase C epoch 40 | act >= 0.35, pose <= 7.0 deg, psr_f1 >= 0.80, det >= 0.15 | If ALL pass: success. If partial: report honestly. |

---

## 3. Timeline

### 3.1 Wall Clock Schedule

| Phase | Calendar Days | GPU Hours | GPU | Cumulative |
|-------|---------------|-----------|-----|------------|
| A: Preservation + Verification | Day 0 | 4 hr eval | RTX 3060 | 4 hr |
| B: Surgical Transplant | Day 1 | 2 hr | RTX 3060 | 6 hr |
| C: Progressive Adaptation | Days 2-7 | ~120 hr (40 epochs x ~3 hr/epoch) | RTX 3060 | ~126 hr |
| D: Full Evaluation | Day 8 | 4 hr eval | RTX 3060 | ~130 hr |
| E: Buffer + Ablations | Days 9-12 | ~40 hr (optional retries, Kendall ablation) | RTX 3060 | ~170 hr |
| **Total** | **12 days** | **~170 GPU-hours** | | |

### 3.2 Resource Requirements

- **GPU:** 1x RTX 3060 (12 GB) for training. RTX 5060 Ti (GPU 0) available for parallel work but not required.
- **Disk:** ~30 GB for checkpoints (40 epochs x ~700 MB with optimizer state), plus ~30 GB for eval cache. Total: ~60 GB.
- **RAM:** 16 GB minimum (dataset loading + 9-channel 16-frame clips).

### 3.3 Deadline Assessment

- **Freeze date:** Aug 22 (21 days from Aug 1)
- **Plan completion:** Aug 13 (12 days) with 9 days buffer
- **Risk of exceeding freeze:** LOW (75% buffer, 1 full retry cycle possible)

---

## 4. Expected Metrics

### 4.1 Per-Head Targets

| Metric | Historical Best (Separate) | Expected (Unified After Phase C) | Probability of >= Target | Risk |
|--------|---------------------------|----------------------------------|--------------------------|------|
| **Activity (top-1)** | 0.394 (v4_fixed) | 0.30-0.38 | ~70% (>= 0.30), ~40% (>= 0.35) | Feature distribution shift from transplant |
| **Detection (mAP50)** | 0.214 (v3.41_safe) | 0.15-0.21 | ~60% (>= 0.15), ~30% (>= 0.21) | Gradient conflict during joint training |
| **Pose (angular MAE)** | 6.15 deg (v4_fixed) | 6.15-7.50 deg | ~85% (<= 7.5), ~50% (<= 6.5) | Pose fix is code-only; FiLM contamination is the risk |
| **PSR (transition F1)** | 0.883 (v3.41_safe) | 0.75-0.85 | ~60% (>= 0.80), ~30% (>= 0.85) | Catastrophic forgetting; eval bug fixes may lower score |

### 4.2 Realistic Unified Model Performance

The honest expected range for the unified model after Phase C:

| Metric | Conservative | Expected | Optimistic |
|--------|-------------|----------|------------|
| act top-1 | 0.28 | 0.34 | 0.38 |
| det mAP50 | 0.10 | 0.18 | 0.22 |
| pose deg | 8.0 | 6.8 | 6.3 |
| psr f1 | 0.72 | 0.82 | 0.87 |

### 4.3 Detection Reality

Detection is the weakest head. It has never exceeded 0.25 in any multi-task configuration, even on MViTv2-S. The 0.5734 claim is a biased subsample artifact. The honest unified model will likely have det in the 0.10-0.22 range. This should be framed as:

1. **Companion model:** YOLOv8m achieves 0.995 mAP50 single-task. Use this for production detection.
2. **Multi-task contribution:** The 0.10-0.22 in a 4-head model demonstrates that detection can partially survive multi-task training, unlike the 99.99% collapse observed on ConvNeXt-Tiny.
3. **Paper framing:** "Detection achieves X in multi-task configuration vs 0.995 single-task. This N% cost vs the 99.99% cost on ConvNeXt-Tiny demonstrates that backbone architecture (spatiotemporal vs per-frame CNN) is the primary determinant of multi-task detection viability."

---

## 5. Risk Assessment

### 5.1 Risk Matrix

| Risk | P(Failure) | Impact | Mitigation |
|------|-----------|--------|------------|
| **9-channel pipeline non-functional** | 15% | Cannot train at all | Both checkpoints were trained with 9ch input. Pipeline must have worked. Verify at Phase A. If broken, revert to two-model. |
| **Feature distribution shift (transplant)** | 40% | act_head + pose_head underperform on v3.41 backbone | Phase C epochs 1-10 explicitly fine-tune these heads. If G1 fails, train from scratch on v3.41. |
| **Catastrophic forgetting (PSR)** | 30% | PSR F1 drops below 0.70 during joint training | Freeze PSR head first. Only unfreeze after act+pose stabilize. Kendall weighting prevents gradient dominance. |
| **Catastrophic forgetting (act/pose)** | 20% | Act drops below 0.25, pose exceeds 10 deg | Freeze act+pose heads after adaptation. Gate G2/3/4 catch this early. |
| **HeadPoseFiLM contamination** | 25% | Pose column fix changes FiLM inputs, degrading backbone features for PSR | After pose fix, run full multi-task eval BEFORE training. If PSR degrades, resume training for FiLM adaptation (2 days). |
| **Detection gradient conflict** | 60% | Detection degrades below 0.10 during joint training | Accept low detection. Frame as pathology contribution. Use YOLOv8m companion. |
| **PSR eval bug fix lowers real F1** | 80% | F1 drops 0.05-0.09 after fixing F1=1.0 bug | This is a CORRECTION, not a regression. Report corrected numbers honestly. The real PSR F1 with bug fix is likely 0.79-0.85. |
| **Time budget exceeded** | 20% | Cannot complete by Aug 22 | 9-day buffer allows one full retry. If both attempts fail, publish partial results. |
| **External drive failure** | 10% | Loss of evaluate.py (6966 lines) and model.py | Copy critical artifacts to swarm-bot repo during Phase A. Mitigation takes 30 minutes. |
| **Disk full during training** | 10% | Cannot save checkpoints | Phase A6 frees 50-100 GB. Checkpoint thinning during training (keep every 5th epoch). |

### 5.2 Combined Feasibility

Assuming all gates pass and mitigations are applied:

- **Probability of ALL 4 heads at >= 70% of best-ever metrics:** ~25-35%
- **Probability of ALL 4 heads at >= 85% of best-ever metrics:** ~10-20%
- **Probability of 3 of 4 heads at >= 85%:** ~40-50%
- **Probability of 2 of 4 heads at >= 90% (act + pose + PSR, det as pathology):** ~60-70%
- **Probability of complete failure (all heads degrade below 50%):** <5%

### 5.3 Key Difference from Prior Analyses

Files 18-20 estimated <1% probability of unified success because they assumed ConvNeXt-Tiny was the only viable backbone and that the two checkpoints used incompatible architectures. File 17's checkpoint inspection disproves both assumptions. The actual probability is substantially higher because:

1. We start from working checkpoints, not from scratch
2. The backbone is MViTv2-S (proven for all tasks), not ConvNeXt-Tiny (proven for only 2)
3. Weight transplant is architecturally possible (544 shared keys)
4. Progressive training avoids catastrophic forgetting
5. Detection at 0.214 on MViTv2-S is weak but not collapsed -- 100x better than ConvNeXt's 0.00009

---

## 6. Rollback Plan

### 6.1 Tiered Fallback Strategy

**Tier 1: Surgical transplant works, fine-tuning needed (70% probability)**
- Proceed through Phase C. Accept whatever metrics emerge.
- Publish unified model with honest per-head metrics.
- Contribution: "First demonstration of 4-task industrial assembly understanding on a single spatiotemporal backbone."

**Tier 2: Transplant works for act+pose but PSR degrades (20% probability)**
- Freeze PSR head weights from v3.41_safe. Do not include PSR in joint training.
- Train act+pose on frozen backbone. Accept detection as weak.
- Contribution: "Three-task model (act+pose+PSR) with separate PSR head. Detection characterized as pathology."

**Tier 3: Feature distribution shift is too severe (5% probability)**
- Head transplant produces degraded act/pose (Gate G1 fails).
- Option A: Train act+pose from scratch on v3.41 backbone (10-14 days, exceeds deadline buffer).
- Option B: Accept two-checkpoint approach. v3.41_safe for PSR+det, v4_fixed for act+pose.
- Contribution: "Two-architecture comparison demonstrating complementary task strengths."

**Tier 4: Complete failure (5% probability)**
- Publish "Transparent Pathology" paper as described in file 20 Section 3 Tier 4.
- Two-column architecture comparison.
- Multi-task cascade analysis as primary contribution.
- Detection 99.99% cost (on ConvNeXt) vs 79% cost (on MViTv2-S) as architectural insight.
- This is genuinely publishable -- negative results with thorough analysis.

### 6.2 Checkpoint Preservation

Before any training starts:
- SHA256 hash all critical checkpoints
- Copy v4_e0_b200.pth, phase2_e3_b0.pth to `/home/newadmin/swarm-bot/checkpoints/`
- Copy evaluate.py (6966 lines), model.py, losses.py, train.py, industreal_dataset.py from external drive
- This takes 30 minutes and protects against external drive failure

### 6.3 Abort Criteria

Training is aborted immediately if:
1. Any head's primary metric drops >30% from baseline after 3 consecutive epochs (catch catastrophic forgetting)
2. Training loss diverges (NaN or exponential growth) for any head
3. GPU OOM cannot be resolved by reducing batch size to 1 and increasing grad_accum to 32
4. Disk free space drops below 10 GB during training

---

## 7. Final Recommendation

### 7.1 Primary Plan: Execute Phases A-C

**The surgical transplant approach is the fastest path to a unified model.** It leverages existing checkpoint weights rather than training from scratch. The architecture is proven (both checkpoints use MViTv2-S). The strategy is conservative (progressive unfreezing, per-epoch gates, Kendall weighting).

**Expected outcome:** A single MViTv2-S model achieving act=0.30-0.35, det=0.10-0.20, pose=6.5-7.5 deg, psr=0.75-0.85. Three of four heads near or at best-ever levels. Detection as documented multi-task cost.

**Timeline:** 12 days, completing by Aug 13. 9 days buffer before Aug 22 freeze.

**GPU budget:** ~170 hours on RTX 3060. No RTX 5060 Ti required.

### 7.2 The ONE Number to Withdraw Immediately

**det_mAP50_pc = 0.5734** must be withdrawn. It is a biased 250-batch class-balanced subsample artifact (only 15 of 24 classes present). The true multi-task detection mAP50 on the full 38k-frame validation set ranges from 0.00009 (ConvNeXt-Tiny) to 0.214 (MViTv2-S). Any paper including 0.5734 is factually incorrect.

### 7.3 The ONE Architectural Finding That Changes Everything

**File 17's checkpoint inspection proves both v4_fixed and v3.41_safe use the SAME MViTv2-S backbone.** This invalidates the architectural impossibility arguments in files 18-20. A unified model is not merely possible -- the checkpoints are already variants of the same multi-task model at different training stages. The weight merging task succeeded in its actual mission (inspection), even though file 20 predicted it would fail.

### 7.4 What This Means for the Paper

The paper contribution is stronger than either the "forced unified model" or the "two-column defeat" narratives:

1. **Architecture insight:** MViTv2-S (spatiotemporal) supports all 4 heads with varying success. ConvNeXt-Tiny (per-frame CNN) supports at most 2. This is a publishable architectural finding.
2. **Multi-task cost quantification:** Detection drops from 0.995 (single-task) to 0.214 (multi-task on MViTv2-S) to 0.00009 (multi-task on ConvNeXt-Tiny). This hierarchy of degradation is a genuine scientific contribution.
3. **Head transplant methodology:** Selective checkpoint surgery + progressive adaptation as a strategy for combining independently-trained task heads. This has broader applicability beyond this dataset.
4. **Honest negative results:** Activity linear probe on ConvNeXt (0.2169 < 0.2217 baseline) as evidence that ImageNet features lack action information. Detection 99.99% collapse as a quantified gradient conflict pathology.

### 7.5 Action Items (Ordered by Priority)

1. **NOW (zero GPU):** Copy evaluate.py, model.py, losses.py, train.py from external drive. Fix F1=1.0 bug in 4 locations. Free 50-100 GB disk space. (2 hours)
2. **TODAY (4 GPU-hours):** Full re-evaluation of both checkpoints on 38k validation set. Verify baseline metrics. (4 hours)
3. **TOMORROW (2 GPU-hours):** Implement and validate surgical head transplant. Run quick eval. (3 hours)
4. **DAYS 2-7 (120 GPU-hours):** Progressive fine-tuning per Phase C schedule. Monitor all gates. (6 days)
5. **DAY 8 (4 GPU-hours):** Full evaluation of unified model. Report all metrics honestly. (4 hours)

---

## Appendix A: Key Paper Citations from Deep-Search Agents (Pending)

The 4 deep-search background agents (22-25) are still running. Their paper citations will be incorporated when available. Based on partial output from Agent 2 (MTL Architectures), relevant papers include:

- **InternVideo2** (2403.15377): Video foundation model with progressive training (masked token reconstruction -> cross-modal contrastive -> next token prediction). SOTA on 60+ video tasks. Supports multi-task video understanding but does not address 9-channel industrial input.
- Agent 3 (Long-tail training recipes), Agent 4 (9-channel backbones) output pending.

These will supplement but not change the core architecture/training plan above, which is based on empirical checkpoint evidence rather than literature survey.

---

## Appendix B: Evidence Hierarchy

| Level | Evidence Type | Files | Weight |
|-------|--------------|-------|--------|
| 1 (Strongest) | Direct checkpoint inspection with torch.load() | 17 | Definitive |
| 2 | Evaluation JSONs from full pipeline runs | 12, 14, 15 | Strong |
| 3 | Training logs and metrics.json | SOTA history | Strong |
| 4 | Code inspection (config.py, model.py) | Various | Moderate |
| 5 | Agent analysis and inference | 11, 18, 19, 20, 21 | Varies -- contradicted by Level 1 evidence in several cases |

**This synthesis prioritizes Level 1 evidence (file 17's checkpoint inspection) over Level 5 analysis (files 18-20's architectural claims).** When documentation and empirical inspection conflict, empirical inspection wins.

---

**Agent 5 (Final Architecture Synthesist) signing off.** The path is clear. Execute Phase A today.
