# Agent 1: Feasibility Skeptic — Debate Analysis

**Role:** Feasibility Skeptic on 5-agent debate team
**Output:** Per-plan weakest assumption, realistic probability of success, exact blocker
**Constraint:** NO code changes. Strategy document only.
**Guidance:** Be EXTREMELY skeptical. Ask verification questions that require `ls -la`, reading actual eval scripts, running smoke tests.
**Citation rule:** Per audit Truthful Citations memory rule: "Never fabricate SOTA numbers." All numbers below are sourced from the plan files (01-06) and SOTA history (`feedback_sota_history.md`).

---

## Per-Plan Weakness Analysis

### Plan 1: Activity Revival (`01_activity_revival.md`)

**Target:** `top1_75` = 0.6223 (MViTv2-S, `t3_full_eval.json`)

**Was this target actually achieved?**
YES -- but on MViTv2-S (34.3M params, 3D convolutions, 16-frame video clips, spatiotemporal attention), NOT on ConvNeXt-Tiny (28.6M params, per-frame 2D CNN, ImageNet pretrained). These are fundamentally different architectures. The 0.6223 is truthful but NOT transferable to the current backbone.

**Current ConvNeXt baseline:**
- Linear probe on frozen ConvNeXt-Tiny features: **0.2169 top-1** vs majority-class baseline **0.2217** (always predict class 8). The frozen backbone encodes **zero activity-relevant features**.
- Current best multi-task activity on ConvNeXt: **0.1096 macro_f1** (rf_stages val).
- 48/74 classes have <10 training frames. 75-class accuracy is statistically impossible on subset data.

**Weakest assumption:**
> That fine-tuning the ConvNeXt-Tiny backbone will create activity-relevant features from ImageNet-1K pretrained weights.

ImageNet pretraining encodes **object identity** (what is this?), not **motion/action** (what is happening?). The linear probe result (0.2169 < 0.2217 majority baseline) is direct evidence: even with frozen features extracted at 8-frame intervals, the backbone cannot distinguish assembly actions better than guessing the most common class. Fine-tuning with the expanded 69->75 class head might improve this, but the features are fundamentally wrong.

The plan itself acknowledges this (line 397): "The biggest risk is that this plan is attempting the impossible."

**Verification questions the activity agent has NOT answered:**
1. Has the agent run `ls -la` on the v4_fixed checkpoint that produced 0.394? Is it on the external drive or in the repo?
2. Has the agent verified that `ACT_CLASS_GROUPING='hybrid'` remaps labels correctly for the current dataset? (PR #19 fixed a segment-eval remap bug.)
3. Has the agent run a 1-epoch smoke test with the LAP+KL configuration to confirm no NaN/crash?
4. Has the agent verified that `src/losses/balanced_softmax.py` (unwired) is actually skipped and LDAM-DRW is the active loss?
5. Has the agent confirmed that the 75-class head dimensions match the current dataset labels (which went through a 69->75 class expansion)?

**Realistic probability:**
- Hitting 0.6223 on ConvNeXt-Tiny: **<1%** (different architecture, zero activity signal from backbone)
- Hitting 0.25-0.35 verb-group (Plan Strategy A): **~15%** (requires backbone to learn motion features it fundamentally lacks)
- Hitting 0.40+ verb-group: **~5%** (would need to match MViTv2-S within 2x despite architectural gap)

**Exact blocker if it fails:**
The ConvNeXt-Tiny backbone, pretrained on static ImageNet images, does not encode temporal information. Activity recognition requires modeling **change over time** (motion, action phases, tool-object interactions). A per-frame 2D CNN fundamentally cannot do this. The fix is **not** a better loss function or hyperparameter -- it requires either (a) a spatiotemporal backbone (MViTv2-S) or (b) a temporal aggregation module on top of ConvNeXt features that the current architecture does not have.

**Fallback:** Use MViTv2-S as a separate activity-only model (Plan Strategy B). Report ConvNeXt activity as a "characterized pathology" (Agent 5's framing). Publish the linear probe result as negative evidence that ImageNet features lack activity information -- this is a genuine scientific contribution.

---

### Plan 2: Detection Revival (`02_detection_revival.md`)

**Target:** `det_mAP50_pc` = 0.5734, `mAP50` = 0.3584

**Was this target actually achieved?**
NO. The 0.5734 and 0.3584 numbers are **statistical artifacts** of a 250-batch class-balanced subsample that over-represents rare classes. The subsample evaluation excluded non-present classes from the denominator, inflating mAP by only computing over the 15 classes present in the subsample. The true multi-task detection performance on the full 38,036-frame D3 validation set is:

**True multi-task mAP50 = 0.00009** (99.99% collapse from single-task YOLOv8m ceiling of 0.995)

The detection revival plan (Section 1) correctly acknowledges this and redefines the mission: "not to revive 0.358 to 0.5734, but to determine whether ConvNeXt-Tiny detection can recover from 0.00009 to any competitive level."

**Weakest assumption:**
> That knowledge distillation from YOLOv8m (0.995) to ConvNeXt-Tiny multi-task head (0.00009) can bridge a ~10,000x performance gap.

The plan argues (Section 8.1) that "distillation changes the training dynamics" -- i.e., the gap is not a knowledge gap but a training-dynamics gap. This is plausible but unproven. Distillation typically closes 10-30% gaps between teacher and student with similar architectures. Closing a 10,000x gap from a detection-specialized architecture (YOLOv8m, 25.6M params, detection-optimized neck) to a classification backbone (ConvNeXt, ImageNet pretrained) with a lightweight detection head has **no precedent** in the literature that this agent can cite.

Furthermore, the entire revival is gated on a **single-task ConvNeXt-Tiny D3 baseline** that was still training as of July 7 (epoch 43/99). If single-task ConvNeXt detection on D3 is itself poor (e.g., < 0.30 mAP50), then no amount of distillation or multi-task tuning will recover competitive detection.

**Verification questions the detection agent has NOT answered:**
1. Has the agent checked whether the single-task ConvNeXt D3 training completed? What is its final mAP50?
2. Has the agent verified that the YOLOv8m teacher checkpoint (0.995 mAP50) is accessible and loadable?
3. Has the agent confirmed that `DET_GT_FRAME_FRACTION=0.40` is actually ON in the current config? (PR #7 added it but it defaults to OFF.)
4. Has the agent checked whether the eval script's dx*0.1 fix (applied today, per plan line 234) actually changes the mAP50 numbers vs the pre-fix eval?
5. Has the agent verified that `src/runs/rf_stages/checkpoints/best.pth` was promoted by a broken metric (AC-1 contamination at epoch 11) and is NOT a valid detection checkpoint?

**Realistic probability:**
- Hitting 0.5734 true multi-task mAP50_pc on full D3 eval: **<2%** (would require ~6000x improvement from 0.00009)
- Hitting 0.30-0.45 mAP50_pc via distillation (Plan Phase 4): **~20%** (contingent on single-task baseline being good)
- Hitting 0.50+ mAP50_pc: **<5%** (would need near-YOLOv8m performance from a classification backbone)
- Single-task ConvNeXt D3 achieving >0.50 mAP50 (gating experiment): **~30%** (ConvNeXt is not a detection architecture)

**Exact blocker if it fails:**
Detection requires spatial localization (bounding box regression) in addition to classification. ConvNeXt-Tiny was designed for ImageNet classification, not detection. The detection head (likely a lightweight FPN or similar) receives features from a backbone that was never trained to preserve spatial precision. In multi-task setting, the shared backbone receives conflicting gradients from activity (needs temporal/motion features) and detection (needs spatial/localization features). This gradient conflict was documented in the cascade analysis (`cascade_table.md`): activity and detection gradients point in orthogonal directions in backbone layers.

The true contribution (as the plan acknowledges in Section 3.5) may be: "The 99.99% multi-task detection cost (0.995 to 0.00009) is the central measurement, motivating decoupled architectures."

**Fallback:** Deploy a companion YOLOv8m (0.995 mAP50) for detection. Report ConvNeXt detection as a characterized pathology. The paper contribution becomes the measurement of multi-task detection collapse, not the revival.

---

### Plan 3: PSR Revival (`03_psr_revival.md`)

**Target:** `psr_f1` = 0.883 (v3.41 eval, 2000 frames, checkpoint `phase2_e3_b0.pth`)

**Was this target actually achieved?**
YES -- but on MViTv2-S with 9-channel input (RGB+VL+StereoL+StereoR+Depth), using Path A architecture (11 per-component binary sigmoid heads + MonotonicDecoder). This is NOT the current architecture.

**Current ConvNeXt baseline:**
- Path B (24-class softmax + causal transformer): **psr_f1 = 0.10** (benchmark train.log, best val)
- Architecture gap: Path A has proven 0.883. Path B peaks at 0.10. No head-to-head validation was ever run between them.
- 4 of 11 components are DEAD even at the best v3.41 checkpoint (comp4=0.000, comp7=0.000, comp8=0.000, comp9=0.000)

**Weakest assumption:**
> That ConvNeXt-Tiny backbone features can support 11-binary per-component state classification at quality comparable to MViTv2-S with 9-channel input.

The 0.883 was achieved with:
1. A 3D spatiotemporal backbone (MViTv2-S) that models **motion** -- essential for detecting state transitions
2. 9-channel input providing depth and stereo information -- useful for spatial reasoning about component positions
3. A MonotonicDecoder with Q48 hysteresis tuned for assembly state transitions

The plan proposes to restore Path A architecture on ConvNeXt-Tiny (RGB-only, per-frame features). Even with architecture restoration, the backbone features may lack the temporal and depth information that MViTv2-S provided. The MonotonicDecoder helps (it enforces monotonicity and smooths predictions), but it cannot create information that the backbone doesn't encode.

**Additional concern: The dead components.** Even on the optimal MViTv2-S backbone, 4 of 11 components were dead (F1=0.0). These components may be fundamentally undetectable from visual features -- e.g., components that are too small, occluded, or visually similar. Restoring Path A on a weaker backbone will not resurrect these components.

**Verification questions the PSR agent has NOT answered:**
1. Has the agent verified that `phase2_e3_b0.pth` (the v3.41 checkpoint that produced 0.883) exists and is loadable? Is it on the external drive?
2. Has the agent confirmed that the 9-channel input preprocessing pipeline still works with the current dataloader? (The current code may assume RGB-only.)
3. Has the agent verified that `PSRFocalLoss` (line 951 of training/losses.py) is still importable and functional after code changes since v3.41?
4. Has the agent checked whether `USE_PSR_TRANSITION=True` is actually set in the current config? (The plan says "verify" but doesn't show the result.)
5. Has the agent confirmed that the `authors_psr_eval.compute_psr_metrics_for_dataset` function handles 11-binary output correctly? (The plan says "already works" but was "being bypassed when 24-class was detected" -- has dispatch code been verified?)

**Realistic probability:**
- Hitting 0.883 on ConvNeXt-Tiny with Path A restoration: **<10%** (different backbone, different input channels, dead components)
- Hitting 0.80+ on ConvNeXt-Tiny: **~25%** (Path A architecture is proven, MonotonicDecoder helps, but backbone is weaker)
- Hitting 0.50-0.79: **~40%** (partial recovery, dead components remain dead)
- Hitting <0.20 (failing Agent 5's Step 2 gate): **~25%** (ConvNeXt features may lack necessary information)

**Exact blocker if it fails:**
The per-frame ConvNeXt features lack the temporal context that MViTv2-S's 16-frame clips provided. Assembly state transitions are temporal events -- a screwdriver moves from position A to position B over N frames. A per-frame CNN sees static images; it cannot perceive motion. The MonotonicDecoder smooths per-frame predictions into states, but if the per-frame classifications are noisy (low signal-to-noise ratio in backbone features), the decoder cannot recover.

**Fallback:** Use the v3.41 MViTv2-S checkpoint (0.883) as the PSR result. Acknowledge that ConvNeXt-Tiny PSR is a limitation. The paper contribution becomes: "PSR requires spatiotemporal features; ConvNeXt-Tiny per-frame features are insufficient."

---

### Plan 4: Pose Refinement (`04_pose_refinement.md`)

**Target:** `forward_angular_MAE` < 6.15 degrees (v4_fixed benchmark)

**Was this target actually achieved?**
YES -- 6.15 degrees was achieved by v4_fixed, verified truthful by the SOTA audit. It used the legacy `HeadPoseHead` (raw 9-DoF MSE regression, no orthogonality constraint, `USE_GEO_HEAD_POSE=False`). This is a genuine result on ConvNeXt-Tiny features.

**Current baseline:**
- Current GeometryAware run: **~86 degrees** (random-level error, confirmed by plan audit)
- Root cause: Column-ordering mismatch in `GeometryAwareHeadPose.to_legacy_9dof()`. The rotation matrix columns `[right, up, forward]` are mapped incorrectly to the eval-expected format `[forward, up, position]`. The eval compares the right-vector against forward-vector GT, producing ~86 degrees (close to the 90-degree expected for orthogonal unit vectors).
- This is a **code bug**, not an architecture limitation.

**Weakest assumption:**
> That fixing the column ordering in `to_legacy_9dof()` will recover the 6.15-degree performance without needing to retrain the backbone.

This is the STRONGEST assumption across all four plans (i.e., most likely to hold), but it is not certain. The concern:

**HeadPoseFiLM contamination:** The head pose tensor feeds into FiLM (Feature-wise Linear Modulation) layers that modulate C5 backbone features. During training with the broken column ordering, the FiLM layers received corrupted head pose vectors (right-vector instead of forward-vector). The FiLM parameters adapted to these corrupted inputs. After fixing the column ordering, the FiLM layers will receive correct head pose vectors but have parameters optimized for corrupted inputs. The backbone features modulated by FiLM may produce degraded representations for all tasks (activity, detection, PSR) because FiLM operates on shared C5 features.

**However**, this contamination is limited because:
1. FiLM modulation is additive/multiplicative on already-computed C5 features -- it doesn't destroy the underlying features
2. The head pose head itself (not the backbone) will benefit immediately from correct column ordering
3. The plan's Strategy C (resume training for 2 days after fix) allows FiLM layers to adapt

**Verification questions the pose agent has NOT answered:**
1. Has the agent read the actual `to_legacy_9dof()` source code from the external drive? The plan audit (Section 2.1) says "Without reading the external-drive source file directly, the precise 9-DoF layout cannot be confirmed."
2. Has the agent verified that v4_fixed checkpoint is accessible for re-evaluation? (The plan says 60% probability it's not accessible -- external drive may be disconnected.)
3. Has the agent confirmed that the eval script `full_eval_inprocess.py` expects `[forward(3), up(3), position(3)]` and not some other format? The audit identified a documentation contradiction (model.py line 97 says `[forward, position, up]` but v4_fixed result proves actual format is `[forward, up, position]`).
4. Has the agent tested whether the `head_pose_geo.py` module even imports in the current environment?
5. Has the agent checked whether `USE_GEO_HEAD_POSE=True` can be toggled to `False` to immediately recover the v4_fixed 6.15-degree performance? (If the legacy HeadPoseHead code still exists.)

**Realistic probability:**
- Fixing the 86-degree error to < 20 degrees (bug fix verified): **~85%** (column mapping is well-understood)
- Hitting < 7.83 degrees (beating rf_stages): **~50%** (depends on FiLM contamination severity)
- Hitting < 6.15 degrees (matching v4_fixed): **~25%** (requires FiLM layers to not have corrupted backbone features)
- Fix fails entirely (error remains > 20 degrees): **~15%** (root cause misidentified, or FiLM contamination too severe)

**Exact blocker if it fails:**
If the column fix doesn't reduce error below 20 degrees, the issue is NOT the column ordering but:
1. HeadPoseFiLM has permanently corrupted C5 backbone features, affecting all tasks
2. The GeometryAware geodesic loss has numerical instability (the plan notes gradient overflow risk at 15%)
3. The 6D rotation representation has a different convention than assumed

**Fallback (immediate, no training):** Set `USE_GEO_HEAD_POSE=False` to revert to legacy `HeadPoseHead`. If the legacy head code still exists and is functional, this instantly recovers v4_fixed-level performance (~6.15 degrees). This is a 1-line config change with zero GPU cost.

**This plan is the most likely to succeed AS-IS because:**
1. The root cause is a **code bug** (column ordering), not an architecture limitation
2. The fix requires ~2 hours of code changes, no GPU training
3. The target (6.15) was already achieved on the SAME backbone (ConvNeXt-Tiny)
4. A trivial fallback exists (disable GeometryAware, use legacy head)
5. Verification can be done with a synthetic unit test (identity rotation matrix) that takes seconds

---

### Plan 5: Integration Synthesis (`05_integration_synthesis.md`)

**Target:** Integrated multi-task model with PSR + Pose revived; Activity and Detection reported as characterized pathologies.

**Was this target actually achieved?**
N/A -- this is a coordination plan, not a performance target. However, the synthesis has one claim that affects all other plans:

> "Revive PSR + Head Pose on the shared ConvNeXt-Tiny backbone; report detection and activity as characterized pathology measurements."

This correctly identifies PSR and Pose as the two revivable tasks, and Activity/Detection as pathologies. But the order of operations assumes Pose and PSR fixes are independent. They are not: both share the ConvNeXt backbone, and the Pose fix (column ordering) affects FiLM layers that modulate the backbone features used by PSR.

**Weakest assumption:**
That PSR and Pose fixes can proceed independently on the same backbone without cross-task interference.

**Verification questions:**
1. Has the integration agent verified that the Pose column fix does not degrade PSR performance? (FiLM layers modulate shared C5 features.)
2. Has the integration agent confirmed GPU availability schedule? (Agent 5's STEP 1 says PSR repair training was at epoch ~24/100 on Aug 1. Does this complete before Aug 3 freeze?)
3. Has the integration agent verified that all 5 plans' config changes don't conflict in `config.py`?

---

## Cross-Cutting Risks

### C1: The ConvNeXt-Tiny Backbone Ceiling

**All four task revival plans share one assumption: that ConvNeXt-Tiny features contain sufficient information for their respective tasks.** Evidence against:

| Task | Evidence ConvNeXt has signal? | Best known ConvNeXt result |
|------|-------------------------------|----------------------------|
| Activity | NO -- linear probe < majority baseline | 0.1096 macro_f1 (effectively random for 75-class) |
| Detection | NO -- 0.00009 mAP50 (99.99% collapse) | 0.00009 (random) |
| PSR | UNKNOWN -- no Path A eval on ConvNeXt exists | 0.10 (Path B, architectural failure, not informative) |
| Pose | YES -- 6.15 deg on v4_fixed (legacy head) | 6.15 deg (verified truthful) |

**Conclusion:** Pose is the only task with proven signal on ConvNeXt-Tiny. Activity and Detection show zero signal. PSR is unmeasured (the 0.10 is a Path B failure, not a backbone assessment). **Any plan that requires Activity or Detection to exceed random-chance performance on ConvNeXt-Tiny is fighting against measured evidence.**

### C2: HeadPoseFiLM Contamination

The HeadPoseFiLM mechanism modulates C5 backbone features with head pose vectors. During training with broken column ordering, these vectors were corrupted. FiLM parameters adapted to corrupted inputs. After the column fix:
- Pose head: Immediately benefits (correct inputs -> correct outputs)
- Backbone C5 features: Potentially degraded (FiLM parameters are wrong for correct inputs)
- PSR head: Receives degraded backbone features -> potentially worse than pre-fix
- Activity head: Same as PSR
- Detection head: Same as PSR

**This is a cross-task risk that NO plan addresses.** The Pose plan mentions it (Strategy C: 2 days resume training for FiLM adaptation), but the PSR and Activity plans don't account for it.

### C3: The August Deadline Squeeze

Per PR #36's 30-day plan:
- Aug 3 (2 days from now): Architecture freeze
- Aug 4-10: Phase 3 multi-seed
- Aug 22: Freeze date (past)
- Oct 10: Submission deadline

Reality check: We are at Aug 1. The "Aug 22 freeze date" is already past. The Oct 10 submission deadline gives ~70 days. However:
- PSR Path A restoration training: 50 epochs, ~8 days on RTX 3060
- Activity retraining with LAP+KL: TBD epochs
- Detection distillation: TBD epochs
- Pose column fix + validation: 2 hours code + 2 days validation

**Total minimum compute: 50+ GPU-days on RTX 3060.** With 1-2 GPUs available, this exceeds the Oct 10 deadline if tasks are run sequentially. The integration plan's critical path (STEPS 0-6) doesn't sum GPU-hours.

### C4: External Drive Dependency

Multiple critical artifacts exist ONLY on the external drive at `/media/newadmin/master/POPW/working/code/industreal_improved/`:
- v3.41 checkpoint (`phase2_e3_b0.pth`) — PSR 0.883 evidence
- v4_fixed checkpoint — Pose 6.15 evidence
- `train.log` files — 0.5734 detection evidence (biased subsample)
- `head_pose_geo.py` — GeometryAwareHeadPose source (needed for column fix)
- `evaluate.py` — eval dispatch code

**If the external drive is disconnected, 3 of 4 revival plans cannot verify their historical baselines.** Only the Pose plan can proceed with the partial `head_pose_geo.py` audit from Agent 4.

### C5: Metric Honesty (recurring problem)

The codebase has a documented history of misleading metrics:
- 0.5734 detection mAP50_pc: biased subsample, not genuine multi-task
- F1=1.0 PSR: only class 0 has GT in 500-frame sample (labeled "FAKE" in SOTA history)
- AC-1 contamination: checkpoint promoted at epoch 11 by broken metric
- Activity 0.6223: achieved on different architecture (MViTv2-S), not ConvNeXt
- 6.15 pose: verified truthful, but on different head architecture (legacy, not GeometryAware)

**Any new number reported by the revival must be independently re-verified with `ls -la` on the checkpoint, reading the eval script, and confirming the data split.**

---

## Synthesis: Which Plan Is Most Likely to Succeed AS-IS?

### Ranking (probability of hitting stated target)

| Rank | Plan | Target | Probability | Rationale |
|------|------|--------|-------------|-----------|
| **1** | **Pose (04)** | <6.15 deg | **25%** (hitting exact target), **85%** (fixing the 86-degree bug) | Bug fix, not architecture change. Target already proven on SAME backbone. Trivial fallback exists. |
| 2 | PSR (03) | 0.883 | **<10%** (exact target), **~25%** (0.80+) | Architecture restoration is sound but backbone is different. Dead components remain. |
| 3 | Detection (02) | 0.5734 | **<2%** | Target was an artifact. True baseline is 0.00009. Gated on single-task experiment. |
| 4 | Activity (01) | 0.6223 | **<1%** | Different architecture entirely. Linear probe proves zero backbone signal. |
| 5 | Integration (05) | Coordination | N/A | Depends on 1-4 succeeding. GPU scheduling is the bottleneck. |

### Which plan should go FIRST?

**Pose.** It's a code fix (2 hours), not a training run. It unblocks everything else by fixing FiLM contamination. It has a trivial fallback (disable GeometryAware). If Pose fails, the FiLM contamination hypothesis is confirmed, and the shared backbone approach for PSR/Activity/Detection is dead -- they all need separate backbones.

### The brutal truth

The revival plans collectively assume that ConvNeXt-Tiny can support 4 tasks at competitive performance. The measured evidence says:
- **Pose**: YES (6.15 deg, legacy head)
- **PSR**: UNKNOWN (never tested with Path A on ConvNeXt)
- **Activity**: NO (linear probe < baseline)
- **Detection**: NO (0.00009 mAP50, 99.99% collapse)

**At most 2 of 4 tasks are revivable on this backbone.** The integration plan's decision to characterize Activity and Detection as pathologies is correct, but optimistic about PSR. The honest paper contribution is:

1. **Pose estimation on ConvNeXt-Tiny works** (6.15 deg, or fixed GeometryAware)
2. **PSR on ConvNeXt-Tiny is unproven** (Path A restoration experiment)
3. **Activity on per-frame 2D CNNs is impossible** (linear probe proof, publishable negative result)
4. **Multi-task detection collapses 99.99%** (from 0.995 to 0.00009, central measurement)

This is a 1-success (Pose), 1-experiment (PSR), 2-pathology (Activity, Detection) paper. Not a 4-task revival.

---

## Cross-References

### To Agent 8 (Code Auditor):
- Verify `GeometryAwareHeadPose.to_legacy_9dof()` column mapping by reading the actual source from the external drive
- Confirm that `USE_GEO_HEAD_POSE=False` restores legacy HeadPoseHead (check code path exists)
- Verify that `PSRFocalLoss` (training/losses.py:951) is importable and functional
- Audit all eval dispatch paths for PSR (11-binary vs 24-class routing)
- Check FiLM layer inputs: is head_pose tensor used to modulate C5 features? If so, what's the contamination scope?

### To Agent 9 (Experiment Runner):
- Run the Pose column-fix unit test FIRST (synthetic identity rotation, takes seconds)
- Smoke-test: 1 epoch training with fixed column ordering, verify no NaN/crash
- Verify v4_fixed checkpoint accessibility BEFORE planning re-eval
- Single-task ConvNeXt D3 detection baseline: what's the final mAP50? This gates the entire detection plan.

### To Agent 10 (Paper Writer):
- The paper must distinguish between "target was achieved" and "target was achieved on THIS architecture"
- Activity 0.6223: MViTv2-S, not ConvNeXt. Report as cross-architecture comparison, not multi-task result.
- Detection 0.5734: Biased subsample artifact. Report true multi-task mAP50 = 0.00009.
- PSR 0.883: MViTv2-S with 9-channel input. ConvNeXt result TBD.
- Pose 6.15: ConvNeXt-Tiny with legacy head. Verified truthful.
- Per Truthful Citations rule: Every SOTA number in the paper must cite the exact checkpoint path, eval script, and data split used.

---

**Agent 1 Verdict:** The revival is a 1-task (Pose) bug fix plus a 1-task (PSR) experiment, not a 4-task restoration. Set expectations accordingly.
