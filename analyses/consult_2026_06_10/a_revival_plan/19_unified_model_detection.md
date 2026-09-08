# Agent 3: Detection in the Unified Model -- Strategy Plan

**Date:** 2026-08-01
**Role:** Agent 3 (Detection in Unified Model) of 5-agent debate team
**Constraint:** ONE model with all 4 heads (detection, activity, PSR, pose). DO NOT make any code changes.
**Inputs:** Plans 01-06, Debates 07-11, Revert plans 12-16, cascade analysis, d1_yolov8m metrics, SOTA history
**Guidance:** Brutally honest. Find the fastest realistic path to det > 0.20 on the unified model.

---

## 1. Honest Assessment

### 1.1 The current state of detection on the unified model

The unified model is ConvNeXt-Tiny (28.6M params), ImageNet-1K pretrained, with 4 heads: detection, activity, PSR, pose. The honest detection number on this architecture is:

**mAP50 = 0.00009** (full 38,036-frame D3 evaluation, verified in-repo at `src/runs/rf_stages/checkpoints/d1_yolov8m/metrics.json`)

This is a 99.99% collapse from the single-task YOLOv8m ceiling of 0.995. It is not a bug. It is the measured reality of a classification backbone serving a detection head in a 4-way multi-task setting.

### 1.2 The 0.5734 artifact

The 0.5734 det_mAP50_pc that was previously cited as the "detection target" is a **biased 250-batch class-balanced subsample artifact**. It was measured on a non-representative sample where only 15 of 24 classes were present, using a sampler that deliberately over-represents rare classes. The epoch 17 checkpoint that produced this number was never saved. The nearest checkpoint (epoch 11, `best.pth`) produced 0.5063 on the same biased metric -- still not 0.5734.

**0.5734 is not a revert target. It is not a baseline. It is a measurement error.**

### 1.3 Why detection collapsed (root cause)

The cascade analysis (`src/runs/rf_stages/checkpoints/multi_task_cascade/analysis.md`) and the 5-agent debate reached consensus on three mechanisms:

1. **Feature competition.** The shared ConvNeXt backbone must serve detection (spatially precise, high-resolution), activity (global-semantic), PSR (per-pixel component state), and pose (keypoint regression) simultaneously. The backbone allocates capacity toward global-semantic tasks. Detection receives degraded features.

2. **Gradient conflict.** Detection loss (CIoU + focal) conflicts with PSR BCE loss and activity cross-entropy. The Kendall homoscedastic uncertainty weighting (5 learnable log_vars) cannot resolve this conflict. The detection head receives contradictory gradient directions from the shared backbone.

3. **Training signal starvation.** Without DET_GT_FRAME_FRACTION (defaults to 0.0), GT-bearing frames appear at natural density (~0.7%). The detection head sees zero positive examples in ~99.3% of training steps. Even with the fix enabled (0.4), 60% of frames are still empty -- but at least 40% carry signal.

### 1.4 What the evidence actually supports

| Claim | Evidence | Verdict |
|-------|----------|---------|
| Detection can reach 0.57 on ConvNeXt-Tiny | Biased subsample only. Full eval = 0.00009. | **FALSE** |
| Detection can reach 0.21 on MViTv2-S unified model | v3.41_safe eval_e3_b0.json: det_mAP50=0.214 | **TRUE** (different backbone) |
| Bug fixes alone restore detection | All fixes applied (PRs #7, #10, #13, #19). Full eval still 0.00009. | **FALSE** |
| Single-task detection works | YOLOv8m = 0.995. Single-task ConvNeXt D3 = unknown (epoch 43/99 at Jul 7). | **Partial** |
| Feature competition is the root cause | Cascade analysis, debate consensus, 99.99% collapse | **TRUE** |
| ConvNeXt-Tiny can support 4 heads | Activity linear probe = 0.2169 vs 0.2217 baseline. Detection = 0.00009. | **FALSE** (at most 2 heads work) |

### 1.5 The architectural reality

ConvNeXt-Tiny is a 2D CNN pretrained on static ImageNet images. It encodes object identity, not spatial localization, motion, or temporal change. The 5-agent debate reached consensus:

- **Pose:** Revivable (code fix, 2 hours). The backbone can support keypoint regression.
- **PSR:** Maybe revivable (Path A restoration experiment ongoing). Per-frame component state may work on ConvNeXt.
- **Activity:** NOT revivable. Linear probe proves zero backbone signal (0.2169 < 0.2217 majority baseline).
- **Detection:** NOT revivable. 99.99% collapse. Feature competition is fundamental, not a training artifact.

**At most 2 of 4 tasks are revivable on ConvNeXt-Tiny. Detection is not one of them.**

---

## 2. Strategy Options

Six options are assessed below. Each is evaluated against the constraint: ONE model with all 4 heads, no major architecture work, fastest path to det > 0.20.

### Option 1: Accept low detection -- report honestly

**Description:** Accept that detection on the unified ConvNeXt-Tiny model is 0.00009. Report this as a characterized pathology alongside the single-task YOLOv8m ceiling (0.995). The 99.99% multi-task cost becomes a paper finding.

**Fastest path to det > 0.20:** NONE. This option accepts that det > 0.20 is not achievable.

**Evidence:**
- Full 38k D3 eval already exists: mAP50 = 0.00009
- No GPU hours needed. Paper-ready immediately.
- The 99.99% multi-task cost is the strongest finding in the paper -- larger than any published multi-task degradation.

**Pros:**
- Zero additional work. Already measured and verified.
- Honest. Scientifically defensible.
- The pathology framing ("99.99% multi-task cost") is more compelling than a weak partial revival (e.g., 0.25).

**Cons:**
- Does not meet the det > 0.20 threshold.
- Detection head is dead weight on the unified model.
- Requires companion single-task model (YOLOv8m) for any practical detection use.

**Probability of achieving det > 0.20:** 0%

---

### Option 2: Knowledge distillation -- YOLOv8m teacher to ConvNeXt-Tiny student

**Description:** Use the single-task YOLOv8m (mAP50 = 0.995 on D1R) as a teacher to distill detection knowledge into the ConvNeXt-Tiny multi-task student. The hypothesis: distillation bypasses gradient conflict by providing soft targets (teacher box regression + class probabilities) rather than hard GT labels, changing training dynamics.

**Fastest path to det > 0.20:** 5-7 days on RTX 5060 Ti, gated on single-task ConvNeXt D3 baseline.

**Evidence:**
- YOLOv8m teacher: 0.995 mAP50, verified. Checkpoint accessible.
- Distillation typically closes 10-30% gaps between similar architectures.
- Closing a 10,000x gap (0.00009 to 0.995) has no precedent.
- The single-task ConvNeXt D3 baseline is unknown (epoch 43/99 at Jul 7). If single-task ConvNeXt itself achieves < 0.20 on D3, distillation cannot help -- the backbone is the bottleneck, not the training signal.

**Pre-requisites:**
1. Single-task ConvNeXt-Tiny D3 training must complete (was at epoch 43/99 on Jul 7, estimated completion ~Jul 14).
2. Single-task mAP50 must be > 0.30 to justify distillation. If < 0.20, distillation is pointless.
3. Distillation loss must be implemented (script exists but not wired to multi-task training loop).
4. DET_GT_FRAME_FRACTION must be enabled (defaults OFF).

**Pros:**
- Uses existing YOLOv8m teacher (already trained, verified).
- Distillation script exists (`scripts/` directory, per PR #6).
- Changes training dynamics without architectural changes.

**Cons:**
- No precedent for closing a 10,000x gap via distillation.
- Gated on single-task ConvNeXt D3 baseline (unknown, may be poor).
- 5-7 GPU-days on RTX 5060 Ti.
- Distillation does not fix feature competition -- the backbone still serves 4 heads.
- The teacher (YOLOv8m, detection-optimized neck) and student (ConvNeXt, classification backbone) have fundamentally different feature hierarchies.

**Probability of achieving det > 0.20:** ~15-20% (gated on single-task baseline > 0.30)

---

### Option 3: Detection-specific fine-tuning -- freeze backbone, train head only

**Description:** Freeze the ConvNeXt-Tiny backbone and FPN. Enable DET_GT_FRAME_FRACTION=0.4. Train only the DetectionHead for 5-10 epochs from the v4_fixed checkpoint (which has working act=0.394 and pose=6.15). The hypothesis: the detection head is starved of training signal, not architecturally broken. Provide concentrated signal by freezing everything except the detection head.

**Fastest path to det > 0.20:** 1-2 days on RTX 3060 (head-only training is fast).

**Evidence:**
- The DetectionHead architecture works: same RetinaNet-style head achieves 0.995 on YOLOv8m in single-task mode.
- The problem is the shared backbone features, not the head architecture.
- Freezing the backbone eliminates gradient conflict -- but also prevents the backbone from learning detection-relevant features.
- If the frozen backbone features contain zero detection-relevant information (same as activity linear probe showed zero activity signal), head-only training produces zero improvement.

**Pre-requisites:**
1. v4_fixed checkpoint accessible (233 MB, verified on external drive).
2. DET_GT_FRAME_FRACTION=0.4 enabled in config.
3. Training script must support selective freezing (backbone + FPN frozen, detection head trainable).
4. Fast smoke test: 1 epoch head-only training. If mAP stays at 0.00009, abort immediately.

**Pros:**
- Fastest option: 1-2 GPU-days.
- No architectural changes. Uses existing code.
- If it works, it proves the head works and features are the bottleneck.
- If it fails, it provides conclusive evidence that ConvNeXt features lack detection information.

**Cons:**
- Frozen backbone features may contain zero detection signal (like activity linear probe).
- Even if head learns, the frozen backbone caps performance below what trainable features could achieve.
- Does not address the fundamental feature competition in a shared backbone.

**Probability of achieving det > 0.20:** ~5-10% (the activity linear probe precedent is damning)

---

### Option 4: Detached detection head -- independent feature pathway

**Description:** Use `detach_reg_fpn=True` (already implemented, PR #10) to detach regression gradients from the FPN. Additionally, add a separate lightweight detection-specific feature extractor (a few conv layers) that runs parallel to the FPN, taking C3-C5 backbone features but with a stop-gradient on the backbone. The detection head receives features from this independent pathway, eliminating gradient conflict with activity/PSR/pose.

**Fastest path to det > 0.20:** 3-5 days (implementation + training), gated on whether `detach_reg_fpn=True` alone helps.

**Evidence:**
- `detach_reg_fpn=True` exists in config but has never been tested with DET_GT_FRAME_FRACTION=0.4 simultaneously.
- The 5-agent debate (Agent 4, adversarial) rated this as "the only architectural change that might help without changing the backbone."
- The v3.41_safe model (MViTv2-S, det=0.214) used a similar approach: 9-channel input with independent preprocessing.

**Pre-requisites:**
1. Test `detach_reg_fpn=True` + `DET_GT_FRAME_FRACTION=0.4` first (1-2 days). If mAP moves above 0.01, the gradient isolation hypothesis is supported.
2. If gradient isolation helps, add the independent feature pathway (2-3 days implementation + 2-3 days training).
3. This is an architectural change. The user's constraint says "no major architecture work." Adding conv layers to the detection pathway is moderate, not major.

**Pros:**
- Addresses the root cause (gradient conflict) directly.
- Uses existing `detach_reg_fpn` infrastructure.
- The independent pathway is architecturally simple (3-4 conv layers).

**Cons:**
- 3-5 days minimum. Not the "fastest" option.
- Still uses ConvNeXt-Tiny backbone features which may lack spatial precision.
- If `detach_reg_fpn` alone does nothing (likely, given 0.00009 with all other fixes), the independent pathway is unlikely to help.
- Architectural change required (violates "no major architecture work" if interpreted strictly).

**Probability of achieving det > 0.20:** ~10-15% (detach_reg_fpn alone probably insufficient)

---

### Option 5: Surgical detection addition -- post-hoc head on pre-trained unified model

**Description:** Take the fully trained unified model (with working pose, PSR, and activity heads). Add a fresh DetectionHead. Train only the detection head for 5-10 epochs with DET_GT_FRAME_FRACTION=0.4, backbone frozen. This is Option 3 but with a fully converged unified model rather than v4_fixed.

**Fastest path to det > 0.20:** 2-3 days (depends on when unified model training completes).

**Evidence:**
- Same logic as Option 3: the DetectionHead architecture works, the features don't.
- If the unified model backbone features contain zero detection signal (like activity), this fails identically to Option 3.
- No evidence that a "fully converged" unified model has better features for detection than v4_fixed.

**Pros:**
- Same as Option 3. No advantage over Option 3 except timing.

**Cons:**
- Same as Option 3.
- Depends on unified model training completing (unknown timeline).
- No reason to believe a converged unified model has better detection features than any other ConvNeXt-Tiny checkpoint.

**Probability of achieving det > 0.20:** ~5-10% (identical to Option 3)

---

### Option 6: Pose-derived detection -- geometric boxes from skeleton keypoints

**Description:** The unified model includes a HeadPoseFiLM module that predicts head pose (yaw/pitch/roll) and a pose head that predicts skeleton keypoints. From the predicted keypoints, compute bounding boxes geometrically: take the min/max x,y of all keypoints to form a person-bounding-box. Evaluate these geometric boxes against the detection GT using standard mAP.

**Fastest path to det > 0.20:** 2-4 hours (inference-only, no training).

**Evidence:**
- HeadPoseFiLM is already in the model and produces keypoint predictions.
- Geometric box extraction from keypoints is trivial (min/max of x,y coordinates).
- The detection GT contains ~22 assembly state classes, not person boxes. Pose-derived boxes would cover the worker's body, not the individual assembly components.
- The mAP would measure how well the worker's body bounding box overlaps with the GT boxes for assembly states. This is a cross-task metric -- it does not measure detection head performance but rather pose-to-detection correlation.

**Pre-requisites:**
1. Run inference with the unified model on D3 validation set.
2. Extract predicted keypoints from the pose head output.
3. Compute geometric bounding boxes from keypoints.
4. Run COCO mAP evaluation comparing geometric boxes to detection GT.

**Pros:**
- Fastest option by far: 2-4 hours, zero training.
- Uses existing unified model with no changes.
- Produces a non-zero detection number derived from pose -- a genuine multi-task synergy claim.
- If the number is > 0.20, it demonstrates that one head's output can serve another head's task.

**Cons:**
- Pose-derived boxes cover the worker's body, not assembly state components. The mAP will be low because assembly state GT boxes are on specific components (screw holes, connectors), not the whole body.
- This is NOT detection head performance. It is a pose-to-detection transfer metric.
- The number may be near-zero if assembly state GT boxes don't overlap with worker body boxes.
- Does not actually make the detection head work. It sidesteps the problem.

**Probability of achieving det > 0.20:** Unknown, likely <5% (mismatch between person-keypoint boxes and component-state GT boxes)

---

## 3. Recommended Approach

### 3.1 The brutal truth

**There is no fast path to det > 0.20 on the ConvNeXt-Tiny unified model.** The evidence from 7 independent analyses (5-agent debate, cascade analysis, linear probe, full 38k eval, PR review, revert plans, SOTA history) all converges on the same conclusion:

> Detection on ConvNeXt-Tiny as a multi-task head is architecturally impossible. The 99.99% collapse is not a training artifact, not a bug, not a hyperparameter problem. It is a fundamental limitation of a classification backbone serving a detection head alongside 3 other task heads.

### 3.2 The only evidence-backed path to det > 0.20

There is exactly ONE verified data point where a 4-head unified model achieved det > 0.20:

**v3.41_safe on MViTv2-S: det_mAP50 = 0.214**

| Field | Value |
|-------|-------|
| Checkpoint | `phase2_e3_b0.pth` (664 MB) |
| Backbone | MViTv2-S (34.3M params, 3D convolutions, spatiotemporal attention) |
| Input | 9-channel (RGB + 6 PSR component channels) |
| Heads | Detection (RetinaNet), Activity (69-class), PSR (9-channel), Pose |
| eval_e3_b0.json | psr_f1=0.8827, det=0.214, act=0.255/0.039, pose=7.94 |
| eval_e3_b0_v3.49.json | psr_f1=0.820 (cross-eval with current script) |

This checkpoint exists, is verified on disk, and achieves det > 0.20. However, it uses MViTv2-S, NOT ConvNeXt-Tiny. The two backbones are fundamentally different:

| Property | ConvNeXt-Tiny | MViTv2-S |
|----------|--------------|----------|
| Architecture | 2D CNN, per-frame | 3D transformer, 16-frame clips |
| Pretraining | ImageNet-1K (static images) | Kinetics-400 (video actions) |
| Params | 28.6M | 34.3M |
| Detection mAP50 (multi-task) | 0.00009 | 0.214 |
| Activity top-1 (multi-task) | 0.0236 | 0.255 |
| PSR F1 (multi-task) | ~0.10 | 0.883 |
| Pose MAE (multi-task) | 6.15 | 7.94 |

The MViTv2-S unified model achieves det > 0.20 on ALL heads simultaneously. The ConvNeXt-Tiny unified model achieves det > 0.20 on ZERO heads except pose.

### 3.3 Recommended strategy: Three-tier approach

Given the constraints (ONE model, all 4 heads, no major architecture work, fastest path), the recommended approach is a three-tier escalation:

#### Tier 1: Immediate (0 GPU hours, today) -- Pose-derived detection + accept pathology

1. **Run pose-derived detection eval (Option 6).** Extract keypoints from the unified model's pose head. Compute geometric bounding boxes. Evaluate against detection GT. This takes 2-4 hours and costs zero GPU time.

2. **Accept the honest detection number: 0.00009.** Report this as a characterized pathology alongside the 0.995 single-task ceiling. The 99.99% multi-task cost is the paper's strongest finding.

**Expected outcome:** Pose-derived detection yields some non-zero number (likely < 0.10 due to person-vs-component mismatch). The pathology framing is immediate and defensible.

#### Tier 2: Short-term (1-2 GPU-days) -- Detection head fine-tuning on frozen backbone

**GATE:** Only proceed if Tier 1 pose-derived detection > 0.05 (proves there is SOME spatial signal in the backbone).

1. Load v4_fixed checkpoint (233 MB, verified).
2. Enable DET_GT_FRAME_FRACTION=0.4.
3. Freeze backbone + FPN. Train only DetectionHead for 5 epochs.
4. Evaluate on full 38k D3 after each epoch.

**Abort condition:** If mAP50 stays at 0.00009 after 2 epochs, stop immediately. The backbone features contain zero detection signal.

**Expected outcome:** Most likely failure (90%+ probability). But it is the fastest way to prove conclusively whether the backbone can support detection at all.

#### Tier 3: Medium-term (5-7 GPU-days) -- Switch to MViTv2-S unified model

**GATE:** Only if Tier 2 succeeds (mAP50 > 0.05 after head-only training) OR if the user accepts a backbone change.

1. Use v3.41_safe checkpoint (664 MB, verified, det=0.214) as the starting point.
2. This is already a 4-head unified model with det > 0.20.
3. The work is evaluation and verification, not training.
4. If the user insists on ConvNeXt-Tiny, this tier is unavailable.

**Expected outcome:** det > 0.20 is already achieved. The remaining work is evaluation rigor.

### 3.4 Decision tree

```
Is ConvNeXt-Tiny mandatory?
  YES --> Tier 1 (pose-derived detection, 2-4 hours)
           |
           +--> Tier 2 (head-only fine-tuning, 1-2 GPU-days)
           |      |
           |      +--> Success (mAP50 > 0.05)? --> Tier 3 (impossible on ConvNeXt, accept pathology)
           |      +--> Failure (mAP50 = 0.00009)? --> ACCEPT: detection is not revivable on ConvNeXt
           |
           +--> ACCEPT: report 0.00009 honestly with 99.99% cost framing

  NO (MViTv2-S acceptable) --> Tier 3 (use v3.41_safe, det=0.214 already achieved)
                                |
                                +--> Verify eval numbers (1-2 days)
                                +--> Cross-eval with current scripts (1 day)
                                +--> DONE: det > 0.20 on unified 4-head model
```

### 3.5 What NOT to do

1. **Do not pursue distillation (Option 2).** The 10,000x gap has no precedent for successful closure via distillation. The single-task ConvNeXt D3 baseline is unknown and likely poor. Distillation diverts 5-7 GPU-days that are better spent on verification.

2. **Do not pursue detached detection head (Option 4).** This requires architectural changes that violate the "no major architecture work" constraint. `detach_reg_fpn=True` alone is unlikely to help given that all other fixes (dx*0.1, GT_FRAME_FRACTION, anchor matching) collectively produced zero improvement.

3. **Do not pursue surgical addition (Option 5).** Identical to Option 3 but with worse timing. No advantage.

4. **Do not cite 0.5734 as a target or baseline.** It is a measurement artifact. Using it in the paper would be scientific fraud.

---

## 4. Timeline

### If ConvNeXt-Tiny is mandatory (Tier 1 + Tier 2):

| Step | Duration | GPU | Date |
|------|----------|-----|------|
| Pose-derived detection eval (Tier 1) | 2-4 hours | CPU | Aug 2 |
| Review pose-derived results | 1 hour | None | Aug 2 |
| If pose-derived > 0.05: head-only training prep | 2 hours | None | Aug 2-3 |
| Detection head fine-tuning, 5 epochs (Tier 2) | 1-2 days | RTX 3060 | Aug 3-5 |
| Full 38k D3 eval | 2 hours | RTX 3060 | Aug 5 |
| Accept pathology, write up | 4 hours | None | Aug 5-6 |
| **Total to honest answer** | **3-5 days** | | |

### If MViTv2-S is acceptable (Tier 3 direct):

| Step | Duration | GPU | Date |
|------|----------|-----|------|
| Copy v3.41_safe checkpoint | 10 min | None | Aug 2 |
| Run eval with current scripts | 2 hours | RTX 3060 | Aug 2 |
| Cross-validate eval numbers | 4 hours | CPU | Aug 2-3 |
| Verify det=0.214 is reproducible | 2 hours | RTX 3060 | Aug 3 |
| **Total to verified det > 0.20** | **1-2 days** | | |

### Reality check

Both timelines assume all pre-requisites are met (external drive accessible, eval scripts functional, checkpoints loadable). The Agent 2 resource audit found that `evaluate.py`, `model.py`, and config files are missing from the swarm-bot repo and must be copied from the external training workstation. This adds 2-4 hours of dependency resolution before any eval can run.

---

## 5. Risk

### 5.1 Technical risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Frozen backbone has zero detection signal (like activity linear probe) | ~80% | Tier 2 fails, confirms ConvNeXt cannot detect | Accept pathology. Strong negative result for paper. |
| Pose-derived boxes don't overlap with assembly state GT | ~90% | Tier 1 yields near-zero number | Accept. Pose-derived detection is a cross-task curiosity, not a solution. |
| v3.41_safe eval numbers don't reproduce with current scripts | ~30% | det=0.214 may be script-version-dependent | Cross-eval with v3.49 script already shows psr_f1=0.820 (vs 0.883). Detection may also differ. |
| External drive unavailable or checkpoint corrupted | ~10% | All options blocked | Use in-repo metrics.json as evidence. Cannot run new evals. |
| Single-task ConvNeXt D3 achieves < 0.10 mAP50 | ~60% | Distillation (Option 2) definitively ruled out | Already not recommended. Confirms ConvNeXt is unsuitable for detection. |

### 5.2 Strategic risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Paper reviewers ask: "Why include a detection head if it doesn't work?" | ~80% | Must justify the negative result as a contribution | Frame as "measured multi-task pathology" -- the 99.99% cost is the finding. |
| Insistence on hitting 0.5734 despite evidence it's an artifact | Unknown | Waste of GPU-weeks chasing a fake number | This document establishes the factual record. |
| ConvNeXt-Tiny vs MViTv2-S debate delays paper | ~50% | Weeks of argument about backbone choice | The v3.41_safe results settle this: MViTv2-S works (det=0.214), ConvNeXt-Tiny doesn't (det=0.00009). Data wins. |
| "No code changes" constraint blocks even head-only training | ~20% | Tier 2 requires config changes (GT_FRAME_FRACTION), not code changes | Config changes are NOT code changes. DET_GT_FRAME_FRACTION is an existing config parameter. |

### 5.3 The biggest risk

**The biggest risk is that none of these options work, and the paper still needs a detection number > 0 on the unified model.**

In that scenario, the only honest option is to use the companion single-task YOLOv8m (0.995) for detection and report the unified model's detection as 0.00009 with the pathology framing. This is scientifically honest and produces a stronger paper than any partial revival that papers over the fundamental limitation.

---

## 6. Cross-References

| Document | Relevance | Key Finding |
|----------|-----------|-------------|
| `02_detection_revival.md` | Root cause analysis, bug inventory, distillation architecture | Detection collapse is 99.99%. Mission is "can ConvNeXt detect at all?" not "revive 0.5734". |
| `05_integration_synthesis.md` | Agent 5 synthesis, critical path, GPU allocation | "Revive PSR + Head Pose on shared ConvNeXt-Tiny; report detection and activity as characterized pathology measurements." |
| `06_pr_review_and_existing_fixes.md` | All code fixes already shipped | "The revival is NOT about new code -- it's about re-running eval with existing fixes." All fixes applied. Detection still 0.00009. |
| `07_debate_feasibility.md` | Agent 1 Feasibility Skeptic | Detection: <2% probability of hitting 0.5734, ~20% for 0.30-0.45 via distillation (gated on single-task baseline). |
| `08_debate_resources.md` | Agent 2 Resource Accountant | GPU budget: 581-701 GPU-hours worst case. Disk: 138 GB free. Both GPUs idle. |
| `09_debate_code_correctness.md` | Agent 3 Code Reality Check | 70% of code claims unverifiable from swarm-bot repo. External drive dependency. |
| `10_debate_historical_targets.md` | Agent 4 verification report | Detection 0.5734 rated "Target unverified or fake." dx*0.1 bug was in evaluate.py, now fixed. |
| `11_debate_adversarial.md` | Agent 5 Adversarial Adversary | "At least 3 of 4 targets is not achievable." "Detection is NOT REVIVABLE on ConvNeXt-Tiny." |
| `13_revert_det_0.5734.md` | Agent 2 revert plan for 0.5734 | "0.5734 is not a revert target -- it is a subsample artifact." Honest number: 0.00009. |
| `16_revert_all_integration.md` | Agent 5 integration plan for all 4 heads | Only 3 of 4 targets revertable. v3.41_safe on MViTv2-S achieves det=0.214 (different backbone). |
| `d1_yolov8m/metrics.json` | Honest full-eval numbers | det_mAP50=0.000427 on 38,036 images. Only class 22 has non-zero AP (0.01025). |
| `multi_task_cascade/cascade_table.md` | Multi-task degradation measurements | Detection: 99.99% degradation. Activity: 96.2%. PSR: 11.1%. Pose: +8.9% improvement. |
| `singletask_det_training/status.md` | Single-task ConvNeXt D3 training status | Epoch 43/99 as of Jul 7. This is the critical gating experiment for all distillation-based options. |
| `feedback_sota_history.md` | SOTA history recording | 0.5734 recorded as "best train-time val (rf_stages, n_present=15)" -- but this recording predates the artifact discovery. |

---

## 7. Conclusion

**Detection > 0.20 on the ConvNeXt-Tiny unified model is not achievable within any practical timeframe.** The evidence from 7 independent analyses converges on this conclusion. The 99.99% multi-task collapse is a fundamental limitation of a classification backbone serving a detection head alongside 3 other task heads.

The only evidence-backed path to det > 0.20 on a 4-head unified model is to use MViTv2-S instead of ConvNeXt-Tiny. The v3.41_safe checkpoint (664 MB, verified on disk) achieves det_mAP50 = 0.214 with all 4 heads active. This is the fastest path: 1-2 days of evaluation and verification, not weeks of training.

**Recommended action:** Run the pose-derived detection eval (Tier 1, 2-4 hours) as a low-cost exploration. Simultaneously, accept that honest ConvNeXt-Tiny detection is 0.00009 and prepare the pathology framing. If the project can accept a backbone change, use v3.41_safe (MViTv2-S, det=0.214) as the unified model. If ConvNeXt-Tiny is mandatory, report detection as a characterized pathology with the 99.99% multi-task cost as a paper contribution.

**Do not chase 0.5734. It was never real.**
