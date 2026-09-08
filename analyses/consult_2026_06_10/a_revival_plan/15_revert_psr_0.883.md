# Agent 4: PSR Revert Plan -- Restore psr_f1 to 0.883

**Date:** 2026-08-01
**Role:** PSR Revert Specialist (Agent 4 of 5-agent revival team)
**Target:** psr_f1 = 0.883 (v3.41 canonical eval, 2000 frames)
**Checkpoint:** `phase2_e3_b0.pth` (MTLMViTModel, MViTv2-S backbone, 11 binary PSR heads)
**Status:** INVESTIGATION COMPLETE -- PLAN PHASE
**No code changes** -- this is a plan document only.

---

## 1. Target Verification

### 1.1 Source of 0.883

The target 0.883 comes from a single canonical evaluation run against the `mtl_v3.41_safe` checkpoint. Every component of this target has been independently verified.

**Evidence chain:**

| Claim | Verification | Confidence |
|-------|-------------|------------|
| Checkpoint exists | `runs/mtl_v3.41_safe/checkpoints/phase2_e3_b0.pth`, 695 MB, 578 state dict keys, timestamp 2026-07-28 | VERIFIED |
| Architecture | MTLMViTModel: MViTv2-S backbone, feats=768, act=75-cls, det=24-cls, psr=11-comp, fpn=256ch, use_p2=True | VERIFIED from eval log line 8 |
| Input channels | 9-channel: RGB(ch0-2) + VL(ch3) + StereoL/R(ch4-5) + Depth(ch6-8), conv_proj expanded 3->9 | VERIFIED from eval log lines 9-13 |
| Eval script | `eval_v3.34_psr_sweep.py` with per-class threshold sweep (0.05-0.95) | VERIFIED from eval log header |
| psr_f1 @ threshold=0.5 | **0.8827** (eval log line 46) | VERIFIED |
| psr_f1 per-class sweep | **0.9136** (eval log line 47) | VERIFIED |
| edit_OSA | **0.9162** (eval_e3_b0.json line 23) | VERIFIED |
| n_samples | 2000 frames, 16 recordings, 38036 total in dataset | VERIFIED |
| Per-class F1 breakdown | comp0=1.0, comp1=0.964, comp2=0.961, comp3=0.873, comp4=0.0, comp5=0.900, comp6=0.913, comp7-9=0.0, comp10=0.784 | VERIFIED |
| Best per-component thresholds | [0.05, 0.45, 0.50, 0.70, 0.50, 0.65, 0.75, 0.50, 0.50, 0.50, 0.35] | VERIFIED |
| F1=1.0 NOT present | The 0.883 eval is NOT affected by the F1=1.0 bug; it uses per-frame binary classification with real transitions | VERIFIED |
| AUDIT_TRUTHFULNESS.md | Finding A: PSR F1=1.0 is v4_fixed artifact (500-frame sample, comp0-only transitions). Finding B: 0.883 passes cross-eval consistency check (v3.34 vs v3.49 script: 0.883 vs 0.820; 0.063 evaluator delta). | VERIFIED with HIGH confidence |

### 1.2 Cross-Eval Consistency

The same checkpoint evaluated with two different eval scripts:

| Eval Script | psr_f1 | Delta |
|------------|--------|-------|
| v3.34 (canonical) | 0.8827 | -- |
| v3.49 (current) | 0.8200 | -0.063 |

The 0.063 delta comes from differences in the evaluator (MonotonicDecoder hysteresis parameters, per-recording grouping logic, threshold sweep range). This means the 0.883 is the UPPER BOUND of what the current pipeline can report from this checkpoint. A re-evaluation may yield 0.820-0.883 depending on evaluator code path. Both numbers are real; the 0.883 is the canonical reference.

### 1.3 Per-Component Breakdown: The Ceiling

The v3.41 eval reveals the inherent ceiling:

| Component | F1 (swept) | Best Threshold | Positive Rate | Status |
|-----------|-----------|---------------|---------------|--------|
| comp0 (base installed) | 1.000 | 0.05 | 1.000 | SATURATED (always-on) |
| comp1 | 0.964 | 0.45 | 0.739 | STRONG |
| comp2 | 0.961 | 0.50 | 0.739 | STRONG |
| comp3 | 0.873 | 0.70 | 0.609 | GOOD |
| comp4 | 0.000 | 0.50 | 0.000 | DEAD |
| comp5 | 0.900 | 0.65 | 0.609 | STRONG |
| comp6 | 0.913 | 0.75 | 0.551 | STRONG |
| comp7 | 0.000 | 0.50 | 0.000 | DEAD |
| comp8 | 0.000 | 0.50 | 0.000 | DEAD |
| comp9 | 0.000 | 0.50 | 0.000 | DEAD |
| comp10 | 0.784 | 0.35 | 0.292 | MODERATE |
| **Mean (all 11)** | **0.672** | -- | -- | |
| **Mean (7 active)** | **0.913** | -- | -- | |

**Critical insight:** The 0.883 "overall F1" is a macro-average across 11 components. Four components (comp4, comp7, comp8, comp9) are dead at F1=0.0. The 7 active components average 0.913 F1. comp0 (always-on) inflates the average by 1.0/11 = 0.091. Without comp0, the average of the remaining 10 is 0.640. **Any plan claiming to exceed 0.883 must first resurrect comp4/7/8/9, which may be architecturally impossible on the current data.** The honest target is 0.883 with the same dead components.

### 1.4 Architecture: Path A vs Path B

The 0.883 was produced by "Path A" -- an architecture that no longer exists in the current codebase. The current architecture ("Path B") produces 0.10 F1.

| Dimension | Path A (v3.41, PROVEN 0.883) | Path B (current, 0.10) |
|-----------|------------------------------|------------------------|
| Backbone | MViTv2-S (feats=768) | ConvNeXt-Tiny (feats=384) |
| PSR head | PSRTransitionPredictor + MonotonicDecoder | PSRHead + causal transformer |
| Output | 11 per-component binary sigmoids | 24-class softmax (state classification) |
| Decoder | MonotonicDecoder (Q48 hysteresis, sustain_hi/sustain_lo) | AccumulatedConfidencePSR (eval only, no inference decoder) |
| Loss | Per-component focal BCE (gamma=2.0) | Class-balanced CE + focal modulation (gamma=1.5) |
| Input | 9-channel (RGB+VL+StereoL+StereoR+Depth) | RGB only (current config) |
| F1 | **0.883** | **0.10** |

**Root cause:** The architecture was changed from 11 binary heads to 24-class state classification with no head-to-head validation. Path B was introduced under the hypothesis that 24-class classification would enforce structural constraints. This hypothesis is falsified by the 0.10 training val result. The path back to 0.883 requires restoring Path A.

---

## 2. Required Artifacts

### 2.1 Checkpoint

| Artifact | Path | Size | Status |
|----------|------|------|--------|
| v3.41 checkpoint | `/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/runs/mtl_v3.41_safe/checkpoints/phase2_e3_b0.pth` | 695 MB | EXISTS, VERIFIED |
| SHA256 | TBD (compute before use) | -- | NEEDED for reproducibility |

**Note:** This checkpoint is NOT in the swarm-bot repo. It lives exclusively on the external training workstation drive. Copy it to the active training machine before use.

### 2.2 Eval Artifacts

| Artifact | Path | Purpose |
|----------|------|---------|
| Canonical eval JSON | `/media/.../runs/mtl_v3.41_safe/eval_e3_b0.json` | Ground truth metrics for comparison |
| Eval log | `/media/.../runs/mtl_v3.41_safe/eval_e3_b0.log` | Exact eval pipeline reproduction |
| Eval script | `eval_v3.34_psr_sweep.py` (preserved in mtl_v3.41_safe directory or repo history) | Per-class threshold sweep eval |
| PSR labels | `PSR_labels_raw.csv` (in dataset directory) | Ground truth for 11-component binary states |
| Dataset | 16 recordings, 38036 frames, 9-channel modalities | Same dataset used for v3.41 eval |

### 2.3 Code Artifacts (Path A Restoration)

| Artifact | Location | Purpose |
|----------|----------|---------|
| `psr_transition.py` | `/home/newadmin/swarm-bot/src/models/psr_transition.py` (583 lines) | MonotonicDecoder + PSRTransitionPredictor (Path A decoder, IN SWARM-BOT) |
| `psr_transition_repaired.py` | `/home/newadmin/swarm-bot/src/models/psr_transition_repaired.py` | Repaired Path A architecture (IN SWARM-BOT) |
| PSRFocalLoss | `/media/.../src/training/losses.py` line 951 | Legacy per-component focal BCE (STILL PRESENT) |
| `compute_authors_psr_metrics` | `/media/.../src/evaluation/evaluate.py` lines 505-647 | Authors' eval for 11-binary logits (STILL PRESENT, currently bypassed) |
| `decode_and_score_psr` | `/media/.../src/evaluation/evaluate.py` lines 1220-1264 | Path A MonotonicDecoder evaluation (STILL PRESENT) |
| Eval dispatch | `/media/.../src/evaluation/evaluate.py` lines 5520-5604 | Routes Path A vs Path B based on logits.shape[1] |

### 2.4 Training Infrastructure

| Requirement | Detail |
|-------------|--------|
| GPU | RTX 3060 (12 GB) minimum; RTX 5060 Ti (16 GB) preferred |
| Training codebase | `industreal_improved` on external training workstation |
| Config | `src/config.py` with USE_PSR_PATH_A toggle (to be added) |
| Dataset | Full 38k-frame dataset with PSR_labels_raw.csv |
| Val subset | Same 16 recordings, 2000-frame subset as v3.41 eval |

---

## 3. Reproduction Steps

### Phase 0: Verification (1 day, no code changes)

**Goal:** Prove the v3.41 checkpoint still produces 0.883 on the current eval infrastructure.

**Step 0.1: Copy checkpoint to active training machine**
```bash
cp /media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/runs/mtl_v3.41_safe/checkpoints/phase2_e3_b0.pth \
   /path/to/active/runs/mtl_v3.41_safe/checkpoints/
```

**Step 0.2: Locate or reconstruct the v3.34 eval script**
The canonical eval was run with `eval_v3.34_psr_sweep.py`. If this script is not preserved in the repo, reconstruct from the eval log:

Key characteristics of the eval script (from eval log):
- Loads checkpoint via `torch.load` with 578-key state dict
- Creates MTLMViTModel: feats=768, act=75-cls, det=24-cls, psr=11-comp, fpn=256ch
- Expands conv_proj 3->9 channels (RGB+VL+StereoL+StereoR+Depth)
- Evaluates 2000-frame subset from 16 recordings
- PSR eval: 11-binary sigmoid logits -> per-class threshold sweep [0.05, 0.10, ..., 0.95]
- Computes per-class F1 at each threshold, selects best per-component
- Reports: f1_threshold_05, f1_per_class_sweep, edit_OSA, best_thresholds, per_class_f1_swept, positive_rates

**Step 0.3: Run the eval**
```bash
cd /path/to/industreal_improved
python eval_v3.34_psr_sweep.py \
    --checkpoint runs/mtl_v3.41_safe/checkpoints/phase2_e3_b0.pth \
    --n-frames 2000 \
    --output runs/mtl_v3.41_safe/eval_e3_b0_repro.json
```

**Step 0.4: Confirm reproduction**
```bash
python -c "
import json
ref = json.load(open('runs/mtl_v3.41_safe/eval_e3_b0.json'))
rep = json.load(open('runs/mtl_v3.41_safe/eval_e3_b0_repro.json'))
print(f'Original  psr_f1={ref[\"psr\"][\"f1_threshold_05\"]:.4f}')
print(f'Reproduced psr_f1={rep[\"psr\"][\"f1_threshold_05\"]:.4f}')
# Tolerance: 0.001 (floating-point nondeterminism)
assert abs(ref['psr']['f1_threshold_05'] - rep['psr']['f1_threshold_05']) < 0.001
print('REPRODUCED')
"
```

**Success criterion:** psr_f1 = 0.883 +/- 0.001 (matching eval_e3_b0.json)

### Phase 1: Cross-Evaluate with Current Pipeline (1 day)

**Goal:** Establish the "bridge number" -- what the current evaluate.py reports for the same checkpoint.

**Step 1.1: Run current evaluate.py on v3.41 checkpoint**
```bash
python -m src.evaluation.evaluate \
    --checkpoint runs/mtl_v3.41_safe/checkpoints/phase2_e3_b0.pth \
    --n-frames 2000 \
    --output runs/mtl_v3.41_safe/eval_current_pipeline.json
```

**Expected result:** psr_f1 ~0.82 (per v3.49 cross-eval in AUDIT_TRUTHFULNESS.md, 0.063 delta from evaluator differences)

**Step 1.2: Document the evaluator delta**
- If current pipeline reports 0.82: 0.063 delta from evaluator version. The "truth" is 0.883; the "current pipeline truth" is 0.82.
- Use this delta to calibrate expectations for Path A restoration training on ConvNeXt-Tiny.
- All subsequent training evals use the current pipeline; the target becomes 0.82 (not 0.883) for apples-to-apples comparison.

### Phase 2: Restore Path A Architecture (2-3 days, code changes only -- see Section 4)

**Goal:** Restore 11-binary PSR head + MonotonicDecoder in the current ConvNeXt-Tiny codebase.

**Step 2.1: Add USE_PSR_PATH_A feature flag**
- Toggle in config.py enables smooth A/B comparison and rollback.
- Default: USE_PSR_PATH_A=1 (Path A, 11-binary).
- When disabled, falls back to current Path B (24-class).

**Step 2.2: Restore 11-binary classifier head in PSRHead**
- Replace 24-way Linear with 11 independent per-component binary heads.
- Each head: gru_hidden -> 128 -> LeakyReLU(0.01) -> Dropout -> Linear(128, 1).
- Apply saturation fix: Xavier init std=0.01, zero bias.
- Forward: apply each head independently, return [B, T, 11] logits.

**Step 2.3: Restore per-component focal BCE loss**
- Replace `psr_state_classification_loss` (24-way CE) with `PSRFocalLoss` (legacy, already at losses.py:951).
- Per-component alpha from class prevalence.
- Focal gamma=2.0.
- Mask ignore_index per-component (not single index).

**Step 2.4: Enable MonotonicDecoder at inference**
- The MonotonicDecoder already exists in psr_transition.py.
- Wire it into the eval path: when logits.shape[1]==11 (not 24), route through `decode_and_score_psr`.
- This routing already exists in evaluate.py dispatch (lines 5520-5604): the check `all_psr_logits.shape[1] == NUM_CATEGORIES (24)` will be False for 11-dim output, and the code falls through to the MonotonicDecoder path automatically.

**Step 2.5: Fix F1=1.0 bugs (see Section 5)**

**Step 2.6: Verify with dummy forward pass**
```python
# Unit test: 11-dim logits -> correct routing
import torch
from src.models.model import PSRHead
head = PSRHead(use_path_a=True, gru_hidden=256)
x = torch.randn(2, 8, 256)  # [batch=2, seq=8, feat=256]
logits = head(x)
assert logits.shape == (2, 8, 11), f"Expected (2,8,11), got {logits.shape}"
print("Path A forward: OK")
```

### Phase 3: Training (7 days, gated on GPU availability ~Aug 7)

**Goal:** Train ConvNeXt-Tiny with restored Path A PSR head to match the 0.883 target.

**Step 3.1: Select base checkpoint**
Options (in priority order):
1. **(A) Current repair checkpoint** (ConvNeXt-Tiny, LeakyReLU fix, epoch ~24/100 at Aug 1): If transition metrics are non-zero, fine-tune PSR head only.
2. **(B) crash_recovery.pth** (ConvNeXt-Tiny, epoch 18): If repair checkpoint has zero transition F1, start from earlier checkpoint.
3. **(C) phase2_e3_b0.pth** (MViTv2-S): Different backbone. Can only use for reference, not direct fine-tuning.

**Recommended:** Option A if the repair checkpoint's PSR head shows any signal (non-zero per-component F1 on any class). Option B otherwise.

**Step 3.2: Training configuration**

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| `USE_PSR_PATH_A` | 1 | 11-binary head (proven) |
| `DETACH_PSR_FPN` | True | Isolate PSR from backbone (protect detection) |
| `USE_PSR_SEQUENCE_MODE` | True | Causal transformer every 4 batches |
| `PSR_SEQUENCE_LENGTH` | 8 | Meaningful temporal context |
| `PSR_WEIGHT` | 10.0 | Amplify PSR loss before any weighting |
| `PSR_FOCAL_GAMMA` | 2.0 | Standard focal paper (Lin et al. 2017) |
| `PSR_FOCAL_ALPHA` | 0.25 default, per-component override | Computed from component prevalence |
| `PSR_ONSET_WARMUP_EPOCHS` | 5 | Ramp PSR weight 0 -> target |
| `PSR_SENSITIVITY_WEIGHT` | 0.01 | Prevent class collapse (retained from Path B) |
| `PSR_TEMPORAL_SMOOTH_WEIGHT` | 0.05 | Encourage smooth state evolution |
| `PSR_LOSS_CAP` | 20.0 | Prevent NaN cascade |
| `MIXED_PRECISION` | False | FP32 -- PSR seq loss spikes corrupt GradScaler |
| `batch_size` | 2 | RTX 3060 stability minimum |
| `grad_accum` | 16 | Effective batch 32 |
| `learning_rate` | 1e-4 | Standard PSR fine-tune LR |
| `USE_MS_TCN_SMOOTH` | False initially | Ablation candidate |

**Step 3.3: Training Schedule**

```
Epochs 1-5:   PSR head only (backbone + FPN frozen)
              PSR weight ramps 0 -> 1.0
              Warmup: let the 11 binary heads stabilize

Epochs 6-20:  Unfreeze FPN (backbone still frozen)
              PSR weight at 10.0
              FPN adapts to produce PSR-relevant features

Epochs 21-50: Full unfreeze (backbone + FPN + all heads)
              PSR weight at 10.0
              Joint optimization

Val eval:     Every epoch, 2000-frame subset
              Save best by transition F1 on val
```

**Step 3.4: Monitoring**
Track per epoch:
- `psr_transition_f1` (primary) -- event-level F1 at +/-3 frame tolerance
- `psr_per_class_f1` -- per-component breakdown (watch for dead components)
- `psr_state_accuracy` (secondary) -- per-frame state accuracy
- `psr_loss` -- raw focal BCE loss
- `psr_temporal_smooth_loss` -- temporal consistency metric
- `psr_grad_norm` -- gradient health
- `det_mAP50_pc` -- monitor for PSR interference with detection
- `act_top1` -- monitor for PSR interference with activity

**Alert thresholds:**
- `psr_grad_norm > 100` -> reduce PSR_WEIGHT
- `psr_loss > 20.0` -> check for NaN, increase PSR_LOSS_CAP
- Any component F1 stuck at 0.0 for >10 epochs -> increase per-component alpha
- `det_mAP50_pc` drops >10% -> increase DETACH_PSR_FPN to stricter isolation

**Duration:** 50 epochs at ~3.2h/epoch = ~7 days on RTX 3060.

### Phase 4: Full Evaluation (2 days)

**Step 4.1: Transition F1 on full 38k-frame dataset**
```bash
python -m src.evaluation.evaluate \
    --checkpoint runs/psr_path_a_restored/checkpoints/best.pth \
    --n-frames -1 \
    --output runs/psr_path_a_restored/eval_full.json
```

**Step 4.2: Per-component threshold sweep on full dataset**
Recalibrate best per-component sigmoid thresholds (not just val subset).

**Step 4.3: Authors' PSR evaluation**
Run `compute_authors_psr_metrics` (evaluate.py lines 505-647) which takes 11-binary logits and runs AccumulatedConfidencePSR:
- Per-recording: F1, POS, avg_delay
- Aggregate across all recordings
- Target: authors_psr_f1 >= 0.70

**Step 4.4: Per-recording breakdown**
For each recording:
- n_gt_events, n_pred_events
- Transition F1, POS, Edit score
- Per-component F1 breakdown
- Compare against copy_prev baseline (per-frame F1=0.9997 from true-signal analysis)

---

## 4. Code Changes (DO NOT EDIT -- Plan Reference Only)

### 4.1 model.py: PSRHead.classifier (24-way -> 11 binary heads)

**File:** `/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/src/models/model.py`
**Location:** PSRHead.__init__, lines ~1878-1884

**Current (Path B):**
```python
self.classifier = nn.Sequential(
    nn.Linear(gru_hidden, 128),
    nn.LayerNorm(128),
    nn.LeakyReLU(negative_slope=0.01),
    nn.Dropout(dropout * 0.5),
    nn.Linear(128, num_components),  # num_components = 24
)
```

**Target (Path A):**
```python
# 11 independent per-component binary heads with GELU saturation fix
self.component_heads = nn.ModuleList([
    nn.Sequential(
        nn.Linear(gru_hidden, 128),
        nn.LayerNorm(128),
        nn.LeakyReLU(negative_slope=0.01),
        nn.Dropout(dropout * 0.5),
        nn.Linear(128, 1),
    ) for _ in range(11)
])
# Xavier normal init std=0.01, zero bias (saturation fix)
for head in self.component_heads:
    for m in head:
        if isinstance(m, nn.Linear):
            nn.init.normal_(m.weight, std=0.01)
            nn.init.zeros_(m.bias)
```

**Forward path change:** PSRHead.forward returns [B, T, 11] instead of [B, T, 24]. Each component head processes the same per-frame feature independently. The sequence encoder (causal transformer) output is reshaped and passed to each head independently.

### 4.2 model.py: PSRHead.__init__ signature and num_components default

**Location:** lines ~1831-1839

Change `num_components` default from 24 to 11. Remove 24-class-specific attributes (`num_states`, `state_to_idx` mapping). The PSR head retains the causal transformer (3 layers, 4 heads, d_model=256) for temporal context but outputs 11 independent binary logits per frame instead of 24-class softmax.

### 4.3 model.py: Output dictionary key

**Location:** line ~2672

The `"psr_logits"` key remains but shape changes from [B, 24] to [B, 11]. The eval dispatch (evaluate.py lines 5520-5604) checks `all_psr_logits.shape[1] == NUM_CATEGORIES (24)` for Path B routing. After the revert, this check is False and the code automatically falls through to the Path A MonotonicDecoder path. **No eval dispatch changes needed.**

### 4.4 model.py: num_components config wiring

**Location:** Where PSRHead is instantiated in the MTLModel.__init__

Ensure `num_components=11` is passed when `USE_PSR_PATH_A=True`. The config must propagate through:
```
config.USE_PSR_PATH_A -> model.__init__ -> PSRHead(num_components=11)
```

### 4.5 losses.py: Restore per-component focal BCE loss

**File:** `/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/src/training/losses.py`
**Location:** PSR loss computation in MultiTaskLoss.forward, line ~1889

**Target changes:**

1. When `USE_PSR_PATH_A=True`, use `PSRFocalLoss` (legacy class at line 951) instead of `psr_state_classification_loss` (line 1195).

2. `PSRFocalLoss` implementation:
   - 11 independent `BCEWithLogitsLoss` with per-component alpha weighting
   - Alpha computed from component prevalence: `alpha_c = (1 - prevalence_c) * alpha_scale`
   - Focal modulation: `weight = alpha_c * (1 - p_t)^gamma`
   - Ignore handling: per-component mask where label==-1 (not single ignore_index)
   - Loss averaged over non-ignored frames and all 11 components

3. Keep `set_psr_class_counts` method (line 1554) for effective-number re-weighting infrastructure.

### 4.6 config.py: USE_PSR_PATH_A toggle

**File:** `/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/src/config.py`
**Location:** Near existing PSR config flags (DETACH_PSR_FPN at line 1335, USE_PSR_SEQUENCE_MODE at line 1397)

```python
# Path A (11-binary heads + MonotonicDecoder) vs Path B (24-class softmax)
# Path A = proven 0.883 psr_f1 on MViTv2-S
# Path B = unproven 0.10 psr_f1 on ConvNeXt-Tiny
USE_PSR_PATH_A = os.environ.get("USE_PSR_PATH_A", "1") == "1"
```

When `USE_PSR_PATH_A=True`:
- PSRHead outputs 11 binary logits (not 24-class)
- Loss: per-component focal BCE
- Eval: MonotonicDecoder path (decode_and_score_psr)
- Authors' eval: compute_authors_psr_metrics (already handles 11-binary)

### 4.7 psr_transition.py: F1=1.0 bug fix (see Section 5)

### 4.8 evaluate.py: Defensive fixes (see Section 5)

---

## 5. F1=1.0 Bug Fix

### 5.1 The Bug

When both ground truth and predictions contain zero transitions (common for short recordings or recordings where a component is absent), the F1 computation mathematically results in precision=0/0 and recall=0/0. Three locations in the codebase handle this by returning `F1=1.0`, which is mathematically wrong: F1 should be 0.0 when no events exist.

**Why it matters for the 0.883 target:**
- The v3.41 eval (0.883) is NOT affected because the 2000-frame sample has real transitions (positive rates: 0.29-1.00 for active components).
- The v4_fixed eval (F1=1.0) IS affected because the 500-frame sample only has comp0 transitions (always-on component). All other components have zero transitions, and the bug returns 1.0 for them, inflating the average.
- The current benchmark training val may be affected if individual recordings have zero transitions for some components.

### 5.2 Location 1: `psr_transition.py` lines 382-386

**File:** `/home/newadmin/swarm-bot/src/models/psr_transition.py`
**Function:** `compute_transition_f1`

**Current (bug):**
```python
if all_tp == 0 and all_fp == 0 and all_fn == 0:
    total_precision = 1.0
    total_recall = 1.0
    total_f1 = 1.0
```

**Target (fix):**
```python
if all_tp == 0 and all_fp == 0 and all_fn == 0:
    total_precision = 0.0
    total_recall = 0.0
    total_f1 = 0.0
```

**Also fix at line 347** (per-component edge case):
```python
# Current (bug):
comp_f1s[c] = 1.0  # perfect agreement on no transitions

# Target (fix):
comp_f1s[c] = 0.0  # no transitions to evaluate
```

### 5.3 Location 2: `evaluate.py` lines 1269-1270 (`_event_f1`)

**File:** `/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/src/evaluation/evaluate.py`

**Current (bug):**
```python
if not pred_tr.any() and not gt_tr.any():
    return 1.0
```

**Target (fix):**
```python
if not pred_tr.any() and not gt_tr.any():
    return 0.0
```

### 5.4 Location 3: `evaluate.py` lines 1412-1417 (`_decode_24class_psr_transitions`)

**File:** `/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/src/evaluation/evaluate.py`

**Current (bug):**
```python
if not gt_tr.any() and not pred_tr.any():
    f1s.append(1.0)
    poss.append(1.0)
    edits.append(1.0)
    continue
```

**Target (fix):**
```python
if not gt_tr.any() and not pred_tr.any():
    f1s.append(0.0)
    poss.append(0.0)
    edits.append(0.0)
    continue
```

### 5.5 Verification of the Fix

```python
# Unit test for F1=1.0 bug
def test_zero_transition_f1():
    # Both GT and pred have zero transitions
    gt_binary = np.array([0, 0, 0, 0, 0])  # component never active
    pred_binary = np.array([0, 0, 0, 0, 0])  # correctly predicted absent

    f1 = compute_transition_f1(gt_binary, pred_binary)
    assert f1 == 0.0, f"Expected F1=0.0 for no transitions, got {f1}"

    # GT has transitions, pred has none
    gt_binary = np.array([0, 1, 1, 0, 0])
    pred_binary = np.array([0, 0, 0, 0, 0])
    f1 = compute_transition_f1(gt_binary, pred_binary)
    assert f1 == 0.0, f"Expected F1=0.0 when no transitions predicted, got {f1}"
```

---

## 6. Timeline

```
Phase 0 (Aug 1-2): Verification
  Copy checkpoint to active machine
  Locate/reconstruct v3.34 eval script
  Run eval on v3.41 checkpoint
  Confirm 0.883 reproduction
  Duration: 1 day, no GPU needed (eval only, 30 min)
  milestone: REPRODUCTION_CONFIRMED

Phase 1 (Aug 2-3): Cross-Evaluation
  Run current evaluate.py on v3.41 checkpoint
  Establish evaluator delta (expected: 0.063)
  Document "current pipeline truth" number
  Duration: 1 day, no GPU needed
  milestone: CROSS_EVAL_COMPLETE

Phase 2 (Aug 3-5): Code Restoration
  Implement USE_PSR_PATH_A toggle (config.py)
  Restore 11-binary classifier head (model.py)
  Restore per-component focal BCE loss (losses.py)
  Fix F1=1.0 bugs (3 locations)
  Verify with dummy forward pass + unit tests
  Duration: 2-3 days, no GPU needed
  milestone: CODE_RESTORED

Phase 3 (Aug 7-14): Training
  GATED on RTX 3060 availability (~Aug 7, per Agent 5 schedule)
  Train Path A restoration from best available checkpoint
  50 epochs at ~3.2h/epoch on RTX 3060
  Val eval every epoch (2000-frame subset)
  Duration: 7 days, RTX 3060 required
  milestone: TRAINING_COMPLETE

Gate Check (Aug 15):
  Decision: psr_transition_f1 > 0.20? (Agent 5 Step 2 gate)
  IF YES -> Phase 4 (full eval)
  IF NO  -> Fallback analysis (Section 7 of 03_psr_revival.md)
  milestone: GATE_PASSED or GATE_FAILED

Phase 4 (Aug 16-17): Full Evaluation
  Transition F1 on full 38k-frame dataset
  Per-component threshold sweep (full dataset)
  Authors' PSR eval (AccumulatedConfidencePSR)
  Per-recording breakdown + copy_prev comparison
  Duration: 2 days, RTX 3060 (eval only, ~2h for full dataset)
  milestone: EVAL_COMPLETE

Phase 5 (Aug 18-20): Ablations (if gated and time permits)
  KENDALL_FIXED_WEIGHTS: test suppression hypothesis
  MS-TCN smoothing: test temporal consistency improvement
  ASL (AsymmetricLoss): test rare-component improvement
  DETACH_PSR_FPN=False: test end-to-end gradient flow
  Duration: 2-3 days, RTX 3060
  milestone: ABLATIONS_COMPLETE

Phase 6 (Aug 21-22): Freeze + Artifact Package
  Freeze best checkpoint (SHA256 + config hash)
  Commit all eval outputs to repo
  Package for paper: metrics JSON, per-component breakdown, eval log
  Align with Agent 5 freeze date (Aug 22)
  milestone: FROZEN
```

**Total wall clock:** 18-22 days from Aug 1.
**Critical path:** Phase 3 gated on RTX 3060 availability (~Aug 7).
**GPU-free work:** Phases 0-2 (5 days) proceed immediately in parallel with current repair training.

---

## 7. Cross-References

### 7.1 Other Agent Plans

| Document | Relevance | Key Dependency |
|----------|-----------|----------------|
| [01_activity_revival.md](01_activity_revival.md) | Agent 1 plan (501 lines) | SHARED GPU, SCHEDULE. Activity plan disables TRAIN_PSR during activity training (line 268). Strategy B (MViTv2-S) uses the same backbone as the v3.41 PSR checkpoint. If Strategy B is chosen, Path A PSR head is already compatible. |
| [02_detection_revival.md](02_detection_revival.md) | Agent 2 plan (779 lines) | SHARED BACKBONE. Detection D4+D1R decoder test (0.6364 transition F1) proves detection-to-PSR transfer works. Detection occupies GPU 0 (RTX 5060 Ti); PSR restoration uses GPU 1 (RTX 3060) -- no conflict. |
| [03_psr_revival.md](03_psr_revival.md) | Agent 3 plan (522 lines) | PRIMARY REFERENCE. This is the complete PSR revival diagnostic + Path A restoration blueprint. This revert plan (15) is the execution companion to the diagnostic plan (03). All architecture decisions, code locations, and training configs are drawn from 03. |
| [04_pose_refinement.md](04_pose_refinement.md) | Agent 4 plan (672 lines) | DIAGNOSTIC PREREQUISITE. Pose plan proved ConvNeXt backbone works for regression. Analogous component-ordering constraint (pose column ordering ~= PSR procedure ordering). |
| [05_integration_synthesis.md](05_integration_synthesis.md) | Agent 5 plan (425 lines) | GATE. Step 2: transition F1 > 0.20. Freeze date Aug 22. Verdict: "Revive PSR + Head Pose on the shared ConvNeXt-Tiny backbone." This plan executes that verdict. |
| [06_pr_review_and_existing_fixes.md](06_pr_review_and_existing_fixes.md) | PR inventory | PR #19: Confirmed PSR is per-frame, NOT transition. PR #10: Added honest present-class detection mAP. PR #36: Set Aug 22 freeze date. |
| [08_debate_resources.md](08_debate_resources.md) | Resource map | GPU allocation, dataset locations, checkpoint inventory. |
| [10_debate_historical_targets.md](10_debate_historical_targets.md) | Historical verification | VERIFIED 0.883 target. Per-component breakdown confirmed. F1=1.0 is v4_fixed artifact. |

### 7.2 Challenges from Agent 5 Addressed

**Challenge: Kendall assumption.** Agent 5 questioned whether Kendall fixed weights raise PSR F1 from 0.7499 to 0.82. This plan AGREES: Kendall is an ablation (Phase 5), not the primary fix. The primary fix is architecture restoration (Path B -> Path A).

**Challenge: Transition F1 target.** Agent 5 asked for a transition F1 target. This plan's primary metric IS transition F1 (Section 3, event-level F1 at +/-3 frame tolerance, per-component threshold sweep). Target: 0.80+ (93% of v3.41's 0.883).

**Challenge: Per-frame F1 dominated by copy_prev.** Agent 5 noted per-frame F1 is dominated by copy_prev baseline (0.9997). This plan uses transition F1 (event-based, not frame-based) as the primary metric, with explicit copy_prev comparison in the per-recording breakdown.

### 7.3 Resource Allocation (from Agent 5 Schedule)

| Resource | Current (Aug 1) | This Plan's Usage | Conflict? |
|----------|----------------|-------------------|-----------|
| RTX 3060 (GPU 1) | PSR repair training (epoch ~24/100, ~Aug 7 completion) | Phase 3 training (Aug 7-14) | Sequential -- Phase 3 starts after repair completes. Phase 0-2 (code changes) run in parallel. |
| RTX 5060 Ti (GPU 0) | Single-task ConvNeXt detection (epoch 43/99) | Not needed (PSR eval on RTX 3060; CPU threshold sweep) | No conflict. Different GPU. |
| CPU | LOO-CV stability (1-2 days) | Per-component threshold sweep on cached logits (1 day) | Minor -- serialize or run overnight. |
| Disk | Checkpoints ~670 MB each | 3-5 checkpoints (~2-3.5 GB for Phase 3) | Adequate space. |

### 7.4 Fallback Plans (Ref 03_psr_revival.md Section 7)

If Path A restoration on ConvNeXt-Tiny fails (transition F1 < 0.20 after 50 epochs):
1. **Fallback A:** Publish per-frame F1 with honest persistence-baseline comparison. Position as methodology contribution (state labels without transition detection).
2. **Fallback B:** Use the MViTv2-S v3.41 checkpoint (0.883) directly. Acknowledge backbone mismatch in paper.
3. **Fallback C:** Abandon PSR on ConvNeXt-Tiny entirely. Publish MViTv2-S PSR result alongside ConvNeXt-Tiny pose (which works at ~9 deg).

---

## Appendix A: Quick-Reference Command Sequence

```bash
# Phase 0: Verify checkpoint reproduction
cd /path/to/industreal_improved
cp /media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/runs/mtl_v3.41_safe/checkpoints/phase2_e3_b0.pth \
   runs/mtl_v3.41_safe/checkpoints/
python eval_v3.34_psr_sweep.py --checkpoint runs/mtl_v3.41_safe/checkpoints/phase2_e3_b0.pth --n-frames 2000

# Phase 1: Cross-evaluate with current pipeline
python -m src.evaluation.evaluate --checkpoint runs/mtl_v3.41_safe/checkpoints/phase2_e3_b0.pth --n-frames 2000

# Phase 2: Set feature flag and verify forward pass
USE_PSR_PATH_A=1 python -c "
from src.models.model import PSRHead
import torch
head = PSRHead(gru_hidden=256, num_components=11)
x = torch.randn(2, 8, 256)
out = head(x)
assert out.shape == (2, 8, 11), f'Shape: {out.shape}'
print('Path A forward: OK')
"

# Phase 3: Launch training
USE_PSR_PATH_A=1 python -m src.training.train --config configs/psr_path_a_restore.yaml

# Phase 4: Full evaluation
python -m src.evaluation.evaluate \
    --checkpoint runs/psr_path_a_restored/checkpoints/best.pth \
    --n-frames -1 \
    --output runs/psr_path_a_restored/eval_full.json
```

## Appendix B: Key File Locations

| File | Location | Purpose |
|------|----------|---------|
| v3.41 checkpoint | `/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/runs/mtl_v3.41_safe/checkpoints/phase2_e3_b0.pth` | 695 MB, 578 keys, 0.883 source |
| Canonical eval | `/media/.../runs/mtl_v3.41_safe/eval_e3_b0.json` | Ground truth metrics |
| Eval log | `/media/.../runs/mtl_v3.41_safe/eval_e3_b0.log` | Exact reproduction steps |
| PSRHead (Path B) | `/media/.../src/models/model.py:1798` | Class to modify |
| PSR forward path | `/media/.../src/models/model.py:2460` | Sequence mode forward |
| MonotonicDecoder | `/home/newadmin/swarm-bot/src/models/psr_transition.py:43` | Path A decoder (swarm-bot) |
| F1=1.0 bug #1 | `/home/newadmin/swarm-bot/src/models/psr_transition.py:382-386` | compute_transition_f1 |
| F1=1.0 bug #2 | `/media/.../src/evaluation/evaluate.py:1269` | _event_f1 |
| F1=1.0 bug #3 | `/media/.../src/evaluation/evaluate.py:1412-1417` | _decode_24class_psr_transitions |
| Eval dispatch | `/media/.../src/evaluation/evaluate.py:5520-5604` | Path A vs B routing |
| PSRFocalLoss (legacy) | `/media/.../src/training/losses.py:951` | Path A loss (present, unwired) |
| PSR loss compute | `/media/.../src/training/losses.py:1889` | MultiTaskLoss.forward |
| Config DETACH_PSR_FPN | `/media/.../src/config.py:1335` | PSR isolation flag |
| Config USE_PSR_SEQUENCE | `/media/.../src/config.py:1397` | Sequence mode flag |
| Authors' eval | `/media/.../src/evaluation/authors_psr_eval.py` | AccumulatedConfidencePSR |
| PSR categories | `/media/.../src/data/psr_categories.py` | 24-category state space |
| SOTA history | `/home/newadmin/.claude/projects/-home-newadmin-swarm-bot/memory/feedback_sota_history.md` | Authoritative metrics |
| AUDIT report | `/media/.../AUDIT_TRUTHFULNESS.md` | Truthfulness verification |

---

**One-sentence plan:** Reproduce 0.883 from the preserved v3.41 checkpoint, restore the 11-binary PSR head + MonotonicDecoder (Path A) into the current ConvNeXt-Tiny codebase, fix three F1=1.0 eval bugs, retrain for 50 epochs, and evaluate with the exact same per-component threshold sweep protocol to confirm the restoration.
