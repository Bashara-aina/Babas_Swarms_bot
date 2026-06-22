# Agent 14: EMA + Distillation Audit Report

**Files examined:**
- `/media/newadmin/master/POPW/working/code/industreal_improved/src/models/model.py` (lines 2135-2192, EMA class)
- `/media/newadmin/master/POPW/working/code/industreal_improved/src/training/ema.py` (6-line re-export shim)
- `/media/newadmin/master/POPW/working/code/industreal_improved/src/training/distillation.py` (298 lines, standalone)
- `/media/newadmin/master/POPW/working/code/industreal_improved/src/training/train.py` (EMA usage throughout)
- `/media/newadmin/master/POPW/working/code/industreal_improved/src/config.py` (no distil config present)

---

## 1. EMA Implementation

### 1.1 Class Definition (`src/models/model.py:2135-2192`)

A plain dict-based EMA with three lifecycle methods:

| Method | Purpose |
|--------|---------|
| `_register()` | Clones all `requires_grad=True` params + all buffers into `self.shadow` |
| `update()` | Updates each shadow: `shadow = decay * shadow + (1-decay) * param.data` |
| `get_ema()` | Saves current params to `self.backup`, then copies shadow values into model |
| `restore()` | Copies backed-up original values back into model |
| `set_decay(d)` | Hot-swaps the decay factor |

Shadows are stored as **flat `{}` dict of `{name: tensor}`**, keyed by parameter/buffer name string.

### 1.2 Decay Rate

- **Default**: `EMA_DECAY = 0.999` (from config, with fallback)
- **Epoch-based schedule** via `_get_ema_decay()` (train.py:2528-2539):
  - Epoch 16 (Stage 3 entry): `0.999` -- slow catch-up, stable init
  - Epoch 17: `0.9995` -- medium
  - Epoch 18+: `0.9999` -- standard final decay
- Applied by `ema.set_decay(_get_ema_decay(epoch))` at each epoch start (train.py:3539-3540)

### 1.3 Update Frequency

- **Every optimizer step** in both training paths:
  - Standard per-batch step (train.py:1680-1681)
  - PSR-sequence path (train.py:1209-1210)
- Guarded by stage check: only updates when `not staged_training or stage >= 3` -- so in the default staged setup, EMA is **not updated during Stages 1-2** (epochs 1-15).

### 1.4 Shadow Storage Device

- **GPU** (same device as model parameters). The `EMA.__init__` receives `device=device` and shadows are cloned from `param.data` which lives on GPU. Verified:
  - `ema.shadow[name] = param.data.clone().detach()` -- stays on param's device (GPU)
  - Crash recovery save explicitly `.cpu()` before serialization
  - EMA checkpoint load does `v.to(ema.device)` to restore shadows to GPU
  - Reinit-heads: `ema.shadow[_n] = _p.data.clone().detach().to(ema.device if ema.device else _p.device)`

### 1.5 Memory Impact

EMA maintains a full shadow copy of all trainable parameters + all buffers on GPU. For this model (ConvNeXt-T ~28M params + heads), this is approximately:
- **~1x model size additional GPU memory** (all shadows are fp32 since model is fp32)
- Plus `self.backup` during validation (temporarily holds original weights during EMA swap)
- This is standard for EMA and expected. The `backup` dict is garbage-collected after `restore()`.

### 1.6 Checkpoint Save/Load

**Save paths:**
1. **Best checkpoint** (train.py:4058-4073): EMA weights applied before saving model_state_dict, then EMA shadows saved separately as `ema_shadow`:
   ```python
   ema.get_ema()
   save_dict['model'] = model.state_dict()
   ema.restore()
   save_dict['ema_shadow'] = {k: v.clone() for k, v in ema.shadow.items()}
   ```
2. **Latest checkpoint** (train.py:4133-4149): Raw model state_dict saved (non-EMA), shadows saved separately
3. **Crash recovery** (train.py:780-784): Shadows `.cpu()`-moved before serialization

**Load path** (train.py:3132-3141):
- Accepts both `ema_shadow` (named checkpoints) and `ema_state` (crash recovery key)
- Only loads keys that exist in the current `ema.shadow` dict (shape-based filtering through `if k in ema.shadow`)

### 1.7 EMA vs Non-EMA Validation Selection

Train.py:3801-3810:
```python
_ema_staged = bool(getattr(C, 'STAGED_TRAINING', True))
ema_warmed = (ema is not None) and (not _ema_staged or current_stage >= 3)
```
- With staged training (default): EMA used only in Stage 3+
- Without staged training: EMA used from epoch 0
- Pre-Stage-3 validation uses raw model weights (EMA shadow exists but is stale)

EMA restore after val (train.py:3949-3951):
```python
if ema_warmed:
    ema.restore()
```

### 1.8 EMA + reinit-heads Interaction (train.py:3271-3283)

When `--reinit-heads` is active, EMA shadows for the following param prefixes are **re-anchored** (cloned from freshly reinitialized model weights):
- `det_head.*`, `detection_head.*`, `activity_head.*`, `psr_head.*`, `fpn.*`

This is correct: dead heads are reinitialized to new random weights, and EMA shadows must match immediately rather than blending old (dead) shadow values with new random weights.

**Potential issue**: The matching uses prefix matching (`startswith`). If any head-related params use nonstandard naming (e.g. `head.pose_head.*` or `activity_head.*.weight` with unexpected subtypes), they would be missed. However, the counts are logged and the three known heads + FPN are covered.

### 1.9 EMA Startup / Warmup

**No explicit warmup.** EMA begins tracking immediately after initialization:
- Initial creation: shadows = clone of current params (instant, no burn-in)
- Stage 3 entry (train.py:3451-3458): Fresh EMA created from scratch with `EMA(model, decay=stage3_decay)`. This uses the epoch-specific decay from `_get_ema_decay()`, so Stage 3 epoch 1 uses `decay=0.999` (lower than final 0.9999), which functions as a soft warmup -- the shadow catches up faster.

The `_get_ema_decay()` schedule (train.py:2528-2539) is the only warmup mechanism. There is no step-count-based warmup (e.g. linear decay ramp from 0.99 to 0.9999 over N steps).

### 1.10 Stage Transitions and EMA

| Event | What happens to EMA |
|-------|---------------------|
| Initialization (epoch 0) | Created with `decay=0.999`, starts tracking from step 0 |
| Stage 2 entry (epoch ~6) | Nothing -- EMA continues tracking |
| Stage 3 entry (epoch ~16) | **Recreated from scratch** -- fresh `EMA(model, decay=stage3_decay)` |
| VideoMAE unfreeze (epoch ~10) | **Recreated from scratch** -- fresh `EMA(model, decay=EMA_DECAY)` |
| reinit-heads | Shadows re-anchored for head/fpn prefixes only |

**Caveat about VideoMAE unfreeze order**: If VideoMAE unfreeze epoch (default 10) occurs before Stage 3 entry (epoch 16), EMA is recreated twice in quick succession -- once at unfreeze, once at Stage 3. The first recreation discards ~10 epochs of EMA tracking. This is intentional (params changed requires_grad status), but means EMA tracking before VideoMAE unfreeze is lost.

### 1.11 Raw-vs-EMA Comparison

Train.py:2592-2639, `_compare_raw_vs_ema()`:
- Runs only in Stage 3 (epoch 16+)
- Builds a separate validation loader, runs eval with raw model, compares metrics
- Logs delta: `mAP50`, `act_macro_f1`, `psr_macro_f1`
- Silently catches and logs errors (no crash if comparison fails)

---

## 2. Distillation

### 2.1 Location

`/media/newadmin/master/POPW/working/code/industreal_improved/src/training/distillation.py` -- standalone module, **never imported or used anywhere** in the codebase.

### 2.2 Architecture

Three loss functions:
1. **Detection logit distillation** (line 47-74): Binary KL divergence on sigmoid outputs, temperature=3.0, alpha=0.5. Uses `sigmoid`, not `softmax` -- correct for multi-label detection.
2. **Activity logit distillation** (line 77-104): Multiclass KL divergence on softmax outputs, temperature=3.0, alpha=0.3. Uses `F.kl_div` with `log_target=False`.
3. **Box distillation** (line 107-129): MSE on box predictions, alpha=0.2. Masks out zero-padded boxes via sum threshold.

`DistillationLoss` module (line 215-277): Wrapper that computes all three losses from student/teacher dicts. Produces per-component metrics.

**Offline teacher prediction system:**
- `TeacherPredictionGenerator`: Runs teacher once, caches `.npz` + `.json` metadata
- `TeacherPredictionLoader`: Loads cached predictions during training
- Teacher models listed in docstring: YOLOv8m (detection), MViTv2 (activity)

### 2.3 CRITICAL FINDING: Distillation Is NOT Wired In

Searching the entire `src/` directory (all `.py` files) for any import or usage of `DistillationLoss`, `distillation`, or `USE_DISTILLATION`:

- **Train.py**: No import of distillation, no reference to any distillation config flag, no `DistillationLoss` instantiation
- **Config.py**: No `USE_DISTILLATION`, `DISTILL_*`, or any distillation-related constants
- **Any other file**: Zero imports of `from src.training.distillation`
- The only matches are within `distillation.py` itself

**Verdict**: Distillation is **placeholdered infrastructure only**. The code is complete, well-structured, and ready for integration, but has never been wired into:
1. The config system (no `USE_DISTILLATION` flag)
2. The loss computation (`MultiTaskLoss.forward()` does not call it)
3. The training loop (no teacher cache loading, no teacher forward passes)

### 2.4 What Would Need to Change to Enable Distillation

1. Add config flags: `USE_DISTILLATION`, `DISTILL_TEACHER_CACHE_DIR`, `DISTILL_TEMPERATURE`, `DISTILL_DET_WEIGHT`, `DISTILL_ACT_WEIGHT`
2. Wire `TeacherPredictionLoader` into training loop init, load teacher cache
3. Add `DistillationLoss` to the loss computation in `MultiTaskLoss` or the training loop
4. Handle frame-ID lookup to match teacher predictions with current batch frames
5. The teacher predictions are offline (pre-generated), so no teacher forward pass needed at training time

---

## 3. Issues Found

### 3.1 Medium: Double EMA recreation at consecutive stage transitions

If VideoMAE unfreeze epoch (default 10) is before Stage 3 entry (epoch 16), EMA is recreated at both points:
1. VideoMAE unfreeze at epoch 10 -- discards 10 epochs of EMA tracking
2. Stage 3 at epoch 16 -- discards another 6 epochs

This means the first meaningful EMA tracking period is from epoch 16 onward. The Stage 3 entry EMA recreation is necessary (newly unfrozen params change trainable set), but the VideoMAE unfreeze recreation also discards tracking. For staged training, this is expected behavior since EMA isn't used for validation until Stage 3 anyway, but the tracking data from epochs 0-10 is permanently lost.

### 3.2 Low: EMA shadow prefix matching in reinit-heads

Train.py:3274 uses hardcoded prefix list for EMA re-anchoring:
```python
_head_prefixes = ('det_head.', 'detection_head.', 'activity_head.', 'psr_head.', 'fpn.')
```
If the model's actual parameter naming diverges (e.g. `head.detection.*` or `pose_head.*`), these would be silently missed. Currently matches the actual model structure, but is a maintenance trap.

### 3.3 Info: EMA backup dict is never cleared on restore failure

If `ema.restore()` is called when `self.backup` is empty (e.g. double-swap bug), it silently copies nothing. The backup is created by `get_ema()` and popped (destroyed) by `restore()`, so calling `restore()` twice would leave model weights at their current (EMA) values -- no crash, but silently wrong.

### 3.4 CRITICAL: Distillation is dead code

As documented in section 2.3, the entire distillation module is standalone infrastructure that has never been integrated. If this is intentional (planned future work), no action needed. If it was supposed to be active, it's a significant gap.

### 3.5 Info: EMA re-export shim

`src/training/ema.py` is a 6-line re-export shim: `from src.models.model import EMA as ModelEMA`. It exists only for backward compatibility and is not imported by `train.py` (which imports directly from `model`). Can be deprecated.
