# Agent 5: Adversarial Adversary -- Final Synthesis

**Date:** 2026-08-01
**Role:** Agent 5 (Adversarial Adversary) of 5-agent debate team
**Inputs:** Plans 01-06, Debate files 07-10, cascade_table.md, SOTA_STATUS.md, config.py, training logs
**Constraint:** NO code changes. Strategy document only.
**Guidance from user:** "HONEST assessment. Don't be optimistic."

---

## 0. The Brutal Truth Up Front

The 5 revival plans describe a 4-task restoration on ConvNeXt-Tiny. The measured evidence says this is impossible. Here is what the data actually supports:

| Task | Historical Best | Architecture | ConvNeXt Signal? | Revivable on ConvNeXt? |
|------|----------------|--------------|------------------|----------------------|
| Pose | 6.15 deg | ConvNeXt-Tiny + legacy HeadPoseHead | YES | YES (code fix, 2 hours) |
| PSR | 0.883 F1 | MViTv2-S + 9-channel + Path A | UNKNOWN (Path A never tested on ConvNeXt) | MAYBE (Path A restoration experiment) |
| Activity | 0.6223 top-1 | MViTv2-S (16-frame 3D clips) | NO (linear probe 0.2169 < majority baseline 0.2217) | NO |
| Detection | 0.995 mAP50 | YOLOv8m (single-task) | NO (0.00009 mAP50, 99.99% collapse) | NO |

**At most 2 of 4 tasks are revivable.** The "4-task revival" framing is false advertising. The honest paper is: 1 bug-fix success (Pose), 1 architecture-restoration experiment (PSR), 2 characterized pathologies (Activity, Detection).

---

## 1. Per-Plan Failure Mode Analysis

### 1.1 Activity Revival -- Worst Case

**Target:** 0.6223 top-1 (MViTv2-S) or 0.25-0.35 verb-group (ConvNeXt)
**Current:** 0.0236 per-frame, 0.028 clip-level on ConvNeXt-Tiny

**Worst-case failure mode:** The ConvNeXt-Tiny backbone, pretrained on static ImageNet-1K images, fundamentally cannot learn action-discriminative features regardless of training duration, loss function, or head architecture.

**Evidence this worst case is the base case:**
- Linear probe on frozen ConvNeXt features: **0.2169 top-1 vs 0.2217 majority-class baseline** (always predict class 8). The backbone encodes ZERO activity-relevant information.
- 41 of 69 classes have zero accuracy. 48/74 classes have <10 training frames.
- ImageNet pretraining encodes object identity (what is this?), not motion/action (what is happening?).
- The plan's own admission (01_activity_revival.md line 397): "The biggest risk is that this plan is attempting the impossible."

**Probability of catastrophic failure (< 0.10 verb-group top-1):** ~80%
**Probability of hitting 0.25-0.35 (Strategy A target):** ~15%
**Probability of hitting 0.6223 on ConvNeXt-Tiny:** <1%

**Earliest warning signal:** If training loss plateaus within first 5 epochs and validation accuracy stays at majority-class baseline levels, abort. The linear probe already proves the backbone has zero signal -- training cannot create information that doesn't exist in the features.

**What happens if it fails:** Activity is abandoned on ConvNeXt-Tiny. The paper contribution becomes the linear probe result as negative evidence that ImageNet features lack action information. Strategy B (MViTv2-S separate model) requires a new project, not a revival.

---

### 1.2 Detection Revival -- Worst Case

**Target:** 0.5734 mAP50_pc (claimed) or >= 0.30 (honest)
**Current:** 0.00009 mAP50 (full D3 eval, verified by cascade_table.md)

**Worst-case failure mode:** Detection is architecturally impossible on the ConvNeXt-Tiny multi-task backbone. The 99.99% collapse is not a training artifact -- it is a fundamental limitation of a classification backbone serving a detection head in a multi-task setting.

**Evidence this worst case is the base case:**
- True multi-task detection mAP50 = **0.00009** (cascade_table.md). The 0.5734 claim is a biased 250-batch subsample artifact (n_present=15 of 24 classes).
- det_mAP50_pc = **0.0** from in-repo metrics (d1_yolov8m/metrics.json).
- YOLOv8m single-task achieves 0.995. The 99.99% multi-task cost is the cleanest pathology measurement in the entire paper.
- DET_GT_FRAME_FRACTION=0.40 exists in code (PR #7) but defaults OFF. Even with it enabled, the best case from a classification backbone doing detection in multi-task mode is unclear.
- Single-task ConvNeXt D3 baseline was still at epoch 43/99 as of July 7. If single-task also fails (< 0.30), the backbone itself cannot detect.

**Probability of catastrophic failure (mAP50 < 0.10 multi-task):** ~80%
**Probability of hitting 0.30-0.45 via distillation:** ~20% (gated on single-task baseline being decent)
**Probability of hitting 0.5734 (the claimed but fake target):** <2%
**Probability of hitting 0.50+:** <5%

**Earliest warning signal:** The single-task ConvNeXt D3 detection baseline is the gating experiment. If single-task mAP50 < 0.10, abort all multi-task detection work immediately. If single-task mAP50 is 0.10-0.30, distillation may help marginally but won't close a 10x+ gap. Only if single-task mAP50 > 0.50 does multi-task revival have a chance.

**What happens if it fails:** Detection is handled by companion YOLOv8m (0.995 mAP50). The paper contribution becomes: "Single-task detection is near-perfect (0.995). Multi-task detection collapses to 0.00009. This is a 99.99% cost that motivates decoupled architectures." This is a stronger finding than any partial revival.

---

### 1.3 PSR Revival -- Worst Case

**Target:** 0.883 F1 (Path A on MViTv2-S) or 0.80+ (Path A on ConvNeXt)
**Current:** 0.10 F1 (Path B, 24-class softmax, architectural failure)

**Worst-case failure mode:** ConvNeXt-Tiny per-frame features lack the temporal and depth information that MViTv2-S's 16-frame 3D clips and 9-channel input provided. Path A restoration (11 binary heads + MonotonicDecoder) cannot recover because the backbone features simply don't contain state-transition information.

**Evidence this is a real risk:**
- The 0.883 was achieved on MViTv2-S with 9-channel input (RGB+VL+StereoL+StereoR+Depth), not ConvNeXt-Tiny with RGB-only per-frame features.
- 4 of 11 components are DEAD even at the best MViTv2-S Path A checkpoint (comp4=0.000, comp7=0.000, comp8=0.000, comp9=0.000). These components may be fundamentally undetectable from visual features.
- PSR requires detecting state transitions -- temporal events. A per-frame CNN sees static images. The MonotonicDecoder smooths per-frame predictions, but it cannot create information that doesn't exist in the features.
- The current Path B (24-class softmax) produces 0.10 F1. The gap to 0.883 is 8.8x. Architecture restoration alone may not bridge this on a weaker backbone.
- HeadPoseFiLM contamination (see Section 2) may further degrade PSR features after the Pose column fix.

**Probability of catastrophic failure (transition F1 < 0.20):** ~25%
**Probability of hitting 0.50-0.79 (partial recovery):** ~40%
**Probability of hitting 0.80+:** ~25%
**Probability of hitting 0.883:** <10%

**Earliest warning signal:** Transition F1 on the repaired checkpoint (LeakyReLU + zero bias). If transition F1 < 0.20 after repair, the head is fundamentally limited on ConvNeXt. Do NOT launch Kendall ablation. Do NOT invest further GPU time. Publish per-frame F1 with honest persistence-baseline comparison.

**What happens if it fails:** Publish per-frame F1 (0.70-0.75) with copy_prev baseline (0.9997) comparison. The finding that per-frame F1 is persistence-dominated is itself a methodology contribution. Alternatively, use the existing MViTv2-S checkpoint (0.883) as the PSR result, acknowledging ConvNeXt-Tiny PSR as a limitation.

---

### 1.4 Pose Refinement -- Worst Case

**Target:** < 6.15 degrees angular MAE
**Current:** ~86 degrees (random-level due to column-ordering bug)

**Worst-case failure mode:** The column-ordering fix in GeometryAwareHeadPose.to_legacy_9dof() works (reducing error from 86 to < 20 degrees) but HeadPoseFiLM contamination prevents recovery to 6.15 degrees. The FiLM layers, trained with corrupted head pose vectors (right-vector fed as forward-vector), have parameters that are wrong for correct inputs. After the column fix, these corrupted FiLM parameters degrade shared C5 backbone features, damaging all other tasks.

**Evidence this is a real risk:**
- FiLM layers modulate C5 backbone features with head pose vectors. During training with broken column ordering, FiLM parameters adapted to corrupted inputs.
- After fixing the column ordering, FiLM layers receive correct vectors but have wrong parameters. The backbone features modulated by FiLM may produce degraded representations.
- The v4_fixed checkpoint that achieved 6.15 degrees had a completely dead PSR head (only component 0 active, all others F1=0.0). This suggests a severe multi-task trade-off existed even before the GeometryAwareHeadPose was introduced.

**Probability of fixing the 86-degree bug (< 20 degrees):** ~85%
**Probability of hitting < 6.15 degrees:** ~25%
**Probability of fix failing entirely (error > 20 degrees):** ~15% (root cause misidentified or FiLM contamination too severe)

**Earliest warning signal:** Run the 5-minute sanity check: `full_eval_inprocess.py --max-batches 10` on the best existing pose checkpoint. If forward_angular_MAE is ~86 degrees, column ordering is confirmed broken. After the fix, if angular MAE drops significantly (to < 20 degrees), the fix is correct. If it stays > 20 degrees, the root cause is misidentified.

**What happens if it fails:** The trivial fallback exists: set `USE_GEO_HEAD_POSE=False` to restore legacy HeadPoseHead. If the legacy head code still exists in the external-drive model.py, this instantly recovers v4_fixed-level performance (~6.15 degrees). This is a 1-line config change with zero GPU cost. If the legacy code was deleted, Strategy D (full retraining from scratch) is 5-7 days on RTX 3060.

**This is the LEAST LIKELY plan to fail catastrophically.** The root cause is a code bug (column ordering), not an architecture limitation. The target was already achieved on the SAME backbone (ConvNeXt-Tiny). A trivial fallback exists. The fix requires 2 hours of code changes, no GPU training.

---

### 1.5 Integration Synthesis -- Worst Case

**Target:** Coordinated multi-task model with PSR + Pose revived; Activity + Detection as characterized pathologies.
**Current:** All plans in various stages of incompleteness.

**Worst-case failure mode:** The integration plan's critical path assumption -- that PSR and Pose fixes can proceed independently on the same backbone -- is violated by HeadPoseFiLM contamination. The Pose column fix changes the FiLM inputs to shared C5 features, potentially degrading PSR performance that was trained with the corrupted FiLM parameters. The two "revivable" tasks conflict.

**Evidence:**
- HeadPoseFiLM operates on shared C5 backbone features. PSR also uses these C5 features (via FPN).
- After the Pose fix, FiLM parameters are wrong for correct inputs. Resuming PSR training with corrupted FiLM parameters produces degraded features.
- The v4_fixed checkpoint proves the trade-off was already severe: good pose (6.15 deg) came with completely dead PSR (only component 0 active).

**Probability of integration succeeding (PSR + Pose both revived):** ~15% (requires both to work individually AND not conflict)
**Probability of 1 of 2 succeeding:** ~60% (Pose most likely, PSR uncertain)
**Probability of 0 of 2 succeeding:** ~25%

---

## 2. Cascade Risk Analysis

### 2.1 HeadPoseFiLM Contamination (CRITICAL -- cross-task, unaddressed)

**Mechanism:** The head pose tensor feeds into FiLM (Feature-wise Linear Modulation) layers that modulate C5 backbone features. During training with the broken column ordering, these vectors were corrupted (right-vector as forward, forward as up). FiLM parameters adapted to these corrupted inputs.

**Cascade chain after Pose column fix:**
```
Pose column fix (correct vectors into FiLM)
  -> FiLM parameters are WRONG for correct inputs
    -> C5 backbone features are modulated incorrectly
      -> PSR head receives degraded C5 features -> PSR F1 may DROP below pre-fix level
      -> Activity head receives degraded C5 features -> already broken, gets worse
      -> Detection head receives degraded C5 features -> already broken, gets worse
      -> Pose head itself: immediately benefits from correct column ordering (FiLM is additive on top of already-computed features)
```

**Severity:** HIGH. This is the only cross-task risk that can make a "fixed" task (Pose) BREAK another "revivable" task (PSR).

**NO plan addresses this.** Plan 04 mentions it as Strategy C (2 days resume training for FiLM adaptation), but:
- Plan 03 (PSR) does not account for FiLM contamination at all
- Plan 01 (Activity) does not account for it
- Plan 02 (Detection) does not account for it
- Plan 05 (Integration) assumes PSR and Pose fixes are independent

**Mitigation:** After the Pose column fix, run a full multi-task eval BEFORE resuming PSR training. If PSR metrics degrade post-fix, the FiLM contamination is confirmed. The only fix is to resume multi-task training for 2+ days to let FiLM parameters adapt, but this risks un-fixing the Pose head if the training objective re-corrupts it.

### 2.2 GPU Serialization Cascade (HIGH -- resource, addressed by Agent 2)

**Mechanism:** RTX 3060 (12 GB) is the only GPU for PSR training (7 days), Pose eval (2 hours), and Activity Strategy A (2-3 days). These must be serialized.

**Cascade:**
```
PSR Phase 2 (7 days, RTX 3060)
  -> Blocks Activity Strategy A (2-3 days) on same GPU
    -> Blocks Kendall ablation (3 days) on same GPU
      -> If PSR fails gate (transition F1 < 0.20), the 7 days were wasted and Activity is delayed
        -> Activity may miss the Aug 22 freeze date
```

**Severity:** HIGH. Agent 2 (08_debate_resources.md) identified this and proposed parallel execution: PSR on RTX 3060 + Detection distillation on RTX 5060 Ti. But if Detection gates to Strategy B (pathology only, no training), RTX 5060 Ti is idle during PSR training -- a scheduling waste.

**Mitigation:** Run Pose eval FIRST (2 hours, RTX 3060) before PSR Phase 2 starts. This gives immediate results on the most likely-to-succeed plan. Then run PSR Phase 2. If PSR fails the transition-F1 gate, immediately pivot to Activity on RTX 3060.

### 2.3 Checkpoint Chain Corruption (MEDIUM -- addressed by Agent 4)

**Mechanism:** The rf_stages/best.pth checkpoint was promoted at epoch 11 by a broken AC-1 metric. Multiple plans reference this checkpoint as their starting point. If the checkpoint is corrupted by the broken metric, all downstream results are contaminated.

**Cascade:**
```
rf_stages/best.pth (epoch 11, AC-1 contaminated)
  -> PSR repair resumes from this checkpoint
    -> PSR transition F1 is evaluated against contaminated features
      -> Activity retraining uses same contaminated checkpoint
        -> All paper numbers are invalid
```

**Mitigation:** Use crash_recovery.pth (epoch 18, not AC-1 contaminated) instead of best.pth. Verify checkpoint lineage with SHA256 hashes. Agent 4's freeze protocol (every number traces to a specific checkpoint identified by commit hash + config hash) is the correct defense.

### 2.4 External Drive Dependency (CRITICAL -- structural, unaddressed)

**Mechanism:** 6 critical Python files exist ONLY on the external training workstation at `/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/`:
- `src/models/model.py` -- needed by all 4 plans
- `src/training/losses.py` -- needed by all 4 plans
- `src/evaluation/evaluate.py` -- needed by all 4 plans
- `src/training/train.py` -- needed by Plans 02, 03
- `src/data/industreal_dataset.py` -- needed by Plans 01, 02
- `src/models/head_pose_geo.py` -- needed by Plan 04 (THE primary fix target)

**If the external drive is disconnected or the files are corrupted, ALL 4 revival plans are dead.** Only the in-repo evaluation scripts (full_eval_inprocess.py, which itself imports from the missing evaluate.py) can run, and they cannot run without evaluate.py.

**This is not a "risk" -- it is a structural dependency.** The swarm-bot repo contains only 11 Python files (6,029 lines). The revival requires the external workstation's codebase. Agent 3 (09_debate_code_correctness.md) confirmed: 70% of all code claims are unverifiable from the swarm-bot repo.

### 2.5 Disk Space Cascade (CRITICAL -- addressed by Agent 2, not yet resolved)

**Mechanism:** 250 GB of checkpoints against 138 GB free. The det_fixed_v1 run alone consumes 162 GB. Starting new training without freeing space risks:
- Checkpoint write failures (silent data loss)
- System instability (root partition and /media share the same 457 GB /dev/sdb2)
- Inability to preserve critical historical checkpoints

**Mitigation:** Agent 2's preservation plan (Section 7 of 08_debate_resources.md) identifies 200+ GB recoverable by thinning det_fixed_v1 checkpoints (keep every 5000th, delete 95% of intermediates). **This MUST be done before ANY training starts.**

### 2.6 Metric Contamination Cascade (MEDIUM -- addressed by multiple agents)

**Mechanism:** The codebase has a documented history of misleading metrics:
- Detection 0.5734: biased 250-batch subsample artifact. True: 0.00009.
- PSR F1=1.0: psr_transition.py:383-386 returns 1.0 when TP=FP=FN=0 (should be 0.0). Confirmed by Agent 3.
- Activity 0.6223: achieved on MViTv2-S, not ConvNeXt-Tiny.
- AC-1 contamination: best.pth promoted at epoch 11 by broken metric.
- dx*0.1 eval bug: contaminated ALL historical detection numbers (now fixed on external workstation).

**Any new number must be independently verified with:**
1. `ls -la` on the checkpoint that produced it
2. Reading the eval script that computed it
3. Confirming the data split (full D3 vs biased subsample)
4. Cross-checking against the persistence baseline (for PSR) or majority-class baseline (for Activity)

---

## 3. Rollback Plan

### 3.1 Per-Plan Rollbacks

**Activity (Plan 01):**
- **Failure trigger:** Training loss plateaus by epoch 5, val accuracy at majority baseline
- **Rollback:** Abandon ConvNeXt activity. Publish the linear probe result (0.2169 < 0.2217 baseline) as proof that ImageNet features lack action information. Report the 96.2% multi-task cost (0.622 -> 0.0236) as a characterized pathology. This is a genuine scientific contribution -- it falsifies the assumption that ImageNet-pretrained backbones can support activity recognition.
- **Recovery time:** 0 GPU-hours (publish existing numbers)
- **Impact on paper:** Activity shifts from "revival target" to "pathology measurement." The paper is stronger for it.

**Detection (Plan 02):**
- **Failure trigger:** Single-task ConvNeXt D3 mAP50 < 0.10 (architectural failure)
- **Rollback:** Document the 99.99% multi-task detection cost (0.995 -> 0.00009) as the central pathology measurement. Deploy companion YOLOv8m (0.995 mAP50) for detection results. Publish the cascade analysis showing that detection requires a dedicated backbone. If single-task D3 is 0.10-0.30, distillation may yield marginal gains but the paper contribution remains the collapse measurement, not the revival.
- **Recovery time:** 0 GPU-hours (publish existing numbers). 2 GPU-hours (run TTA eval on YOLOv8m for additional result).
- **Impact on paper:** Detection shifts from "revival target" to "strongest pathology evidence." The 99.99% cost is the most dramatic number in the paper.

**PSR (Plan 03):**
- **Failure trigger (Tier 1):** Transition F1 < 0.20 after Path A restoration
- **Rollback:** Publish per-frame F1 (0.70-0.75) with honest persistence-baseline comparison (copy_prev = 0.9997). The finding that per-frame F1 is persistence-dominated is a methodology contribution. OR use the existing MViTv2-S checkpoint (0.883, verified by Agent 4) as the PSR result, with honest disclosure that ConvNeXt-Tiny PSR is an open question.
- **Failure trigger (Tier 2):** Kendall ablation shows no improvement (expected outcome per Opus Q1)
- **Rollback:** Publish the negative result: "Kendall uncertainty weighting does not suppress PSR. The gradient starvation originates from dead ReLU paths, not loss weighting." This falsifies a common hypothesis with controlled evidence. Combined with the GELU saturation finding, this is two publishable pathology discoveries.
- **Recovery time:** 0 GPU-hours (publish existing numbers) for Tier 1. 2-3 days already invested for Tier 2 (publishable either way).
- **Impact on paper:** PSR contributes either a revival result (best case) or two characterized pathologies (GELU saturation + Kendall irrelevance). Both are publishable.

**Pose (Plan 04):**
- **Failure trigger:** Column fix reduces error but not below 20 degrees
- **Rollback (trivial):** Set `USE_GEO_HEAD_POSE=False` to revert to legacy HeadPoseHead. If legacy code exists, instantly recovers ~6.15 degrees. If legacy code was deleted, fall back to Strategy D (full retraining, 5-7 days) or publish the fixed GeometryAwareHeadPose result whatever it is.
- **Failure trigger (extreme):** Column fix has no effect (error stays ~86 degrees)
- **Rollback:** The root cause is misidentified. The 6D rotation representation, the FiLM integration, or the eval pipeline has a different convention than assumed. Publish the 86-degree result as a documented failure of the geometry-aware approach, with the 6.15-degree legacy result as the working alternative.
- **Recovery time:** 0 GPU-hours (legacy fallback) or 5-7 days (retraining)
- **Impact on paper:** Minimal. The legacy 6.15-degree result is already verified and publishable. The GeometryAwareHeadPose was an attempted improvement that failed in a well-characterized way -- this is a publishable negative result.

**Integration (Plan 05):**
- **Failure trigger:** PSR + Pose cannot coexist on shared backbone (FiLM contamination confirmed)
- **Rollback:** Publish Pose as the sole revived task on ConvNeXt-Tiny. Publish PSR from the MViTv2-S checkpoint (0.883, separate model). Document the cross-task contamination as a multi-task limitation finding. The paper becomes: "Pose estimation works on ConvNeXt-Tiny (6.15 deg). PSR requires spatiotemporal features (0.883 on MViTv2-S). Activity and Detection are characterized pathologies."
- **Recovery time:** 0 GPU-hours (both numbers already exist)
- **Impact on paper:** The "multi-task" story weakens, but the individual results are all real and publishable.

### 3.2 Multi-Plan Failure -- The Nuclear Scenario

**Trigger:** ALL 4 revival attempts fail catastrophically.

**Probability:** ~15% (two tasks already have proven signal: Pose at 6.15 deg, PSR at 0.883 on MViTv2-S)

**Rollback:** Publish the "Transparent Pathology" narrative:
1. **Head pose estimation on ConvNeXt-Tiny works** (6.15 deg, legacy head, verified truthful)
2. **PSR requires spatiotemporal features** (0.883 on MViTv2-S, 0.10 on ConvNeXt per-frame)
3. **Activity on per-frame 2D CNNs is impossible** (linear probe proves zero backbone signal)
4. **Multi-task detection collapses 99.99%** (0.995 -> 0.00009, central measurement)
5. **Three characterized training pathologies** (GELU saturation, gradient starvation, class collapse)

**This is a stronger paper than a partial 2-task revival.** It provides:
- Quantitative evidence for WHY multi-task training on a single backbone is hard
- Clear methodology contributions (linear probe protocol, persistence baseline, transition-F1 vs per-frame F1)
- Reproducible negative results (unusual and valuable in the MTL literature)
- An honest accounting of what the architecture can and cannot do

---

## 4. Mitigation Strategies

### 4.1 Earliest Warning Signals (what to monitor, when to abort)

| Plan | Metric | Warning Threshold | Abort Threshold | Measurement Frequency |
|------|--------|-------------------|-----------------|----------------------|
| Activity | Val top-1 vs majority baseline | < 0.25 by epoch 5 | < 0.10 by epoch 10 | Every epoch |
| Detection | Single-task ConvNeXt D3 mAP50 | < 0.30 | < 0.10 | Once (gating experiment) |
| Detection | Multi-task mAP50 after DET_GT_FRAME_FRACTION=0.4 | < 0.05 by epoch 5 | < 0.01 by epoch 10 | Every 5 epochs |
| PSR | Transition F1 after Path A restoration | < 0.30 | < 0.20 | Once (after repair completes) |
| PSR | Gradient norm on psr_decoder_classifier_2 | Zero for > 100 steps | Zero for > 500 steps | Every 100 steps |
| PSR | Post-activation mean (should be > 0 for LeakyReLU) | < 0.0 (saturation) | < -10 (severe saturation) | Every 500 steps |
| Pose | Forward angular MAE after column fix | > 20 degrees | > 50 degrees | Once (after fix applied) |
| Pose | FiLM contamination: PSR F1 delta pre/post fix | > 0.05 F1 drop | > 0.10 F1 drop | Once (after fix applied) |
| All | Disk free space | < 50 GB | < 20 GB | Before each training run |
| All | OOM events | 1 crash | 2 crashes in same experiment | Per run |

### 4.2 Monitoring Infrastructure

**Before any training starts:**
1. Free 200+ GB disk space (thin det_fixed_v1 checkpoints, remove incomplete MTL runs)
2. Verify all 9 critical checkpoint paths with `ls -lah`
3. Fix F1=1.0 bug at psr_transition.py:383-386 (`total_f1 = 1.0` -> `total_f1 = 0.0`)
4. Verify DET_GT_FRAME_FRACTION is enabled in the external-drive config (defaults to 0.0)
5. Run `nvidia-smi` to confirm both GPUs idle
6. Verify external drive is mounted and all 6 critical Python files are accessible

**During training:**
- Log per-component PSR gradients every 100 steps (detect dead heads early)
- Log post-activation mean for PSR classifier layers (detect saturation)
- Log per-class activity accuracy every epoch (detect class collapse)
- Auto-save crash_recovery.pth every epoch (already implemented)
- Monitor VRAM usage; abort if > 90% of GPU capacity

**After each experiment:**
- Run full eval on the checkpoint immediately (don't queue -- eval takes minutes, training takes days)
- Compare against all baselines (majority class, persistence, zeros)
- Commit metrics.json and eval logs to repo immediately
- Flag any metric that exceeds its persistence/majority baseline by < 5% as "below noise floor"

### 4.3 Decision Gates (Go/No-Go)

| Gate | Condition | Go | No-Go |
|------|-----------|-----|-------|
| G1: Disk | Free > 50 GB | Proceed with training | Clean up checkpoints first |
| G2: Single-task Detection | ConvNeXt D3 mAP50 > 0.30 | Proceed with multi-task detection | Abandon multi-task detection, deploy YOLOv8m |
| G3: PSR Transition F1 | Transition F1 > 0.20 after repair | Proceed with Kendall ablation | Abandon PSR revival, publish per-frame F1 |
| G4: Pose Column Fix | Forward MAE < 20 degrees after fix | Proceed with validation | Investigate root cause misidentification |
| G5: FiLM Contamination | PSR F1 drops < 0.05 after Pose fix | PSR + Pose can coexist | Must choose: Pose with dead PSR OR PSR with broken Pose |
| G6: Activity Training | Val top-1 > 0.25 by epoch 5 | Continue training | Abandon ConvNeXt activity, publish linear probe |
| G7: OOM Stability | < 2 crashes in experiment | Continue | Halt experiment, reduce batch size, investigate |
| G8: Freeze Date | Aug 22, 2026 | Freeze all numbers | All incomplete experiments become "ongoing work" |

---

## 5. Final Verdict

### 5.1 Probability of Achieving Targets

| Target | Current | Historical | ConvNeXt Signal? | P(success) |
|--------|---------|------------|------------------|------------|
| Pose < 6.15 deg | 86 deg (bug) | 6.15 deg | YES | **85%** (fixing 86-degree bug), **25%** (matching 6.15) |
| PSR > 0.80 F1 | 0.10 (Path B) | 0.883 (MViTv2-S) | UNKNOWN | **25%** (0.80+), **40%** (0.50-0.79) |
| Activity > 0.35 top-1 | 0.024 | 0.622 (MViTv2-S) | NO | **15%** (0.25-0.35), **<1%** (0.6223) |
| Detection > 0.30 mAP50 | 0.00009 | 0.995 (YOLOv8m ST) | NO | **20%** (via distillation, gated), **<2%** (0.5734) |

### 5.2 Probability of Achieving At Least 3 of 4 Targets

**The question assumes "4 targets" means: Pose < 6.15 deg, PSR > 0.80, Activity > 0.35, Detection > 0.30.** This assessment is based on evidence, not plans.

```
P(Pose success) = 0.85 (fixing the bug, conservative target < 20 deg)
P(PSR success) = 0.25 (hitting 0.80+ on ConvNeXt-Tiny)
P(Activity success) = 0.15 (hitting 0.25-0.35 verb-group)
P(Detection success) = 0.20 (hitting 0.30+ via distillation, gated on single-task baseline)
```

**Scenario A: All 4 succeed (independent):**
P(all 4) = 0.85 * 0.25 * 0.15 * 0.20 = **0.0064** (< 1%)

**Scenario B: At least 3 succeed (independent):**
P(3 of 4) requires summing the 4 combinations where exactly 3 succeed:
```
P(Pose+PSR+Activity, no Detection) = 0.85 * 0.25 * 0.15 * 0.80 = 0.0255
P(Pose+PSR+Detection, no Activity) = 0.85 * 0.25 * 0.85 * 0.20 = 0.0361
P(Pose+Activity+Detection, no PSR)    = 0.85 * 0.75 * 0.15 * 0.20 = 0.0191
P(PSR+Activity+Detection, no Pose)    = 0.15 * 0.25 * 0.15 * 0.20 = 0.0011
```
P(at least 3) = 0.0064 + 0.0255 + 0.0361 + 0.0191 + 0.0011 = **0.0882** (~9%)

**But the independence assumption is WRONG.** PSR and Pose share the ConvNeXt backbone and conflict via FiLM contamination. Activity and Detection have zero backbone signal and are architecturally collapsed. These are not independent dice rolls.

**Adjusted assessment accounting for dependencies:**

| Combination | Adjusted Probability | Rationale |
|-------------|---------------------|-----------|
| Pose only succeeds | 40% | Most likely -- bug fix, trivial fallback |
| Pose + PSR both succeed | 15% | Requires both to work AND not conflict via FiLM |
| Pose + PSR + Detection | 1% | Detection is architecturally collapsed |
| Pose + PSR + Activity | 0% (< 0.1%) | Activity has zero backbone signal |
| All 4 succeed | 0% (< 0.01%) | Impossible on this backbone |
| At least 3 of 4 | **< 2%** | Detection and Activity are not revivable |

### 5.3 The Honest Verdict

**At least 3 of 4 targets is not achievable. At most 2 of 4 tasks are revivable on ConvNeXt-Tiny.**

The evidence is clear:
1. **Pose: REVIVABLE.** Code bug (column ordering), trivial fallback (legacy head), target already proven on same backbone. Success probability: 85% for meaningful improvement, 25% for matching historical 6.15 deg.
2. **PSR: UNCERTAIN.** Path A architecture is proven (0.883 on MViTv2-S) but never tested on ConvNeXt-Tiny. Success probability: 25% for 0.80+, 40% for partial recovery. Transition F1 is the gating metric -- if < 0.20 after repair, the head is fundamentally limited.
3. **Activity: NOT REVIVABLE.** Linear probe proves zero backbone signal (0.2169 < 0.2217 majority baseline). No training duration, loss function, or head architecture can create information that doesn't exist in the features. Publish as a characterized pathology with the linear probe as proof.
4. **Detection: NOT REVIVABLE.** 99.99% multi-task collapse (0.995 -> 0.00009). Single-task ConvNeXt D3 is the gating experiment -- if < 0.10, the backbone cannot detect. Distillation from YOLOv8m (0.995) to ConvNeXt (0.00009) is a 10,000x gap with no precedent. Publish as the central pathology measurement.

### 5.4 What Should Actually Happen

**Stop calling this a "4-task revival."** Call it what it is:

> **A 1-task bug fix (Pose) + 1-task architecture-restoration experiment (PSR) + 2 characterized pathologies (Activity, Detection).**

The execution order that maximizes results:
1. **TODAY (Aug 1):** Free 200 GB disk space. Fix F1=1.0 bug. Verify external drive mounted.
2. **Aug 1-2:** Apply Pose column fix on external workstation. Evaluate. This takes 2 hours CPU + 2 hours GPU.
3. **Aug 2:** If Pose fix works, evaluate FiLM contamination impact on PSR. If PSR degrades, the two revivable tasks conflict -- must choose one.
4. **Aug 2-9:** PSR Path A restoration training (7 days, RTX 3060). Run in parallel with Detection single-task eval on RTX 5060 Ti.
5. **Aug 9-10:** Evaluate PSR transition F1. Decision gate: > 0.20 -> Kendall ablation (3 days). < 0.20 -> publish per-frame F1.
6. **Aug 10-17:** Kendall ablation OR salvage analysis. Detection decision based on single-task result.
7. **Aug 17-22:** Re-evaluate ALL metrics on freeze checkpoint. Fill 8 honest disclosures. Commit artifacts. FREEZE.

**This schedule is tight but achievable.** 21 days from Aug 1 to Aug 22. Critical path: PSR (7 days) + Kendall (3 days) = 10 days, leaving 11 days for evaluation, writing, and buffer. But it requires starting Pose fix TODAY and PSR training by Aug 2. Every day of delay pushes the freeze date.

### 5.5 The Paper This Produces

**Title:** "What Four Tasks Really Cost on One Backbone: Multi-Task Training Pathologies for Industrial Assembly Understanding"

**Genuine contributions (all verifiable):**
1. First ego-pose baseline on IndustReal: 6.15 deg forward angular MAE (ConvNeXt-Tiny, legacy head)
2. PSR with MonotonicDecoder: 0.883 F1 (MViTv2-S) or 0.70-0.80 F1 (ConvNeXt-Tiny, TBD)
3. Single-task detection beats SOTA: YOLOv8m mAP50 = 0.995 on IndustReal D1R
4. Multi-task detection cost: 99.99% (0.995 -> 0.00009) -- the central pathology measurement
5. Multi-task activity cost: 96.2% (0.622 -> 0.0236), with linear probe confirming zero backbone signal
6. Three characterized training pathologies: GELU saturation, gradient starvation, class collapse
7. Falsification of common MTL assumption: Kendall uncertainty weighting does NOT cause gradient starvation
8. Methodology contribution: transition-F1 vs per-frame F1 distinction, persistence baseline protocol

**What this paper does NOT claim (and why):**
- "Beats SOTA on all heads" -- FALSE. Only detection (YOLOv8m single-task) genuinely beats SOTA. Pose is competitive. PSR is TBD. Activity is a pathology.
- "Multi-task ConvNeXt detection is competitive" -- FALSE. It's 0.00009 mAP50.
- "Activity recognition within a multi-task framework" -- FALSE. The backbone has zero activity signal.
- "Kendall uncertainty weighting automatically balances tasks" -- FALSE. The config has 5 manual guards, and Kendall is irrelevant to the actual failure mechanisms.

---

## 6. Cross-References

### To Agent 1 (07_debate_feasibility.md):
- **Agreement:** ConvNeXt backbone ceiling is the fundamental constraint. At most 2 of 4 tasks are revivable. Pose first, PSR second.
- **Disagreement:** None. Agent 1's probability estimates (Pose 85%, PSR 40%, Activity 15%, Detection 20%) are slightly more optimistic than this analysis but within tolerance.
- **This analysis adds:** Cascade risk analysis (HeadPoseFiLM contamination) that Agent 1 did not explore. The FiLM mechanism means Pose and PSR fixes are NOT independent -- a finding that affects both probability estimates.

### To Agent 2 (08_debate_resources.md):
- **Agreement:** Disk space is CRITICAL and must be freed before any training. Parallel GPU execution (PSR on RTX 3060 + Detection on RTX 5060 Ti) is the only viable schedule. 14-day best case, 26-day worst case.
- **Disagreement:** Agent 2's wall-clock estimate (14-26 days) assumes all plans proceed to training. This analysis argues that Activity and Detection should be gated to "no training" (pathology documentation only), reducing the critical path to ~10 days.
- **This analysis adds:** Decision gates (Section 4.3) that Agent 2 did not define. The single-task Detection D3 result gates the entire detection plan. The PSR transition F1 gates the Kendall ablation.

### To Agent 3 (09_debate_code_correctness.md):
- **Agreement:** F1=1.0 bug at psr_transition.py:383-386 must be fixed. head_pose_geo.py does not exist in swarm-bot repo. External drive dependency is structural. 70% of code claims are unverifiable.
- **Disagreement:** None. Agent 3's verification tally (14 verified, 60 unverifiable, 4 wrong/missing) is the most rigorous cross-check in the debate.
- **This analysis adds:** The cascade risk of codebase split (Section 2.4) that Agent 3 identified but did not frame as a multi-plan dependency. If the external drive is inaccessible, ALL plans are dead -- not just Plan 04.

### To Agent 4 (10_debate_historical_targets.md):
- **Agreement:** Activity 0.6223 is real but on wrong architecture. Detection 0.5734 is a biased artifact. PSR 0.883 is verified but on MViTv2-S. Pose 6.15 is verified and on ConvNeXt-Tiny.
- **Disagreement:** Agent 4's verdict on Detection ("Target unverified or fake") understates the problem. The 0.5734 is not just unverified -- it is provably wrong. The true multi-task detection mAP50 is 0.00009 (cascade_table.md) or 0.000427 (d1_yolov8m/metrics.json). The 0.5734 was produced by a class-balanced sampler on a 250-batch subsample with the dx*0.1 eval bug active. It is an artifact of three compounding errors, not a measurement.
- **This analysis adds:** The FiLM contamination risk that Agent 4's v4_fixed analysis hinted at (dead PSR at 6.15 deg pose) but did not fully develop as a cross-task cascade.

### To Integration (05_integration_synthesis.md):
- **Agreement:** The integration plan correctly identifies PSR + Pose as the two revivable tasks and Activity + Detection as pathologies. The freeze date of Aug 22 is correct. The 8 honest disclosures need filling.
- **Disagreement:** The integration plan assumes PSR and Pose fixes are independent. They are not. HeadPoseFiLM creates a cross-task dependency. The execution order must account for this: apply Pose fix first, evaluate FiLM impact on PSR, THEN decide whether both can coexist on the shared backbone.
- **This analysis adds:** Explicit decision gates (G1-G8) that the integration plan lacks. Without gates, training will continue past the point of proven failure.

---

## 7. Actionable Recommendations (What To Do Right Now)

1. **IMMEDIATE (today, Aug 1):** Free 200+ GB disk space. Fix F1=1.0 bug at psr_transition.py:383-386. Verify external drive is mounted and all 6 critical Python files are accessible. Verify both GPUs idle.
2. **TODAY (Aug 1):** Run Pose column fix on external workstation (2 hours CPU). Evaluate on existing best pose checkpoint. Run FiLM contamination check (compare PSR F1 pre/post Pose fix).
3. **TOMORROW (Aug 2):** Decision: If Pose fix works and FiLM contamination is minimal, proceed with PSR Path A restoration training. If FiLM contamination is severe, choose: Pose with dead PSR OR PSR with broken Pose.
4. **BY AUG 3:** Start PSR Path A training on RTX 3060 (7 days). Start single-task Detection D3 eval on RTX 5060 Ti (2 hours eval, not full training).
5. **BY AUG 9:** Decision gate: If single-task Detection D3 mAP50 < 0.10, abandon all multi-task detection work. If PSR transition F1 < 0.20, abandon PSR revival, publish per-frame F1.
6. **BY AUG 17:** Complete Kendall ablation (if gated) OR publish existing PSR numbers. Complete all paper disclosures (D1-D8).
7. **BY AUG 22:** Freeze all numbers. No more training. Paper writing only.

---

**Final word:** The revival plans collectively describe a 4-task restoration. The measured evidence says at most 2 tasks are revivable on this backbone. The paper is stronger if it honestly reports this limitation rather than claiming a partial success as a full revival. The three training pathologies (GELU saturation, gradient starvation, class collapse) plus the 99.99% detection cost and the linear-probe-proven zero activity signal are more valuable contributions than any amount of hyperparameter tuning.
