# Agent 20/20: End-to-End Integration Audit

**Focus**: Cross-component bugs — argument compatibility, stage transitions,
checkpoint lifecycle, config consistency, and silent failures between
`stage_manager.py`, `train.py`, `config.py`, and `model.py`.

**Audit Date**: 2026-06-17

---

## BUG 1 (CRITICAL) — Detach flags absent from config presets

### Symptom
Running `train.py --preset stage_rf1` **outside** `stage_manager.py` silently
omits gradient isolation for the regression and PSR heads. After
`--reinit-heads`, the freshly-initialized heads receive **full-strength
backprop through shared FPN features**, causing detection head collapse within
epochs.

### Root Cause
The `--detach-reg-fpn` and `--detach-psr-fpn` flags are only set by
`stage_manager.py` via CLI args (train.py lines 4387-4393). The config presets
in `config.py` (`apply_preset()`, lines 1188-1281) do **not** set
`C.DETACH_REG_FPN` / `C.DETACH_PSR_FPN`. The rf1–rf10 stage presets contain
task ablation flags (TRAIN_DET, TRAIN_HEAD_POSE, etc.) and LR/momentum
overrides but **zero detach flags**.

### Files
- `stage_manager.py` line ~1580: sets `--detach-reg-fpn` `--detach-psr-fpn` in
  CLI args when `stage_cfg.get('detach_reg_fpn', stage_cfg.get('reinit_heads'))`
  evaluates truthy.
- `train.py` lines 4387-4393: sets `C.DETACH_REG_FPN = True` / `C.DETACH_PSR_FPN
  = True` from CLI flags only.
- `config.py` lines 1188-1281: `apply_preset()` — no detach flag set.
- `model.py` lines 494-517: `DetectionHead.__init__` accepts `detach_reg_fpn`
  param, controls `feat.detach()` at line 550.
- `model.py` lines 1957-1960: PSR head checks `C.DETACH_PSR_FPN` at runtime.

### Impact
Anyone running `train.py --preset stage_rf3 --reinit-heads` directly (outside
stage_manager orchestration) gets silent detection head degradation over 2-3
epochs. The detection mAP may appear to improve initially (shared FPN still
benefits from activity/PSR gradients) but the regression head's own gradients
are corrupting the FPN features it depends on.

### Fix
Add detach flag defaults in `apply_preset()` for any preset that
includes `reinit_heads: true`:

```python
if preset.get('reinit_heads', False):
    C.DETACH_REG_FPN = True
    C.DETACH_PSR_FPN = True
```

---

## BUG 2 (CRITICAL) — Per-stage checkpoint subdirectories assumed but never created

### Symptom
`stage_manager.py` expects checkpoints in stage-specific subdirectories
(e.g., `checkpoints/rf1/best.pth`, `checkpoints/rf2/best.pth`), but
`train.py` always saves to the flat shared path (`checkpoints/best.pth` and
`checkpoints/latest.pth`). Resume works only via a silent fallback, and the
intended per-stage checkpoint isolation is entirely non-functional.

### Root Cause
Two mismatched design assumptions:

1. **Save side** (train.py lines 4059-4149): Always saves to
   `C.CHECKPOINT_DIR / 'best.pth'` and `C.CHECKPOINT_DIR / 'latest.pth'` —
   no stage-specific subdirectory logic.

2. **Load side** (stage_manager.py `_determine_resume_source()`, lines
   2722-2763): Resolves resume checkpoint as:
   `CKPT_DIR / prev_stage['name'] / 'best.pth'`
   This path **never exists** because train.py never created it. The function
   silently falls through to the shared `CKPT_DIR / 'best.pth'`.

### Impact
- All 10 stages (RF1–RF10) share the same `checkpoints/best.pth` file.
- Stage N+1 overwrites Stage N's best checkpoint when it improves the combined
  metric. If RF3 retraining produces a better model than RF2 did, RF2's
  reference checkpoint is lost.
- The per-stage subdirectory structure (clearly intended from the code) is
  entirely vestigial.
- `_verify_next_stage_has_resume_source()` (line 2766) always returns `True`
  because it checks `shared_best.exists()` as the OR condition — so the failure
  is completely silent.

### Fix
Either:
- **(a)** Have train.py save to `checkpoints/{stage_name}/best.pth` when
  `_STAGE_MANAGER_ACTIVE` env var is set (detected at line 4101), or
- **(b)** Have stage_manager copy/rename `checkpoints/best.pth` to
  `checkpoints/{prev_stage}/best.pth` after each stage completes, or
- **(c)** Fix `_determine_resume_source()` to only check the shared path and
  remove the per-stage subdirectory logic.

---

## BUG 3 (HIGH) — `_STAGE_LR_MULT` retry scaling overwritten by optimizer state dict

### Symptom
When `stage_manager.py` retries a stage with `strategy['lr_mult'] != 1.0`,
the reduced LR computed by train.py is silently **overwritten** by the
checkpoint's optimizer state dict. The retry trains at the original LR,
defeating the retry strategy.

### Root Cause
The execution chain:

1. `stage_manager.py` line 1592 sets `env['_STAGE_LR_MULT'] =
   str(strategy['lr_mult'])` — e.g., `"0.5"` for a halved-LR retry.

2. `train.py` line 2980 reads `_stage_lr_mult =
   float(os.environ.get('_STAGE_LR_MULT', 1.0))` and applies it to
   `backbone_lr` (line 2983) and `head_lr` (line 2984) at optimizer
   construction time.

3. `train.py` line 3147 loads the checkpoint: `optimizer.load_state_dict(
   ckpt.get('optimizer_state_dict', ...))`. This restores the optimizer's
   internal `param_groups[0]['lr']` etc. from the checkpoint's last epoch —
   **overwriting** the `_STAGE_LR_MULT`-scaled values set in step 2.

4. The `--reset-scheduler` fix (lines 3153-3157) only applies when
   `args.reset_scheduler` is set, which only happens for `--reinit-heads`
   retries (stage_manager line 1578-1580). General retries without
   reinit-heads lose the LR scaling.

### Impact
Retry strategies that reduce LRs (e.g., `lr_mult: 0.5`) are silently
ineffective for the optimizer state. The first optimizer step after checkpoint
load uses the original (unscaled) LR. The warmup epochs may also be
unaffected (see Bug 5). This wastes the retry attempt and can delay or
prevent convergence recovery.

### Fix
After checkpoint optimizer load and after the `--reset-scheduler` block, add:

```python
# Re-apply STAGE_LR_MULT to all param groups (retry strategies)
if _stage_lr_mult != 1.0:
    for pg in optimizer.param_groups:
        pg['lr'] *= _stage_lr_mult
```

---

## BUG 4 (MEDIUM) — Pre-advance symlink mechanism is dead code

### Symptom
The pre-advance symlink creation (lines 2369-2381, 2562-2572, 2615-2626 in
stage_manager.py) **never executes**. The verification gate always passes
because the shared `checkpoints/best.pth` exists, making the entire per-stage
symlink fallback vestigial.

### Root Cause
`_verify_next_stage_has_resume_source()` (line 2766) checks:

```python
prev_best = CKPT_DIR / prev_stage['name'] / 'best.pth'
shared_best = CKPT_DIR / 'best.pth'
if prev_best.exists() or shared_best.exists():
    return True
```

After the first epoch of any RF stage, `shared_best.exists()` is `True`
(because train.py saves `best.pth` to `CKPT_DIR`). So the function always
returns `True`, and the `if not _verify_next_stage_has_resume_source(...)`
guard at lines 2370, 2564, 2618 is **never** satisfied.

Even if it did execute, the symlink would be:
`checkpoints/next_stage/best.pth` -> `checkpoints/best.pth` (absolute path)

This points to the shared checkpoint, not a per-stage checkpoint — so the
symlink would not provide the intended per-stage isolation anyway.

### Impact
- 180 lines of dead code (3 almost-identical symlink creation blocks)
- Misleading log messages about "fallback" that never triggers
- The per-stage directory structure (`checkpoints/rf1/`, etc.) is created
  by `_verify_next_stage_has_resume_source` -> `_determine_resume_source`
  looking for them, but they remain empty directories forever

### Fix
Remove the symlink creation blocks entirely. If per-stage checkpoint
isolation is desired, implement it at save time (in train.py) rather than
with post-hoc symlinks.

---

## BUG 5 (MEDIUM) — Checkpoint key naming convention mismatch across save/load

### Symptom
The save and load paths in train.py use different primary key names and
fallback priorities for checkpoint dictionaries. The save consistently uses
bare names (`'model'`, `'optimizer'`, `'scheduler'`) while the load prefers
the `_state_dict` suffix variant. Though both paths are self-consistent, the
mismatch is a maintenance liability and creates silent compatibility risks
when mixing checkpoint sources.

### Root Cause
**Save** (train.py lines 4059-4149, multiple save points):
```python
'model':     model.state_dict(),
'optimizer': optimizer.state_dict(),
'scheduler': scheduler.state_dict(),
```

**Load** (train.py lines 3113-3177):
```python
# Model: prefers model_state_dict -> model_state -> model
model_state = ckpt.get('model_state_dict',
               ckpt.get('model_state',
               ckpt.get('model')))

# Optimizer: prefers optimizer_state_dict -> optimizer_state -> optimizer
opt_state = ckpt.get('optimizer_state_dict',
             ckpt.get('optimizer_state',
             ckpt.get('optimizer')))

# Scheduler: prefers scheduler_state_dict -> scheduler -> lr_scheduler_state
sched_state = ckpt.get('scheduler_state_dict',
               ckpt.get('scheduler',
               ckpt.get('lr_scheduler_state', {})))

# Scaler: prefers scaler_state_dict -> scaler_state -> scaler
scaler_state = ckpt.get('scaler_state_dict',
                ckpt.get('scaler_state',
                ckpt.get('scaler', {})))
```

The save always uses the **third fallback** (`'model'`, `'optimizer'`,
`'scheduler'`). The load prefers the **first variant**
(`'model_state_dict'`, etc.) — keys that are **never used by the save code**.

Additionally, the scheduler fallback order is inconsistent with the others:
model/optimizer/scaler follow the pattern `_state_dict` -> `_state` -> bare,
but scheduler goes `_state_dict` -> bare -> `lr_scheduler_state`.

### Impact
- Self-consistent operation works correctly (load always finds `'model'` on
  the 3rd try), but the first two `get()` calls are wasted on every resume.
- If a checkpoint from any external source happened to contain BOTH
  `model_state_dict` and `model` keys (e.g., from a merge or partial
  restore), the load would silently pick `model_state_dict` — potentially
  stale or incompatible weights — with no warning.
- The inconsistent fallback order across keys means the scheduler loads
  differently (`scheduler` before `lr_scheduler_state`) compared to
  model/optimizer (`bare` last), creating subtle asymmetric behavior.

### Fix
Align the save and load key names. Either:
- **(a)** Change the save to use `model_state_dict`, `optimizer_state_dict`,
  `scheduler_state_dict` (matching load preference), or
- **(b)** Change the load to try the bare name first (matching save reality),
  keeping the fallbacks only for backward compatibility with old checkpoints:
  ```python
  model_state = ckpt.get('model', ckpt.get('model_state_dict',
                              ckpt.get('model_state')))
  ```

---

## Summary Table

| # | Severity | Bug | Components | Impact |
|---|----------|-----|-----------|--------|
| 1 | CRITICAL | Detach flags absent from config presets | config.py, train.py, model.py, stage_manager.py | Silent detection head collapse when running train.py outside stage_manager |
| 2 | CRITICAL | Per-stage checkpoint subdirs never populated | stage_manager.py, train.py | All 10 stages share same `best.pth`; per-stage isolation non-functional |
| 3 | HIGH | `_STAGE_LR_MULT` overwritten by optimizer state | stage_manager.py, train.py | Retry LR scaling silently ignored for optimizer state (reinit-heads retries only partially fixed via `--reset-scheduler`) |
| 4 | MEDIUM | Pre-advance symlink mechanism is dead code | stage_manager.py | 180 lines of never-executed code; misleading log messages |
| 5 | MEDIUM | Checkpoint key naming mismatch save vs load | train.py | Load tries `model_state_dict` first; save writes `model` — wastes 2 dict lookups per key, creates silent compatibility risk |
