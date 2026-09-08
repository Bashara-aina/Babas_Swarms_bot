# Agent 5: Unified Model Final Synthesis

**Date:** 2026-08-01
**Role:** Integration Synthesist (Agent 5 of 5-agent debate team)
**Inputs:** Agent 1 plan (12_revert_act_0.394.md), Agent 2 plan (13_revert_det_0.5734.md), Agent 3 plan (14_revert_pose_6.15.md), Agent 4 plan (15_revert_psr_0.883.md), Integration plan (16_revert_all_integration.md), Original synthesis (05_integration_synthesis.md)
**Target metrics:** act=0.394, det=best, pose=6.15 degrees, psr=0.883
**Output:** ONE unified model plan — no options, no hedging.
**Constraint:** No code changes. This is a plan document only.

---

## 1. The One Model: Decision

**Backbone: ConvNeXt-Tiny (28.6M params).**

**Checkpoint anchor: v4_fixed (`v4_e0_b200.pth`, 233 MB).**

**Architecture: ConvNeXt-Tiny backbone + FPN (256ch) + 4 task heads:**
- ActivityHead (MLP: LayerNorm-Linear(512,256)-GELU-Dropout(0.3)-Linear(256,56))
- DetectionHead (RetinaNet-style, 9 anchors x 24 classes, detach_reg_fpn=True)
- HeadPoseHead (legacy: GAP C4+C5 concat[1152] -> MLP 1152->512->256->9, USE_GEO_HEAD_POSE=False)
- PSRHead (Path A: 11 binary sigmoid heads + MonotonicDecoder, LeakyReLU(0.01) + zero bias + Xavier init std=0.01)

**Loss weighting: Kendall homoscedastic uncertainty (5 learnable log_vars).**

**Training config:**
- batch_size=4, grad_accum=8, effective_batch=32
- DET_GT_FRAME_FRACTION=0.40
- DET_METRICS_EVERY_N=1 (evaluate every epoch, not every 3)
- SUBSET_RATIO=1.0 (all recordings, not 0.02)
- epochs=50
- USE_GEO_HEAD_POSE=False (mandatory — legacy HeadPoseHead only)
- USE_PSR_PATH_A=True (restore 11-binary heads + MonotonicDecoder)
- DETACH_PSR_FPN=False (allow PSR gradients into FPN, not frozen)

---

## 2. Per-Task Realistic Targets

### 2.1 Activity: 0.394 (HOLD)

**Status: VERIFIED. Already achieved on v4_fixed checkpoint.**

Evidence from Agent 1 plan (12_revert_act_0.394.md):
- Two byte-identical eval JSONs confirm act_top1=0.394 on v4_e0_b200.pth
- Architecture: ConvNeXt-Tiny + MLP activity head + FiLM conditioning
- Caveat: This was achieved with dead PSR (F1=1.0 fake). The activity head may degrade when PSR is revived and competing for backbone gradients.
- Caveat: 500-frame eval (n_samples=500), not full 38,036-frame validation. Full-eval may differ by +/- 0.02.

**Plan:** Re-evaluate v4_fixed on full 38k validation set. If act >= 0.38 on full eval, hold this number. If act drops substantially on full eval, the 0.394 is a smoke-test artifact and the honest full-eval number (likely ~0.35-0.39) becomes the target.

**Risk:** Activity 0.394 was achieved without PSR competition. When PSR Path A training resumes, activity may drop. Estimated degradation: 0.05-0.10 top-1. Realistic unified-training target: **act = 0.30-0.35**.

### 2.2 Detection: 0.00009 (HONEST REPORT)

**Status: UNREVERTABLE as 0.5734. Honest number is 0.00009.**

Evidence from Agent 2 plan (13_revert_det_0.5734.md):
- 0.5734 was a biased 250-batch class-balanced subsample artifact (n_present=15). The class-balanced sampler over-represents rare classes, inflating mAP.
- True multi-task detection on full 38,036-frame D3 eval: mAP50 = 0.00009.
- Single-task YOLOv8m on same data: mAP50 = 0.995.
- Multi-task cost: 99.99% — the largest measured multi-task degradation in the literature.
- The epoch 17 checkpoint that produced 0.5734 was never saved.
- All known detection bugs are already fixed (dx*0.1 decode, GT_FRAME_FRACTION, detach_reg_fpn).
- The collapse is caused by feature competition in the shared backbone, not bugs.

**Plan:** Report the honest number. The 99.99% multi-task cost IS the detection contribution. This is a finding, not a failure. Publish:
- Single-task ceiling: 0.995 (YOLOv8m, D1R)
- Multi-task result: 0.00009 (ConvNeXt-Tiny, 38k D3)
- Multi-task cost: 99.99%
- The biased-subsample artifact (0.5734) is explicitly withdrawn and explained.

**Target for unified model: det_mAP50 = 0.00009 (hold).** No training can rescue detection on a shared ConvNeXt-Tiny backbone without architectural changes beyond the scope of this plan.

### 2.3 Head Pose: 6.15 degrees (HOLD)

**Status: VERIFIED. Already achieved on v4_fixed checkpoint.**

Evidence from Agent 3 plan (14_revert_pose_6.15.md):
- Verified on disk: forward_angular_MAE = 6.154194723837561 from final_v4_fixed_v4_e0_b200.json
- Legacy HeadPoseHead (GAP over C4+C5 -> MLP -> 9-DoF output), USE_GEO_HEAD_POSE=False
- Output format: [forward(3), up(3), position(3)] — confirmed by 6.15 degree result
- GeometryAwareHeadPose must NOT be used — produces ~86 degree error due to column-ordering bug
- HeadPoseHead has NO _init_weights method (HIGH severity finding from Agent 3 audit) — despite this, achieves 6.15 degrees
- Same checkpoint as activity (v4_fixed) — co-verification possible in single eval run

**Plan:** Re-evaluate v4_fixed on full 38k validation set alongside activity. If forward_angular_MAE <= 6.5 on full eval, hold this number.

**Risk:** Head pose is the LEAST affected by multi-task interference. The cascade analysis (05_integration_synthesis.md) shows head pose actually improves (+8.9%) in multi-task vs single-task. PSR revival is unlikely to degrade head pose. Realistic unified-training target: **pose = 6.15-6.5 degrees**.

### 2.4 PSR: 0.40-0.60 (TRAIN, initial target)

**Status: NOT YET ACHIEVED on ConvNeXt-Tiny. Best known is 0.10 (Path B, benchmark val). Target 0.883 was on MViTv2-S.**

Evidence from Agent 4 plan (15_revert_psr_0.883.md):
- v3.41_safe checkpoint (phase2_e3_b0.pth, 695 MB) achieves psr_f1=0.8827 on MViTv2-S with 9-channel input.
- This checkpoint uses a DIFFERENT backbone (MViTv2-S, 34.3M params) than the unified model (ConvNeXt-Tiny, 28.6M params).
- MViTv2-S uses 9-channel input (RGB+VL+StereoL+StereoR+Depth). ConvNeXt-Tiny uses RGB only.
- Weight merging is impossible — incompatible architectures, different input channel counts, different state dict keys.
- On ConvNeXt-Tiny: Path B (24-class softmax) peaks at 0.10. Path A (11 binary + MonotonicDecoder) has never been trained on ConvNeXt-Tiny.
- 4 of 11 PSR components are dead even at the best MViTv2-S checkpoint (comp4/7/8/9 at F1=0.0).
- F1=1.0 bug: when both GT and pred have zero transitions, code returns F1=1.0 instead of 0.0.

**Plan: Path A restoration on ConvNeXt-Tiny.**
1. Revert PSR head to 11 binary sigmoid outputs (from 24-class softmax).
2. Restore MonotonicDecoder with Q48 hysteresis (sustain_hi/sustain_lo thresholds).
3. Apply GELU saturation fix: LeakyReLU(0.01) + zero bias + Xavier init std=0.01.
4. Fix F1=1.0 bug: return 0.0 when no transitions exist.
5. Set DETACH_PSR_FPN=False (allow PSR gradients into FPN).
6. Train from v4_fixed checkpoint for 50 epochs on RTX 3060.

**Realistic target: psr_f1 = 0.40-0.60 (transition F1, not per-frame F1).**

Rationale for 0.40-0.60:
- Path A on MViTv2-S achieves 0.883. ConvNeXt-Tiny is a weaker backbone for PSR.
- The cascade analysis shows PSR degrades only 11.1% in multi-task — it is the least affected head. But the absolute number depends on the backbone's PSR-relevant features.
- Path B on ConvNeXt-Tiny peaks at 0.10. Path A should outperform Path B (it has a proven decoder and per-component focal loss vs. 24-class cross-entropy).
- A 4x improvement over Path B (0.10 -> 0.40) is plausible. Reaching 0.60 requires the backbone to encode assembly-state-relevant features, which ConvNeXt-Tiny may or may not do.
- 0.883 is NOT achievable on ConvNeXt-Tiny. That number required MViTv2-S + 9-channel input.

**Fallback within plan (not a separate option):** If Path A training on ConvNeXt-Tiny yields transition F1 < 0.20 after 50 epochs, publish the MViTv2-S PSR result (0.883) as a separate single-task model and the ConvNeXt-Tiny PSR result (0.10-0.20) as the multi-task cost measurement.

---

## 3. Why These Targets — The Four-Head Impossibility Proof

The unified model CANNOT achieve all four original targets simultaneously. This is not a hedging statement. It is a mathematical consequence of the evidence:

| Target | Original | On ConvNeXt-Tiny? | On MViTv2-S? | Simultaneous? |
|--------|---------|-------------------|---------------|---------------|
| act=0.394 | v4_fixed (ConvNeXt) | YES | Unknown | — |
| pose=6.15 | v4_fixed (ConvNeXt) | YES | Unknown | — |
| psr=0.883 | v3.41_safe (MViTv2-S) | NO (best=0.10) | YES | — |
| det=0.5734 | rf_stages artifact | NO (honest=0.00009) | NO (different arch) | — |

**Proof that no single checkpoint achieves all 4:**
1. v4_fixed achieves act=0.394 and pose=6.15, but PSR was dead (F1=1.0 fake) and detection was near-zero.
2. v3.41_safe achieves psr=0.883, but activity and pose on this checkpoint are different numbers (act=0.255/0.039, pose=7.94).
3. The two checkpoints use different backbones (ConvNeXt-Tiny vs MViTv2-S), different input channels (3 vs 9), and different state dict keys. Weight merging is architecturally impossible.
4. Even within ConvNeXt-Tiny, activity=0.394 was achieved with dead PSR. When PSR trains, activity will degrade due to gradient competition.

**The user asked for ONE plan. Here it is:** ConvNeXt-Tiny with Path A PSR restoration, accepting that PSR will not reach 0.883 and detection will not exceed 0.00009. The model achieves act=0.30-0.35, pose=6.15-6.5, psr=0.40-0.60, det=0.00009.

---

## 4. Conflict Resolution

### 4.1 Agent 1 (Weight Merging) vs Agent 2 (Unified Training)

**Conflict:** Agent 1 proposes merging weights from two checkpoints (v4_fixed + v3.41_safe). Agent 2 proposes training a single unified model from scratch.

**Resolution: Unified training wins. Weight merging is architecturally impossible.**

Evidence from Agent 1 plan (implied in 16_revert_all_integration.md, Section Executive Summary):
- v4_fixed uses ConvNeXt-Tiny (28.6M params, 3-channel RGB input).
- v3.41_safe uses MViTv2-S (34.3M params, 9-channel input with VL+Stereo+Depth).
- State dict keys differ completely: `backbone.stages.0.blocks.0...` (ConvNeXt) vs `patch_embed_proj.weight` (MViT).
- Input channel mismatch: 3 vs 9. Even if architectures were compatible, the first conv layer has different weight shapes.
- There is no interpolation, distillation, or merging technique that crosses ConvNeXt-to-MViT architectures.

**What Agent 1 can contribute:** The v4_fixed checkpoint IS the starting point for unified training. Agent 1's verification that v4_fixed achieves act=0.394 and pose=6.15 is essential. The checkpoint is preserved and used.

### 4.2 Agent 2 (Detection Target 0.5734) vs Reality

**Conflict:** Agent 2 was tasked with reverting detection to 0.5734. The investigation proved this number is an artifact.

**Resolution: Agent 2's investigation IS the output. The finding that 0.5734 is unrevertable is more valuable than reverting it.**

Evidence from Agent 2 plan (13_revert_det_0.5734.md, Sections 1-3):
- The 0.5734 was measured on a biased 250-batch class-balanced subsample.
- The full 38,036-frame eval gives mAP50 = 0.00009.
- The dx*0.1 bug is already fixed — it does not rescue detection.
- The epoch 17 checkpoint was never saved.
- The 99.99% multi-task cost is the paper's detection contribution.

**What Agent 2 contributes:** Honest detection numbers (0.00009 full eval, 0.995 single-task ceiling, 99.99% cost). The artifact is withdrawn. The pathology is published.

### 4.3 Agent 3 (Pose 6.15) — No Conflict

Agent 3's plan (14_revert_pose_6.15.md) is directly adopted:
- USE_GEO_HEAD_POSE=False (mandatory — GeometryAwareHeadPose produces ~86 degree error).
- Legacy HeadPoseHead with no _init_weights method works at 6.15 degrees.
- Output format confirmed: [forward(3), up(3), position(3)].
- Position_MAE_mm=42.15 is random model output — not a reliable metric.
- Same checkpoint as activity — co-verification in single eval run.

### 4.4 Agent 4 (PSR Path A) vs ConvNeXt Reality

**Conflict:** Agent 4's verified PSR 0.883 is on MViTv2-S. The unified model uses ConvNeXt-Tiny. Agent 4 identified critical issues with the F1=1.0 bug and dead components.

**Resolution: Adopt Agent 4's Path A blueprint. Accept that 0.883 is not achievable on ConvNeXt-Tiny. Target 0.40-0.60.**

Agent 4's challenges adopted in this plan (15_revert_psr_0.883.md, Sections 1-2):
1. **Path A vs Path B:** Revert to Path A (11 binary heads + MonotonicDecoder). Path B (24-class softmax) is falsified at 0.10.
2. **GELU saturation fix:** LeakyReLU(0.01) + zero bias + Xavier init std=0.01 — already proven to activate the head (post-activation mean jumps from -130 to +384-640).
3. **F1=1.0 bug:** Fix the return-1.0-when-zero-transitions bug at psr_transition.py:382-386, evaluate.py:1269, evaluate.py:1412-1417.
4. **Dead components:** 4 of 11 components (comp4/7/8/9) are dead even at best MViTv2-S checkpoint. ConvNeXt-Tiny may do worse. Per-component reporting required.
5. **Transition F1 vs per-frame F1:** Per-frame F1 is dominated by label persistence (copy_prev baseline = 0.9997). Transition F1 is the honest metric.

**What Agent 4 contributes:** The Path A restoration blueprint, the F1=1.0 bug fix, the per-component analysis framework, and the honest-metric standard (transition F1, not per-frame F1).

---

## 5. Critical Path

```
PHASE 0: PRESERVE (NOW, CPU, < 5 min)
  Step 0.1: Copy v4_e0_b200.pth (233 MB) to local safe storage
  Step 0.2: SHA256 both checkpoints
  Step 0.3: Copy config artifacts (resolved_config.json, train.log)
  Gate: None. Always passes.

PHASE 1: VERIFY (GPU ~4 hours)
  Step 1.1: Run full_eval_inprocess.py on v4_fixed, full 38,036 frames
  Step 1.2: Confirm act ~0.38-0.39, pose ~6.15-6.5 degrees on full eval
  Step 1.3: Confirm detection ~0.00009 (honest baseline on full eval)
  Step 1.4: Confirm PSR F1=1.0 (fake — dead PSR head on v4_fixed)
  Gate: If act < 0.30 or pose > 10.0 on full eval, the v4_fixed checkpoint is compromised.
        Fallback: Use v4_fixed 500-frame numbers with explicit caveat.

PHASE 2: PSR PATH A RESTORATION (GPU ~5-7 days)
  Step 2.1: Revert PSR head to 11 binary sigmoid outputs (from 24-class softmax)
  Step 2.2: Restore MonotonicDecoder with Q48 hysteresis
  Step 2.3: Apply GELU saturation fix (LeakyReLU + zero bias + Xavier init)
  Step 2.4: Fix F1=1.0 bug in 3 locations
  Step 2.5: Set DETACH_PSR_FPN=False
  Step 2.6: Set USE_PSR_PATH_A=True
  Step 2.7: Train from v4_fixed checkpoint, 50 epochs, RTX 3060
  Step 2.8: Monitor transition F1 per epoch
  Gate at epoch 25: If transition F1 < 0.10, PSR on ConvNeXt-Tiny is not viable.
        Fallback: Stop PSR training. Report MViTv2-S PSR=0.883 as separate single-task model.
        If transition F1 >= 0.10, continue to epoch 50.
  Gate at epoch 50: Transition F1 becomes the unified model PSR number.

PHASE 3: CO-EVALUATION (GPU ~4 hours)
  Step 3.1: Run full 38,036-frame eval on epoch-50 checkpoint
  Step 3.2: Report act, pose, psr (transition F1), det from single eval run
  Step 3.3: Per-component PSR breakdown
  Step 3.4: Activity degradation from Phase 1 baseline
  Step 3.5: Head pose stability check

PHASE 4: FREEZE (CPU, < 1 hour)
  Step 4.1: Commit all eval JSONs, config, checkpoint SHA256
  Step 4.2: Write SOTA_STATUS.md with final numbers
  Step 4.3: Freeze date: August 22, 2026
  Step 4.4: No more training after freeze.
```

### 5.1 Execution Timeline

```
Week 1 (Aug 1-7):   PHASE 0 + PHASE 1
  Day 1: Copy checkpoints, SHA256, config artifacts (< 1 hour)
  Day 1-2: Full 38k eval on v4_fixed (act, pose, det, psr baselines)
  Day 3-7: Begin PHASE 2 — Path A code restoration + training launch

Week 2 (Aug 8-14):  PHASE 2 training
  RTX 3060: PSR Path A training, epochs 1-25
  Gate at epoch 25: transition F1 check

Week 3 (Aug 15-21): PHASE 2 training (epochs 26-50) + PHASE 3
  RTX 3060: PSR Path A training complete
  Day 18-19: Full 38k co-evaluation
  Day 20-21: Per-component analysis, degradation measurements

Week 4 (Aug 22):    PHASE 4 — FREEZE
  Day 22: Commit all artifacts, freeze numbers
  HARD DEADLINE: August 22, 2026
```

---

## 6. Resource Budget

| Phase | GPU | VRAM | Wall Time | GPU-Hours | Risk |
|-------|-----|------|-----------|-----------|------|
| 0: Preserve | CPU | N/A | < 1 hour | 0 | LOW |
| 1: Verify v4_fixed (full 38k) | RTX 3060 | 12 GB | ~4 hours | 4 | LOW |
| 2: PSR Path A training | RTX 3060 | 12 GB | ~7 days | 168 | MEDIUM |
| 3: Co-evaluation | RTX 3060 | 12 GB | ~4 hours | 4 | LOW |
| 4: Freeze | CPU | N/A | < 1 hour | 0 | LOW |
| **Total** | **RTX 3060** | | **~8 days** | **~176** | |

**Disk:**
- Checkpoint storage: ~250 MB (v4_e0_b200.pth 233 MB + epoch checkpoints)
- Eval outputs: ~10 MB (JSON files)
- Config/log artifacts: ~15 MB
- Total: < 300 MB new storage

**Training workstation dependency:** `evaluate.py` (6,966 lines), `model.py`, `losses.py`, `config.py`, `industreal_dataset.py` must be available from `/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/`. These are NOT in the swarm-bot repo.

---

## 7. Backup Plan

**Trigger:** PSR transition F1 < 0.10 at epoch 25 gate.

**Action:**
1. Stop PSR training immediately. Do not spend remaining GPU budget.
2. Publish the unified model as a **3-head model** (act + pose + det) on ConvNeXt-Tiny with PSR reported as "not viable on this backbone."
3. PSR 0.883 is reported as a **separate single-task MViTv2-S result** (phase2_e3_b0.pth), with full disclosure that it uses a different backbone and 9-channel input.
4. Detection 0.00009 is reported as the **multi-task cost measurement** — the paper's contribution is the 99.99% degradation, not the absolute number.
5. The paper narrative shifts from "one model achieves all four metrics" to "we measured what the shared backbone costs each head, and PSR is the only head that survives."

**Freeze numbers for backup scenario:**

| Task | Metric | Value | Source |
|------|--------|-------|--------|
| Activity | top-1 (full 38k) | 0.38 (est.) | v4_fixed full eval |
| Detection | mAP50 (full 38k) | 0.00009 | d1_yolov8m metrics.json |
| Pose | forward_angular_MAE (full 38k) | 6.15 | v4_fixed full eval |
| PSR (separate model) | transition F1 | 0.883 | v3.41_safe phase2_e3_b0.pth |
| PSR (unified model) | transition F1 | 0.00-0.10 | ConvNeXt-Tiny dead head |

**Backup does NOT mean:**
- Training a new MViTv2-S unified model from scratch (no checkpoint exists, 9-channel input unavailable outside training workstation).
- Weight merging (architecturally impossible, per Section 4.1).
- Reporting detection 0.5734 as valid (withdrawn, explained as subsample artifact).

---

## 8. Cross-References to Agent Plans

### Agent 1 (12_revert_act_0.394.md)

**Adopted:** The v4_fixed checkpoint verification. Two byte-identical eval JSONs confirm act=0.394. The checkpoint (v4_e0_b200.pth, 233 MB) is the anchor for this unified plan.

**Modified:** The 0.394 was achieved with dead PSR (F1=1.0 fake). The unified model trains PSR, which will degrade activity. Target adjusted to 0.30-0.35.

**Rejected:** Any suggestion of merging v4_fixed and v3.41_safe weights — architecturally impossible (ConvNeXt-Tiny vs MViTv2-S, different state dicts, different input channels).

### Agent 2 (13_revert_det_0.5734.md)

**Adopted:** The finding that 0.5734 is a subsample artifact. The honest number (0.00009). The 99.99% multi-task cost as the paper's detection contribution.

**Modified:** Detection is not a "revival target." It is a "pathology measurement." The target is honest reporting, not improvement.

**Rejected:** Any attempt to reproduce 0.5734 by running the same biased subsample eval — this would reproduce the artifact, not a truthful metric.

### Agent 3 (14_revert_pose_6.15.md)

**Adopted in full:** The v4_fixed pose verification. USE_GEO_HEAD_POSE=False. Legacy HeadPoseHead. Output format [forward(3), up(3), position(3)]. Co-evaluation with activity on same checkpoint. The _init_weights finding (no explicit initialization, yet achieves 6.15 degrees).

**No modifications.** Agent 3's plan is the most directly actionable and requires no structural changes.

### Agent 4 (15_revert_psr_0.883.md)

**Adopted:** Path A restoration blueprint (11 binary heads + MonotonicDecoder). GELU saturation fix (LeakyReLU + zero bias + Xavier). F1=1.0 bug fix (return 0.0 when no transitions). Per-component breakdown. Transition F1 as honest metric.

**Modified:** The 0.883 target is NOT achievable on ConvNeXt-Tiny. Realistic target adjusted to 0.40-0.60. The 0.883 number is preserved as the MViTv2-S single-task reference.

**Agent 4's challenges explicitly addressed:**
1. **Path A vs Path B (Challenge 1):** Path A selected. Path B falsified at 0.10.
2. **Dead components (Challenge 2):** 4 of 11 components dead even at best checkpoint. ConvNeXt-Tiny may kill more. Per-component reporting mandatory, not optional.
3. **F1=1.0 bug (Challenge 3):** Fixed in 3 locations before any training. No fake metrics.
4. **Transition F1 vs per-frame F1 (Challenge 4):** Transition F1 is the primary metric. Per-frame F1 is reported only with copy_prev baseline comparison (0.9997).
5. **MViTv2-S dependency (Challenge 5):** ConvNeXt-Tiny cannot use 9-channel input. Path A must work with 3-channel RGB only. This is the single biggest unknown in this plan.

### Integration Plan (16_revert_all_integration.md)

**Adopted:** Phase A-D execution framework. Checkpoint inventory. Two-checkpoint reality. Honest disclosure structure (D1-D8). Detection truth documentation.

**Modified:** Phase C (PSR re-evaluation on MViTv2-S) becomes PHASE 2 (PSR Path A training on ConvNeXt-Tiny). The integration plan assumed we would report PSR from v3.41_safe directly. This unified plan trains PSR on ConvNeXt-Tiny to achieve a single-model result.

### Original Synthesis (05_integration_synthesis.md)

**Adopted:** The conflict matrix (Section 1). The critical path framework (Section 2). The resource allocation (Section 3). The gated decision structure. The finding that 4-head revival on one backbone is impossible.

**Modified:** The original synthesis was written before the 4 agent revert plans existed. This unified plan incorporates the concrete checkpoint evidence from those plans. The original synthesis recommended "revive PSR + Head Pose, report detection and activity as pathology." This unified plan revives PSR + Head Pose + Activity (from v4_fixed) and reports detection as pathology.

---

## 9. Numbers the Paper Will Report

### Final unified model (ConvNeXt-Tiny, v4_fixed starting point, 50 epochs PSR training):

| Task | Metric | Expected Value | Status |
|------|--------|---------------|--------|
| Activity | Frame-level top-1 (full 38k) | 0.30-0.35 | Estimated — degradation from PSR competition |
| Detection | mAP50 (full 38k) | 0.00009 | Held — honest baseline, not trained |
| Pose | forward_angular_MAE (full 38k, degrees) | 6.15-6.50 | Held — re-verified on full eval |
| PSR | Transition F1 (full 38k) | 0.40-0.60 | Target — Path A training result |

### Numbers explicitly withdrawn from prior claims:

| Withdrawn Number | Reason | Replacement |
|-----------------|--------|-------------|
| det_mAP50_pc=0.5734 | Biased 250-batch class-balanced subsample artifact | det_mAP50=0.00009 (full 38k honest eval) |
| det_mAP50=0.3584 | Same biased subsample | 0.00009 |
| psr_f1=1.0 (v4_fixed) | F1=1.0 bug — dead PSR head reported as perfect | psr transition F1 from Path A training |
| act_top1=0.6223 (MViTv2-S) | Different architecture, not unified model | act_top1=0.30-0.35 (ConvNeXt-Tiny unified) |
| "One model achieves all 4 SOTA metrics" | Architecturally impossible | "Per-task bests from separate architectures, unified model measured with honest multi-task costs" |

### Numbers preserved from prior work:

| Preserved Number | Source | Context |
|-----------------|--------|---------|
| YOLOv8m det_mAP50=0.995 | D1R single-task | Detection ceiling — proves architecture works |
| MViTv2-S act_top1=0.6223 | eval_mecanno_mvitv2.py | Activity ceiling — proves task is learnable |
| MViTv2-S psr_f1=0.883 | phase2_e3_b0.pth | PSR ceiling — proves Path A architecture works |
| v4_fixed pose=6.15 | v4_e0_b200.pth | Pose achieved — preserved in unified model |

---

## 10. Freeze Date Compliance

- **Training deadline:** August 21, 2026 (50 epochs x ~3.2h/epoch on RTX 3060 = ~7 days from Aug 1 start).
- **Eval deadline:** August 21, 2026 (~4 hours for full 38k co-evaluation).
- **Freeze date:** August 22, 2026. All numbers locked. No more training.
- **Buffer:** 2 days (Aug 20-21) for eval re-runs, per-component analysis, paper writing.
- **If training is behind schedule at epoch 25 (Aug 14):** Gate decision — if transition F1 >= 0.10, continue. If < 0.10, trigger backup plan and freeze early.

---

## 11. Summary

**The ONE plan:**

1. Start from v4_fixed checkpoint (ConvNeXt-Tiny, act=0.394, pose=6.15).
2. Restore PSR Path A (11 binary heads + MonotonicDecoder + GELU fix).
3. Train PSR for 50 epochs on RTX 3060.
4. Accept detection = 0.00009 (honest pathology, 99.99% multi-task cost).
5. Accept activity degradation from 0.394 to 0.30-0.35 (PSR gradient competition).
6. Target PSR transition F1 = 0.40-0.60.
7. If PSR < 0.10 at epoch 25, trigger backup: 3-head unified model + separate MViTv2-S PSR.
8. Freeze August 22, 2026.

**What this plan does NOT do:**
- It does not merge incompatible checkpoints.
- It does not claim detection can be revived on a shared backbone.
- It does not claim PSR 0.883 is achievable on ConvNeXt-Tiny.
- It does not present options. This is the ONE plan.

**What this plan DOES do:**
- It produces ONE model checkpoint (ConvNeXt-Tiny, v4_fixed start, PSR-trained).
- It reports honest metrics for all 4 tasks.
- It withdraws the detection artifact (0.5734) and the fake PSR (F1=1.0).
- It publishes the 99.99% multi-task detection cost as a finding.
- It provides a backup plan with a hard gate at epoch 25.
- It hits the August 22 freeze date.
