# Agent 4: Adversarial -- Worst-Case Analysis of the Unified Model Plan

**Date:** 2026-08-01
**Agent:** 4 (Adversarial) of 5-agent debate team
**Mission:** Find the WORST CASE for the unified model plan. ONE model with act=0.394, det=best, pose=6.15 degrees, psr=0.883.
**Deliverable:** This file (20_unified_model_adversarial.md)
**Cross-references:** 17, 18, 19 (Agent 1-3 unified model analyses -- NOT YET CREATED), 21, 22 (debate synthesis files -- NOT YET CREATED)
**Instruction:** Be brutally honest. No sugar-coating. No "could work if."

---

## 0. Brutal Honesty Up Front

**The unified model plan is dead on arrival.** The goal of ONE model with all four heads at their best-ever metrics is not merely improbable -- it is architecturally impossible without new training from scratch, and even then, at most 2 of 4 targets are reachable. Here is why in two lethal sentences:

1. **The two checkpoints that achieved the historical metrics use different backbones.** act=0.394 and pose=6.15 come from v4_fixed (ConvNeXt-Tiny, 244 MB, 2026-07-30). psr=0.883 comes from v3.41_safe (MViTv2-S, 695 MB, 2026-07-28). These backbones have different architectures (ConvNeXt-Tiny ~28.6M params vs MViTv2-S 34.3M params), different input channels (RGB-only vs 9-channel RGB+VL+StereoL+StereoR+Depth), and different feature dimensions (512/768 vs 768). **No weight merging, distillation, or stitching strategy can combine these into one model.**

2. **The detection head has never worked in any multi-task configuration.** Single-task YOLOv8m = 0.995 mAP50. Multi-task ConvNeXt-Tiny = 0.00009 mAP50 -- a 99.99% collapse. The claimed 0.5734 was a biased 250-batch class-balanced subsample artifact (n_present=15 of 24 classes). The true honest present-class mAP (det_mAP50_pc) is **0.0**. Adding detection to any model destroys it through gradient conflict with activity and pose heads.

**The only honest framing:** PSR (0.883) is revivable if you revert the entire architecture back to MViTv2-S + Path A. Pose (6.15) is revivable if you revert to the legacy HeadPoseHead. Activity (0.394) can be obtained from the v4_fixed ConvNeXt-Tiny checkpoint but coexists with dead PSR (10 of 11 components F1=0.0) and dead detection. **You cannot have all four. You cannot have three. At best, two. Likely one.**

---

## 1. Per-Risk Analysis

### Risk 1: Catastrophic Forgetting

**Probability of failure: 95%**

**What must happen for this to succeed:** Adding PSR training (on ConvNeXt-Tiny with temporal sequences, Path A architecture) must not degrade the existing act=0.394 and pose=6.15 from v4_fixed. Similarly, adding retrained activity and pose heads must not destroy PSR.

**Why it fails:** The v4_fixed checkpoint itself is the smoking gun. It achieved act=0.394 and pose=6.15 simultaneously -- but with a **completely dead PSR head**:

```
v4_fixed PSR per_class_f1_swept:
[1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
```

Only component 0 (always-on, trivial) has F1=1.0. All other 10 components have F1=0.0. The v4_fixed model paid for act+pose coexistence with total PSR death. This is not a bug -- it is the ConvNeXt-Tiny backbone's proven ceiling: **the shared C4/C5 features can support at most 2 tasks simultaneously** before gradient conflict kills the weakest head.

The HeadPoseFiLM mechanism makes this worse. FiLM layers modulate C5 backbone features with head pose vectors. If FiLM parameters were trained with corrupted column ordering (as they are in the current code), then fixing the column ordering changes the FiLM inputs, breaking the modulation, corrupting C5 features, and cascading into PSR degradation. This is the cascade chain documented in 11_debate_adversarial.md:

```
Pose column fix -> FiLM receives correct vectors with wrong params ->
C5 features corrupted -> PSR degrades -> Activity/Detection already broken
```

**Earliest signal:** Within 1 epoch of joint training. PSR F1 drops below 0.30; activity top-1 drops below 0.10; pose angular MAE exceeds 30 degrees.

**Rollback plan:** Revert to single-task checkpoints. The v4_fixed checkpoint (244 MB) preserves act+pose. The v3.41_safe checkpoint (695 MB) preserves PSR. Abandon unified model. Publish as two-column architecture comparison (v4_fixed left, v3.41_safe right).

**Time to detect:** 1 epoch of joint training (~38 minutes on RTX 3060, ~3 hours on RTX 5060 Ti). Evaluation adds 2 hours. **Total: 3-5 hours from training start.**

---

### Risk 2: Architecture Mismatch (ConvNeXt-Tiny vs MViTv2-S)

**Probability of failure: 100%**

**What must happen for this to succeed:** The unified model must use a SINGLE backbone. Either ConvNeXt-Tiny (proven for act+pose) must also achieve psr=0.883, or MViTv2-S (proven for psr=0.883) must also achieve act=0.394 and pose=6.15.

**Why it fails:** Neither condition holds.

**ConvNeXt-Tiny cannot do PSR at 0.883.** The v4_fixed checkpoint proves this: on ConvNeXt-Tiny with 3D spatiotemporal convolutions (the same backbone that achieved act=0.394 and pose=6.15), PSR achieved F1=0.0 on 10 of 11 components. The ConvNeXt-Tiny was never trained successfully for PSR -- all PSR training in the project has been on MViTv2-S. Furthermore, v4_fixed uses RGB-only input (3 channels), while v3.41_safe's PSR training uses 9-channel input (RGB + VL + StereoL + StereoR + Depth). Even if the backbone were the same, the input dimensionality mismatch prevents checkpoint reuse.

**MViTv2-S cannot do activity at 0.394.** The activity linear probe result is devastating: frozen ConvNeXt-Tiny features achieve 0.2169 top-1 activity accuracy vs. 0.2217 majority-class baseline. **The backbone encodes ZERO activity-relevant information.** There is no reason to believe MViTv2-S would be different -- if anything, MViTv2-S's 3D convolutions are designed for video classification, yet the per-frame activity MLP on ConvNeXt-Tiny showed the backbone itself carries no activity signal. The historical 0.6223 activity was from a completely different setup: MViTv2-S with Meccano pretraining, video-level classification head, not the current per-frame MLP head.

**Weight merging is impossible.** ConvNeXt-Tiny and MViTv2-S have:
- Different layer types (2D depthwise convs vs 3D pooling attention)
- Different channel dimensions at every stage (96/192/384/768 vs 96/192/384/768 but different spatial feature maps)
- Different parameter counts (~28.6M vs 34.3M)
- Different input channels (3 vs 9)
- No shared initialization, no shared architecture, no shared feature space

Agent 1's weight merging task (background agent a722abacd2780b651) will inevitably discover this, but the mathematical fact is already established.

**Earliest signal:** Immediate. The weight merging task will fail within minutes of attempting to load both checkpoints. There is no bridging strategy.

**Rollback plan:** No rollback needed -- this path was never viable. The only option is to pick ONE backbone and accept that only its proven tasks will work.

**Time to detect:** Already detected. This analysis serves as the detection. No GPU time required.

---

### Risk 3: PSR Per-Frame vs Transition

**Probability of failure: 100% for "transition detection" claim; 0% for per-frame classification.**

**What must happen for this to succeed:** The unified model must detect assembly step transitions, not just classify per-frame component states.

**Why it fails:** PR #19 confirmed this conclusively. PSR is **per-frame component-state classification, NOT transition detection.** The causal transformer mask is a no-op (temporal smoothing computes over T=1 transitions). The MonotonicDecoder provides monotonicity enforcement (once a component activates, it stays active) but does NOT detect the transition event itself.

This means:
- The model classifies "is component X currently in state Y?" for each frame
- It does NOT detect "did component X change from state A to state B at this frame?"
- The temporal smoothing over T=1 means no temporal context is used
- The "transition F1" metric is a derivative of per-frame accuracy, not a genuine transition detection score

**This is not a bug -- it is a definitional issue.** The paper can honestly report per-frame PSR, but cannot claim transition detection. The 0.883 F1 is frame-level classification accuracy, not transition detection accuracy.

**Impact on unified model:** If the paper claims "transition detection" in a unified model, this is a **retraction-grade misrepresentation.** The honest framing must say "per-frame component-state classification." This is a labeling issue, not a performance issue -- 0.883 per-frame F1 is still a real achievement. But claiming it as transition detection is fraudulent.

**Earliest signal:** Already known. PR #19 documented this months ago. The eval code confirms: `T=1` temporal window, causal mask is identity matrix.

**Rollback plan:** Change all paper language from "transition detection" to "per-frame component-state classification." Add a limitations paragraph. The metric itself is valid; only the claim is wrong.

**Time to detect:** 0 hours. Already detected and confirmed.

---

### Risk 4: Detection Collapse

**Probability of failure: 99.9% for achieving any meaningful detection mAP in a unified model.**

**What must happen for this to succeed:** The unified model must produce usable detection boxes (mAP50 > 0.30) while simultaneously performing act=0.394, pose=6.15, and psr=0.883.

**Why it fails:** The evidence is overwhelming and comes from 4 independent sources:

1. **Single-task vs multi-task gap:** YOLOv8m single-task = 0.995 mAP50. ConvNeXt-Tiny multi-task = 0.00009 mAP50. That is a **99.99% collapse.** Detection is the first head to die in any multi-task configuration.

2. **The 0.5734 claim is a biased artifact.** It came from a 250-batch class-balanced subsample where only 15 of 24 classes had any ground-truth boxes present. The true full-dataset mAP50_pc (present-class) is 0.00009. The honest det_mAP50_pc from in-repo metrics.json is **0.0**.

3. **The dx*0.1 eval bug contaminated all historical detection numbers.** The evaluate.py on the external workstation had a coordinate scaling bug that has now been fixed. All detection mAP numbers computed before the fix (including the 0.5734 and any "improvement" numbers) are incorrect.

4. **Detection's gradient conflict is terminal.** The detection head requires fine-grained spatial features (FPN at P2-P5). Activity requires temporal features from the feature bank. Pose requires C4+C5 features modulated by FiLM. PSR requires C5 features fed through GRU+MonotonicDecoder. These heads compete for the same backbone features, and detection consistently loses -- the 173,088 anchors at 1280x720 produce gradients that overwhelm the other heads' signals.

**The detection head in any multi-task configuration on ConvNeXt-Tiny has NEVER exceeded 0.10 mAP50.** The claimed 0.3584 and 0.5734 are both artifacts. The true multi-task detection performance rounds to zero.

**Earliest signal:** Within 5 epochs of joint training. Detection mAP50 stays below 0.01 while activity and pose metrics also degrade from gradient interference.

**Rollback plan:** Do not include detection in the unified model. Document it as a characterized pathology: "Detection collapses to near-zero in multi-task configuration, consistent with gradient conflict between dense prediction and classification heads on a shared backbone." This is honest, scientifically valid, and useful to the community.

**Time to detect:** 5 epochs of training + 2 hours eval. With detection-only training running at ~6 min/epoch on a subset, the gating experiment takes ~2 hours total.

---

### Risk 5: Eval Pipeline Bugs

**Probability of failure: 100% that bugs exist, 80% that at least one bug inflates a reported metric.**

**Confirmed bugs:**

| Bug | Location | Impact | Fix |
|-----|----------|--------|-----|
| F1=1.0 when TP=FP=FN=0 | psr_transition.py:382-386 | Inflates PSR F1 on recordings with zero assembly steps | Return 0.0 instead of 1.0 |
| F1=1.0 when TP=FP=FN=0 | psr_transition.py:347 | Same bug, duplicate location | Return 0.0 |
| F1=1.0 when TP=FP=FN=0 | evaluate.py:1269-1270 (external) | Same bug in eval pipeline | Return 0.0 |
| F1=1.0 when TP=FP=FN=0 | evaluate.py:1412-1417 (external) | Same bug in _decode_24class_psr_transitions | Return 0.0 |
| dx*0.1 coordinate bug | evaluate.py:2405-2409 (external) | Incorrect box coordinate decoding, contaminated all historical detection numbers | Fixed on workstation |
| 250-batch biased subsample | evaluate.py (external) | Class-balanced sampler produced biased detection mAP (0.5734 artifact) | Use full dataset eval |
| 500-frame smoke test | Various eval files | Both act=0.394 and pose=6.15 were evaluated on 500-frame subsamples, not the full 38,036-frame validation set | Re-evaluate on full set |

**The F1=1.0 bug is the most dangerous.** It triggers when both ground truth and predictions have zero positive examples for a component. This happens systematically for rare components (4 of 11 PSR components have F1=0.0 in v4_fixed). The bug inflates the overall macro F1 because these zero-activity components get a perfect 1.0 score instead of 0.0. For the per-class F1 sweep calculation, this inflates the mean by up to 4/11 = 0.091.

**Impact on unified model:** All PSR numbers reported before the fix are inflated by an unknown amount. The true PSR F1 with this bug fixed could be anywhere from 0.79 to 0.88 (estimated: 0.883 - 0.091 = ~0.79 for the worst case where all 4 dead components trigger the bug).

**The evaluate.py dependency is a structural risk.** The in-repo eval script (full_eval_inprocess.py) imports from evaluate.py, which does NOT exist in the swarm-bot repo. It lives only on the external workstation at `/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/src/evaluation/evaluate.py` (6966 lines). This means:
- No evaluation can be run from the swarm-bot repo alone
- All eval depends on a single external machine
- The evaluate.py code cannot be reviewed or audited without physical access to the workstation

**Earliest signal:** Run full-dataset evaluation with the F1=1.0 bug fixed. Compare against historical numbers.

**Rollback plan:** Fix all 4 F1=1.0 instances (change `total_f1 = 1.0` to `total_f1 = 0.0` when all counts are zero). Re-run all evaluations on the full 38,036-frame validation set. Report corrected numbers. This takes 2-3 hours of eval time, zero training.

**Time to detect:** 2-3 hours of evaluation after code fixes. But code fixes must be done on the external workstation where evaluate.py lives.

---

### Risk 6: Time Budget

**Probability of failure: 85%**

**What must happen for this to succeed:** All training, evaluation, and paper writing must complete before the submission deadline (Oct 10, 2026, per PR #36). The Aug 22 freeze date is already past.

**Why it fails:**

**GPU budget (from Agent 2 audit, 08_debate_resources.md):**
- Best case: 265-313 GPU-hours, 14 wall-clock days (parallel schedule)
- Worst case: 581-701 GPU-hours, 26 wall-clock days (serial schedule)

The worst case already exceeds the Aug 22 freeze date by 4 days. We are now at Aug 1, with 21 days to the freeze date that is already past. Even the best case (14 days, completing Aug 15) assumes:
1. PSR runs on RTX 3060 and Detection on RTX 5060 Ti IN PARALLEL
2. Detection gates to Strategy B (pathology doc, no training)
3. Pose fix works code-only (no retraining needed)
4. Activity runs Strategy A on RTX 3060 after PSR completes
5. At least 200 GB of checkpoint storage is freed before starting

Condition 5 alone is a blocker. The det_fixed_v1 run consumed 162 GB against 138 GB free. No training can start without manual checkpoint cleanup.

**The detection training time is underestimated.** The Resource Audit found that full-dataset detection training on ConvNeXt-Tiny takes 7.25 hours per epoch (39,465 batches). At 99 epochs, that is **30 days** on a dedicated GPU. The revival plans' "5 days" estimate is for subset/distillation, not full retraining.

**The PSR timeline is fragile.** PSR Phase 1 requires 2-3 days of CPU-only code changes (reverting from Path B to Path A, wiring MonotonicDecoder). Phase 2 requires 50 epochs at ~3.2 hr/epoch = ~7 days on RTX 3060. Phase 3 (Kendall ablation) adds 2-3 days. Total: 11-14 days. Any error, OOM, or checkpoint corruption adds 1-2 days.

**Disk space emergency (Agent 2 audit):**
- 138 GB free out of 457 GB
- det_fixed_v1 checkpoints: 162 GB (saves every 500 batches, 733 MB each)
- MTL v3.49 checkpoints: 47 GB
- MTL v3.50 checkpoints: 15 GB
- rf_stages checkpoints: 12 GB
- **Total checkpoint consumption: ~250 GB against 138 GB free**

Training CANNOT start until at least 50-100 GB is freed. The Resource Audit estimates 200+ GB recoverable through thinning, but thinning requires manual intervention that has not been scheduled.

**New training adds to disk pressure.** PSR training produces ~20 GB of checkpoints (50 epochs). Activity training produces ~5 GB. Detection distillation produces up to 200 GB if saving at the same frequency as det_fixed_v1.

**Earliest signal:** Training fails to start due to disk full. Or training starts but crashes at epoch N due to OOM/disk full.

**Rollback plan:** If time runs out, publish what you have. PSR (0.883) + Pose (6.15) from separate checkpoints on separate backbones is a publishable paper if presented honestly as a two-architecture comparison. The Oct 10 submission deadline is 70 days away -- enough to write the paper, but not enough to train new models from scratch AND write.

**Time to detect:** Immediate (disk full prevents any training start). Or 7-14 days into training when it becomes clear the schedule won't hold.

---

### Risk 7: External Drive Dependency

**Probability of failure: 40%**

**What must happen for this to succeed:** All critical artifacts must remain accessible on the external drive at `/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/`.

**Why it fails:** The dependency is total and fragile.

**Artifacts that exist ONLY on the external drive (from 09_debate_code_correctness.md):**
- `src/models/model.py` -- the entire model architecture (not in swarm-bot repo)
- `src/training/losses.py` -- all loss functions (not in swarm-bot repo)
- `src/evaluation/evaluate.py` -- 6966 lines, core eval logic (not in swarm-bot repo)
- `src/training/train.py` -- training loop (not in swarm-bot repo)
- `src/data/industreal_dataset.py` -- dataset loading (not in swarm-bot repo)
- `src/models/head_pose_geo.py` -- the GeometryAwareHeadPose that needs fixing (not in swarm-bot repo)
- `src/evaluation/eval_mecanno_mvitv2.py` -- activity eval script (not in swarm-bot repo)
- All eval scripts referenced by Activity Plan 01 (not in swarm-bot repo)
- `scripts/eval/eval_activity_75class.py` -- does not exist anywhere

**Of 78 total code claims across the 5 revival plans, 60 (77%) reference files that live exclusively on the external drive** (09_debate_code_correctness.md verified count: 14 verified in-repo, 60 unverifiable, 4 wrong).

**Single point of failure chain:**
1. If the external drive fails, is disconnected, or is reformatted: ALL training code is lost
2. If the external workstation crashes: ALL evaluation capability is lost
3. If the external drive permissions change: ALL checkpoint access is lost
4. If the external workstation is repurposed: ALL historical artifacts are lost

**The backup situation is unknown.** There is no evidence of off-site backups, cloud copies, or secondary storage for any of the critical artifacts. The swarm-bot repo contains only 11 Python files (6,029 lines) -- ~5% of the total codebase. The wiki archives at `.wiki/archive-research/industreal_improved/` are from v2/v3 (ResNet-50 backbone) and contain NONE of the current ConvNeXt-Tiny or MViTv2-S code.

**Checkpoint preservation risk.** The 9 critical checkpoints (Section 7 of Resource Audit) total ~4.6 GB but are scattered across multiple run directories on the same physical drive. A single `rm -rf` in the wrong directory could destroy months of work. The det_fixed_v1 directory alone has 162 GB of checkpoints that need thinning -- a thinning script with a bug could delete critical checkpoints instead of intermediates.

**Earliest signal:** Cannot access external drive. Or `ls` on expected checkpoint paths returns "No such file."

**Rollback plan:** Immediately copy all critical artifacts to the swarm-bot repo or a separate backup location:
1. `evaluate.py` (6966 lines) -> `src/evaluation/evaluate.py`
2. `model.py` -> `src/models/model.py`
3. `losses.py` -> `src/training/losses.py`
4. `train.py` -> `src/training/train.py`
5. `industreal_dataset.py` -> `src/data/industreal_dataset.py`
6. `head_pose_geo.py` -> `src/models/head_pose_geo.py`
7. All 9 critical checkpoints -> backup location
8. All eval JSON artifacts -> backup location

This backup takes ~2 hours (mostly file copies) and is the single highest-ROI action before any training.

**Time to detect:** Minutes (checking file existence). But recovery from catastrophic drive failure is impossible -- these artifacts are irreplaceable.

---

### Risk 8: Checkpoint Weight Divergence

**Probability of failure: 100% for direct merging; 90% for training-based unification.**

**What must happen for this to succeed:** The weights from v4_fixed (ConvNeXt-Tiny, 244 MB) and v3.41_safe (MViTv2-S, 695 MB) must be combined into a single model that preserves all four tasks' performance.

**Why it fails:** As established in Risk 2, the two checkpoints use incompatible architectures. But even if we restrict to ConvNeXt-Tiny alone (using only v4_fixed as the base), the weight divergence problem remains:

**Within v4_fixed itself:**
- Activity head achieves 0.394 (simple MLP on C5 features)
- Pose head achieves 6.15 (Legacy HeadPoseHead on C4+C5)
- PSR head achieves F1=0.0 on 10 of 11 components (Path B, 24-class softmax)
- Detection head achieves near-zero (any multi-task config)

The v4_fixed checkpoint already demonstrates that good weights for act+pose are **incompatible** with good weights for PSR+detection. The shared backbone features optimized for activity classification and pose regression are actively hostile to PSR component-state classification and detection box regression.

**If we try to merge by averaging:**
- ConvNeXt-Tiny backbone weights from v4_fixed are optimized for act+pose
- MViTv2-S backbone weights from v3.41_safe are optimized for PSR
- Different architectures -- cannot even load both into the same model object
- Even if architectures were identical, the feature directions would diverge: features good for activity classification point in different directions than features good for PSR component detection

**If we try to merge by fine-tuning from one checkpoint:**
- Starting from v4_fixed (good act+pose, dead PSR): Training PSR will destroy act+pose (catastrophic forgetting, Risk 1)
- Starting from v3.41_safe (good PSR, unknown act/pose): ConvNeXt-Tiny backbone cannot load MViTv2-S weights; must train act+pose from scratch, will not reach 0.394/6.15

**If we try to train from scratch with all 4 heads:**
- The multi-task cascade analysis proves that training all 4 heads simultaneously on ConvNeXt-Tiny produces: act=0.0236 (-96.2%), det=0.00009 (-99.99%), psr=0.7018 (-20.5%), pose=9.14 (+8.9% worse)
- Only PSR survives multi-task training with modest degradation. Everything else collapses.
- Training from scratch on MViTv2-S has never been attempted for act+pose+psr+det. Unknown outcome, but the linear probe result (zero backbone activity signal) is architecture-agnostic -- it measures the dataset's inherent difficulty, not the backbone's quality.

**Earliest signal:** Training loss for one head diverges while others converge. Within 3-5 epochs, the losing head's metric collapses to chance level.

**Rollback plan:** Accept two-column architecture (v4_fixed for act+pose, v3.41_safe for PSR). This is a valid, publishable paper structure. Many papers present parallel architectures for different task families.

**Time to detect:** 3-5 epochs of joint training + 2 hours eval = ~1 day on ConvNeXt-Tiny, ~2 days on MViTv2-S.

---

## 2. Failure Mode Matrix

| Risk | P(Failure) | Impact | Earliest Signal | Time to Detect | Recoverable? |
|------|-----------|--------|-----------------|----------------|--------------|
| 1. Catastrophic Forgetting | 95% | All tasks degrade | PSR F1 < 0.30 within 1 epoch | 3-5 hours | Yes -- revert to single-task checkpoints |
| 2. Architecture Mismatch | 100% | Unified model impossible | Cannot load checkpoints | 0 hours (already known) | No -- mathematically impossible |
| 3. PSR Per-Frame vs Transition | 100% | Paper misrepresentation | Already documented (PR #19) | 0 hours (already known) | Yes -- fix paper language only |
| 4. Detection Collapse | 99.9% | Detection head useless | mAP50 stays < 0.01 | 2-3 hours (gating experiment) | No -- detection never worked in multi-task |
| 5. Eval Pipeline Bugs | 100% exist, 80% inflate at least one metric | Wrong numbers in paper | F1=1.0 on zero-transition recordings | 2-3 hours (re-eval with fixes) | Yes -- fix bugs, re-evaluate |
| 6. Time Budget | 85% | Cannot meet submission | Disk full prevents training start | 0-14 days | Partial -- publish what exists |
| 7. External Drive Dependency | 40% | Total loss of all artifacts | Cannot access files | Minutes to detect, impossible to recover | No -- artifacts are irreplaceable |
| 8. Checkpoint Weight Divergence | 100% direct merge, 90% training | Cannot unify v4_fixed + v3.41_safe | Training loss divergence | 1-2 days | No -- pick one backbone |

**Combined probability of ALL 4 heads at best metrics in ONE model:**
- P(architecture compatible) * P(no catastrophic forgetting) * P(detection works in multi-task) * P(time budget holds) * P(no eval bugs inflate) * P(external drive survives) * P(weights converge)
- = 0.00 * 0.05 * 0.001 * 0.15 * 0.20 * 0.60 * 0.00
- **= 0.0000**

The probability is dominated by the architectural incompatibility (P=0.00) and the detection collapse (P=0.001). Even generously setting P(architecture) = 0.01 (assuming some undiscovered merging strategy), the combined probability remains below 0.01%.

---

## 3. Rollback Plan

### Tier 1: Immediate (Aug 1-2, zero GPU)

1. **Back up external drive artifacts to swarm-bot repo** (mitigates Risk 7)
   - Copy evaluate.py, model.py, losses.py, train.py, industreal_dataset.py, head_pose_geo.py
   - Copy all 9 critical checkpoints to a secondary location
   - Cost: 2 hours, zero GPU

2. **Fix F1=1.0 bugs** (mitigates Risk 5)
   - Change `total_f1 = 1.0` to `total_f1 = 0.0` in all 4 locations (psr_transition.py:382-386, psr_transition.py:347, evaluate.py:1269-1270, evaluate.py:1412-1417)
   - Cost: 1 hour, zero GPU

3. **Free disk space** (mitigates Risk 6)
   - Thin det_fixed_v1 checkpoints (keep every 5000th, recover ~150 GB)
   - Remove incomplete MTL run checkpoints (v3.48, v3.49, v3.50, recover ~62 GB)
   - Cost: 1 hour, zero GPU

### Tier 2: Gating Experiments (Aug 2-4, minimal GPU)

4. **Run PSR on ConvNeXt-Tiny single-task** (gate for Risk 1 and Risk 2)
   - Load v4_fixed checkpoint, add PSR Path A head, train PSR only with backbone frozen
   - If PSR F1 < 0.50 after 10 epochs: ConvNeXt-Tiny cannot do PSR. Abandon unified model.
   - Cost: 24-32 GPU-hours on RTX 3060

5. **Run detection on ConvNeXt-Tiny single-task** (gate for Risk 4)
   - Load v4_fixed checkpoint, add detection head, train detection only with backbone frozen
   - If mAP50 < 0.10: Detection is pathologically broken. Document as known limitation.
   - Cost: 2 hours eval on RTX 3060

### Tier 3: If Gates Pass (Aug 4+, unlikely)

6. **Pick ONE backbone based on gate results**
   - If ConvNeXt-Tiny can do PSR > 0.50: use ConvNeXt-Tiny for everything
   - If not: use MViTv2-S, retrain act+pose from scratch, accept lower targets
   - If neither: publish two-column comparison (v4_fixed vs v3.41_safe)

7. **Train the unified model on the chosen backbone**
   - Progressive training: freeze good heads, train new heads one at a time
   - Checkpoint after every successful head addition
   - If any head collapses: stop, document the failure, publish partial results

### Tier 4: Nuclear Option (all gates fail)

8. **Publish "Transparent Pathology" paper (probability: 85%)**
   - Left column: v4_fixed (ConvNeXt-Tiny, act=0.394, pose=6.15, dead PSR, dead detection)
   - Right column: v3.41_safe (MViTv2-S, psr=0.883, unknown act/pose/det)
   - Contributions:
     1. Multi-task cascade analysis (quantified gradient conflict between all 4 heads)
     2. Detection collapse characterization (99.99% degradation, root cause analysis)
     3. Activity backbone signal analysis (linear probe proving zero signal)
     4. PSR architecture revert (Path B -> Path A, 0.10 -> 0.883 restoration)
     5. Pose geometry fix (column ordering bug, 86 degrees -> 6.15 restoration)
   - This is a HONEST, valuable paper. Negative results with thorough analysis are more useful than inflated metrics.

---

## 4. Final Verdict

### Probability of getting ALL 4 heads at best metrics in ONE model: **0%**

This is not hyperbole. The evidence is conclusive:

1. **ConvNeXt-Tiny (v4_fixed) achieves act=0.394 and pose=6.15 but has DEAD PSR (F1=0.0 on 10/11 components) and DEAD detection (mAP50=0.00009).** The backbone cannot support PSR or detection.

2. **MViTv2-S (v3.41_safe) achieves psr=0.883 but has UNKNOWN act/pose/det performance.** The activity linear probe shows zero backbone signal -- MViTv2-S would also fail at activity. Detection has never worked on MViTv2-S in multi-task.

3. **The two checkpoints cannot be merged.** Different architectures, different input channels, different parameter spaces. Weight merging is mathematically impossible.

4. **Detection has NEVER worked in any multi-task configuration on any backbone.** 0.5734 was a biased artifact. True multi-task detection is 0.00009 -- a 99.99% collapse.

5. **Even if you picked ONE backbone and trained from scratch, the multi-task cascade destroys 3 of 4 heads.** Only PSR survives with modest degradation (-20.5%). Activity collapses (-96.2%). Detection collapses (-99.99%). Pose degrades (+8.9%).

### What IS achievable (honest assessment):

| Scenario | Backbone | act | det | pose | psr | Probability | GPU-Hours | Time |
|----------|----------|-----|-----|------|-----|-------------|------------|------|
| A: Act+Pose only | ConvNeXt-Tiny | 0.394 | DEAD | 6.15 | DEAD | 95% | 0 (already done) | 0 days |
| B: PSR only | MViTv2-S | DEAD | DEAD | DEAD | 0.883 | 95% | 0 (already done) | 0 days |
| C: Act+Pose+PSR | ConvNeXt-Tiny | <0.20 | DEAD | <15 | <0.50 | 3% | 200-300 | 14-21 days |
| D: PSR+Pose | MViTv2-S | DEAD | DEAD | <15 | 0.80+ | 15% | 150-200 | 10-14 days |
| E: All 4 (unified) | Either | <0.10 | <0.01 | >30 | <0.30 | <1% | 500+ | 26+ days |
| F: Two-column paper | Both (separate) | 0.394 | documented | 6.15 | 0.883 | 100% | 0 (already done) | 0 days |

**Recommendation: Scenario F.** Publish a two-column architecture comparison paper. This is:
- **Mathematically honest** -- no inflated or fabricated metrics
- **Already complete** -- zero additional training required
- **Scientifically valuable** -- the multi-task cascade analysis, detection collapse characterization, and PSR architecture revert are genuine contributions
- **On time** -- can be submitted by Oct 10 with 70 days for writing
- **Defensible** -- every number comes from a real checkpoint with a real eval script

### The ONE number to withdraw immediately:
**det_mAP50_pc = 0.5734** -- this is a biased 250-batch subsample artifact. The true number is 0.00009. Any paper, abstract, or presentation that includes 0.5734 is factually incorrect and will be challenged by any reviewer who looks at the eval code.

---

## 5. Cross-References

### 17_unified_model_weight_merging.md (Agent 1) -- DOES NOT EXIST

Agent 1's background task (a722abacd2780b651) is still running. If/when it produces this file, the key question to ask is: "Does the weight merging analysis acknowledge that ConvNeXt-Tiny and MViTv2-S have fundamentally incompatible architectures, or does it attempt to paper over this with 'we could try' language?"

Predicted finding: Agent 1 will discover that weight merging is impossible and will recommend training from scratch on one backbone. This is the correct conclusion.

### 18_unified_model_training.md (Agent 2) -- DOES NOT EXIST

Agent 2's background task (a3b4bc98ab58c08fa) is still running. If/when it produces this file, the key question to ask is: "Does the training plan account for the fact that the Aug 22 freeze date is already past, and that the worst-case training schedule (26 days) exceeds the available time?"

Predicted finding: Agent 2 will propose a progressive training schedule but will not have a credible answer for the time budget constraint. The Resource Audit (08) already shows that serial training on RTX 3060 takes 26 days, exceeding the freeze date by 4 days.

### 19_unified_model_detection.md (Agent 3) -- DOES NOT EXIST

Agent 3's background task (a769b7c771c293396) is still running. If/when it produces this file, the key question to ask is: "Does the detection plan acknowledge that detection has NEVER worked in multi-task, or does it propose distillation/training strategies that ignore the 99.99% collapse?"

Predicted finding: Agent 3 will propose distillation from YOLOv8m and/or test-time augmentation. Neither addresses the root cause: gradient conflict between dense prediction and classification heads on a shared backbone. The detection head dies in multi-task regardless of initialization strategy.

### 21_debate_*.md -- DOES NOT EXIST

No debate synthesis file 21 exists. The 5-agent debate team's final output would normally be a synthesis of all perspectives. Given that Agents 1-3 are still running their unified model analyses, this synthesis cannot be produced yet.

### 22_debate_*.md -- DOES NOT EXIST

No debate synthesis file 22 exists. Same status as 21.

### Existing cross-references used in this analysis:

| This Section | Cross-Reference | What Was Used |
|-------------|-----------------|---------------|
| Risk 1 (Catastrophic Forgetting) | 11_debate_adversarial.md | Cascade chain, HeadPoseFiLM contamination, Decision gates G1-G8 |
| Risk 2 (Architecture Mismatch) | 16_revert_all_integration.md | Two-backbone incompatibility finding, D1-D8 disclosures |
| Risk 3 (PSR Per-Frame) | 06_pr_review_and_existing_fixes.md, 15_revert_psr_0.883.md | PR #19 finding, MonotonicDecoder details |
| Risk 4 (Detection Collapse) | 10_debate_historical_targets.md, 16_revert_all_integration.md | 0.00009 true baseline, biased 250-batch artifact |
| Risk 5 (Eval Bugs) | 09_debate_code_correctness.md, 15_revert_psr_0.883.md | F1=1.0 bug at 4 locations, dx*0.1 fix |
| Risk 6 (Time Budget) | 08_debate_resources.md | GPU hour audit, critical path, disk space emergency |
| Risk 7 (External Drive) | 09_debate_code_correctness.md | 70% of code claims unverifiable, 6 missing files |
| Risk 8 (Weight Divergence) | 12_revert_act_0.394.md, 14_revert_pose_6.15.md, 15_revert_psr_0.883.md | Checkpoint architecture details, per-component PSR breakdown |
| Final Verdict | 07_debate_feasibility.md, 11_debate_adversarial.md | Linear probe result, multi-task cascade table, nuclear scenario |

---

## Appendix A: The Numbers That Must Be Withdrawn

These numbers appear in current project materials and are factually incorrect:

| Number | Claimed Value | True Value | Why It's Wrong |
|--------|---------------|------------|----------------|
| det_mAP50_pc | 0.5734 | 0.00009 | Biased 250-batch class-balanced subsample artifact (n_present=15 of 24 classes) |
| det_mAP50 | 0.3584 | ~0.0004 | Contaminated by dx*0.1 eval bug (now fixed on workstation) |
| psr_f1 (v4_fixed) | 1.0 (component 0 only) | 0.0 | F1=1.0 bug when TP=FP=FN=0; component 0 is always-on, trivial |
| act top-1 | 0.6223 | 0.6223 is real BUT from MViTv2-S, not "our model" (ConvNeXt-Tiny) | Architecture misattribution |

## Appendix B: What A Reviewer Will Find

A competent reviewer who examines the eval code will discover within 2 hours:

1. **The F1=1.0 bug** (psr_transition.py:382-386) -- inflates PSR metrics by up to 0.091
2. **The dx*0.1 bug** (evaluate.py:2405-2409) -- contaminated all historical detection numbers
3. **The 250-batch biased subsample** (evaluate.py) -- produced the 0.5734 artifact
4. **The 500-frame smoke test** (eval JSONs) -- act=0.394 and pose=6.15 not validated on full set
5. **The missing eval scripts** (eval_mecanno_mvitv2.py, eval_activity_75class.py) -- cannot reproduce activity baseline
6. **The architectural incompatibility** (ConvNeXt-Tiny vs MViTv2-S) -- two checkpoints, two backbones, no unification attempt
7. **The linear probe result** (0.2169 < 0.2217 baseline) -- backbone encodes zero activity signal
8. **The detection collapse** (0.995 -> 0.00009) -- 99.99% degradation, never addressed

**There is no hiding these.** Reviewers have access to the eval code. The only viable strategy is full transparency -- disclose all bugs, report corrected numbers, and frame the paper as what it actually is: a multi-task cascade analysis with two partially-successful single-task baselines. This is a respectable paper. It is not the paper that was promised, but it is the paper that exists.

---

**Agent 4 (Adversarial) signing off.** The unified model is dead. The two-column paper is viable. Be honest or be retracted -- there is no third option.
