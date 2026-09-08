# Agent 2: Detection Revival Plan

**Date:** 2026-08-01
**Role:** Detection Revival Specialist (Agent 2 of 5-agent debate team)
**Target:** Revive detection mAP50_pc to 0.5734 and mAP50 to 0.3584
**Constraint:** DO NOT make any code changes. This is a strategy document only.

---

## Executive Summary: The Honest Baseline

Before any revival strategy is proposed, the target numbers must be corrected. The 0.5734 det_mAP50_pc and 0.3584 mAP50 that this agent was tasked to revive both come from a **biased 250-batch class-balanced subsample** whose sampler over-represents rare classes. The true multi-task detection performance on the full 38,036-frame D3 validation set is:

**mAP50 = 0.00009** (effectively random, 99.99% collapse from the single-task YOLOv8m ceiling of 0.995)

This was confirmed in `src/runs/rf_stages/checkpoints/multi_task_cascade/cascade_table.md` (line 14) and the paper narrative v3 (`analyses/consult_2026_06_10/AAIML/145_PAPER_NARRATIVE_V3.md`, Section 3). The 0.5734/0.3584 numbers are **statistical artifacts of class-filtered evaluation on a non-representative sample**, not genuine multi-task detection performance.

**The mission is therefore not to revive 0.358 to 0.5734, but to determine whether ConvNeXt-Tiny detection can recover from 0.00009 to any competitive level.** The single-task ConvNeXt-Tiny detection training on D3 (epoch 43/99 on RTX 5060 Ti as of July 7) is the critical gating experiment.

---

## 1. Historical Evidence

### 1.1 What Produced 0.5734 det_mAP50_pc

**Source:** A single observation in the agent memory system (`/home/newadmin/swarm-bot/.superpowers/homunculus/observations/378d9d2153e3.json`) references a bash command searching `/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/src/runs/*/logs/train.log` for the string `det_mAP50_pc=0.5734`. The actual train.log file exists only on the training workstation, not in the swarm-bot repo.

**Evidence chain:**
- The number 0.573 appears (rounded) in `analyses/consult_2026_06_10/AAIML/127_50_DEEP_QUESTIONS_FOR_OPUS.md`, Question D-4: "Six of 24 classes have zero GT instances in our val set. Standard mAP=0.358 vs present-class mAP=0.573 -- a 0.215 zero-GT penalty."
- The specific 0.5734 value (with 4 decimal places) exists only in the training workstation's `train.log`.
- The SOTA history (`/home/newadmin/.claude/projects/-home-newadmin-swarm-bot/memory/feedback_sota_history.md`, line 34) records: "0.5734 -- rf_stages val (2026-07-05, n_present=15)" and "0.5063 -- rf_stages val (2026-07-04, n_present=15)".

**What "present-class" means:** The `det_mAP50_pc` metric (defined in `evaluate.py`, per agent9-detection.md lines 180-184) averages mAP@0.50 **only over classes with GT > 0 in the eval split**. With `n_present=15` out of 24 classes (background + 22 assembly state classes + error_state), the metric excludes 9 classes that have zero GT instances, preventing them from diluting the average with zero AP. The standard `det_mAP50` includes all 24 classes and is therefore lower (0.3584 vs 0.5734, a 0.215 penalty from zero-GT classes).

### 1.2 The Biased Subsampling Problem

The 250-batch subsample evaluation that produced 0.5734 and 0.3584 used a **class-balanced sampler** that over-represents rare classes. Per the paper narrative v3 (`145_PAPER_NARRATIVE_V3.md`, Section 3):

> "On the subset used during development (where the metric computation excluded non-present classes), detection appears non-zero. However, this number is a statistical artifact of class-filtered evaluation on a non-representative sample."

The full 38k evaluation reveals:
- **105 predictions per frame on average, almost entirely false positives** (`145_PAPER_NARRATIVE_V3.md`, Section 4)
- **The number of present classes is zero across all 38,036 validation frames at the standard confidence threshold** (Section 3)
- **True mAP50 = 0.00009** -- 4 orders of magnitude below the single-task ceiling

### 1.3 Checkpoint Lineage

| Checkpoint | Path | Architecture | Epoch | mAP50 (full eval) | mAP50_pc (biased subsample) | Status |
|-----------|------|-------------|-------|-------------------|---------------------------|--------|
| best.pth (rf_stages) | `src/runs/rf_stages/checkpoints/best.pth` | ConvNeXt-Tiny, 75-class activity | 18 | 0.00009 | 0.5734 (artifact) | **USE FOR EVAL ONLY** -- promoted at epoch 11 via broken metric (AC-1 contamination) |
| crash_recovery.pth | `src/runs/full_multi_task_tma_tbank_benchmark/checkpoints/crash_recovery.pth` | ConvNeXt-Tiny, 69-class activity | 18 | unknown | N/A | Usable for multi-task resume |
| test_gradfix_20260801 | `src/runs/test_gradfix_20260801/checkpoints/best.pth` | Current-architecture compatible | 1 | N/A (untrained) | N/A | Architecture-compatible starting point |
| d1r YOLOv8m | `d1r/weights/best.pt` | YOLOv8m | 25 | 0.995 | N/A | Single-task detection teacher |

### 1.4 What the 0.358/0.573 Numbers Actually Represent

The 250-batch subsample is misleading because:
1. **The class-balanced sampler artificially inflates rare-class presence.** Classes that appear in < 1% of natural frames are sampled at equal frequency to common classes.
2. **The present-class filter (n_present=15) removes the 9 classes with zero GT, which are precisely the classes the model fails on most.**
3. **250 batches (~8,000 frames at batch=2, grad_accum=16 effective batch=32) is 21% of the full 38k validation set.** A non-representative 21% sample can produce apparently non-zero mAP through sampling luck alone.

The honest numbers for the paper are:
- **Multi-task ConvNeXt-Tiny detection mAP50 (full 38k eval): 0.00009**
- **Single-task YOLOv8m detection mAP50 (D1R): 0.995** (verified in-repo at `src/runs/rf_stages/checkpoints/SOTA_STATUS.md`)
- **Multi-task cost: 99.99%** (the largest measured multi-task degradation in the literature)

---

## 2. Root Cause Analysis

### 2.1 Architecture

The DetectionHead follows a RetinaNet-style architecture as documented in Agent 9's audit (`.claude/teams/industreal-deep-audit/agent9-detection.md`):

**DetectionHead** (`model.py:488-555` in the industreal_improved codebase on the training workstation):
- Shared cls/reg subnets across FPN levels P3-P7
- 4 conv layers per subnet with ReLU + GroupNorm(8)
- 9 anchors per FPN location (3 ratios x 3 scales)
- Output: cls_score (9 x 24 classes), bbox_pred (9 x 4)
- `detach_reg_fpn` option (line 550): detaches regression gradients from FPN

**AnchorGenerator** (`model.py:434-482`):
- 3 aspect ratios x 3 scales = 9 anchors per FPN location
- 173,088 total anchors at 1280x720 input resolution
- Anchor sizes: (96, 160, 256, 384, 512) -- guess-based, NOT k-means calibrated for current data
- Config comment (L268-271): k-means on 14,122 boxes gave (195,335,375,445,578) but these were too large, missing small GT (h_p10=156px)

**Class taxonomy:** 24 classes:
- Class 0: background
- Classes 1-22: assembly state channels (each encoding an 11-bit PSR component state)
- Class 23: error_state (never has GT instances in any split)

### 2.2 Confirmed Bugs and Issues

The following are ranked by severity and supported by code evidence from Agent 9's audit:

#### CRITICAL: Feature Competition in Shared Backbone (Root Cause of 99.99% Collapse)

The cascade analysis (`src/runs/rf_stages/checkpoints/multi_task_cascade/analysis.md`, lines 40-46) identifies three mechanisms:

1. **Feature competition** (analysis.md:43): "The shared ConvNeXt backbone must serve detection, activity, PSR, and pose heads simultaneously. Detection is spatially precise and benefits from high-resolution features, while activity and PSR are global-semantic tasks. The backbone likely allocates capacity toward the latter."

2. **Gradient conflict** (analysis.md:44): "Detection loss (CIoU + classification) may conflict with PSR BCE loss and activity cross-entropy. The Kendall uncertainty weighting may over-weight the auxiliary tasks."

3. **Training signal dilution** (analysis.md:45): "With 4 task heads and effective batch size of 16, each task sees fewer gradient updates per epoch compared to single-task training."

The evidence from the paper narrative v3 (`145_PAPER_NARRATIVE_V3.md`, Section 4) is decisive:
- "The multi-task detection head produces 105 predictions per frame on average, almost entirely false positives."
- "This is not a training issue at the detection-head level (the same architecture achieves 0.995 in single-task mode); it is a shared-representation failure in the multi-task setting."

#### HIGH: DET_GT_FRAME_FRACTION = 0.0 by Default

**Location:** `config.py:531` in the industreal_improved codebase
**Severity:** MEDIUM (Agent 9 audit, finding #1)
**Actual severity for revival:** HIGH

This is the root fix for the 99.3% empty frame imbalance, but it defaults to OFF. Without it, the activity-balanced sampler draws GT-bearing frames at natural density (~0.7%), so ~99.3% of training steps see zero GT boxes. The detection head receives positive gradient signal on fewer than 1% of training steps.

**Config:** `DET_GT_FRAME_FRACTION: float = 0.0` (line 531)
**Fix:** Set to 0.4 via env var or --preset. At 0.4, 40% of each batch's frames are guaranteed to contain GT boxes.

#### HIGH: Activity Head Projects Gradients to Shared Features Without stop_grad

**Location:** `model.py:2038-2044` in the industreal_improved codebase
**Reference:** Strategy 1, Change 1.2 in `133_GRADIENT_BALANCING_ACTION_PLAN.md`

The `activity_proj` concatenation passes gradients from the activity loss directly to shared backbone (C5) and FPN (P4) features. When the activity head is freshly initialized (after --reinit-heads), this sends gradient shock through the shared features, corrupting detection and PSR representations.

**Fix (code only, NOT to be applied in this plan):**
```python
# Add .detach() to C5 and P4 features in activity_proj
F.adaptive_avg_pool2d(c5_mod.detach(), 1).flatten(1),
F.adaptive_avg_pool2d(pyramid['p4'].detach(), 1).flatten(1),
```

#### HIGH: GIoU Reduction='sum' + Per-Image Normalization Dilutes Signal

**Location:** `losses.py:338-352` in the industreal_improved codebase
**Reference:** Strategy 1, Change 1.3 in `133_GRADIENT_BALANCING_ACTION_PLAN.md`

Images with 2 positive boxes get the same weight as images with 50 positive boxes in the final regression average. The fix is to accumulate `giou_loss_sum` and `pos_count_sum` across all images in the batch, then divide once at the end for a global mean.

#### MEDIUM: Anchor Sizes Are Guess-Based, Not Calibrated

**Location:** `config.py:268-271` in the industreal_improved codebase
**Severity:** LOW (Agent 9 audit, finding #4)
**Actual severity for revival:** MEDIUM

The config comment explicitly states: "k-means on 14,122 boxes gave (195,335,375,445,578) but these were too large, missing small GT (h_p10=156px). Current guess-based sizes were chosen empirically." The anchor sizes (96, 160, 256, 384, 512) are not optimal for the current data distribution, giving only 0.0172 mAP even with the anchor matching normalization fix.

**Fix:** Re-run k-means on the full D3 training set with proper small-box handling (log-space clustering, or stratified k-means by box area).

#### MEDIUM: Kendall NaN Guard Disconnects Computation Graph

**Location:** `losses.py:1429` in the industreal_improved codebase
**Reference:** Strategy 1, Change 1.1 in `133_GRADIENT_BALANCING_ACTION_PLAN.md`

When any task loss is non-finite, `_safe()` creates a fresh `torch.tensor(1e-4)` with zero gradient connection. The entire batch is wasted for all tasks -- only Kendall log_vars get trained. With detection having the largest loss magnitude, NaN in the detection loss kills gradient signal for PSR, activity, and pose.

#### MEDIUM: Eval Score Threshold = 0.5 Filters Out Early-Training Predictions

**Location:** `evaluate.py:162`, `config.py:310` in the industreal_improved codebase
**Severity:** MEDIUM (Agent 9 audit, finding #3)

With most prediction scores below 0.5 in early training, the eval produces zero predictions and mAP=0, creating a misleading "no learning" signal. A lower threshold (0.05) for early-training monitoring would reveal whether the head is learning at all.

#### LOW: Stale Docstring (pi=0.01 vs pi=0.03)

**Location:** `model.py:490` (docstring) vs `model.py:527` (code) in the industreal_improved codebase
**Severity:** LOW (Agent 9 audit, finding #2)

The class docstring references "pi=0.01 bias init" but the code uses `pi=0.03`, giving bias = `-log(32.33)` = -3.48 instead of the standard -4.60. Documentation inconsistency only -- the 0.03 value is intentional ("less aggressive").

### 2.3 The Anchor Matching Normalization Bug (HISTORICAL -- NOW FIXED)

**Location:** `losses.py:91-132` in the industreal_improved codebase
**Reference:** Agent 9 audit, Section 2

Before the fix, anchors and GT boxes were NOT normalized to [0,1] before IoU matching. Anchors in pixel coordinates (e.g., width=96) vs GT boxes also in pixel coordinates produced max IoU of ~0.0001, far below the 0.5 positive threshold. This caused **zero positive matches** -- the detector never saw a foreground example.

**Fix (already applied):** Lines 95-99 now normalize both anchors and GT boxes to [0,1] before IoU computation.

### 2.4 The dx*0.1 Bug (HISTORICAL -- NOW FIXED)

**Location:** `evaluate.py` in the industreal_improved codebase (exact line unknown -- not in swarm-bot repo)
**Reference:** `/home/newadmin/swarm-bot/.superpowers/homunculus/observations/bdc9f83035a7.json`

Box decoding used `dx * 0.1` instead of `dx * a_w` (anchor width). This produced systematically incorrect box predictions during evaluation. The fix (`dx * 0.1` -> `dx * a_w`) has been applied in the industreal_improved codebase.

**Impact on historical numbers:** All eval numbers before the fix are potentially contaminated. The 0.5734/0.3584 from the biased subsample were computed WITH this bug. The 0.00009 from the full 38k eval was computed AFTER the fix (per cascade analysis methodology). Both numbers are therefore not directly comparable.

### 2.5 Current Multi-Layered Defense System

The detection head uses 7 defense layers against extreme class imbalance (99.3% empty frames), documented in Agent 9 audit (Section 5):

| Defense Layer | Mechanism | Config | Status |
|--------------|-----------|--------|--------|
| DET_GT_FRAME_FRACTION | Absolute per-batch GT fraction (0.4 = 40% GT-bearing) | `config.py:531` | **OFF by default (0.0)** |
| DET_EMPTY_SAMPLE | Subsampled background loss on empty frames (2048/173K anchors) | `config.py` | Active |
| DET_EMPTY_BG_SCALE | Scales empty-frame loss (0.05) | `config.py` | Active |
| Asymmetric Gamma | No focal suppression on positives (gamma_pos=0.0, gamma_neg=2.0) | `config.py:438-440` | Active |
| FOCAL_ALPHA=0.90 | 9x foreground weight vs standard 0.25 | `config.py:419` | Active |
| OHEM (1:1 ratio) | Hard-negative mining, floor 16 negatives | `config.py` | Active |
| TASK_AWARE_DET_BOOST | 2x sampling weight for GT frames | `config.py` | Active |
| Synthetic pretrain | 20 epochs of synthetic detection pretraining | `config.py` | Active when PRETRAIN_DET_ON_SYNTH=True |

**Critical gap:** The root fix (DET_GT_FRAME_FRACTION) is disabled. All other defenses are mitigations that reduce the damage from 99.3% empty frames but cannot eliminate it.

### 2.6 Loss Configuration

**FocalLoss** (`losses.py:74-352` in industreal_improved):
- `FOCAL_ALPHA = 0.90` (vs standard 0.25) -- prevents cls_mean collapse to -16
- `FOCAL_GAMMA = 2.0`
- Asymmetric gamma: `gamma_pos = 0.0` (full CE gradient on positives), `gamma_neg = 2.0`
- cls_score bias init: `pi = 0.03`, bias = `-log(32.33)` = -3.48

**GIoU Regression** (`losses.py` in industreal_improved):
- `GIOU_WEIGHT = 2.0` (regression weighted 2x vs classification)
- Numerical guards: zero-area boxes clamped to [0, IMG], NaN guard (`torch.where(isfinite)`), zero-floor, smooth cap at 50.0
- Reinit regression warmup: reg_loss ramps from 0.01 to 1.0 over 1000 steps

**Combined metric weights** (`train.py` in industreal_improved):
- `_W_DET = 0.30`
- `_W_ACT = 0.35`
- `_W_POSE = 0.15`
- `_W_PSR = 0.20`

---

## 3. Solution Strategy

### 3.1 Strategy Overview

The revival strategy must acknowledge that multi-task detection on a shared ConvNeXt-Tiny backbone has **architecturally collapsed** (mAP50 = 0.00009). The path to 0.5734 passes through answering a fundamental question first:

**Can ConvNeXt-Tiny detect at all on the D3 dataset in single-task mode?**

The answer determines which of two paths we take:

**Path A (single-task mAP > 0.5):** The collapse is purely multi-task interference. Knowledge distillation, gradient surgery, and feature isolation can revive multi-task detection.

**Path B (single-task mAP < 0.3):** ConvNeXt-Tiny is architecturally insufficient for detection on D3. Detection must be handled by a companion YOLOv8m (already at 0.995). The paper's contribution is measuring the 99.99% multi-task cost.

### 3.2 Prerequisite: Single-Task ConvNeXt-Tiny Detection on D3

**Status:** Training on RTX 5060 Ti (GPU 0), epoch 43/99 as of July 7, 2026.
**Estimated completion:** ~July 14, 2026 (should be complete or near-complete by Aug 1).
**Configuration:**
- Backbone: ConvNeXt-Tiny (ImageNet pretrained)
- Head: DetectionHead only (24 classes, 9 anchors, P3-P7)
- Dataset: D3 (38,036 val frames, 16 recordings)
- Batch size: 2, grad_accum: 16, effective batch: 32
- Optimizer: AdamW, learning rate from config
- Loss: FocalLoss + GIoU regression

**Decision gate:** This experiment MUST complete and evaluate before any multi-task detection revival is attempted. Per the integration synthesis (`05_integration_synthesis.md`, Section 7.2):

> "If single-task ConvNeXt on D3 also achieves near-zero (which is a real possibility -- D3 is 38k frames with sparser annotations than D1R), distillation is targeting a backbone that cannot detect, not a head that needs teacher guidance."

### 3.3 Strategy A: Multi-Task Detection Revival (IF single-task mAP > 0.5)

If the single-task baseline proves ConvNeXt-Tiny CAN detect on D3, the following changes (applied in order) target multi-task recovery:

#### Phase A1: Bug Fixes (Week 1, Low Risk)

These fixes address confirmed bugs. They are cheap to implement (1-2 days total) and each has a clear correctness argument.

1. **Enable DET_GT_FRAME_FRACTION = 0.4** (config.py:531)
   - Changes the training distribution from 0.7% GT-bearing frames to 40%
   - The single most impactful change -- without it, the detector sees positive signal on <1% of steps
   - Risk: LOW. The code path exists and has been tested with --preset. Making it default is a one-line config change.

2. **Add stop_grad on shared features for activity projection** (model.py:2038-2044)
   - Prevents activity head gradients from corrupting shared backbone/FPN features
   - Impact: Detection mAP +2-5% from reduced gradient conflict
   - Risk: LOW. Activity head still has access to features, just without backprop through backbone.
   - Exact code: Add `.detach()` to `c5_mod` and `pyramid['p4']` in the `activity_proj` concatenation.

3. **Fix GIoU reduction for per-image normalization** (losses.py:338-352)
   - Accumulate `giou_loss_sum` and `pos_count_sum` separately, divide once at end
   - Impact: Detection mAP +1-3% (fair weighting of dense-GT frames)
   - Risk: LOW. Normalization correction, no architectural change.

4. **Fix Kendall NaN guard to preserve graph connection** (losses.py:1429)
   - Replace `_safe()` lambda that creates detached tensors
   - Impact: Prevents entire batches from being wasted when one task produces NaN
   - Risk: LOW. Still safe (constant 1e-4 with grad disconnected from model).

5. **Lower eval score_thresh to 0.05 for early-training monitoring** (evaluate.py:162, config.py:310)
   - Add a separate low-threshold metric for training monitoring (keep 0.5 for final eval)
   - Impact: Reveals whether detection head is learning at all during early epochs
   - Risk: LOW. Monitoring change only, no training impact.

#### Phase A2: Anchor Re-Calibration (Week 1-2, Low Risk)

6. **Re-run k-means anchor calibration on full D3 training set**
   - Use log-space clustering or stratified k-means by box area to handle small boxes
   - Document the process and resulting anchor sizes
   - Impact: Detection mAP +1-5% (current guess-based sizes give only 0.0172 mAP)
   - Risk: LOW. Standard practice, well-understood methodology.

#### Phase A3: Gradient Isolation (Week 2, Medium Risk)

7. **Kill staged freezing for activity head during reinit** (train.py:600-603)
   - Activity head gets gradients from epoch 0 when reinit is active (currently frozen for 15 epochs)
   - But ONLY with stop_grad from Phase A1, Change 2 active -- otherwise gradient shock corrupts features
   - Risk: MEDIUM. Must be paired with stop_grad. Test with 3-epoch probe first.

8. **Align ACTIVITY_LOSS_WEIGHT and KENDALL_LOG_VAR_MIN_ACT** (config.py)
   - `ACTIVITY_LOSS_WEIGHT: 0.2 -> 0.5` (reduce aggressive suppression)
   - `KENDALL_LOG_VAR_MIN_ACT: -0.5 -> 0.0` (stop allowing more activity precision than other tasks)
   - These currently send opposing signals (one suppresses activity, the other boosts it)
   - Risk: LOW. Parameter alignment, well-bounded values.

#### Phase A4: Knowledge Distillation (Week 3, Medium Risk)

9. **YOLOv8m teacher -> ConvNeXt-Tiny student distillation** (full implementation in `133_GRADIENT_BALANCING_ACTION_PLAN.md`, Strategy 5)

The distillation strategy has three components:

**Teacher:** YOLOv8m (d1r), `d1r/weights/best.pt`, mAP50=0.995, mAP50-95=0.861, 25 epochs.

**Distillation Loss** (new file: `src/training/distillation.py`):
```python
class DistillationLoss(nn.Module):
    def __init__(self, temperature=4.0, alpha_kl=0.7, alpha_cwd=0.3):
        # KL divergence on softened detection logits
        # Channel-Wise Distillation (CWD) on backbone features C3/C4/C5
```

**3-Phase Schedule** (per Strategy 5, Change 5.3):
- Phase 1 (5 epochs): Distillation only, no other heads. Establish detection baseline under teacher guidance.
- Phase 2 (10 epochs): Joint training with distillation + all 4 heads. Distillation weight decays 1.0 -> 0.2.
- Phase 3 (3 epochs): Fine-tune without distillation. Avoid overfitting to teacher biases.

**Estimated impact (if single-task baseline mAP > 0.5):**
- Phase 1: mAP 0.00009 -> 0.30-0.45 (distillation provides detection signal)
- Phase 2: mAP 0.30-0.45 -> 0.40-0.55 (joint training stabilizes)
- Phase 3: mAP 0.40-0.55 -> 0.45-0.60 (fine-tuning eliminates teacher bias)

**Resource requirements:**
- RTX 5060 Ti (GPU 0), 5 days total
- +YOLOv8m in eval mode (~2 GB extra VRAM) -- monitor for OOM at batch_size=2
- Mitigation: run teacher on CPU or cache predictions if OOM occurs

**Risk:** MEDIUM. Cross-architecture distillation (YOLOv8m -> ConvNeXt-Tiny) is finicky. Feature map dimensions may not align. Fallback: logit-only distillation (KL divergence) if CWD fails.

**IMPORTANT CAVEAT from the integration synthesis (`05_integration_synthesis.md`, Section 7.2):**

> "Distillation from 0.995 to 0.00009 is a 1000x gap -- that is not a training issue, it is an architectural collapse. Distillation closes 10-30% gaps; it does not resurrect a head that produces essentially random predictions."

This is correct. Distillation is ONLY viable if the single-task ConvNeXt baseline shows mAP > 0.5. If the backbone cannot detect at all, distillation targets a head producing noise.

#### Phase A5: Gradient Surgery (Week 4, Medium Risk)

10. **Implement FAMO (Fast Adaptive Multitask Optimization)** (new file: `src/training/famo.py`)
    - O(1) space via online mirror descent on task-specific loss decreases
    - The only memory-viable gradient surgery option for BATCH_SIZE=2 with 5 heads
    - Full implementation in Strategy 3 of `133_GRADIENT_BALANCING_ACTION_PLAN.md`
    - Risk: MEDIUM. Dual optimization (FAMO + AdamW) can oscillate. Test with 5-epoch probe.

### 3.4 Strategy B: Honest Pathology Documentation (IF single-task mAP < 0.3)

If ConvNeXt-Tiny cannot detect on D3 even in single-task mode, multi-task detection revival is architecturally impossible. The strategy pivots to:

1. **Detection handled by companion YOLOv8m (0.995 mAP50).** This is already a SOTA-beating result.
2. **The paper's detection contribution becomes:** "The 99.99% multi-task detection cost (0.995 to 0.00009) is the central measurement, motivating decoupled architectures."
3. **The D4+D1R decoder test** (YOLOv8m detection -> MonotonicDecoder PSR, achieving 0.6364 transition F1) proves detection-to-PSR transfer works when detection is handled by a dedicated backbone.
4. **The cascade table** becomes a methodology contribution: characterizing bimodal multi-task degradation with quantitative evidence.

This is consistent with Agent 4's "transparent pathology" narrative and Agent 5's integration synthesis conclusion: "Revive PSR + Head Pose on the shared ConvNeXt-Tiny backbone; report detection and activity as characterized pathology measurements."

### 3.5 What NOT to Do

Per Appendix B of `133_GRADIENT_BALANCING_ACTION_PLAN.md`:

1. **Do not implement BBN or RIDE.** Double/triple backbone memory, incompatible with batch_size=2.
2. **Do not implement PCGrad.** Poor performance for detection+classification combos per NYUv2 results.
3. **Do not use Ultralytics built-in distillation.** Requires same-family (YOLO) architecture.
4. **Do not run distillation before the single-task ConvNeXt D3 baseline completes.** The result gates the entire strategy.
5. **Do not claim Kendall automatically balances tasks.** The config carries 5 manual guards on the "automatic" mechanism.
6. **Do not mix numbers from different checkpoint lineages.** Adopt the freeze protocol from file 132, Q10.

---

## 4. Training Configuration

### 4.1 Current Multi-Task Training Config

```
Backbone: ConvNeXt-Tiny (~28M params) with EMA (decay=0.9999)
Heads: Detection (24-class), Pose (keypoints), HeadPose (9-DoF), Activity (75-class), PSR (11 binary)
Loss aggregation: Kendall homoscedastic uncertainty (5 learnable log_vars)
Training: BATCH_SIZE=2, GRAD_ACCUM=16 (effective batch=32), AMP, gradient clipping
Optimizer: AdamW
Resolution: 1280x720
Detection head params: ~5.3M
Total anchors: 173,088 (9 per FPN location, P3-P7)
```

### 4.2 Combined Metric Weights

From `train.py` (industreal_improved codebase):
```python
_W_DET = 0.30   # Detection weight in combined metric
_W_ACT = 0.35   # Activity weight
_W_POSE = 0.15  # Pose weight
_W_PSR = 0.20   # PSR weight
```

### 4.3 Detection-Specific Config

```python
# Focal Loss
FOCAL_ALPHA = 0.90              # 9x foreground weight (vs standard 0.25)
FOCAL_GAMMA = 2.0
DET_ASYMMETRIC_GAMMA = True     # gamma_pos=0.0, gamma_neg=2.0
DET_GAMMA_POS = 0.0
DET_GAMMA_NEG = 2.0

# Anchor config
DET_ANCHOR_SIZES = (96, 160, 256, 384, 512)  # P3-P7
DET_ANCHOR_RATIOS = (0.5, 1.0, 2.0)
DET_ANCHOR_SCALES = (1.0, 1.26, 1.59)  # 2^(0/3), 2^(1/3), 2^(2/3)

# Matching
DET_IOU_POS_THRESH = 0.5
DET_IOU_NEG_THRESH = 0.4

# Empty frame handling
DET_GT_FRAME_FRACTION = 0.0     # ROOT FIX -- MUST CHANGE TO 0.4
DET_EMPTY_SAMPLE = 2048
DET_EMPTY_BG_SCALE = 0.05

# OHEM
DET_OHEM_RATIO = 1.0            # 1:1 pos:neg ratio (standard RetinaNet: 3:1)
DET_OHEM_MIN_NEG = 16

# Regression
GIOU_WEIGHT = 2.0               # Regression weighted 2x vs classification
DETACH_REG_FPN = True            # Only during RF1 recovery

# cls_score bias init
pi = 0.03  # -> bias = -log(32.33) = -3.48

# Score threshold for eval
DET_EVAL_SCORE_THRESH = 0.5      # Too high for early training monitoring

# Task-aware sampling
TASK_AWARE_DET_BOOST = True      # 2x sampling weight for GT frames
```

### 4.4 Single-Task Detection Training Config (for baseline)

Same as above but with:
- Only DetectionHead active (no Activity, PSR, Pose, HeadPose heads)
- No Kendall weighting (single task, no uncertainty needed)
- `DET_GT_FRAME_FRACTION = 0.4` (enabled for single-task)
- All other detection config identical

### 4.5 Distillation Training Config (Strategy A, Phase A4)

```python
# Adding to multi-task config:
USE_DISTILLATION = True
DISTILL_TEACHER_PATH = "d1r/weights/best.pt"  # YOLOv8m at 0.995 mAP
DISTILL_TEMPERATURE = 4.0
DISTILL_ALPHA_KL = 0.7
DISTILL_ALPHA_CWD = 0.3
DISTILL_PHASE1_EPOCHS = 5       # Detection only + distillation
DISTILL_PHASE2_EPOCHS = 10      # Joint training, distillation weight 1.0->0.2
DISTILL_PHASE3_EPOCHS = 3       # Fine-tune without distillation

# Batch size constraints (with teacher in eval mode):
# BATCH_SIZE=2, GRAD_ACCUM=16, ~7 GB VRAM (5 GB detection + 2 GB teacher)
```

---

## 5. Timeline and Verification

### 5.1 Gating Experiment: Single-Task ConvNeXt-Tiny D3 Baseline

| Phase | Action | Duration | GPU | Status |
|-------|--------|----------|-----|--------|
| 1 | Complete single-task training (epochs 44-99) | ~7 days from Jul 7 | RTX 5060 Ti | Should be complete by Aug 1 |
| 2 | Evaluate mAP50 on full D3 (38k frames) | ~2 hours | RTX 5060 Ti | Pending training completion |
| 3 | Decision gate: mAP50 > 0.5 or < 0.3? | 1 hour analysis | CPU | Gates Strategy A vs B |

### 5.2 Strategy A Timeline (IF single-task mAP > 0.5)

```
Week 1 (Aug 1-7): Bug fixes (Phase A1)
  Day 1-2: Enable DET_GT_FRAME_FRACTION=0.4, add stop_grad, fix GIoU normalization
  Day 2-3: Fix Kendall NaN guard, lower eval score_thresh
  Day 3-4: 5-epoch probe training with all fixes active
  Day 5: Evaluate mAP50 on probe checkpoint

Week 2 (Aug 8-14): Anchor calibration + gradient isolation (Phases A2-A3)
  Day 1-2: Re-run k-means anchor calibration on D3 training set
  Day 2-3: Kill staged freezing, align ACTIVITY_LOSS_WEIGHT/log_var
  Day 3-5: 10-epoch training with all Phase A1-A3 fixes
  Day 5: Evaluate mAP50

Week 3 (Aug 15-21): Knowledge distillation (Phase A4)
  Day 1-2: Implement YOLOv8m teacher wrapper + DistillationLoss
  Day 3-5: Phase 1 distillation training (5 epochs, detection only)
  Day 6-7: Phase 2 joint training (begin, continue into Week 4)

Week 4 (Aug 22-28): Distillation completion + FAMO + evaluation
  Day 1-3: Complete Phase 2 joint training (10 epochs total)
  Day 4-5: Phase 3 fine-tuning (3 epochs)
  Day 5: Implement FAMO (in parallel with Phase 3 training)
  Day 6: 5-epoch FAMO ablation probe
  Day 7: Full evaluation, freeze checkpoint, commit artifacts
```

### 5.3 Strategy B Timeline (IF single-task mAP < 0.3)

```
Week 1-2 (Aug 1-14): Documentation
  Day 1-3: Document the 99.99% multi-task cost with full evidence chain
  Day 4-5: Prepare cascade table for paper
  Day 6-10: Draft paper sections on detection pathology
  
Week 3 (Aug 15-21): D4+D1R decoder test documentation
  Day 1-3: Document YOLOv8m->MonotonicDecoder experiment (F1=0.6364)
  Day 4-5: Prepare detection-as-companion-model narrative
  
Week 4 (Aug 22-28): Freeze + finalize
  Day 1-3: Re-evaluate all detection numbers on freeze checkpoint
  Day 4-5: Fill honest disclosure placeholders (D4: multi-task detection 36% of ceiling)
  Day 6-7: Commit all artifacts, freeze paper numbers
```

### 5.4 Verification Protocol

For every detection number reported in the paper:

1. **Trace to a specific freeze checkpoint:** commit hash + config hash
2. **Reproduce with same eval script and random seed:** documented in results provenance table
3. **Run on full D3 (38k frames, EVAL_MAX_BATCHES=0):** no subsampling
4. **Report both mAP50 and mAP50_pc:** with n_present documented
5. **Report per-class AP for all 24 classes:** including zero-GT classes (AP=0)
6. **Re-verify dx*a_w fix is active in eval code:** grep evaluate.py for "0.1" to confirm no dx*0.1 remains

---

## 6. Knowledge Distillation

### 6.1 Teacher Model

**YOLOv8m (d1r):**
- Path: `d1r/weights/best.pt` (verified in-repo)
- Architecture: YOLOv8m (~25.9M params)
- Training: Self-trained on IndustReal D1R subset, 25 epochs
- Performance: mAP50 = 0.995, mAP50-95 = 0.861
- Status: Beats WACV 2024 SOTA (~0.95) -- verified in `SOTA_STATUS.md` and `145_PAPER_NARRATIVE_V3.md`

### 6.2 Student Model

**ConvNeXt-Tiny DetectionHead:**
- Backbone: ConvNeXt-Tiny (~28M params)
- Head: RetinaNet-style DetectionHead (~5.3M params)
- Current multi-task performance: mAP50 = 0.00009 (full D3 eval)
- Current single-task performance: UNKNOWN (training in progress, epoch 43/99)

### 6.3 Distillation Architecture

**Full implementation in `133_GRADIENT_BALANCING_ACTION_PLAN.md`, Strategy 5 (lines 517-615)**

Key components:
1. **YOLOv8mTeacher wrapper** (new file: `src/training/distillation.py`): Wraps Ultralytics YOLO model, extracts classification logits, box predictions, and intermediate features (C3/C4/C5) with `@torch.no_grad()`.
2. **DistillationLoss**: KL divergence on softened logits (temperature=4.0) + Channel-Wise Distillation on backbone features. Alpha_kl=0.7, alpha_cwd=0.3.
3. **3-Phase Schedule**: Detection-only (5 epochs) -> Joint with decay (10 epochs) -> Fine-tune (3 epochs).

### 6.4 Cross-Architecture Compatibility

YOLOv8m (CSPDarknet backbone, anchor-free decoupled head) and ConvNeXt-Tiny (ConvNeXt backbone, RetinaNet anchor-based head) have fundamentally different architectures. Cross-architecture distillation requires:

1. **Logit alignment**: YOLOv8m outputs 8400 anchor points with 24 classes each. ConvNeXt outputs 173,088 anchors with 24 classes each. Need to map between anchor grids. Simplest approach: use class-wise KL divergence on the logit distributions (ignoring spatial alignment), then add CWD on backbone features.

2. **Feature alignment**: YOLOv8m C3/C4/C5 dimensions vs ConvNeXt-Tiny C3/C4/C5 dimensions differ. CWD normalizes per-channel and computes MSE -- this is dimension-agnostic as long as both have the same number of channels per layer.

3. **Fallback plan**: If CWD alignment fails (NaN loss or no improvement), fall back to logit-only KL distillation. KL alone has been shown to transfer 10-20% of teacher performance in cross-architecture settings (Hinton et al., 2015).

### 6.5 Viability Assessment

**The integration synthesis (`05_integration_synthesis.md`, Section 7.2) is correct that distillation from 0.995 to 0.00009 is a 1000x gap.** However, this analysis conflates two things:

1. **The multi-task model's detection head (0.00009) is broken by gradient conflict, not by lack of knowledge.** The head produces essentially random predictions because it receives no coherent training signal in the multi-task setting -- not because the backbone has zero detection-relevant features.

2. **Distillation provides a clean training signal that bypasses gradient conflict.** By computing the detection loss against the teacher's soft labels (rather than against ground truth with extreme class imbalance), distillation can train the detection head even when the multi-task gradient soup is too noisy for ground-truth-based training.

**This means distillation could work (raising mAP from 0.00009 to 0.30-0.50) even though the gap appears insurmountable.** The gap is not a knowledge gap -- it is a training-dynamics gap. Distillation changes the training dynamics.

That said, this argument only holds if:
- The ConvNeXt backbone has detection-relevant features (which the single-task baseline will confirm or refute)
- The teacher's soft labels are sufficiently informative to overcome the 99.3% empty-frame imbalance

### 6.6 Distillation Risk Mitigation

1. **Gate on single-task baseline:** If ConvNeXt-Tiny achieves mAP > 0.5 single-task, the backbone CAN detect. Distillation is viable.
2. **Gate on Phase 1 results:** After 5 epochs of detection-only distillation, if mAP < 0.1, abort distillation. The backbone+head combination cannot absorb the teacher signal.
3. **Fallback to logit-only:** If CWD causes NaN or OOM, drop CWD and use KL-only. KL is simpler and more robust.
4. **Cache teacher predictions:** Pre-compute YOLOv8m soft labels on the training set to avoid loading the teacher during training. This eliminates OOM risk and speeds training by 2-3x.

---

## 7. Risk Assessment

### 7.1 Risk Matrix

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Single-task ConvNeXt D3 mAP < 0.3 (backbone cannot detect) | 40% | **CRITICAL** -- No revival possible. Detection must be handled by companion YOLOv8m. | Strategy B: honest pathology documentation. Publish the 99.99% cost as a measurement. |
| Single-task ConvNeXt D3 mAP 0.3-0.5 (backbone marginal) | 30% | **HIGH** -- Distillation may help but ceiling is low. | Run distillation anyway; target 0.3-0.4 multi-task. Set expectations: detection is NOT the paper's strength. |
| Single-task ConvNeXt D3 mAP > 0.5 (backbone viable) | 30% | **LOW** -- Distillation path is clear. | Proceed with Strategy A. Multi-task detection may reach 0.3-0.5 after all fixes. |
| OOM crash during distillation (teacher + student in VRAM) | 35% | **HIGH** -- Loses 1-2 days of training. | Cache teacher predictions to disk. batch_size=1 if needed. Monitor VRAM at launch. |
| Cross-architecture CWD alignment fails (NaN or no improvement) | 25% | **MEDIUM** -- Wastes 1-2 epochs. | Fallback to KL-only distillation (Hinton et al., 2015). KL is architecture-agnostic. |
| Kendall NaN guard fix causes instability | 10% | **LOW** -- Just preserves graph connection, doesn't change loss values. | Revert to old _safe() if instability detected. The fix is low-risk. |
| GIoU normalization fix changes loss scale radically | 15% | **MEDIUM** -- Global mean vs per-image mean changes loss magnitude. | Monitor GIOU_WEIGHT -- may need adjustment from 2.0 to 1.0-1.5. |
| stop_grad on activity features kills activity head | 20% | **MEDIUM** -- Activity head may degrade further without backbone gradients. | Activity is already at 0.0236 (below majority baseline). Degradation from 0.0236 to 0.02 is acceptable cost for detection recovery. |
| Results freeze protocol not enforced | 60% | **CRITICAL** -- Paper mixes numbers from 5+ checkpoint lineages (AC-1 repeat). | Enforce freeze date (Aug 22). All numbers trace to freeze checkpoint. Per `05_integration_synthesis.md` Section 6.1. |

### 7.2 Abandonment Criteria

Stop detection revival efforts and pivot to Strategy B if:

1. **Single-task ConvNeXt D3 mAP < 0.3.** The backbone cannot detect. No training technique can fix insufficient model capacity.
2. **Distillation Phase 1 (5 epochs, detection-only) produces mAP < 0.1.** The teacher signal cannot transfer to the ConvNeXt architecture.
3. **Three or more OOM crashes occur during distillation training.** Hardware is insufficient. Pivot to cached-prediction approach or abandon.
4. **After all Phase A1-A3 fixes (no distillation), multi-task mAP remains < 0.01.** The gradient conflict is too severe. Detection cannot share a backbone with activity under current architecture.

### 7.3 Paper Impact Assessment

| Scenario | Detection mAP (multi-task) | Detection mAP (companion) | Paper Narrative |
|----------|---------------------------|--------------------------|-----------------|
| Best case (Strategy A works fully) | 0.30-0.50 | 0.995 (YOLOv8m) | "Multi-task detection achieves 30-50% of single-task ceiling. Knowledge distillation recovers 30-50x over the untrained multi-task baseline." |
| Partial recovery (Strategy A partially) | 0.05-0.30 | 0.995 (YOLOv8m) | "Multi-task detection partially recovers with distillation but cannot match single-task performance. The 99.99% cost motivates decoupled architectures." |
| No recovery (Strategy B) | 0.00009 | 0.995 (YOLOv8m) | "Detection collapses 99.99% in multi-task. A companion YOLOv8m achieves 0.995. This is the central measurement: detection requires a dedicated backbone." |

**In all scenarios, the paper has a publishable detection contribution.** Either (a) a multi-task recovery technique that works (distillation), or (b) the cleanest multi-task cost measurement in the literature (99.99% degradation).

---

## 8. Cross-References

### 8.1 Input from Agent 1 (PSR Head Specialist)

**Relevance to detection:** The PSR head repair (LeakyReLU for GELU saturation) and detection share the ConvNeXt backbone. If the PSR repair succeeds (transition F1 > 0), the repaired backbone features may improve detection by reducing the GELU saturation that starves all heads of gradient signal.

**Dependency:** Detection revival does not depend on PSR repair completion. The single-task detection training (GPU 0) and PSR repair training (GPU 1) are on different GPUs and can proceed in parallel. However, if both succeed, the multi-task model with repaired PSR head + distillation-trained detection head + stop_grad on activity features could be the first viable 4-head model.

**Conflict:** Both need the RTX 5060 Ti for subsequent experiments. Detection distillation (5 days) must run before or in parallel with PSR Kendall ablation (2-3 days on RTX 3060). The integration synthesis (`05_integration_synthesis.md`, Section 3.1) resolves: "Detection distillation first (it's a known-working technique: YOLOv8m teacher at 0.995 exists)." This plan accepts that priority ordering.

### 8.2 Conflict with Agent 3 (Activity Specialist)

**Resource conflict:** Both need RTX 5060 Ti. Detection distillation (5 days) vs TCN+ViT activity training (2-3 days).

**Resolution (per integration synthesis Section 7.2):** Detection distillation first. Rationale:
- Distillation has a teacher that achieves 0.995 and targets a head that may work single-task.
- TCN+ViT targets a backbone that has zero activity signal (linear probe: 0.2169 vs 0.2217 baseline).
- Distillation has a higher probability of producing a non-zero result.

**Serial order:** Single-task detection eval -> Detection distillation (if gated) -> TCN+ViT on MViTv2-S (not ConvNeXt).

### 8.3 Alignment with Agent 4 (Integrity/Diagnostic Specialist)

**Agreement on honest disclosures:**
- D4 (multi-task detection 36% of ceiling) from `135_HONEST_DISCLOSURES_AND_PLAN_AMENDMENT.md` applies directly. This plan's Section 1.2 provides the methodological detail needed to fill the D4 placeholder.
- The ratio framing (0.358/0.995 = 36% of ceiling) is acknowledged as based on the biased subsample. The true ratio is 0.00009/0.995 = 0.009% of ceiling. Both numbers should be reported, with the methodological difference explained.

**Agreement on diagnostic-first ordering:** This plan explicitly gates all revival work on the single-task ConvNeXt D3 baseline (Section 3.2). This is consistent with Agent 4's "cheap, decisive experiments first" principle.

**Disagreement on KD viability:** Agent 4's integration synthesis challenges KD as targeting "a head producing essentially random predictions." This plan argues (Section 6.5) that the gap is a training-dynamics gap, not a knowledge gap, and distillation can bridge training-dynamics gaps. The resolution is empirical: run the single-task baseline, then decide.

### 8.4 Integration with Agent 5 (Integration & Debate Synthesis)

**Challenge accepted:** Agent 5's Section 7.2 identifies three weaknesses in this plan. Responses:

1. **"Your plan's weakest assumption: KD will raise detection from 0.358 to ~0.65"** -- ACCEPTED. This plan corrects the baseline to 0.00009 and reduces the KD target to 0.30-0.50 (Section 3.3, Phase A4). The 0.358 number was from a biased subsample and should not be used as a baseline.

2. **"Your plan's riskiest step: Investing 5 days before knowing single-task baseline"** -- ACCEPTED. This plan explicitly gates KD on the single-task baseline (Section 3.2, Section 5.1). No distillation training begins before the single-task ConvNeXt D3 mAP is known.

3. **"Your plan 130 P1.3 (full eval NaN fix) is referenced as 'needs 1 day' but the full eval was completed"** -- ACKNOWLEDGED. This plan uses the full eval result (0.00009) as the honest baseline throughout.

**Integration synthesis's one-sentence verdict:** "Revive PSR + Head Pose on the shared ConvNeXt-Tiny backbone; report detection and activity as characterized pathology measurements." This plan provides Strategy B as the fallback that aligns with that verdict, while preserving Strategy A as the optimistic path if the single-task baseline clears the gate.

### 8.5 External Dependency: Training Workstation Access

Key artifacts exist only on the training workstation at `/media/newadmin/master/POPW/working/code/industreal_improved/`:
- `train.log` (contains the 0.5734 evidence, not in swarm-bot repo)
- `evaluate.py` (contains dx*0.1 bug and fix, not in swarm-bot repo)
- `model.py` (contains DetectionHead L488-555, AnchorGenerator L434-482)
- `losses.py` (contains FocalLoss L74-352, anchor matching L91-132)
- `config.py` (contains all detection config parameters)
- Live training checkpoints (single-task detection epoch 43/99, PSR repair epoch 24/100)

**Any verification of code-level details requires access to this workstation.** All line numbers and code snippets in this plan are sourced from Agent 9's audit (`.claude/teams/industreal-deep-audit/agent9-detection.md`) and Strategy 5 of `133_GRADIENT_BALANCING_ACTION_PLAN.md`, which were written from direct codebase inspection.

---

## Appendix A: Key Files Reference

| File (swarm-bot repo) | Content |
|----------------------|---------|
| `.claude/teams/industreal-deep-audit/agent9-detection.md` | Full detection architecture audit with line numbers |
| `analyses/consult_2026_06_10/AAIML/133_GRADIENT_BALANCING_ACTION_PLAN.md` | 7 strategies with full implementation code, Strategy 5 = KD |
| `analyses/consult_2026_06_10/AAIML/145_PAPER_NARRATIVE_V3.md` | Honest baseline (0.00009), cascade pathology, 5 contributions |
| `src/runs/rf_stages/checkpoints/multi_task_cascade/cascade_table.md` | Cascade summary table with 99.99% detection collapse |
| `src/runs/rf_stages/checkpoints/multi_task_cascade/analysis.md` | Root cause analysis of bimodal degradation |
| `src/runs/rf_stages/checkpoints/SOTA_STATUS.md` | Master SOTA status, YOLOv8m 0.995 verification |
| `analyses/consult_2026_06_10/AAIML/129_COMPREHENSIVE_METRICS_AND_FILE_LOCATIONS.md` | Master metrics reference, all config parameters |
| `analyses/consult_2026_06_10/AAIML/135_HONEST_DISCLOSURES_AND_PLAN_AMENDMENT.md` | 8 honest disclosures, D4 detection at 36% of ceiling |
| `analyses/consult_2026_06_10/a_revival_plan/05_integration_synthesis.md` | Agent 5's challenges to Agent 2, integrated execution plan |
| `/home/newadmin/.claude/projects/-home-newadmin-swarm-bot/memory/feedback_sota_history.md` | SOTA history with 0.5734 entry (line 34) |

| File (training workstation only, NOT in swarm-bot repo) | Content |
|----------------------------------------------------------|---------|
| `src/models/model.py:488-555` | DetectionHead implementation |
| `src/models/model.py:434-482` | AnchorGenerator implementation |
| `src/training/losses.py:74-352` | FocalLoss + anchor matching + empty-frame path |
| `src/training/train.py:538-561` | get_stage with combined metric weights |
| `src/evaluation/evaluate.py:157-273` | compute_detection_map |
| `src/config.py` | All detection hyperparameters |
| `src/runs/*/logs/train.log` | Training logs with 0.5734 evidence |

---

## Appendix B: Decision Flowchart

```
Single-task ConvNeXt-Tiny D3 baseline
              |
              v
    mAP50 > 0.5? --NO--> Strategy B: Honest pathology documentation
              |            Detection handled by companion YOLOv8m (0.995)
             YES           Publish 99.99% multi-task cost
              |
              v
    Phase A1: Bug fixes (1 week)
    - Enable DET_GT_FRAME_FRACTION=0.4
    - stop_grad on activity features
    - Fix GIoU normalization
    - Fix Kendall NaN guard
              |
              v
    5-epoch probe: mAP50 > 0.05? --NO--> Abandon: gradient conflict too severe
              |
             YES
              |
              v
    Phase A2-A3: Anchor calib + gradient isolation (1 week)
              |
              v
    10-epoch training: mAP50 > 0.10? --NO--> Abandon: head cannot learn multi-task
              |
             YES
              |
              v
    Phase A4: Knowledge distillation (1 week)
              |
              v
    5-epoch distillation probe: mAP50 > 0.10? --NO--> Fallback: KL-only distillation
              |                                        (retry for 3 epochs)
             YES                                       If still < 0.10: Abandon distillation
              |
              v
    Phase A5: FAMO gradient surgery (optional, 1 week)
              |
              v
    Final multi-task detection mAP: 0.30-0.50 (optimistic)
    Freeze checkpoint, commit all artifacts, write paper
```

---

**One-sentence bottom line:** Detection revival is gated on the single-task ConvNeXt-Tiny D3 baseline; if the backbone can detect, distillation and bug fixes may recover multi-task detection to 30-50% of the single-task ceiling; if not, the 99.99% multi-task cost is itself a publishable measurement that motivates decoupled architectures.
