# Agent 3: PSR Revival Plan — From ~0.00 to 0.883

**Date:** 2026-08-01
**Role:** PSR Revival Specialist (Agent 3 of 5-agent debate team)
**Target:** psr_f1=0.883 (v3.41 eval, 2000 frames, checkpoint phase2_e3_b0.pth) / psr_pos=0.977 (benchmark training val)
**Status:** DIAGNOSTIC COMPLETE -- PLAN PHASE
**No code changes** — this is a plan document only.

---

## 1. Root Cause Analysis

### 1.1 The Architecture Gap: Path A vs Path B

The PSR head has undergone a complete architectural rewrite without any validation against the known-good baseline:

| Dimension | Path A (v3.41, PROVEN) | Path B (current, UNPROVEN) |
|-----------|----------------------|--------------------------|
| **Architecture** | MTLMViTModel with MViTv2-S backbone | ConvNeXt-Tiny with PSRHead |
| **Output format** | 11 per-component binary sigmoid outputs | Single 24-class softmax (background+22 states+error) |
| **PSR head** | PSRTransitionPredictor with MonotonicDecoder | PSRHead with causal transformer (3 layers, 4 heads, d_model=256) |
| **Decoder** | MonotonicDecoder (sustain_hi/sustain_lo, min_sustain) | None at inference; AccumulatedConfidencePSR at eval only |
| **Loss** | Per-component focal BCE loss | Class-balanced CE with focal modulation (gamma=1.5, label_smoothing=0.1) |
| **Input channels** | 9-channel (RGB+VL+StereoL+StereoR+Depth) | Current RGB-based |
| **Best known psr_f1** | **0.883** (eval_e3_b0.json, 2000 frames) | **0.10** (benchmark train.log, best val) |
| **Best known psr_pos** | Not measured in v3.41 | **0.977** (benchmark, per-frame state accuracy) |

**Root cause conclusion:** The architecture was changed from Path A (11 binary heads + MonotonicDecoder, which worked at 0.883) to Path B (24-class state classification, which peaks at 0.10) with no head-to-head validation. Path B has never been evaluated against the v3.41 baseline checkpoint. The eval infrastructure wasn't even wired for 24-class output when Path B was introduced -- `_decode_24class_psr_transitions` was added as a bridge only on 2026-07-16.

### 1.2 Three Independent Failure Mechanisms

**Failure 1: GELU Saturation (DEAD HEAD) -- FIXED**
The original PSRHead classifier used ReLU activation with bias=-1.0 initialization. This caused complete neuron death: post-GELU mean dropped to -130, post-ReLU became all zeros, and gradients were exactly zero on all 11 sub-heads for 3800+ steps. The repair (LeakyReLU(0.01) + zero bias + Xavier init std=0.01) was applied on 2026-07-07. The repair DOES activate: post-LeakyReLU mean on sequence frames jumps to +384-640. However, this only fixes the forward path -- the 24-class architecture has never been validated even with a working head.

**Failure 2: Eval Routing — FAKE metrics**
The eval dispatch (evaluate.py lines 5520-5604) has critical issues for Path B:
- `_decode_24class_psr_transitions` (line 1413) returns F1=1.0 when both GT and pred have zero transitions per recording -- the same mathematical contradiction documented in Agent 5's plan (precision=recall=0 but F1=1.0). When aggregated across recordings with mixed zero/nonzero transitions, the reported F1 is inflated.
- `compute_authors_psr_metrics` returns all zeros when no recordings are processed (line 617-627). This is the correct behavior but the debug output shows WHY: `n_no_events` recordings, `n_short` recordings, `n_no_gt` recordings. The training val benchmark showed `authors_psr_recordings=0` because the 24-class output was routed differently and the authors' path required 11-binary logits (sigmoid threshold 0.5), not 24-class softmax.
- The per-frame PSR metrics default to state_accuracy when transition F1 is zero (line 5576: `_psr_primary_f1 = _trans_f1 if _trans_f1 > 0.0 else _state_acc`). This means psr_f1=0.977 (pos) was reported as the primary metric when transition F1 was actually zero.

**Failure 3: ConvNeXt-Tiny Backbone -- insufficient PSR signal**
The v3.41 MViTv2-S backbone achieved 0.883. The current ConvNeXt-Tiny backbone achieves 0.10. Per Agent 5's cascade analysis: PSR degrades only 11.1% in multi-task vs single-task (the least affected of all heads), but the absolute number (0.10) is still far below the target. The DETACH_PSR_FPN=True default (config.py line 1335) means PSR gradients don't flow into the shared backbone -- but this also means PSR relies entirely on the frozen FPN features extracted by the detection+pose-trained backbone. If ConvNeXt-Tiny's FPN features don't encode enough assembly-state-relevant information, no PSR head architecture can compensate.

### 1.3 Per-Component Breakdown from v3.41 (Why 0.883, Not 1.0)

The v3.41 eval reveals that even the best PSR checkpoint has dead components:

| Component | F1 (swept threshold) | Best threshold | Positive rate | Status |
|-----------|---------------------|----------------|---------------|--------|
| comp0 (base installed) | 1.000 | 0.05 | 1.000 | SATURATED -- always predicts positive |
| comp1 | 0.964 | 0.45 | 0.739 | STRONG |
| comp2 | 0.961 | 0.50 | 0.739 | STRONG |
| comp3 | 0.873 | 0.70 | 0.609 | GOOD |
| comp4 | 0.000 | 0.50 | 0.000 | DEAD -- never predicted |
| comp5 | 0.900 | 0.65 | 0.609 | STRONG |
| comp6 | 0.913 | 0.75 | 0.551 | STRONG |
| comp7 | 0.000 | 0.50 | 0.000 | DEAD |
| comp8 | 0.000 | 0.50 | 0.000 | DEAD |
| comp9 | 0.000 | 0.50 | 0.000 | DEAD |
| comp10 | 0.784 | 0.35 | 0.292 | MODERATE |

**Key insight:** Four of 11 components (comp4, comp7, comp8, comp9) are dead even at the best checkpoint. The overall 0.883 F1 is heavily skewed by comp0 (always-on, F1=1.0) and comp1-2 (0.96). The actually discriminative components are comp3 (0.873), comp5 (0.900), comp6 (0.913), and comp10 (0.784). Any revival target must account for this -- achieving 0.90+ overall F1 requires resurrecting the dead components, which may be architecturally impossible on the current data.

---

## 2. Recommended Approach: Path A Restoration with Head Repair

### 2.1 Strategic Decision

**Verdict: Revert to Path A (11-binary + MonotonicDecoder) with the head repair applied.**

Rationale:
1. Path A has a proven 0.883 F1. Path B has a proven 0.10 F1. The architecture choice is not a matter of research exploration -- it is a matter of restoring known-working performance.
2. The GELU saturation fix (LeakyReLU + zero bias + Xavier init) applies equally to Path A and Path B. A repaired Path A head should at minimum recover pre-collapse performance.
3. Path B was introduced under the hypothesis that 24-class state classification would enforce structural constraints missing from independent binary classification. This hypothesis is falsified by the 0.10 training val result. Hypothesis-driven research is fine, but the hypothesis was wrong.
4. Agent 5's Step 2 gate requires transition F1 > 0.20. Path A at 0.883 passes this gate. Path B at 0.10 fails it.
5. The v3.41 checkpoint (`phase2_e3_b0.pth`) and its eval script are preserved and independently reproducible.

### 2.2 Why Not Fix Path B?

| Argument for Path B | Counter-argument |
|---------------------|------------------|
| "24-class output matches authors' pipeline (softmax -> state strings -> AccumulatedConfidencePSR)" | The authors' AccumulatedConfidencePSR operates on ANY per-frame state prediction. 11-binary -> state string conversion is trivial (threshold at 0.5 -> concatenate). The 24-class output doesn't add information; it just constrains the output space. |
| "Structural constraints prevent invalid state transitions" | The MonotonicDecoder already enforces fill-forward monotone constraint and procedure order. The 24-class output ADDS constraints at the classification level, but those constraints aren't the bottleneck -- dead components are. |
| "Class-balanced CE handles the severe class imbalance better than per-component focal BCE" | Per-component focal BCE with class-specific alpha (alpha=0.25 default, configurable per-component) handles imbalance at the component level, where the imbalance actually exists (comp0 appears in 100% of frames, comp10 appears in 29%). A single 24-class CE pools all imbalance together. |
| "Path B's causal transformer learns temporal dependencies" | Path A's MonotonicDecoder with Q48 hysteresis (sustain_hi/sustain_lo thresholds) is specifically designed for industrial assembly state transitions. A generic causal transformer doesn't encode the monotonicity constraint that assembly states only advance forward. |

### 2.3 The Path A Restoration Blueprint

The restoration requires reverting three components to their v3.41-era equivalents:

**Component 1: PSR Head Output (model.py)**
- Replace PSRHead's `classifier` (24-way) with 11 per-component transition heads
- Each head: Linear(gru_hidden, 128) -> LayerNorm -> LeakyReLU(0.01) -> Dropout -> Linear(128, 1)
- Apply the GELU saturation fix: LeakyReLU(0.01) + zero bias + Xavier init std=0.01
- Keep the causal transformer and per-frame MLP (they provide temporal context even for binary heads)
- Output: [B, 11] logits per frame (sigmoid activation in loss/decoder)

**Component 2: PSR Decoder (psr_transition.py)**
- Restore MonotonicDecoder with Q48 hysteresis: sustain_hi/sustain_lo thresholds for transition detection
- Fix the F1=1.0 bug: when TP=FP=FN=0, return F1=0.0 (not 1.0), precision=0.0, recall=0.0
- Keep the per-recording grouping that was repaired in [F22 2026-07-03]
- Enable per-component threshold calibration (sweep 0.05-0.95 in 0.05 steps)

**Component 3: Loss Function (losses.py)**
- Restore per-component focal BCE: `BCEWithLogitsLoss` with per-component alpha weighting
- Per-component alpha computed from class prevalence (analogous to current `set_psr_class_counts`)
- Focal gamma=2.0 (paper standard), alpha=0.25 default with per-component overrides from prevalence
- Enable ASL (AsymmetricLoss) as an ablation: gamma_neg=1.0, gamma_pos=0.0, clip=0.05

**Component 4: Evaluation (evaluate.py)**
- Route 11-binary output through the MonotonicDecoder path (USE_PSR_TRANSITION=True)
- Use `decode_and_score_psr` through `_group_psr_by_recording`
- Run compute_authors_psr_metrics in parallel (converts 11-binary to state strings internally)
- Compute both: transition F1/POS/Edit AND authors' F1/POS/delay
- Report per-component breakdown: F1, best threshold, positive rate, mean prob

### 2.4 What to Keep from Path B

Not everything from Path B is a regression. Retain:
- The causal transformer architecture (3 layers, 4 heads, d_model=256) -- it provides useful temporal context. Just revert the output from 24-class to 11-binary.
- The temporal smoothing loss (`_psr_temporal_smooth_weight`) -- encourages smooth state transitions.
- The sensitivity penalty (`PSR_SENSITIVITY_WEIGHT=0.01`) -- prevents class collapse.
- The MS-TCN truncated MSE smoothing (optional, USE_MS_TCN_SMOOTH flag).
- The DETACH_PSR_FPN=True default -- protects detection features.
- The class-balanced weighting infrastructure (effective-number weights via Cui et al.).

---

## 3. Specific Code Changes Required (Plan Only -- No Edits)

### 3.1 model.py: PSRHead.classifier

**Location:** `/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/src/models/model.py`, lines 1878-1884

**Current (Path B, 24-way):**
```python
self.classifier = nn.Sequential(
    nn.Linear(gru_hidden, 128),
    nn.LayerNorm(128),
    nn.LeakyReLU(negative_slope=0.01),
    nn.Dropout(dropout * 0.5),
    nn.Linear(128, num_components),  # num_components = 24
)
```

**Target (Path A, 11 binary heads):**
```python
# 11 independent per-component binary heads, each with the saturation fix.
# Each head: gru_hidden -> 128 -> LeakyReLU -> Dropout -> 1 (binary logit)
self.component_heads = nn.ModuleList([
    nn.Sequential(
        nn.Linear(gru_hidden, 128),
        nn.LayerNorm(128),
        nn.LeakyReLU(negative_slope=0.01),
        nn.Dropout(dropout * 0.5),
        nn.Linear(128, 1),
    ) for _ in range(11)
])
# Initialize: Xavier normal std=0.01, zero bias
for head in self.component_heads:
    for m in head:
        if isinstance(m, nn.Linear):
            nn.init.normal_(m.weight, std=0.01)
            nn.init.zeros_(m.bias)
```

**Forward path change:** PSRHead.forward returns [B, 11] instead of [B, 24]. Each component head processes the same per-frame feature independently. Output: concatenated [B, 11] logits.

**Sequence path change:** In model.py forward (lines ~2522-2527), replace `self.psr_head.classifier(enc_flat)` with per-component head application: iterate over 11 heads, each on `enc_flat`, concatenate.

### 3.2 model.py: PSRHead.__init__ signature

**Location:** lines 1831-1839

Change `num_components` default from 24 to 11, remove 24-class-specific attributes (`num_states`). The PSR head still uses the causal transformer internally but outputs 11 independent binary logits per frame.

### 3.3 model.py: Output dictionary key

**Location:** line 2672

Keep `"psr_logits": psr_logits` but shape changes from [B, 24] to [B, 11]. The eval dispatch checks `all_psr_logits.shape[1] == NUM_CATEGORIES (24)` for Path B routing. After the revert, this check will be False, and the code falls through to the Path A MonotonicDecoder path automatically -- no dispatch changes needed.

### 3.4 psr_transition.py: F1=1.0 bug fix

**Location:** `/home/newadmin/swarm-bot/src/models/psr_transition.py`, lines 382-386 (approximate)

**Current (bug):**
```python
if tp == 0 and fp == 0 and fn == 0:
    return 1.0  # BUG: F1=1.0 when no transitions exist
```

**Target (fix):**
```python
if tp == 0 and fp == 0 and fn == 0:
    return 0.0  # No transitions -- F1 is meaningfully zero
```

Also apply the same fix in `_decode_24class_psr_transitions` (evaluate.py line 1413) as a defensive measure even after reverting to Path A.

### 3.5 losses.py: Restore per-component binary focal loss

**Location:** `/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/src/training/losses.py`

Add a `PSRBinaryFocalLoss` class (or use existing `PSRFocalLoss` at line 951 which is already present). Key differences from Path B's `psr_state_classification_loss`:

| Dimension | Path B (current) | Path A (target) |
|-----------|-----------------|-----------------|
| Loss type | 24-way CE | 11-way independent BCE |
| Per-sample weight | Focal (1-p_t)^gamma + class weights | Focal (1-p_t)^gamma + per-component alpha |
| Label smoothing | 0.1 (PyTorch CE built-in) | Not applicable (binary) |
| Ignore handling | ignore_index=-1 (single class index) | Per-component: mask where label==-1 |
| Gradient per component | Aggregated into one CE gradient | Independent per-component gradient |

Implementation plan:
1. Each of the 11 components gets independent `BCEWithLogitsLoss` with per-component alpha
2. Alpha computed from component prevalence: alpha_c = (1 - prevalence_c) * alpha_scale
3. Focal modulation applied per-component: weight = alpha_c * (1 - p_t)^gamma
4. Loss averaged over non-ignored frames and all 11 components
5. Keep the existing `set_psr_class_counts` method (line 1554) for re-weighting

### 3.6 config.py: Toggle between Path A and Path B

**Location:** `/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/src/config.py`

Add a feature flag:
```python
USE_PSR_PATH_A = os.environ.get("USE_PSR_PATH_A", "1") == "1"  # 1 = 11-binary (proven), 0 = 24-class
```

This allows A/B comparison and smooth rollback. When USE_PSR_PATH_A=True:
- PSRHead outputs 11 binary logits
- Loss is per-component focal BCE
- Eval uses MonotonicDecoder path
- Authors' eval converts 11-binary to state strings internally

### 3.7 evaluate.py: Fix _decode_24class_psr_transitions bug defensively

**Location:** line 1413

Keep the function (it's used for Path B eval) but fix the F1=1.0 edge case:
```python
if not gt_tr.any() and not pred_tr.any():
    f1s.append(0.0)  # was 1.0 -- mathematically correct when no events
    poss.append(0.0)  # was 1.0
    edits.append(0.0)  # was 1.0
    continue
```

### 3.8 evaluate.py: Wire authors_psr_eval.py for Path A

**Location:** evaluate.py, near the existing `compute_authors_psr_metrics` call

For Path A (11-binary), convert per-frame sigmoid outputs to state strings and feed to `authors_psr_eval.compute_psr_metrics_for_dataset` instead of `compute_authors_psr_metrics`. The conversion: sigmoid(11-dim logits) > 0.5 -> binary 11-vector -> concatenate bits -> state string. The `_group_psr_by_recording` already handles per-recording grouping.

The `compute_authors_psr_metrics` function (lines 505-647) already handles 11-binary logits through its `pred_bin = (np.asarray(pred_rows) > 0.5).astype(np.int32)` conversion at line 558. This path ALREADY WORKS for 11-binary output but was being bypassed when 24-class was detected. After reverting to Path A, this function resumes working automatically.

---

## 4. Training Configuration

### 4.1 Phase 1: Verification (no training required)

**Goal:** Verify the v3.41 checkpoint still produces 0.883 on the current eval infrastructure.

**Steps:**
1. Load `mtl_v3.41_safe/checkpoints/phase2_e3_b0.pth` (MTLMViTModel, MViTv2-S, 11-component PSR)
2. Run the standalone v3.41 eval script (preserved at `mtl_v3.41_safe/eval_e3_b0.log`)
3. Confirm psr_f1=0.8827, per-class F1 breakdown matches eval_e3_b0.json
4. Cross-evaluate with the current evaluate.py to confirm the eval pipeline correctly reports the same numbers

**Duration:** 1 day (eval only, 2000 frames)
**GPU:** RTX 3060 (12 GB) or RTX 5060 Ti (16 GB)

### 4.2 Phase 2: Path A Restoration Training

**Goal:** Train a new ConvNeXt-Tiny model with restored Path A PSR head from scratch (or from the repaired checkpoint), and match or exceed 0.883.

**Checkpoint base:** Start from one of:
- (A) The repaired PSR head checkpoint (ConvNeXt-Tiny, LeakyReLU fix, epoch 24+ at July 7 -- current in-flight training)
- (B) The crash_recovery.pth from benchmark dir (ConvNeXt-Tiny, epoch 18) -- retrain from scratch with Path A head
- (C) The v3.41 phase2_e3_b0.pth (MTLMViTModel, MViTv2-S) -- different backbone, not directly usable for ConvNeXt

**Recommended:** Option A if the repaired checkpoint has non-trivial transition metrics. Option B if the repaired checkpoint's transition F1 is still zero.

**Config:**

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| `TRAIN_PSR` | True | |
| `USE_PSR_PATH_A` | 1 | 11-binary head |
| `DETACH_PSR_FPN` | True | Isolate PSR from backbone |
| `USE_PSR_SEQUENCE_MODE` | True | Causal transformer every 4 batches |
| `PSR_SEQUENCE_LENGTH` | 8 | Gives transformer meaningful temporal context |
| `PSR_WEIGHT` | 10.0 | Amplify PSR loss before Kendall weighting |
| `PSR_FOCAL_GAMMA` | 2.0 | Standard focal paper value |
| `PSR_FOCAL_ALPHA` | 0.25 | Default, overridden per-component by prevalence |
| `PSR_ONSET_WARMUP_EPOCHS` | 5 | Ramp PSR weight 0 -> target after unfreeze |
| `KENDALL_FIXED_WEIGHTS` | 0 (variable) | Opus Q1 ruling: Kendall is NOT the bottleneck; test as ablation only |
| `MIXED_PRECISION` | False | FP32 -- PSR seq loss spikes corrupt GradScaler |
| `batch_size` | 2 | Minimum for RTX 3060 stability |
| `grad_accum` | 16 | Effective batch 32 |
| `learning_rate` | 1e-4 | Standard for PSR fine-tuning |
| `PSR_SENSITIVITY_WEIGHT` | 0.01 | Prevent class collapse (carried from Path B) |
| `PSR_TEMPORAL_SMOOTH_WEIGHT` | 0.05 | Encourage smooth state evolution |
| `USE_MS_TCN_SMOOTH` | False (ablation) | Test as separate ablation |
| `PSR_LOSS_CAP` | 20.0 | Prevent NaN cascade from logit spikes |

**Dataset:** All recordings with PSR_labels_raw.csv (same as v3.41). Full dataset (38k frames). No subsampling -- class imbalance is handled by per-component focal alpha.

**Training schedule:**
- Epochs 1-5: Unfreeze PSR head only (backbone + FPN frozen). PSR weight ramps 0 -> 1.0.
- Epochs 6-20: Unfreeze FPN (backbone frozen). PSR weight at 10.0.
- Epochs 21-50: Full unfreeze (backbone + FPN + all heads). PSR weight at 10.0.
- Val eval every epoch (2000-frame subset, same recordings as v3.41 eval).

**Duration:** 5-7 days on RTX 3060 (12 GB)
**Checkpoint frequency:** Every epoch (save best by transition F1 on val)

### 4.3 Phase 3: Ablations (contingent on Phase 2 success)

Run only if Phase 2 achieves transition F1 > 0.20 (Agent 5 Step 2 gate):

1. **KENDALL_FIXED_WEIGHTS ablation** (2 days): Prove/disprove Kendall suppression. Expected: negative result (no effect).
2. **MS-TCN smoothing ablation** (1 day): Test USE_MS_TCN_SMOOTH=True. Expected: +0.02-0.05 F1.
3. **Per-component threshold sweep** (1 day, CPU): Re-calibrate best per-component sigmoid thresholds on val set.
4. **ASL (AsymmetricLoss) ablation** (2 days): gamma_neg=1.0, gamma_pos=0.0. Expected: small improvement on rare components.
5. **DETACH_PSR_FPN=False ablation** (2 days): Allow PSR gradients into shared FPN. Risk: may corrupt detection features. Monitor detection mAP alongside PSR F1.

---

## 5. Verification Protocol

### 5.1 Primary Metric: Transition F1 at threshold 0.5 (with per-component sweep)

The evaluation protocol from v3.41 (eval_e3_b0.json) must be reproduced exactly:

**Input:** Model checkpoint, input channels (RGB or 9-channel), 2000-frame val subset (same 16 recordings as v3.41 eval), PSR_labels_raw.csv

**Pipeline:**
1. Forward pass: model -> [B, 11] sigmoid logits
2. Per-component threshold sweep: [0.05, 0.10, ..., 0.95]
3. For each threshold: 11-bit binary state per frame -> transition detection (0->1 flips) -> event F1 at +/-3 frame tolerance
4. Per-component: sweep F1, select best threshold
5. Overall F1: mean of per-component best-threshold F1s (weighted or unweighted -- reproduce v3.41 methodology)
6. Compute: overall F1, per-class F1, edit score (OSA), POS, per-component positive rates

**Success criteria:**
- Primary: psr_f1 >= 0.80 (93% of 0.883 target)
- Aspirational: psr_f1 >= 0.883 (match v3.41)
- Per-component: No component at F1=0.0 (resurrect comp4, comp7, comp8, comp9)

### 5.2 Secondary Metric: Authors' PSR (F1/POS/delay)

Using `authors_psr_eval.compute_psr_metrics_for_dataset`:

1. Convert 11-binary per-frame predictions to state strings: for each frame, threshold sigmoids at best-threshold-per-component -> concatenate bits -> map to state string (or "error_state" if unmapped)
2. Run AccumulatedConfidencePSR (B2, cum_threshold=8.0, decay=0.75)
3. Score against PSR_labels.csv: F1, POS, avg_delay per recording
4. Aggregate across recordings

**Success criteria:**
- authors_psr_f1 >= 0.70 (authors' event-level metric is stricter than per-frame)
- authors_psr_pos >= 0.90
- authors_psr_recordings > 0 (current is 0 -- the pipe is broken)

### 5.3 Full-Dataset Validation (38k frames)

After Phase 2 training completes, run evaluation on ALL frames (not just 2000-frame subset):

1. Compute transition F1 with per-component thresholds from val sweep
2. Compute authors' PSR F1/POS/delay on all recordings with PSR_labels.csv
3. Compute per-recording breakdown: F1, POS, delay, n_gt_events, n_pred_events
4. Compare against copy_prev baseline (per-frame F1=0.9997 from true-signal analysis)

### 5.4 Reproducibility Checklist

- [ ] Checkpoint identified by SHA256 hash
- [ ] Config hash recorded (all config values captured)
- [ ] Eval script committed to repo
- [ ] Eval output (metrics.json) committed to repo
- [ ] Eval log (stdout) committed to repo
- [ ] Results match when re-run from the same checkpoint

---

## 6. Timeline

```
Phase 0 (NOW -- Aug 1): Verification
  Verify v3.41 checkpoint (phase2_e3_b0.pth) still produces 0.883
  Evaluate current PSR repair checkpoint for transition F1
  Duration: 1 day

Phase 1 (Aug 2-4): Code Restoration
  Revert PSRHead.classifier: 24-class -> 11-binary (model.py)
  Restore per-component focal BCE loss (losses.py)
  Fix F1=1.0 bug (psr_transition.py, evaluate.py)
  Wire authors_psr_eval.py for 11-binary input
  Add USE_PSR_PATH_A toggle (config.py)
  Unit-test with dummy 11-D logits
  Duration: 2-3 days

Phase 2 (Aug 7-15): Training
  START GATED on RTX 3060 availability (~Aug 7 per Agent 5 synthesis, Section 3.1).
  Current LeakyReLU repair (epoch ~24/100) occupies GPU 1 until ~Aug 7.
  Launch Path A restoration training from best available checkpoint.
  Monitor: transition F1, per-component F1, state accuracy, loss.
  Val eval every epoch (2000-frame subset).
  Duration: 50 epochs at ~3.2h/epoch = ~7 days on RTX 3060.

Phase 3 (Aug 16-17): Gate Evaluation
  Decision gate: transition F1 > 0.20? (Agent 5 Step 2)
  IF YES: Launch Kendall ablation (Phase 4, 2-3 days)
  IF NO: PSR revival FAILS on ConvNeXt-Tiny -> salvage analysis (Section 7.1)
  Duration: 2 days

Phase 4 (Aug 18-20): Ablations (if gated)
  Kendall fixed weights, MS-TCN, ASL, DETACH_PSR_FPN=False
  Per-component threshold sweep
  Duration: 2-3 days on RTX 3060 (parallelizable with CPU eval)

Phase 5 (Aug 21-22): Full Evaluation + Freeze
  Full 38k-frame transition F1 eval
  Full authors' PSR eval on all recordings
  Per-recording breakdown
  Freeze checkpoint + config + all artifacts
  Duration: 2 days
```

**Total wall clock:** 18-22 days from Aug 1. Realistic completion: ~Aug 22, 2026 (aligned with Agent 5's freeze date).
**Critical path:** Phase 2 is gated on RTX 3060 availability (~Aug 7). Phases 0-1 (verification, code changes) require no GPU and proceed immediately in parallel with current repair training.

---

## 7. Fallback Plans

### 7.1 If Path A restoration fails (transition F1 < 0.20 after Phase 2)

The ConvNeXt-Tiny backbone is fundamentally limited for PSR. Per Agent 5's cascade analysis, PSR degrades only 11.1% in multi-task but the absolute number is 0.10. With a working head architecture, 0.10 -> 0.20 should be achievable. If not:

- **Fallback A:** Publish per-frame F1 (0.70-0.75 from v3.41 era) with honest persistence-baseline comparison (copy_prev=0.9997). "The PSR head computes state labels but does not detect transitions. This is a methodology contribution."
- **Fallback B:** Use the v3.41 MViTv2-S checkpoint (0.883) as the PSR result. The paper acknowledges this is a different backbone and the ConvNeXt-Tiny PSR is a limitation.
- **Fallback C:** Abandon PSR on ConvNeXt-Tiny entirely. Publish PSR as the MViTv2-S result alongside ConvNeXt-Tiny's head pose (which works: ~9 deg) and detection/activity pathologies.

### 7.2 If v3.41 checkpoint cannot be reproduced

The eval infrastructure has changed since the v3.41 era. The standalone eval script may not work with current dependencies. If reproduction fails:

1. Port the v3.41 architecture (MTLMViTModel with PSRTransitionPredictor) into the current codebase as a reference model
2. Implement it as a `PSRReferenceModel` that loads phase2_e3_b0.pth and provides a forward pass
3. Evaluate with the current pipeline to establish the "oracle" number for the current eval infrastructure

### 7.3 If dead components (comp4, comp7, comp8, comp9) cannot be resurrected

These components correspond to assembly steps that may be extremely rare or visually indistinct in the data. Options:
1. **Data augmentation:** Increase sampling of frames where these components transition (targeted data loader)
2. **Class-weighted sampling:** Over-sample frames containing these transitions
3. **Accept the limitation:** Publish per-component breakdown honestly, acknowledge that some components are near-invisible in ego-centric video
4. **Component grouping:** Merge comp4+comp5 (they always appear together per procedure_info.json order) into a single prediction target

---

## 8. Cross-References

### 8.1 Dependencies on Other Agents

| Agent | Plan Reference | Dependency Type | Description |
|-------|---------------|----------------|-------------|
| Agent 1 (Activity) | `01_activity_revival.md` (501 lines, completed) | SHARED GPU, SCHEDULE | Activity plan sets TRAIN_PSR=False during activity-focused training (line 268) -- no gradient conflict. Activity training queues behind PSR repair on RTX 3060 (~Aug 7 per Agent 5). Strategy A (ConvNeXt push) and Strategy B (MViTv2-S) both compatible with PSR restoration. Linear probe result (0.2169 vs 0.2217 baseline) confirms ConvNeXt backbone has zero activity signal -- PSR is unaffected since PSR uses different feature representations (binary state classification vs 75-class activity). |
| Agent 2 (Detection) | `02_detection_revival.md` (779 lines, completed) | SHARED BACKBONE, PARALLEL GPU | Detection plan's D4+D1R decoder test (YOLOv8m detection -> MonotonicDecoder PSR, 0.6364 transition F1) proves detection-to-PSR transfer works with dedicated backbones. Detection training occupies RTX 5060 Ti (GPU 0); PSR restoration uses RTX 3060 (GPU 1) -- no GPU conflict. Detection plan references PSR repair (LeakyReLU for GELU saturation, line 651) and notes both heads share the ConvNeXt backbone. Risk: if detection single-task training succeeds, it proves the backbone CAN support detection; PSR restoration on the same backbone becomes more credible. |
| Agent 4 (Pose) | `04_pose_refinement.md` (672 lines, completed) | DIAGNOSTIC PREREQUISITE | Pose diagnostics proved the ConvNeXt backbone works for regression tasks (pose +8.9% in multi-task). This supports the hypothesis that PSR (classification) on the same backbone may be feasible. Pose plan's emphasis on column ordering (Section 1.4-1.5) is analogous to PSR's component ordering -- both require consistent input/output alignment. |
| Agent 5 (Integration) | `05_integration_synthesis.md` (425 lines, completed) | GATE | Step 2 gate: transition F1 must be > 0.20. This plan targets 0.883. NOTE: Agent 5's synthesis was written before the PSR revival plan was complete (pre-dates 03_psr_revival.md by ~20 min). It references a minimalist "PSR head repair (LeakyReLU + zero bias)" already in progress. This plan goes further -- full Path A restoration with 11-binary heads + MonotonicDecoder. |
| Agent 5 (Integration) | `05_integration_synthesis.md` | SCHEDULE | Freeze date Aug 22, 2026. This plan's Phase 5 (full eval) aligns with that date. Agent 5's one-sentence verdict: "Revive PSR + Head Pose on the shared ConvNeXt-Tiny backbone." This plan executes that verdict. |

### 8.2 Challenges from Agent 5 Addressed

**Challenge 7.1 (Kendall assumption):** Agent 5 challenged the assumption that Kendall fixed weights would raise PSR F1 from 0.7499 to 0.82. This plan AGREES -- Kendall is an ablation (Phase 3), not the primary fix. The primary fix is architecture restoration (Path B -> Path A).

**Challenge 7.1 (transition F1 target):** Agent 5 asked "What is your transition F1 target?" This plan's primary metric IS transition F1 (section 5.1), with the same methodology as the v3.41 eval (event F1 at +/-3 frame tolerance). Target: 0.80+ (93% of v3.41).

**Challenge 7.1 (per-frame F1 persistence):** Agent 5 noted per-frame F1 is dominated by copy_prev baseline (0.9997). This plan uses transition F1 (event-based) as the primary metric and includes copy_prev comparison in the verification protocol.

### 8.3 Resource Allocation (from Agent 5)

| Resource | Current Status (Aug 1) | This Plan's Usage | Conflict? |
|----------|----------------------|-------------------|-----------|
| RTX 3060 (GPU 1) | PSR repair training (LeakyReLU, epoch ~24/100, ~Aug 7 completion per Agent 5) | Phase 2 training (Aug 7-15, 50 epochs Path A) | No -- sequential. Phase 1 (code changes, Aug 2-5) runs in parallel with repair completion. Phase 2 starts after repair finishes. Agent 1's activity training queues after PSR. |
| RTX 5060 Ti (GPU 0) | Single-task ConvNeXt detection (epoch 43/99, ~Aug 7 completion) | Not needed (PSR eval fits on RTX 3060; CPU-friendly per-component threshold sweep) | No -- different GPU. Agent 2's detection distillation also queues for GPU 0, serial with current detection run. |
| CPU | LOO-CV stability, per-recording breakdown (1-2 days) | Per-component threshold sweep, transition F1 eval on cached logits (1 day) | Minor -- can serialize or run overnight. |
| Disk | Checkpoints ~670 MB each | 3-5 checkpoints (~2-3.5 GB for Phase 2) | No -- adequate space available. |

---

## 9. Appendix: Key File Locations

| File | Purpose |
|------|---------|
| `/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/runs/mtl_v3.41_safe/eval_e3_b0.json` | Canonical 0.883 PSR results |
| `/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/runs/mtl_v3.41_safe/checkpoints/phase2_e3_b0.pth` | Best v3.41 checkpoint |
| `/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/runs/mtl_v3.41_safe/eval_e3_b0.log` | v3.41 eval log |
| `/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/src/models/model.py:1798` | PSRHead class (Path B) |
| `/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/src/models/model.py:2460` | Forward path PSR sequence mode |
| `/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/src/evaluation/evaluate.py:1330` | _decode_24class_psr_transitions (Path B bridge) |
| `/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/src/evaluation/evaluate.py:505` | compute_authors_psr_metrics |
| `/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/src/evaluation/evaluate.py:5520` | Eval dispatch (Path B vs Path A routing) |
| `/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/src/evaluation/authors_psr_eval.py` | Canonical authors' eval module |
| `/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/src/training/losses.py:1195` | psr_state_classification_loss (Path B) |
| `/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/src/training/losses.py:951` | PSRFocalLoss (Path A legacy, still present) |
| `/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/src/training/losses.py:1889` | PSR loss computation in MultiTaskLoss.forward |
| `/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/src/config.py:1335` | DETACH_PSR_FPN config |
| `/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/src/config.py:1397` | USE_PSR_SEQUENCE_MODE config |
| `/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/src/data/psr_categories.py` | 24-category state space (source of truth) |
| `/home/newadmin/swarm-bot/src/models/psr_transition.py` | Path A MonotonicDecoder + F1=1.0 bug |
| `/home/newadmin/swarm-bot/src/models/psr_transition_repaired.py` | Repaired Path A architecture |
| `/home/newadmin/.claude/projects/-home-newadmin-swarm-bot/memory/feedback_sota_history.md` | Authoritative SOTA history |

---

**One-sentence plan:** Revert PSR architecture from unproven Path B (24-class state classification, 0.10 F1) back to proven Path A (11 per-component binary heads + MonotonicDecoder, 0.883 F1), apply the GELU saturation fix (LeakyReLU + zero bias), fix the F1=1.0 eval bug, retrain on ConvNeXt-Tiny for 50 epochs, and evaluate with the exact v3.41 protocol on 2000+ frames to confirm restoration.
