# Agent 3: Stage Manager State Machine — Deep Audit

**File:** `/media/newadmin/master/POPW/working/code/industreal_improved/src/training/stage_manager.py` (3125 lines)

**Date:** 2026-06-17

---

## BUG-01: `_determine_resume_source()` ignores per-stage `resume_source` config [CRITICAL]

**Lines:** 108, 140, 175, 213, 250, 287, 324, 361, 398, 437 (config) + 2722-2763 (function)

Every stage definition declares a `resume_source` field (`'latest'` for rf1, `'best'` for rf2-rf10), but the function `_determine_resume_source()` **never reads this field**. It has its own hardcoded resolution logic:

- `stage_index > 0`: always looks for previous stage's `best.pth` -> shared `best.pth` (never checks `latest`)
- `stage_index == 0, not retry`: always uses `LATEST_CKPT` or None
- `retry`: always uses stage-specific `latest.pth` -> shared `latest.pth` (never checks `best`)

The config field `resume_source` is dead code — it only survives as a comment. The code does something different from what the config specifies. This is a maintenance hazard: anyone reading the stage definitions would think rf2 "resumes from best" but that's not actually what the code enforces.

**Recommendation:** Either remove `resume_source` from definitions, or make `_determine_resume_source()` parse and respect it.

---

## BUG-02: Retry path never considers `best.pth` as resume source [HIGH]

**Lines:** 2752-2761

On retry, the resume resolution chain is:
1. `CKPT_DIR / stage_name / latest.pth` (stage-specific latest)
2. `CKPT_DIR / latest.pth` (shared latest)
3. `None` (fresh start)

It **never** checks `CKPT_DIR / best.pth` (shared best) or `CKPT_DIR / stage_name / best.pth` (stage-specific best). This means:
- If the training that just crashed had partially corrupted its `latest.pth` (right at the crash boundary), but `best.pth` is intact, the retry will correctly detect corruption on the latest and fall through to `None` — a fresh start, losing ALL progress.
- If the latest checkpoint was saved at a low epoch and best was at a higher metric, the retry resumes from the worse checkpoint.

`validate_checkpoint()` at line 2825 is called on the resume source, so a corrupted `latest.pth` would be caught, but the function should fall back to `best.pth` before giving up entirely.

---

## BUG-03: Progress can exceed 100% (220%+ / overflow) [MEDIUM]

**Lines:** 1202-1231, especially 1206 and 1227

The progress calculation:
```python
current_epoch = max(snapshot.epoch, state.epoch)
progress_pct = (current_epoch / max_epochs * 100)
```

After a crash and retry with `--start-epoch 0` (fresh start, no resume checkpoint), train.py writes fresh `--- Epoch 0/N ---` lines to the log. But the log TAIL (500 lines) still contains entries from the previous failed run with epoch 20+. The last `--- Epoch N ---` in the window is from the old run, so `snapshot.epoch` = old run's epoch.

Concrete scenario:
- rf7 with `max_epochs=10` completes 15 epochs (extended via dynamic adjustment)
- Training crashes at epoch 15 out of 15
- Retry from fresh start: `max_epochs` = 10 (no resume checkpoint, so no adjustment)
- Tail 500 still contains `--- Epoch 15/15 ---` from the old run
- `current_epoch = max(15, state.epoch)` = 15
- `progress_pct = 15 / 10 * 100 = 150%`

This is amplified when `_compute_dynamic_max_epochs()` (line 1305) extends training to 150% of base, and then the next fresh-start retry sees epoch 22 / base 10 = 220%.

**Cause:** `estimate_progress()` has no awareness that the current check window may contain log entries from a prior retry. It assumes all log entries belong to the current run.

---

## BUG-04: LR increases on retry 4+ for non-det, non-final stages [HIGH]

**Lines:** 1012 (RETRY_STRATEGIES table) + 1036 (indexing)

The retry strategies table is:
- retry 0: `default` (lr_mult=1.0)
- retry 1: `reduce_lr_10x_warmup_2x` (lr_mult=0.1)
- retry 2: `reduce_lr_20x_warmup_3x` (lr_mult=0.05)
- retry 3: `reduce_lr_5x` (lr_mult=0.2) **<-- INCREASE**
- retry 4: `reduce_lr_2x_warmup_2x` (lr_mult=0.5) **<-- INCREASE**
- retry 5+: same as 4

At `retry_count >= 3`, the LR goes BACK UP from 0.05x to 0.2x to 0.5x. The stage-aware override in `select_retry_strategy()` (lines 1049-1068) mitigates this for rf1 (det-only) and rf8-rf10 (final), but **NOT for rf2-rf3 with retry_count >= 3**. If a lower LR (0.05x) failed to converge, a higher LR (0.2x) is extremely unlikely to succeed.

---

## BUG-05: `stale_crash_window` zeroes crash count even for genuine crashes [MEDIUM]

**Lines:** 1950-1957

```python
effective_crash_count = snapshot.crash_count
if snapshot.stale_crash_window or total_liveness > 0:
    effective_crash_count = 0
```

The condition `total_liveness > 0` zeroes crash counts whenever the training produced **any** liveness data in the window. This means:
1. Training runs healthily for 3 hours (producing LIVENESS lines every 10 steps)
2. Training crashes at epoch 25
3. Next `--check` reads tail 500, finds crash patterns AND liveness data from before the crash
4. `total_liveness > 0` is True -> `effective_crash_count = 0`
5. Stability check passes

This is **redundant**: the crash is detected by `is_pid_alive()` at line 2400, not by the stability checklist. But it incorrectly labels the crash as "stable" in stored checklist results. More critically, if cron fires during a zombie-PID window where `is_pid_alive()` still returns True but crash patterns are already in the log, the stability check would incorrectly zero the count.

---

## BUG-06: No atomic checkpoint saves — crash during `torch.save` corrupts checkpoint [HIGH]

**Lines:** train.py lines 793, 4083, 4133 (direct `torch.save` calls)

All checkpoint saves use direct `torch.save(save_dict, path)`. If the process crashes mid-write (OOM, SIGKILL, disk full), the file is left partially written. The stage manager's `validate_checkpoint()` catches this on the next launch, but:
- The best/latest checkpoint is gone — only recourse is fresh start
- If `latest.pth` is corrupted and `best.pth` is also old, ALL progress since last save is lost

Safe pattern not used:
```python
tmp = path.with_suffix('.tmp')
torch.save(save_dict, tmp)
os.replace(tmp, path)  # atomic on same filesystem
```

---

## BUG-07: TOCTOU race between training PID lock check and lock write [MEDIUM]

**Lines:** 2797 (read lock) vs 2860 (write lock)

Two concurrent `--check` invocations could both read the lock as empty, pass duplicate prevention, and launch separate training subprocesses. The second writes its PID to the lock file, overwriting the first.

Partial mitigation: `get_existing_train_pids()` (line 2837) kills existing matching processes before launch. But both invocations could scan simultaneously, see no matches, and both launch.

---

## BUG-08: `_STAGE_SEED_OFFSET` env var set but never consumed by train.py [MEDIUM]

**Lines:** stage_manager.py 1594 (set), train.py (not found)

The stage manager sets `env['_STAGE_SEED_OFFSET']` for each retry strategy (line 1594), but `train.py` never reads this variable. Every retry uses the same random seed regardless of the configured seed_offset in the strategy. This reduces retry effectiveness at escaping bad local minima.

---

## BUG-09: cmd_launch destroys issues_log audit trail [LOW]

**Lines:** 3079

```python
state.issues_log = []
```

The force-launch command clears the entire failure history. If a user runs `--launch RF3` to manually intervene, the complete failure history from RF1-RF2 is erased, making post-mortem analysis impossible without external logs.

---

## BUG-10: Near-gate stall detection uses only first gate metric [LOW]

**Lines:** 1295

```python
primary = next(iter(gate.keys()))
```

This always picks `det_mAP50` (first key in every gate dict) for stall detection. If det_mAP50 is improving but another metric is far from threshold, the function might incorrectly allow near-gate advancement. Gap magnitudes are informational only (line 1299) — they don't factor into the decision.

---

## BUG-11: PID reconciliation doesn't verify lock PID belongs to train.py [LOW]

**Lines:** 2269-2287

The reconciliation at line 2273 overwrites `state.training_pid` with any alive lock PID, but never verifies that PID actually runs a train.py process. This could cause the manager to:
- Skip launching training (thinks it's already running at line 2400)
- Send SIGTERM/SIGKILL to a non-training process during `kill_training()`

The lock PID verification only happens in `_launch_current_stage()` (lines 2801-2806), not during reconciliation.

---

## BUG-12: Fragile pgrep pattern for process matching [LOW]

**Lines:** 1428-1444

```python
result = sp.run(['pgrep', '-f', f'train.py.*--preset {preset}'], ...)
```

The `-f` flag matches any process whose command line contains this pattern. Any system process with similar args would be matched. Conversely, different arg ordering would miss the match.

---

## BUG-13: Double epoch tracking creates progress errors on retry [MEDIUM]

**Lines:** 1206, 1549-1561, 1576-1583

After retry with `--start-epoch 0`:
1. `launch_training()` inflates `max_epochs = resume_epoch + stage_cfg['max_epochs']` (line 1557)
2. train.py resets epoch counter to 0 via `--start-epoch 0`
3. Progress shows `0 / inflated_max * 100 = 0%` — under-reports actual remaining epochs

Without `--start-epoch 0` (normal resume):
- `state.epoch` may retain the OLD run's last epoch (e.g., 25 from pre-crash)
- `snapshot.epoch` reflects the new run's progress (e.g., 1)
- `current_epoch = max(1, 25) = 25` — over-reports progress

---

## BUG-14: `_verify_next_stage_has_resume_source()` only handles `'best'` case [LOW]

**Lines:** 2766-2784

Reads `resume_source` at line 2771 but only acts on `'best'`. For any other value (including `'latest'`), it returns True unconditionally without checking whether the checkpoint actually exists.

---

## SUMMARY TABLE

| ID | Severity | Lines | Description |
|----|----------|-------|-------------|
| BUG-01 | CRITICAL | 108-437, 2722-2763 | `_determine_resume_source()` ignores per-stage `resume_source` config field |
| BUG-02 | HIGH | 2752-2761 | Retry never falls back to `best.pth` — loses progress on corrupt latest |
| BUG-03 | MEDIUM | 1202-1231 | Progress >100% (220%+) after crash/retry with fresh start |
| BUG-04 | HIGH | 1012, 1036, 1049-1068 | LR increases (0.05x -> 0.2x -> 0.5x) on retry 4+ for rf2-rf3 |
| BUG-05 | MEDIUM | 1950-1957 | `total_liveness > 0` always zeroes crash count in stability checklist |
| BUG-06 | HIGH | train.py:793,4083,4133 | No atomic checkpoint saves — crash mid-write corrupts checkpoint |
| BUG-07 | MEDIUM | 2797-2860 | TOCTOU race between lock check and lock write (double launch) |
| BUG-08 | MEDIUM | 1594 (set), train.py (not read) | `_STAGE_SEED_OFFSET` env var set but never consumed by train.py |
| BUG-09 | LOW | 3079 | `cmd_launch` destroys `issues_log` audit trail |
| BUG-10 | LOW | 1295 | Near-gate stall detection uses only first gate metric (det_mAP50) |
| BUG-11 | LOW | 2269-2287 | PID reconciliation doesn't verify lock PID belongs to train.py |
| BUG-12 | LOW | 1428-1444 | `pgrep -f` pattern fragile — can match wrong processes |
| BUG-13 | MEDIUM | 1206, 1549-1583 | Double epoch tracking creates progress calculation errors on retry |
| BUG-14 | LOW | 2766-2784 | `_verify_next_stage_has_resume_source()` only handles `'best'` case |

---

## CROSS-CUTTING: DESIGN OBSERVATIONS

### State file as single source of truth — no WAL or transactions

The state file (`rf_stage_state.json`) is written in-place with `json.dump` (line 526). No atomic write pattern. A crash during `save_state()` corrupts the state file. The `load_state()` catches this with a `try/except` and starts fresh (line 518), but this loses all retry history, metric history, and cross-stage memory.

### 20-Why analysis is disconnected from retry selection

`run_20_why_analysis()` (line 2136) produces detailed root cause analysis, but the output is only **logged** — it never influences retry strategy selection. `select_retry_strategy()` is purely based on `retry_count`, not on the diagnosed failure mode. A "CUDA OOM" failure gets the same strategy as "All heads DEAD" collapse.

### Cron-driven design limitation

The stateless-cron architecture means `cmd_check()` re-reads the full log tail on every invocation. After a retry, the first 2-3 checks operate on a mixed window of old+new log entries. The `stale_crash_window` flag is the only mitigation, and it only covers crash pattern filtering, not epoch/metric contamination.
