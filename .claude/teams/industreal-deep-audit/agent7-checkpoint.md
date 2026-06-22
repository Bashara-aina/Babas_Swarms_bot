# Agent 7: Checkpoint Save/Load and Resume Logic Audit

## Files Audited
- `/media/newadmin/master/POPW/working/code/industreal_improved/src/training/train.py`
- `/media/newadmin/master/POPW/working/code/industreal_improved/src/training/checkpoint.py` (69 lines)
- `/media/newadmin/master/POPW/working/code/industreal_improved/src/training/stage_manager.py`

---

## 1. Checkpoint Format

There are **4 checkpoint file types** with **4 different key naming conventions**:

### a) `latest.pth` (epoch end, train.py:4133)
Keys: `epoch`, `model`, `optimizer`, `scheduler`, `scaler`, `best_metric`, `patience_counter`, `ema_shadow`, `criterion`

### b) `best.pth` (new best metric, train.py:4059)
Keys: `epoch`, `optimizer`, `scheduler`, `scaler`, `best_metric`, `patience_counter`, `val_metrics`, `model`, `ema_shadow`, `criterion`

### c) `crash_recovery.pth` (signal handler / epoch start / every 50 steps, train.py:765)
Keys: `tag`, `epoch`, `step`, `batch`, `total_steps`, `seq_steps`, `model`, `optimizer`, `scaler`, `nan_skips`, `running`, `best_metric`, `timestamp`, `ema_shadow`, `criterion`

### d) `swa.pth` (train.py:4244)
Keys: `epoch`, `model`, `optimizer`, `swa`

---

## 2. Key Naming Inconsistency (Multiple Formats)

**Issue 7.1: Four different key names for the same data, resolved with fallback chains.** Severity: MEDIUM.

- Model: `model_state_dict` / `model_state` / `model` (train.py:3116)
- Optimizer: `optimizer_state_dict` / `optimizer_state` / `optimizer` (train.py:3145)
- Scheduler: `scheduler_state_dict` / `scheduler` / `lr_scheduler_state` (train.py:3167)
- Scaler: `scaler_state_dict` / `scaler_state` / `scaler` (train.py:3168)
- EMA: `ema_state` / `ema_shadow` (train.py:3134)

The `crash_recovery.pth` saves use `model`, `optimizer`, and `ema_shadow` (train.py:772-773, 781) -- same as `latest.pth`. But earliest crash_recovery code wrote `model_state`, creating the inconsistency. The fallback chains (train.py:3116, 3145) handle this at load time, but `validate_checkpoint` (stage_manager.py:1172) only checks `model_state_dict` and `model` -- missing `model_state` from old crash_recovery checkpoints.

---

## 3. Save Timing

### Per-Epoch Saves
- `_save_crash_recovery('epoch_start')` at train.py:972 -- before first batch
- `latest.pth` at train.py:4133 -- after validation success each epoch
- `_save_crash_recovery(f'epoch_{epoch}_end')` at train.py:4152 -- after epoch end

### Intra-Epoch Crash Recovery
- Every 50 batches (train.py:974), `_save_crash_recovery('batch_XX')` is intended -- but **the variable `_checkpoint_interval` is never consulted** in the loop.

**Issue 7.2: `_checkpoint_interval = 50` declared but never used.** Severity: HIGH.

The variable `_checkpoint_interval` is set at line 974: `_checkpoint_interval = 50  # Save crash checkpoint every 50 batches`. However, there is **no loop body code** that checks `step % _checkpoint_interval == 0` or similar. The intra-batch crash recovery save for mid-epoch crashes was **removed**. The comment at line 1789 confirms:
> `crash_recovery.pth is always overwritten -- minimal storage, maximum safety.`
> `Named per-batch checkpoints removed -- they are redundant with crash_recovery.`

This means: if training crashes mid-epoch, the only available mid-epoch state is the last `crash_recovery.pth` written at `epoch_start` or the previous `epoch_N_end`. The `resume_batch` field in crash_recovery.pth (key `batch`) is **always saved as 0** (train.py:769), so mid-epoch resume will never detect it was mid-epoch -- it will restart the epoch from batch 0 with the last saved state.

### Best Model Save
- On combined metric improvement (train.py:4055-4083) -- saves `best.pth`
- Optionally swaps EMA weights before saving (train.py:4070-4072)

### Signal Handlers
- `fatal_signal_{sig_name}` for SIGSEGV/SIGABRT/SIGBUS/SIGFPE (train.py:823, 949)
- `signal_{sig_name}` for SIGTERM/SIGINT (train.py:833, 965)
- Guard: skips save if `IN_EVALUATION_PHASE` is True (train.py:820-821)

### Stage Manager Pre-flight Checkpoint Validation
- `validate_checkpoint()` at stage_manager.py:1155-1199
- Called before launch (stage_manager.py:2824-2825), falls back to fresh start if invalid
- Checks: file exists, size >= 1024 bytes, torch.load-able, has a state dict, no NaN weights, no extreme values (>1e4) in >50% of tensors

---

## 4. Load Logic

### `_load_model_compat()` (train.py:1960-1981)
- **Shape-matching only, no strict mode.** Iterates all keys in the loaded state dict; keeps only those where `k in model_state AND model_state[k].shape == v.shape`.
- Calls `load_state_dict(compatible, strict=False)` -- so missing keys in the checkpoint are silently initialized from model defaults.
- Returns `(load_result, skipped_keys)` tuple. `skipped_keys` contains `(key_name, checkpoint_shape, model_shape)` for shape mismatches.
- **Issue 7.3: Silent dtype mismatches.** Severity: LOW. Only checks `shape`, not `dtype`. If a checkpoint is saved in FP32 and the model expects FP16 (or vice versa), `load_state_dict` will upcast/downcast silently. This can cause precision changes invisible from the logs.

### Resume Code Path (train.py:3113-3249)
1. `torch.load(args.resume, map_location=device, weights_only=False)` -- all tensors on GPU immediately
2. `_load_model_compat()` loads compatible keys
3. EMA shadow restored with filter: `if k in ema.shadow` (train.py:3139)
4. Optimizer state restored with `load_state_dict()` -- wrapped in try/except (train.py:3143-3164)
5. Scheduler + scaler restored (train.py:3165-3181)
6. Epoch counter: `start_epoch = ckpt['epoch'] + 1` (train.py:3183) or `ckpt['epoch']` for mid-epoch (3200)
7. Criterion (Kendall log_vars) restored (train.py:3211-3227)
8. Early-epoch log_var reset if `start_epoch < C.WARMUP_EPOCHS` (train.py:3231-3249)

---

## 5. `--resume` vs `--pretrained` vs `--from-scratch`

- **`--resume`** (train.py:4287-4291): Loads full checkpoint state including optimizer, scheduler, EMA, criterion, epoch counter. Continues from where training left off.
- **`--from-scratch`** (train.py:4328-4329): Explicitly documented as "Does NOT load checkpoint -- model starts fresh." This is a **no-op flag** that just blocks resume.
- **`--pretrained`**: Not an argparse argument. Pretrained backbone weights are loaded in model construction (not in train.py), controlled by config.

**Issue 7.4: `--from-scratch` is a no-op.** Severity: LOW. The flag exists at line 4328-4329 with help text "Does NOT load checkpoint -- model starts fresh", but it is never read anywhere in the code. Nothing checks for `args.from_scratch`. The variable `_override_start_epoch` (set by `--start-epoch`) achieves the same effect.

---

## 6. `--reinit-heads` Interaction with Resume (train.py:3251-3321)

Executed AFTER checkpoint loading (train.py line 3252 runs after the resume block at 3113-3249).

1. **Epoch offset calculation** (train.py:3258-3259):
   ```python
   _actual_start = _override_start_epoch if _override_start_epoch is not None else start_epoch
   _REINIT_EPOCH_OFFSET = max(0, _actual_start - 1)
   ```
   Used to compute `effective_epoch = max(1, epoch - _REINIT_EPOCH_OFFSET)` for stage determination (train.py:553). When `--start-epoch 0` is passed (as stage_manager does for retry + reinit_heads at train.py:1583), the offset becomes 0 and the effective epoch equals the actual epoch, so stages reset properly.

2. **EMA shadow re-anchor** (train.py:3271-3283): Only resets shadow for params matching head/FPN prefixes. All other EMA shadow entries retain old checkpoint values. This is correct -- weight decay and EMA update will gradually overwrite stale values for non-reinit'd params.

3. **AdamW optimizer state reset** (train.py:3284-3305): Zeros `exp_avg` and `exp_avg_sq` in-place only for reinit'd head params. Old momentum from collapsed heads is discarded. Non-head params retain optimizer state.

4. **Kendall log_vars reset** (train.py:3308-3312): All four log_vars reset to 0.0 regardless of checkpoint values.

5. **PSR warmup counter** (train.py:3319-3320): Set to 200 steps for 2x grad multiplier.

6. **Step-0 assertion** (train.py:3331-3367): Runs diagnostic forward pass to verify logit magnitude < 8.0. Guard only fires on first epoch after reinit (train.py:1364: `epoch == _REINIT_EPOCH_OFFSET + 1`).

**Issue 7.5: `--reinit-heads` blocks unless `--start-epoch` is also used correctly.** Severity: MEDIUM. Stage_manager's `_launch_current_stage` passes `--reinit-heads` at line 1570. For retry+reinit, it also passes `--start-epoch 0 --reset-scheduler` at line 1583. But these flags are **hardcoded in stage_manager.py, not in train.py**. If a user manually runs `python train.py --preset rf1 --reinit-heads --resume latest.pth` without `--start-epoch 0`, the `_REINIT_EPOCH_OFFSET` will be based on the checkpoint's `start_epoch` (e.g., epoch 15), not 0, so stage detection will be wrong -- the effective epoch will be 1 (= 16 - 15), potentially skipping Stage 1 entirely.

---

## 7. `--reset-scheduler` (train.py:3169-3170, 3184-3187, 3208)

When `--reset-scheduler` is passed:
- Scheduler state is NOT loaded (line 3169: `if getattr(args, 'reset_scheduler', False)` -- skips `scheduler.load_state_dict`)
- Scaler IS still loaded (line 3171-3172)
- Optimizer LRs are overwritten with initial warmup LRs (train.py:3153-3157) after optimizer state is loaded
- `best_metric` and `patience_counter` are reset to 0 (line 3185-3186)
- Mid-epoch detection is skipped -- always does `start_epoch = ckpt['epoch'] + 1` (line 3208, but this is INSIDE the `else` branch at line 3206 which expects `resume_batch == 0`)

**Issue 7.6: `--reset-scheduler` forces epoch-boundary resume even for mid-epoch crashes.** Severity: MEDIUM. At line 3196, if `resume_batch > 0`, the code enters the mid-epoch branch which sets `start_epoch = ckpt['epoch']` (line 3200). But `--reset-scheduler` is only used with `--start-epoch 0`, which overrides start_epoch anyway (train.py:3406). So this is a design smell rather than a real bug currently, but it is fragile -- if someone uses `--reset-scheduler` without `--start-epoch 0`, the mid-epoch branch would still fire (and correctly resume mid-epoch), but the scheduler reset would conflict.

---

## 8. Checkpoint Corruption Detection

### `validate_checkpoint()` (stage_manager.py:1155-1199)
- File existence check
- File size < 1024 bytes -> corrupt (stage_manager.py:1162-1163)
- `torch.load()` exception -> corrupt
- NaN weight detection
- Extreme value detection (>1e4 in >50% of tensors)

### `_checkpoint_has_nan()` (train.py:656-666)
- Scans only `requires_grad=True` params for NaN/Inf
- **Issue 7.7: `_checkpoint_has_nan` only checks `requires_grad=True` params.** Severity: MEDIUM. Frozen params (requires_grad=False) are skipped. If a frozen backbone layer has NaN weights (from a prior corrupt checkpoint load), the NaN guard won't catch it, and a corrupt checkpoint could be saved.

### Save-time Corruption Protection
- `_save_crash_recovery()` moves model to CPU before saving if CUDA is unhealthy (train.py:718-723)
- Runs in a daemon thread with 30s timeout (train.py:804-808) -- prevents hang
- Model on GPU data is moved to CPU via `detach().cpu()` before serialization (train.py:726-734)
- Optimizer and scaler state similarly copied (train.py:739-763)

### Atomicity
**Issue 7.8: No atomic save (write-to-temp-then-rename).** Severity: HIGH.

All `torch.save()` calls write directly to the target path: `latest.pth` (train.py:4149), `best.pth` (train.py:4083), `crash_recovery.pth` (train.py:793), `swa.pth` (train.py:4250). If the process crashes mid-save, the file is **corrupt** with a partial write. This is especially dangerous for `best.pth` and `latest.pth` because:
- Stage_manager checks file size (stage_manager.py:1162-1163), which would catch 0-byte files but NOT partial writes that happen to exceed 1024 bytes
- A partial `.pth` file over 1024 bytes will pass `validate_checkpoint()` and fail at `torch.load()` with an opaque error

---

## 9. `crash_recovery.pth` Save Timing and Recovery Logic

### Saves occur at:
1. `epoch_start` (train.py:972)
2. `epoch_N_end` (train.py:4152)
3. Signal handlers (train.py:823, 833, 949, 965)

### Key field: `batch` is always 0 (train.py:769)
This means the mid-epoch resume path (train.py:3196-3204) **never triggers** from crash_recovery.pth. If a crash happens mid-epoch:
- On restart, the crash_recovery.pth `batch` field = 0
- `resume_batch = 0` (line 3196)
- Code takes the `else` branch (line 3206-3209): `start_epoch = ckpt['epoch'] + 1`
- Training resumes at the **next epoch**, losing all progress from the current epoch

**Issue 7.9: Mid-epoch crash recovery loses the current epoch's progress.** Severity: HIGH.

The `batch` field in crash_recovery.pth is **hardcoded to 0** at save time (train.py:769). There is no code in `train_one_epoch` that saves crash_recovery mid-batch with the current step count. The per-batch crash checkpoint functionality was removed (train.py:1789 comment confirms). So mid-epoch crashes always lose 1 full epoch of training.

The intra-epoch crash check every 50 batches (train.py:974: `_checkpoint_interval = 50`) is a **dead variable** -- it is never referenced in a save call within the batch loop.

---

## 10. `_REINIT_EPOCH_OFFSET` Calculation (train.py:3258-3259)

```python
_actual_start = _override_start_epoch if _override_start_epoch is not None else start_epoch
_REINIT_EPOCH_OFFSET = max(0, _actual_start - 1)
```

When used with stage_manager (which always passes `--start-epoch 0 --reset-scheduler` for retry+reinit, stage_manager.py:1583):
- `_override_start_epoch = 0`
- `_actual_start = 0`
- `_REINIT_EPOCH_OFFSET = max(0, 0 - 1) = 0`
- `effective_epoch = max(1, epoch - 0) = epoch` (starts from actual epoch 0)

This is correct -- stages reset to Stage 1 on the first epoch.

**Issue 7.10: When used without `--start-epoch`, offset gives confusing log output (logic is still correct).** Severity: MEDIUM (cosmetic). If user runs `--reinit-heads --resume latest.pth` without `--start-epoch 0`, the `_actual_start` will be `start_epoch`. The stage replay actually works correctly (the offset causes a full stage replay). The only issue is the misleading log message at train.py:3263-3265 which reports `start_epoch` (the raw checkpoint epoch) not the effective epoch corrected by `_override_start_epoch`.

---

## 11. EMA Shadow Weights Save/Load

### Save
- In `latest.pth` (train.py:4141): `{k: v.clone() for k, v in ema.shadow.items()} if ema is not None else {}`
- In `best.pth` (train.py:4073): Same pattern, but EMA weights are swapped temporarily for model save
- In `crash_recovery.pth` (train.py:781-783): `{k: (v.detach().cpu() if isinstance(v, torch.Tensor) else v) for k, v in ema.shadow.items()}`

### Load
- Filter: `if k in ema.shadow` (train.py:3139) -- only loads keys that exist in current EMA shadow
- **Issue 7.11: EMA shadow load filters by key but ignores shape.** Severity: MEDIUM. At train.py:3136-3139, shadow values are updated with `.update({k: v.to(...) for k, v in ckpt[ema_key].items() if k in ema.shadow})`. There is **no shape check**. If the model architecture changed between save and load (e.g., after `--reinit-heads` which reinitializes head dimensions), the EMA shadow could contain stale-shaped tensors. The `ema.shadow` dict will be populated with wrong-sized tensors, causing runtime errors at EMA swap time.

### Best Checkpoint EMA Swap
- At train.py:4068-4073: Before saving `best.pth`:
  1. `ema.get_ema()` -- swaps model weights to EMA shadow
  2. Saves model state dict
  3. `ema.restore()` -- swaps back
  4. Saves `ema_shadow` separately in the same dict
- **Issue 7.12: EMA swap during best checkpoint save is not perfectly signal-handler safe.** Severity: LOW. If a signal handler fires during the EMA swap between `get_ema()` and `restore()`, the model will be saved with EMA weights but the `ema_shadow` in the checkpoint will contain the pre-swap EMA values. However, signal handlers skip saves during evaluation (train.py:820), and the best checkpoint save path is within the evaluation phase, so this is mostly theoretical.

---

## 12. Best Checkpoint Selection Criteria (train.py:4055)

- Uses `combined` metric (computed at train.py:4047)
- Components: `det_mAP50`, `act_macro_f1`, `head_pose_MAE`, `psr_f1_at_t`
- NaN handling: non-finite components clamped to neutral values (0.0 for F1/mAP50, 360.0 for head_pose_MAE) before computing combined metric (train.py:4034-4036)
- Guard skips best-checkpoint update if task metrics are NaN (train.py:4010-4015)
- Comparison: `combined > best_metric` (train.py:4055)

**Issue 7.13: Best checkpoint comparison uses strict greater-than.** Severity: LOW. At train.py:4055, `if combined > best_metric:` means if the metric is equal (stable training), no checkpoint is saved. This is standard behavior but means the LAST best checkpoint ("first to reach it") is kept even if the final epoch has equal metric to the best.

---

## 13. Optimizer State Compatibility When LR Changes

- **Snapshot of initial param-group LRs** taken at train.py:3028: `_init_pg_lrs = [pg['lr'] for pg in optimizer.param_groups]`
- Restored only when `--reset-scheduler` is active (train.py:3153-3157)
- Without `--reset-scheduler`, checkpoint optimizer LRs overwrite the fresh scheduler's LRs (because `optimizer.load_state_dict()` at line 3147 restores per-param-group LR values from the checkpoint)
- The scheduler state dict also contains cached LR values -- loading it at line 3175 overwrites what `SequentialLR` computed

**Issue 7.14: Optimizer LR from checkpoint overrides scheduler LR during resume.** Severity: MEDIUM. At train.py:3147: `optimizer.load_state_dict(opt_state)` restores the checkpoint's per-param-group LRs. Then at line 3175: `scheduler.load_state_dict(sched_state)` restores scheduler state. But `SequentialLR`'s state dict includes `_last_lr`, which was computed from the checkpoint's optimizer state. The scheduler thinks it is at the checkpoint epoch, not epoch 0. Without `--reset-scheduler`, the LR curve continues smoothly but the actual LR values are from the checkpoint's optimizer state, not the scheduler's intended values for the resumed epoch.

---

## 14. Stage Manager Resume Source Determination (stage_manager.py:2722-2763)

### Resolution Order:
1. Stage > 0: previous stage's `best.pth` -> shared `best.pth`
2. RF1 (stage 0, not retry): run-specific `latest.pth`
3. Retry: stage-specific `latest.pth` -> shared `latest.pth`
4. Otherwise: None (fresh start)

**Issue 7.15: `_determine_resume_source` has no fallback to `latest.pth` when `best.pth` is missing.** Severity: LOW. At stage_manager.py:2734-2740, for stage > 0, only previous stage's `best.pth` and the run-root `BEST_CKPT` are checked. If neither exists, returns `None`. There is no fallback to `latest.pth`. A stage with no `best.pth` (because no metric improvement occurred) will cause a fresh restart even if `latest.pth` exists.

**Issue 7.16: `_verify_next_stage_has_resume_source` (stage_manager.py:2766-2784) only checks `best.pth`.** Severity: LOW. It does not fall back to `latest.pth`. If a stage finishes without saving a `best.pth` (e.g., all metrics were NaN, or no improvement over baseline), the next stage will warn "no best checkpoint" even though `latest.pth` exists and could be used.

---

## 15. Mixed Precision / GradScaler State in Checkpoints

- GradScaler state is always saved and loaded
- In `latest.pth` and `best.pth`: full `scaler.state_dict()` is saved
- In `crash_recovery.pth`: scaler state is saved at train.py:752-763 and 774
- On load: scaler state is restored (train.py:3168, 3172, 3177)
- **No issue detected** -- scaler state (scale factor, growth/backoff counters) is small and device-agnostic

---

## 16. SWA Checkpoint (train.py:4190-4251)

- Saved at train.py:4250 as `swa.pth`
- Contains: `epoch`, `model` (AveragedModel state dict), `optimizer`, `swa=True`
- `swa.pth` is never loaded by any code path -- it is output-only
- No crash_recovery or latest.pth for SWA phase

---

## 17. Summary of All Issues

| ID | Severity | Line(s) | Description |
|----|----------|---------|-------------|
| 7.1 | MEDIUM | train.py:3116,3145,3167, stage_manager.py:1172 | Four different key naming conventions for same data; validate_checkpoint misses `model_state` key |
| 7.2 | HIGH | train.py:974 | `_checkpoint_interval = 50` declared but never used -- no mid-epoch crash recovery saves |
| 7.3 | LOW | train.py:1960-1981 | `_load_model_compat` ignores dtype mismatches, only checks shape |
| 7.4 | LOW | train.py:4328 | `--from-scratch` flag defined but never read in any code path |
| 7.5 | MEDIUM | train.py:3252-3265 | Manual `--reinit-heads --resume` without `--start-epoch 0` misaligns stage timing |
| 7.6 | MEDIUM | train.py:3153-3208 | `--reset-scheduler` forces epoch-boundary resume, conflicts with mid-epoch path |
| 7.7 | MEDIUM | train.py:656-666 | `_checkpoint_has_nan` only scans `requires_grad=True` params; NaN in frozen layers missed |
| 7.8 | HIGH | train.py:793,4083,4149,4250 | No atomic save (write-to-temp-then-rename). Process crash mid-save corrupts checkpoint files |
| 7.9 | HIGH | train.py:769,974 | `crash_recovery.pth` batch=0 always; no mid-batch saves. Mid-epoch crashes lose full epoch |
| 7.10 | MEDIUM | train.py:3258-3259 | Offset calculation log without `--start-epoch` confusing (logic correct) |
| 7.11 | MEDIUM | train.py:3136-3139 | EMA shadow load ignores shape mismatches -- stale-shaped tensors cause runtime errors |
| 7.12 | LOW | train.py:4068-4073 | EMA swap during best checkpoint save not signal-handler safe (prevented by IN_EVALUATION_PHASE) |
| 7.13 | LOW | train.py:4055 | Strict `>` comparison means tied metrics don't save new checkpoint |
| 7.14 | MEDIUM | train.py:3147,3175 | Optimizer LR from checkpoint silently overrides fresh scheduler LR on resume |
| 7.15 | LOW | stage_manager.py:2734-2740 | No fallback to `latest.pth` when `best.pth` doesn't exist for stage transitions |
| 7.16 | LOW | stage_manager.py:2766-2784 | `_verify_next_stage_has_resume_source` only checks `best.pth`, not `latest.pth` |

## 18. Top 3 Critical Fixes

1. **Issue 7.8: Atomic save.** Wrap every `torch.save()` with save-to-temp-file + `os.rename()` so partial writes never corrupt the live checkpoint file.

2. **Issue 7.9: Mid-epoch crash recovery.** Either (a) save `batch` counter in crash_recovery.pth by adding periodic saves inside the batch loop, or (b) remove the misleading `batch` field defaulting to 0 since it is never populated, and accept the 1-epoch loss.

3. **Issue 7.2: Dead save interval.** Either implement the 50-batch intra-epoch crash saves (restoring mid-epoch resume functionality) or remove the dead variable `_checkpoint_interval` to avoid confusion.
