# Agent 12: Activity Classification Head — Deep Audit Report

## 1. Architecture Overview

**File:** `/media/newadmin/master/POPW/working/code/industreal_improved/src/models/model.py`

**Class:** `ActivityHead` (line 1233)

**Flow:**
```
det_conf [B,24] --(stop_grad)--> concat --> Linear(1048->512) --> TCN (kernel=5) --> 
GAP(c5_mod) [B,768] -----------/                                              |
GAP(p4) [B,256] ----------------/                                              |
                                                                              v
                                                     2x ViT blocks (8 heads, d_k=64)
                                                              |
                                                        CLS token pooling
                                                              |
                                                    Dropout(0.1) -> Linear -> act_logits [B, 75]
```

**NUM_CLASSES_ACT = 75** (config.py line 187). This is FIXED to `max_raw_action_id + 1 = 75`, NOT data-derived. The 75 channels map directly to raw action IDs 0-74. ID 37 is absent from the dataset (permanent cold channel).

**Prediction mode:** Frame-level. Each frame produces independent logits. Temporal context via TCN + ViT blocks over a 16-frame feature bank, but the bank accumulates frames over time via `FeatureBank` (line 2051). However, the FEATURE_BANK_SLOT_OVERWRITE option (default True, line 1357) causes the current frame to overwrite slot -1 each step, limiting temporal learning.

---

## 2. NUM_CLASSES_ACT = 75 Verification

| Property | Value | Status |
|---|---|---|
| Config value | `NUM_CLASSES_ACT = 75` (line 187) | VERIFIED |
| ActivityHead init receives | `num_classes=75` (line 1751) | VERIFIED |
| Classifier output | `Linear(512 -> num_classes)` = 75 channels | VERIFIED |
| Dataset labels | Raw action IDs 0-74, no shift | VERIFIED |
| Label 37 | Absent (cold channel, harmless) | DOCUMENTED |
| Assert | `len(ACT_CLASS_NAMES) == 75` (line 228) | VERIFIED |

**Finding:** The NUM_CLASSES_ACT = 75 is correct and pinned to a fixed constant. The docstring on line 1265 says "The final classifier outputs 75 classes" but line 1260 says `[B, 74]` -- this docstring is **INCORRECT** (doc says 74, code uses 75). This is a cosmetic documentation bug only.

**Severity: LOW.** Documentation vs. code mismatch on line 1260 column 101 (`act_logits [B, 74]` should read `[B, 75]`).

---

## 3. Activity Loss Function

**File:** `/media/newadmin/master/POPW/working/code/industreal_improved/src/training/losses.py`

**Selection logic** (MultiTaskLoss.__init__, lines 983-996):
```python
if bool(getattr(C, 'USE_LDAM_DRW', False)):
    self.act_loss_fn = LDAMLoss(num_classes=num_classes_act, ...)
else:
    self.act_loss_fn = ClassBalancedFocalLoss(num_classes=num_classes_act, ...)
```

**Default:** CB-Focal Loss (`ClassBalancedFocalLoss`, line 618) with:
- `beta=0.999` (effective number smoothing)
- `gamma=2.0`
- `label_smoothing=0.1`

**Alternate:** LDAM-DRW (`LDAMLoss`, line 433) when `USE_LDAM_DRW=True`:
- LDAM margin: `m_c = 1 / sqrt(sqrt(n_c))`
- DRW at epoch 60: CB re-weighting activated
- Label smoothing = 0.1
- Logits clamped to [-50, 50] after s=30 scaling

**Finding:** The LDAM-DRW alternate has a `max_m=0.5` and `s=30` default. At epoch 0, LDAM uses margins only (no CB weights unless `LDAM_USE_DRW=True`). The DRW epoch is 60 -- if training runs fewer epochs, DRW never activates.

**Severity: MEDIUM.** If `STAGED_TRAINING=False` (production default) and training runs only ~50 epochs with LDAM, the DRW re-weighting at epoch 60 never fires, leaving only the LDAM margin mechanism to handle imbalance.

---

## 4. Class Imbalance Handling

**File:** `/media/newadmin/master/POPW/working/code/industreal_improved/src/data/industreal_dataset.py`

**Mechanisms:**
1. **Class-balanced WeightedRandomSampler** (lines 1317-1334) -- sqrt-count weighting at the data loader level. Uses `beta=C.CB_BETA` for effective number smoothing.
2. **CB-Focal class weights** -- computed in `ClassBalancedFocalLoss.set_class_counts()` (line 657)
3. **LDAM margins** -- per-class margins inversely proportional to 4th root of count (line 458)
4. **class_counts** computed via `np.bincount` on valid labels (line 723), passed to `criterion.set_class_counts()` at train.py line 2919

**Finding:** The class weights from `set_class_counts` go through a complex reconciliation in `LDAMLoss.set_class_counts()` (lines 484-511). The `_fit_to_width` method (line 534) is a band-aid for the 74-vs-75 hazard. If `class_counts` has 74 entries (when the label file was scanned by the old code), and `num_classes` is 75, padding with 1.0 creates a misleading weight for class 0.

**Severity: MEDIUM.** The count-length mismatch path (lines 498-507) silently pads with 1.0, giving class 0 (NA/take_short_brace) potentially incorrect LDAM margin.

---

## 5. `act_accuracy = 0.0` in Best Checkpoints -- Root Cause Analysis

**Evidence:** All checkpoint evaluations return `act_accuracy=0.0`. The eval debug log shows exactly 1-2/75 classes predicted (line 3349: `[EVAL COLLAPSE] activity head predicts only N/75 classes`).

**Root Cause: Multi-Task Collapse Cascade** (documented in config.py lines 533-537 and loss function comments)

The collapse proceeds in three stages:

### Stage 1: Activity dominates backbone (epochs 0-15)
- Activity loss magnitude ~1-5 vs PSR loss ~0.01-0.13 (documented at losses.py line 1573)
- The naive Kendall weighting gives activity excessive precision, causing backbone features to overfit to activity task
- **Fix applied:** `ACTIVITY_LOSS_WEIGHT=0.2` (config.py line 539, reduced from 0.3)

### Stage 2: Activity head collapses (epochs 15-30)
- Once backbone overfits to activity, the activity head finds a degenerate local minimum predicting class 0 (NA) for every frame -- this is the easiest solution since NA is the majority class
- The per-head gradient clip `ACTIVITY_HEAD_GRAD_CLIP=0.1` (config.py line 538) was intended to prevent this but may be too aggressive -- when the activity head needs to break out of the degenerate equilibrium, the clipped gradient may be insufficient
- **Issue:** ACTIVITY_HEAD_GRAD_CLIP applies to the NORM of activity head gradient, not the signal. If gradient norm is already tiny due to saturation, clipping at 0.1 does nothing; if gradient norm is large (activity dominating), clipping helps -- but the collapse happened before the clip threshold.

### Stage 3: Irreversible collapse (epochs 30+)
- Activity head freezes into predicting NA (class 0) for every frame
- Kendall log_var_act drops (precision rises) because the loss is "stable" at predicting NA
- When other heads try to recover, their gradients disturb shared backbone features already specialized for activity
- The system cannot escape this equilibrium without reinitialization

### Contributing Factors:

**(a) Staged training and reinit interaction** (train.py lines 587-621)
- Activity head is FROZEN during stages 1-2 (epochs 0-15)
- When reinit is used, the stage counter resets. If training from epoch 0 with --reinit-heads and staged training:
  - Stage 1 (epochs 1-5): activity head frozen
  - Stage 2 (epochs 6-15): activity head frozen  
  - Stage 3 (epoch 16+): activity head unfrozen with random weights
- **Line 602:** `if 'activity_head' in name or 'psr_head' in name: p.requires_grad = False`
- **Severity: HIGH.** Activity head gets ZERO gradient signal for the first 15 epochs in staged mode.

**(b) PSR sequence batches** (train.py lines 1065-1068)
- During PSR sequence batches, `criterion.train_act = False` (line 1067)
- These batches bypass activity loss entirely
- **Severity: LOW.** Only applies to ~10% of batches (sequence vs frame), correct by design.

**(c) Activity bias initialization** (_reinit_dead_heads, train.py line 2329)
- `nn.init.constant_(m.bias, -0.5)` -- the bias is set to -0.5
- For a 75-class classifier, bias=-0.5 means initial logits for all classes are -0.5, giving a softmax probability of ~1/75 per class
- This is REASONABLE but combined with the frozen stages means the head spends its first 15 epochs at random initialization while the backbone converges to something else

**(d) KENDALL_LOG_VAR_MIN_ACT = -0.5** (config.py line 545)
- This clamp prevents activity precision from exceeding `exp(-(-0.5)) = 1.65`, which is reasonable
- But the log_var_act floor was CHANGED from 0.0 to -0.5 -- meaning the activity head can now get MORE precision than before
- **Paradox:** The recent fix allows MORE activity dominance precisely when the intent was to reduce it

---

## 6. Gradient Flow: Feature Sharing Analysis

**File:** `/media/newadmin/master/POPW/working/code/industreal_improved/src/models/model.py`

**The activity head shares features from:**
1. **Detection head** -- `det_conf` (line 2038-2039): [B, 24] max-pooled detection CLS scores with stop_grad
2. **Backbone C5** -- `c5_mod` (line 2040): GAP-pooled FiLM-modulated C5 features [B, 768]
3. **FPN P4** -- `pyramid['p4']` (line 2041): GAP-pooled FPN P4 features [B, 256]

**Gradient path to shared parameters:**
```
act_logits -> activity_head.proj_features -> concat([det_conf, GAP(c5_mod), GAP(p4)])
                                                          |            |
                                                     backbone.C5   FPN.P4
```

**Critical:** The `det_conf` input comes from STOP_GRAD detached features (losses.py comment line 1247 says "stop_grad"), but `c5_mod` and `p4` do propagate gradients back to backbone and FPN parameters. This is the **root cause of the collapse cascade** -- the activity head can directly modify shared visual features.

**Lines 2038-2044** -- the `activity_proj` construction has NO stop_grad on `c5_mod` or `p4`:
```python
activity_proj = torch.cat([
    det_conf,  # already stop_grad from detection head
    F.adaptive_avg_pool2d(c5_mod, 1).flatten(1),  # NO stop_grad -- gradients flow to backbone
    F.adaptive_avg_pool2d(pyramid['p4'], 1).flatten(1),  # NO stop_grad -- gradients flow to FPN
], dim=1)
```

**Severity: HIGH.** The gradient path from activity loss through `c5_mod` and `p4` corrupts shared backbone/FPN features. On PSR sequence steps, this is explicitly prevented (train.py lines 1124-1129 zero backbone + FPN gradients), but on normal frame steps, activity loss modifies backbone features freely.

---

## 7. Activity Prediction: Frame-Level vs Sequence-Level

**Prediction:** Frame-level. Each forward pass produces act_logits for a single frame.

**Temporal context** via `FeatureBank` (line 2051): A 16-frame rolling buffer stores projected features. The `ActivityHead.forward` uses this bank (line 1357-1358):
```python
if getattr(C, 'FEATURE_BANK_SLOT_OVERWRITE', True):
    bank_seq[:, -1, :] = proj_feat  # Overwrites last slot with current frame
```

**Finding:** `FEATURE_BANK_SLOT_OVERWRITE=True` (default) means the current frame REPLACES the last bank slot. This means:
- The bank has T-1 historical frames + current frame
- The current frame appears TWICE in the bank (once in the accumulated position, once overwritten at slot -1)
- This effectively gives the current frame double weight in the temporal attention
- **The ViT blocks see a contaminated temporal sequence** where the current frame is duplicated

**Severity: MEDIUM.** The slot-overwrite mechanism gives the current frame disproportionate influence in temporal attention, reducing the value of the TCN and ViT temporal blocks.

---

## 8. Gradient Signal Receipt Analysis

### Normal training (STAGED_TRAINING=False, production default):
- Activity head receives gradient on EVERY frame batch (train.py line 1227)
- Trainable from epoch 0
- Activity loss ramped via ACT_RAMP_EPOCHS=5 (line 476)

### PSR sequence batches:
- `criterion.train_act = False` (train.py line 1067)
- **No activity gradient on these batches**
- These are ~10% of batches (1 sequence batch per 10 frame batches)
- **Severity: LOW** -- correct by design

### Staged training (STAGED_TRAINING=True):
- **Stage 1 (epochs 0-5):** Activity head FROZEN via `requires_grad=False` (line 602)
- **Stage 2 (epochs 6-15):** Activity head FROZEN (line 620)
- **Stage 3 (epoch 16+):** Activity head UNFROZEN

### With --reinit-heads + STAGED_TRAINING:
- Heads are reinitialized at epoch 0
- Stage counter is reset via _REINIT_EPOCH_OFFSET
- **Activity head frozen for epochs 0-15** despite being freshly initialized
- **Severity: HIGH.** Freshly initialized activity head gets ZERO gradient for 15 epochs. By epoch 16, the backbone is fully converged to detection/pose tasks, making it nearly impossible for the randomly initialized activity head to learn useful features.

---

## 9. Summary of All Issues

| # | Severity | Location | Line(s) | Issue |
|---|---|---|---|---|
| 1 | LOW | model.py | 1260 | Docstring says `act_logits [B, 74]` but output is `[B, 75]` |
| 2 | MEDIUM | losses.py | 498-507 | Count-length mismatch silently pads with 1.0 for class 0 weight |
| 3 | MEDIUM | losses.py | 598-606 | LDAM DRW epoch=60 may never fire in short training runs |
| 4 | HIGH | model.py | 2038-2041 | Activity proj_feat passes gradients to backbone C5 and FPN P4 with NO stop_grad, causing multi-task collapse cascade |
| 5 | HIGH | train.py | 600-603, 618-621 | Activity head frozen for 15 epochs in staged mode even after --reinit-heads |
| 6 | MEDIUM | model.py | 1357-1358 | FEATURE_BANK_SLOT_OVERWRITE duplicates current frame, reducing temporal context value |
| 7 | CRITICAL | (systemic) | -- | act_accuracy=0.0 is confirmed model collapse (predicts 1-2/75 classes), not eval bug |
| 8 | MEDIUM | config.py | 538 | ACTIVITY_HEAD_GRAD_CLIP=0.1 may be too restrictive for breaking out of degenerate equilibria |
| 9 | MEDIUM | config.py | 539 | ACTIVITY_LOSS_WEIGHT=0.2 reduces activity signal by 80%, conflicting with KENDALL_LOG_VAR_MIN_ACT=-0.5 |
| 10 | LOW | train.py | 2329 | Activity classifier bias initialized to -0.5 (reasonable but unprincipled) |
| 11 | MEDIUM | training/losses.py | 1250-1252 | Activity warmup r AMP epoch 0 gets 0.2× signal (+1 divisor), which may be too slow in 100-epoch runs |

## 10. Recommendations

1. **Add stop_grad on c5_mod and p4** in the activity projection (model.py lines 2040-2041) to prevent activity gradients from corrupting shared backbone features. This is the single highest-impact fix.

2. **Kill staged training for activity head** when --reinit-heads is active. A freshly reinitialized head should not be frozen for 15 epochs. Override the stage-freeze for activity_head in the reinit path.

3. **Remove or raise ACTIVITY_HEAD_GRAD_CLIP** (currently 0.1). The activity head gradient norm at a degenerate equilibrium is already near-zero; clipping doesn't help. Use gradient centralization instead.

4. **Increase ACTIVITY_LOSS_WEIGHT** from 0.2 to at least 0.5, and KENDALL_LOG_VAR_MIN_ACT should stay at 0.0 (not -0.5). The current configuration sends conflicting signals.

5. **Set FEATURE_BANK_SLOT_OVERWRITE=False** to allow true temporal accumulation. If slot overwrite is needed, apply it via a learnable gating mechanism rather than hard replacement.
