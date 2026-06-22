# Agent 1: Training Loop, Optimizer, and Scheduler Audit

## Files Analyzed
- `/media/newadmin/master/POPW/working/code/industreal_improved/src/training/train.py` (4431 lines)
- `/media/newadmin/master/POPW/working/code/industreal_improved/src/training/optimizer.py`
- `/media/newadmin/master/POPW/working/code/industreal_improved/src/config.py` (key params)

## Current Config Values
| Parameter | Value |
|-----------|-------|
| BASE_LR | 5e-4 |
| WEIGHT_DECAY | 1e-4 |
| WARMUP_EPOCHS | 5 |
| GRAD_CLIP_NORM | 1.0 |
| MIXED_PRECISION | False |
| GRAD_ACCUM_STEPS | 16 |
| BATCH_SIZE | 2 |
| EPOCHS | 100 |
| PATIENCE | 10 |
| DET_LR_MULTIPLIER | 1.0 |
| ACTIVITY_HEAD_GRAD_CLIP | 0.1 |
| USE_COSINE_ANNEALING | True (T_0=10, T_mult=2) |
| STAGED_TRAINING | False |
| STAGE3_WARMUP_EPOCHS | 3 |
| REINIT_REG_WARMUP_STEPS | 1000 |

---

## Issues Found

### CRITICAL

#### 1. `_override_start_epoch` module-level NameError when imported [train.py:3258, 3406]
- **Location**: Lines 3258 and 3406 reference `_override_start_epoch` which is defined at line 4407 inside the `if __name__ == '__main__':` guard block.
- **Problem**: If `train.py` is ever imported as a module (instead of run as `__main__`), `_override_start_epoch` does not exist in the module namespace. Both `main()` references will raise `NameError`.
- **Evidence**: Line 3258 explicitly suppresses the Flake8 warning with `# noqa: F821` ("undefined name"), confirming the author is aware this is a technically unbound name.
- **Risk**: Currently only triggered when `main()` is called without `__main__` guard. Low in production (always run as script), but blocks any library-style import of the training loop.
- **Fix**: Move `_override_start_epoch = None` to module level outside the `if __name__` guard, or use `globals().get('_override_start_epoch', None)` in `main()`.

#### 2. `loss_dict_seq` full overwrite discards criterion outputs [train.py:1092]
- **Location**: Line 1092: `loss_dict_seq = {k: 0.0 for k in loss_dict_seq}`
- **Problem**: Immediately after `criterion(fake_outputs, fake_targets)` returns the full loss dict at line 1085 (with keys: `total`, `psr`, `w_det`, `w_pose`, `w_act`, `w_psr`, `log_var_det`, `log_var_pose`, `log_var_act`, `log_var_psr`), line 1092 overwrites ALL values to 0.0. Only `psr` and `total` are selectively restored (lines 1096-1100). All Kendall weight keys (`w_*`) and log_var keys silently become 0.0.
- **Impact**: Running averages for Kendall weights do not include contributions from seq batches (50% of all batches when `seq_every=2`). This systematically under-represents Kendall uncertainty weights in the per-epoch metrics. The metrics logged for `w_det`/`w_pose`/`w_act`/`w_psr` are biased toward non-seq-batch dynamics.
- **Severity**: The epoch-level average metrics for Kendall weights are ~50% missing data. The training itself is unaffected (weights are computed per-batch, not from running averages), but logged metrics are misleading for PSR/activity uncertainty analysis.
- **Fix**: Keep the 0.0 overwrite for task-loss keys but preserve `w_*` and `log_var_*` keys from the original criterion output.

---

### HIGH

#### 3. Gradient clipping creates full parameter list copies every accumulation window [train.py:1178-1181, 1622-1625]
- **Location**: Lines 1178-1181 (seq path), 1622-1625 (non-seq path)
- **Problem**: `list(model.parameters())` creates a full copy of all parameter references every accumulation window (every 16 batches). With a multi-head model (ConvNeXt backbone + 4 task heads + FPN + transformer + criterion), this is thousands of tensors. The same pattern repeats inside `torch.nn.utils.clip_grad_norm_()` which iterates the list.
- **Impact**: Unnecessary CPU memory churn and GC pressure at every gradient update step. On a model with ~30M+ params, calling this 1000+ times per epoch adds measurable overhead.
- **Fix**: Cache the parameter list or use precomputed lists. `model.parameters()` already returns a generator; `list()` materializes it.

#### 4. Seq-batch gradient clipping does double duty with per-head clip [train.py:1172-1181]
- **Location**: Lines 1172 (per-head activity clip) and 1178 (global clip) in seq path
- **Problem**: The per-head activity gradient clip at `ACTIVITY_HEAD_GRAD_CLIP=0.1` is applied FIRST, then the global clip at `GRAD_CLIP_NORM=1.0` recomputes the total norm across ALL params (including already-clipped activity head). Since 0.1 < 1.0, the per-head clip always wins for activity params, but the global clip still scans all params to compute the norm.
- **Impact**: Wasted computation. Every accumulation window computes two full gradient norms: one for activity head only (line 1177) and one for all params including criteria (line 1178-1181). The per-head clip on the seq path is also wrongly labeled "(AMP path)" — it applies in FP32 mode too.
- **Note**: Same pattern in non-seq path (lines 1587-1591, then 1622-1625) but there the comment says "(FP32 path)" — so the labeling inconsistency is cosmetic but the double-computation applies to both paths.

#### 5. Scheduler LR and Stage-3-warmup LR race on activity_psr param group [train.py:3630, 3648-3658]
- **Location**: scheduler.step() at line 3630, Stage 3 warmup override at lines 3648-3658
- **Problem**: `scheduler.step()` at line 3630 updates ALL param groups (including `ACTIVITY_PSR_PARAM_GROUP_IDX`). Then lines 3648-3658 unconditionally overwrite the activity_psr group LR with the Stage 3 warmup value. The scheduler's internal `last_epoch` counter for CosineAnnealingLR continues advancing on the activity_psr group even though the LR is immediately replaced.
- **Impact**: When Stage 3 warmup ends (after STAGE3_WARMUP_EPOCHS), the activity_psr LR jumps from the warmup's final value to the cosine-decayed value at that epoch, creating a discontinuity. The cosine has been "counting" epochs against this group the entire time, so its value at handoff may be significantly lower than the warmup final value. If cosine has decayed from 5e-4 to ~3e-4 over ~14 epochs, the sudden LR drop can shock the freshly-unfrozen activity/PSR heads.
- **Fix**: Either (a) exclude activity_psr from cosine scheduler's compute (not directly supported by SequentialLR), or (b) set cosine to start from the warmup's final LR when Stage 3 warmup ends (complex), or (c) move scheduler.step() after the override block so the cosine doesn't "waste" steps on the overridden group.

---

### MEDIUM

#### 6. `build_optimizer()` is dead code diverged from main optimizer construction [optimizer.py:17-39 vs train.py:3012-3023]
- **Location**: optimizer.py `build_optimizer()` vs inline optimizer in train.py `main()`
- **Problem**: The optimizer in `main()` defines 6 param groups (backbone, det_head, head, activity_psr, bias, videomae + optional loss), while `build_optimizer()` defines only 3 (backbone, head, bias). The `main()` optimizer has detailed per-group LR (including DET_LR_MULTIPLIER, activity_psr separation, videomae preregistration). `build_optimizer()` assigns all non-backbone/non-bias params to a single `head_params` group.
- **Impact**: If someone runs tests using `build_optimizer()` from `optimizer.py`, they get a fundamentally different optimizer configuration than production. No weight decay separation for bias/LayerNorm — all groups get the same weight_decay=1e-4. No detection head LR multiplier. No activity_psr separation for Stage 3 warmup.
- **Fix**: Either delete `build_optimizer()` (dead code) or make it match `main()`'s construction exactly.

#### 7. `feature_bank.reset()` called without attribute guard [train.py:1116, 1491]
- **Location**: Lines 1116 (seq path) and 1491 (non-seq path)
- **Problem**: `model.feature_bank.reset()` is called directly without `hasattr(model, 'feature_bank')` guard. If `feature_bank` is absent (e.g., specific config or model variant), this raises AttributeError.
- **Impact**: A NaN-batch detection would crash with AttributeError instead of gracefully continuing. The outer epoch retry loop (lines 3542-3628) would catch it and retry up to 6 times, but each retry would fail with the same error, eventually raising RuntimeError. Since the model always has `feature_bank` in current configs, this is latent.
- **Fix**: Add `if hasattr(model, 'feature_bank'):` guard.

#### 8. Kendall log_var NaN reset uses `fill_(0.0)` then `clamp_()` with no effect [train.py:2065-2069]
- **Location**: `_clamp_kendall_log_vars`, lines 2065-2069
- **Problem**: When a log_var param is NaN, line 2067 resets to 0.0 via `fill_(0.0)`. Then lines 2068-2069 call `clamp_(_lo, _hi)`. Since 0.0 is always within bounds [-4, 2], the clamp_ is always a no-op after a NaN reset. The clamp_ is only meaningful for non-NaN values that have drifted outside bounds.
- **Impact**: Minor code smell — unnecessary clamp_ call after every NaN reset. No behavioral issue.
- **Fix**: Skip clamp when data was just reset to 0.0, or use a guard to avoid the redundant operation.

#### 9. Logit magnitude guard at step 0 ignores seq_every offset [train.py:1344-1361]
- **Location**: Lines 1344-1361 (step-0 assertion in non-seq path)
- **Problem**: The "step-0 assertion" at line 1344 checks `if step == 0`, but this code runs only for non-seq-batch steps. With `seq_every=2`, if step 0 is a seq batch, step 1 is the first non-seq batch. The step-0 gate fires at step=1, not step=0. The guard condition `if step == 0` never fires.
- **Impact**: The step-0 logit-magnitude guard (`cls_loss_val >= 1e4`) is a dead branch when `seq_every=2` and step 0 is a seq batch. The guard still works for non-seq configurations or when seq_every > 1 and step 0 is non-seq (depends on DataLoader ordering, which has sampler).
- **Fix**: Check `if total_steps == 0` (global counter) or move the check out of the if-seq-branch.

#### 10. `scaler.unscale_()` called unconditionally in FP32 mode [train.py:1153, 1581]
- **Location**: Lines 1153 (seq) and 1581 (non-seq)
- **Problem**: `GradScaler(enabled=False)` makes `unscale_()` a no-op. But the function call overhead still occurs every accumulation window. With `MIXED_PRECISION=False` as current default, every optimizer window pays this cost for nothing.
- **Impact**: Minor (function call overhead). Trivial on its own but compounds with issue #3 (double list creation).
- **Fix**: Guard with `if C.MIXED_PRECISION:` before unscale calls.

---

### LOW

#### 11. Epoch loop guard `_train_start_epoch >= C.EPOCHS` uses wrong comparison [train.py:3411]
- **Location**: Line 3411
- **Problem**: `if _train_start_epoch >= C.EPOCHS` fires a warning. But the range on line 3418 is `range(_train_start_epoch, C.EPOCHS)`, which with EPOCHS=100 and start=99 would iterate epoch 99 (one epoch). Only start >= 100 produces an empty range. The warning at line 3411 fires at start=100, but the natural reading suggests start >= EPOCHS means "out of range." It's actually correct but confusing.
- **Impact**: Cosmetic — warning text is slightly misleading for the edge case.

#### 12. Mixed `some_label_mask` mixup variable never used [train.py:445-449]
- **Location**: Lines 445-449 in `mixup_activity()`
- **Problem**: `same_label_mask` is computed at line 445 (an O(B^2) operation for batch_size=2 → trivial) but only used at line 450 in a sum check. For B=2 (actual batch size), this allocates a 2x2 matrix, compares element-wise, then sums. If batch size increases, this becomes O(B^2) for a rarely-firing early-return heuristic.
- **Impact**: Avoidable O(B^2) computation. Currently negligible at B=2 but should not be the limiting factor.
- **Fix**: Use `(activity_labels.unsqueeze(0) == activity_labels.unsqueeze(1)).float().sum() > 0.5 * B` or remove the heuristic entirely.

#### 13. CutMix alpha=1.0 but Mixup alpha=0.4 [train.py:430, 478]
- **Location**: Lines 430 and 478
- **Problem**: Mixup uses alpha=0.4 (default parameter) while CutMix uses alpha=1.0 (config parameter `C.CUTMIX_ALPHA=1.0`). The two augmentations alternate every epoch. The different alpha values mean they operate at different "strengths" — Mixup's beta(0.4) produces more extreme mixing (U-shaped distribution) while CutMix's beta(1.0) is uniform. This is intentional design but undocumented — no comment explains the asymmetry.
- **Impact**: Not a bug, but the asymmetry should be documented so it's not mistaken for an oversight.

#### 14. SWA code path accesses potentially stale train_loader [train.py:4239-4241]
- **Location**: Lines 4239-4241 (SWA BN update)
- **Problem**: `update_bn(train_loader, swa_model)` uses the last `train_loader` reference. If CUDA OOM auto-reduction triggered a loader rebuild (lines 3616-3622), the old `train_loader` variable points to the reduced-batch loader, not the original. SWA statistics would be computed on the reduced batch size, which may differ from the original training distribution.
- **Impact**: Only matters when CUDA OOM recovery was triggered during training AND SWA is enabled. Rare edge case.
- **Fix**: Track original loader separately, or rebuild from config params for SWA.

---

## Issues NOT Found (Clean Items)

### Gradient Clipping
- The global clip at `GRAD_CLIP_NORM=1.0` is correctly applied at every accumulation window (both seq and non-seq paths).
- The NaN gradient guard (lines 1641-1648, 1154-1161) correctly catches inf/NaN grads before optimizer.step().
- Per-head activity clip at `ACTIVITY_HEAD_GRAD_CLIP=0.1` is correctly scoped to activity_head params.
- The [RC-29] telemetry (lines 1669-1679) correctly tracks skipped optimizer windows.

### LR Scheduler
- Warmup (LinearLR, 5 epochs, start_factor=0.1) correctly transitions to the main scheduler.
- CosineAnnealingWarmRestarts with T_0=10, T_mult=2 is correctly configured.
- CosineAnnealingLR with T_max=EPOCHS-WARMUP_EPOCHS=95 is correctly configured for 100-epoch schedule.
- SequentialLR milestones=[5] correctly switches at warmup boundary.
- `scheduler.step()` called once per epoch (line 3630) — correct.

### Mixed Precision
- `GradScaler(enabled=True/False)` properly respects `MIXED_PRECISION` config flag.
- `amp.autocast('cuda', enabled=C.MIXED_PRECISION)` correctly wraps forward passes.
- The `scaler.update()` skip on seq batches (line 1200) is correctly commented out.
- The RC-29 scaler-skip detect (lines 1669-1679) correctly monitors scaler scale.

### Epoch Counting and `_REINIT_EPOCH_OFFSET`
- `_REINIT_EPOCH_OFFSET = max(0, start_epoch - 1)` at line 3259 correctly resets the stage counter.
- `get_stage()` at line 553 uses `effective_epoch = max(1, epoch - reinit_epoch_offset)` — correct.
- Stage boundaries (Stage 1: 1-5, Stage 2: 6-15, Stage 3: 16+) are correctly computed from effective_epoch.

### NaN Guards
- Per-batch NaN detection (lines 1474-1493) correctly skips, zeroes grads, clears feature bank, continues.
- Kendall NaN clamp counter (lines 1503-1523) correctly raises RuntimeError after 100 events.
- The NaN guard at lines 1411-1472 correctly handles staged-training mode with per-stage fallback.
- `_safe_log` (lines 3692-3709) correctly guards all train metric logging against NaN/Inf.

### Zero-Loss Detection
- The all-task-zero check (lines 1921-1929) correctly replaces 0.0 with 1e-4 fallback.
- The `num_batches == 0` guard (lines 1936-1941) correctly raises RuntimeError for empty loaders.

### DataLoader Recovery
- CUDA OOM auto-reduction (lines 3593-3627) correctly halves batch size, adjusts accumulation, rebuilds loader.
- DataLoader worker SHM error recovery (lines 3570-3591) correctly falls back to num_workers=0.
- Epoch retry loop (lines 3542-3628) correctly retries up to 6 times before raising.

### EMA
- Stage 3 EMA reinit (lines 3451-3458) correctly uses epoch-appropriate decay from `_get_ema_decay()`.
- VideoMAE unfreeze EMA reinit (lines 3526-3532) correctly re-creates EMA with new params.
- EMA swap for validation (lines 3806-3812) correctly guards with stage check.

---

## Summary Statistics

| Severity | Count |
|----------|-------|
| CRITICAL | 2 |
| HIGH | 3 |
| MEDIUM | 5 |
| LOW | 4 |
| **Total** | **14** |

## Key Takeaways

1. **Most serious**: `_override_start_epoch` is a `NameError` waiting to happen on import (lines 3258, 3406).
2. **Most impactful**: The `loss_dict_seq` overwrite at line 1092 silently discards Kendall weight info from 50% of batches, corrupting logged uncertainty metrics.
3. **Most wasteful**: Gradient clipping scans all parameters at every accumulation window, creating full list copies (lines 1178, 1622). With 100 epochs x ~156 windows/epoch = ~15,600 redundant allocations.
4. **Scheduler issue**: The Stage 3 warmup races with the cosine scheduler for activity_psr LR, creating a potential discontinuity at warmup termination (lines 3630, 3648).
5. **Code health**: The training loop has extensive defensive guards (NaN, OOM, zero-loss, grad-nan) that make it robust in production. The issues found are primarily in logging correctness and computational efficiency, not training correctness.
