# Agent 19: Logging, Monitoring, and Observability Audit

## 1. Log Level Usage

| Level      | Count in train.py | Assessment |
|------------|-------------------|------------|
| `debug`    | 6                 | Severely underused. Root logger set to `INFO` (line 2744) so all debug is silently discarded. |
| `info`     | 156               | Overloaded — includes per-batch diagnostics that should be `debug`. |
| `warning`  | ~60               | Used for liveness, NaN detection, crash recovery, OOM — good. |
| `error`    | ~29               | Used for fatal signals, zero-loss, OOM — appropriate. |
| `exception` | 3                | Used in training loop exception handlers — appropriate. |

**Problems:**
- `logger.debug` used only for: worker shutdown details, stage param count, Kendall gradient sentinel, loss component breakdown. All of these are legitimate diagnostics.
- Per-batch DET-DEBUG (line 1303), GPU memory snapshots (line 998), and heartbeat (line 1006) are logged at `info` level, which makes the log very noisy at scale (every 10 steps = hundreds of lines per epoch).
- The `_FlushingFileHandler` (line 2732) flushes every write. This is necessary for liveness in stage_manager's incremental log reader, but it means `info` floods the disk I/O with tiny writes.
- **Suggestion**: Move GPU mem snapshots and heartbeat to `debug`, or add a `LOG_PER_STEP` config to gate them.

## 2. tqdm Progress Bar Format

Defined at line 932:
```python
pbar = tqdm(loader, desc=f'Epoch {epoch} [{stage_label}]', leave=True, dynamic_ncols=True)
```

Postfix string (line 1778-1785):
```
loss=0.1234567 det=0.0123456(c=0.0012345,g=0.0111111) pose=0.0000123 act=0.0456789 psr=0.0012345 wd=0.30
```

**Issues:**
- **7 decimal places** on all loss values (`:.7f`) is excessive. Losses rarely change beyond 4 decimal places. This eats horizontal space and updates every step, causing unnecessary terminal redraw.
- **No liveness indicator** in the tqdm bar. The only dynamic update is `BAD_SAMPLE skip=N` on corruption — otherwise the bar gives no information about head health, grad norm, or GPU memory.
- **No batch-level learning rate** shown in the tqdm bar.
- **No speed metric** (it/s) — tqdm shows this by default, but the custom `set_postfix_str` overwrites it; the default tqdm `it/s` is lost.
- The `seq=1` tag on PSR sequence batches (line 1145) is only shown in the seq-branch postfix, not the main branch (line 1778). If you glance at the main bar you cannot tell if a seq batch ran.

## 3. Liveness Monitoring

### Per-Head Grad-Norm Liveness (`_log_per_head_grad_norm`, line 2096)
- Runs every `LIVENESS_GRAD_EVERY` (default 200) steps.
- Checks 5 head prefixes: `detection_head`, `pose_head`, `head_pose_head`, `activity_head`, `psr_head`.
- Threshold: ALIVE if grad-norm > 1e-6, otherwise DEAD.
- Logs both first-layer and last-layer grad norm for each head.
- PSR per-component: logs per-head output head grad norms for heads 0-11.
- GPU memory appended to same line.

**Strengths:** Granularity is per-head, per-layer, and per-PSR-component. Really good for diagnosing collapsed heads.

**Issues:**
- **Logged at `warning` level** (line 2153). This is semantically wrong — liveness checks are normal monitoring, not warnings. Warnings should be reserved for actual DEAD detection.
- The 1e-6 threshold is hardcoded (line 2130). Could be too strict for early training when heads are warming up.
- Stage manager parses liveness from the OLD format (`_PARSE_LIVENESS_RE` at line 586), which does NOT match the current `_log_per_head_grad_norm` output format (which uses `det:ALIVE[6.25e+00]/DEAD[0.00e+00]` syntax). **The stage manager liveness parser is broken** — it expects `det=6.25e+00 ALIVE | act=...` pipe-delimited format, but the current code produces `detection_head:ALIVE[6.25e+00]/DEAD[0.00e+00] | activity_head:ALIVE[...]` colon-delimited with different prefixes.

### Loss-Based Liveness (in losses.py, not examined here)
- Referenced in comments but not checked in this audit. The stage manager relies on grad-norm liveness from log parsing.

## 4. GPU Memory Logging

Two locations:
1. **Training loop** (line 994-1001): Every 10 steps, logs `memory_allocated` and `memory_reserved` in GB.
2. **LIVENESS_GRAD** (line 2147-2151): Appended to grad-norm liveness line.

**Uses both** `torch.cuda.memory_allocated()` and `torch.cuda.memory_reserved()` — correct. Shows allocated vs reserved gap which indicates fragmentation.

**Strengths:** Both allocated and reserved are captured. Included in liveness for free.

**Issues:**
- **No peak memory tracking.** `memory_allocated` is a point-in-time snapshot taken AFTER backward/forward but BEFORE optimizer step in some cases. True peak (during forward) is not captured.
- **No memory growth trend** over epochs. A slow leak is invisible until OOM.
- **No CUDA memory summary** (`torch.cuda.memory_summary()`), which would show fragmentation.
- **No per-allocator breakdown** (caching allocator, pool allocations).
- Frequency (every 10 steps) is frequent enough for trend detection but adds log noise at `info` level.

## 5. Log Frequency Summary

| Event | Frequency | Level | Line |
|-------|-----------|-------|------|
| GPU memory snapshot | Every 10 steps | INFO | 998 |
| Heartbeat (elapsed, speed) | Every 10 steps | INFO | 1006 |
| Loss component breakdown | Every 50 steps | DEBUG | 1776 |
| CPU RAM watchdog | Every 50 steps | INFO | 1794 |
| DET-DEBUG grad norms | Every 500 steps (step 0 only) | INFO | 1720 |
| DET-DEBUG tally | Every 500 steps | INFO | 1314 |
| Kendall grad sentinel | Every 100 steps | DEBUG | 1568 |
| Per-head grad-norm liveness | Every 200 steps | WARNING | 1574 |
| DataLoader health check | Every 100 steps | INFO | 1826 |
| Crash recovery checkpoint | Every 50 batches | WARNING | 974 |
| Epoch metrics | Once per epoch | INFO | 3711 |
| Validation metrics | Per `C.VAL_EVERY` epochs | INFO | 3976 |
| Efficiency metrics | Per `C.LOG_EFFICIENCY_EVERY` epochs | INFO | 3746 |

## 6. Task-Specific Loss Logging

All 4 task losses are logged separately in:
- **tqdm bar** (line 1778): `det(c,g) pose act psr`
- **Epoch summary** (line 3711):
  ```
  Train: loss=0.1234  det=0.0123  pose=0.0000  act=0.0456  psr=0.0012
  ```
- **Loss breakdown** (line 2429, at debug): includes Kendall weights and log_vars
- **JSONL** (line 4163): full `train` dict with per-task keys
- **Val summary** (line 3976): 14+ metrics including per-task breakdown

**Adequately covered.** All 4 ASD detection, head pose, activity, PSR are tracked independently.

## 7. Learning Rate Logging

**Problem**: LR is logged from a hardcoded param group index (line 3682):
```python
current_lr = optimizer.param_groups[2]['lr']
```

This assumes param_group[2] is always the "heads" group. If:
- Optimizer has < 3 groups (Lion path)
- Groups are reordered
- VideoMAE unfreeze adds groups

...the wrong LR is logged silently.

**Missing**: No per-param-group LR logging. The optimizer has up to 5-6 param groups (backbone, det_head, heads, activity+psr, loss params, VideoMAE). Only one LR is logged.

## 8. Gradient Norm Logging

**What IS logged:**
- Per-head first/last layer grad norm (LIVENESS_GRAD, every 200 steps)
- Kendall log_var gradient sentinel (every 100 steps, at DEBUG)
- DET-DEBUG detailed: cls_weight grad norm/mean/std, reg_weight, cls_subnet/reg_subnet final layer (every 500 steps)

**What is MISSING:**
- **Global gradient norm** after clipping is not logged. The clipped norm is computed inside `torch.nn.utils.clip_grad_norm_` but the return value is discarded (line 1622-1624, line 1178-1181). This is a critical omission — you cannot tell if clipping is actually happening or if the global norm is stable.
- **Pre-clip global norm** is not logged.
- **Per-head grad norm fraction** (what fraction of total grad norm each head contributes) is not logged. This would show if one head dominates training.
- Spike detection: max grad norm over epoch is not tracked, only warned at epoch level if >10x median.

## 9. Missing Metrics

| Metric | Status | Impact |
|--------|--------|--------|
| Peak GPU memory | NOT tracked | Can't detect fragmentation-induced OOM |
| GPU memory summary / fragmentation | NOT tracked | Can't diagnose "reserved >> allocated" |
| Disk space (`shutil.disk_usage`) | NOT in train.py | Can't warn before checkpoint write fails |
| Per-param-group LR | Only group[2] | Silent wrong LR if param groups change |
| Global grad norm (pre/post clip) | NOT logged | Can't tell if clipping is active |
| Per-head grad norm fraction | NOT logged | Can't see which head dominates |
| DataLoader stall time | NOT tracked | Can't diagnose I/O bottlenecks |
| Throughput (imgs/sec) | Only `batch/s` via heartbeat | Rough estimate, not precise |
| ETA remaining | Stage manager shows per-epoch | Often wrong (see bug below) |
| Learning rate per group trend | NOT in JSONL | Missing from metrics history |
| CUDA allocator retries/failures | NOT tracked | Can't diagnose allocator thrashing |
| `torch.cuda.memory_summary()` | NOT called | Would show fragmentation in detail |

## 10. TensorBoard/WandB Integration

**`TensorBoardLogger`** class exists in `src/utils/logger.py` (lines 11-38) but is **NEVER IMPORTED OR USED** by `train.py`. It's dead code.

**No WandB integration.** All metrics go only to:
- Console (logger + print)
- `train.log` (via `_FlushingFileHandler`)
- `metrics.jsonl` (open/append/close pattern at line 4188)

The JSONL at line 4163-4185 writes per-epoch records with `epoch`, `lr`, `train`, `val` keys. NaN/Inf are sanitized to 0.0 before serialization (line 4173-4182). This is parseable but loses NaN information.

**Impact**: No real-time dashboarding. No experiment comparison. No remote monitoring.

## 11. Console Output Format

Format: `%(asctime)s | %(levelname)s | %(message)s` (line 2742)
Example: `10:32:15 | INFO |   [GPU mem] step=10  allocated=4.25GB  reserved=5.10GB`

**Issues:**
- **No date in timestamp** (`%H:%M:%S` only). Cannot distinguish logs across day boundaries or multi-day runs.
- **Leading spaces** in many messages (e.g., `  [GPU mem]`, `  [LIVENESS_GRAD]`). This is inconsistent — some messages start with the tag, some have leading spaces. Makes regex parsing fragile.
- **LIVENESS_GRAD at warning level** is anomalous. A liveness check with all-ALIVE heads still prints `WARNING`, which trips monitoring alerts.
- Stage manager output format uses `HH:MM:SS` as well (line 63-65).

## 12. Disk Space Monitoring

**None in train.py or stage_manager.py.** The `shutil.disk_usage` import exists (line 67) but is only used for `/dev/shm` usage (line 323), not checkpoint directory space. Checkpoint writes can silently fail on a full disk, and there is no pre-check.

## 13. Subprocess Log File Management

**`subprocess.log`** (line 1608, `RF_RUN_DIR / 'logs' / 'subprocess.log'`):
- Opened in append mode (line 1610: `with open(log_file, 'a')`).
- **No log rotation.** No size limit. No truncation.
- On repeated retries, this file grows unbounded.
- Stage manager reads `train.log` (separate file) for parsing, but `subprocess.log` captures the subprocess stdout/stderr mix.
- The `train.log` file (line 2740) is also opened in append mode with a `_FlushingFileHandler`. Also no rotation.

## 14. Stage Manager Check Output — Root Cause of "Progress: 44/20 (220%)"

**Observed bug**: `Progress: 44/20 (220%) ETA: -1m`

**Root cause**: The `estimate_progress` function in stage_manager.py (line 1202-1231) has TWO bugs:

### Bug A: `max_epochs` never reflects dynamic extension
```python
max_epochs = stage_cfg.get('max_epochs', 20)  # line 1205 — always reads static config
```
The `_compute_dynamic_max_epochs` function (line 1305) can extend epochs (e.g., from 20 to 44), but its return value is only stored in `dynamic_max_epochs` local variable (line 2443), which is logged but never stored to state or passed to `estimate_progress`. The progress function always uses the original `max_epochs=20`.

### Bug B: `current_epoch` can exceed `max_epochs`
```python
current_epoch = max(snapshot.epoch, state.epoch)  # line 1206 — can be 44
remaining_epochs = max_epochs - current_epoch       # line 1217 — can be -24
```
These produce: `44/20` fraction, `220%` progress, and negative `ETA`.

By convention `Progress: epoch/max_epochs`, the denominator should be `max_epochs` (20) and numerator `current_epoch` (0-20). But when dynamic adjustment extends to 44, there's no clamping.

### Bug C: Stage manager parses epoch from `--- Epoch 44/19 ---` where denominator is `C.EPOCHS-1`
Train.py line 3419: `--- Epoch {epoch}/{C.EPOCHS - 1} ---` — the denominator is `EPOCHS-1`, not `EPOCHS`. Stage manager captures `group(2)=19` but does not use it for max_epochs. This is fine for parsing epoch number but misleading if someone reads the raw log and sees `--- Epoch 44/19 ---` wondering why the epoch counter exceeds the denominator.

### Summary of all logging bugs found:

1. **Hardcoded `param_groups[2]` for LR logging** (train.py:3682) — breaks if optimizer group order changes.

2. **`max_epochs` never takes dynamic extension into account** (stage_manager.py:1205) — causes "220%" progress display.

3. **No clamping on remaining_epochs** (stage_manager.py:1217) — negative ETA.

4. **LIVENESS_GRAD at `warning` level** (train.py:2153) — semantic misuse, trips alert systems.

5. **Stage manager liveness parser does NOT match current output format** — `_PARSE_LIVENESS_RE` (stage_manager.py:586) expects `det=6.25e+00 ALIVE | act=...` but current `_log_per_head_grad_norm` emits `detection_head:ALIVE[6.25e+00]/DEAD[0.00e+00] | ...`. **Stage manager liveness monitoring is effectively broken.**

6. **No date in log timestamps** — `%H:%M:%S` only (train.py:2742, stage_manager.py:64).

7. **Global grad norm pre/post clip not logged** — `clip_grad_norm_` return value discarded.

8. **TensorBoardLogger is dead code** — defined in `src/utils/logger.py` but never imported.

9. **Log level misuse** — 156 `info` calls include per-batch diagnostics that should be `debug`.

10. **`subprocess.log` and `train.log` grow unbounded** — no rotation, no size limit.

11. **No disk space monitoring** before checkpoint writes.

12. **tqdm precision too high** — 7 decimal places on loss values, updated every step.

13. **NaN sanitization to 0.0 in JSONL** (train.py:4180) — silently destroys NaN diagnostic signal.

14. **Leading whitespace inconsistency** in log messages — some have `  [TAG]`, others start with `[TAG]`.

15. **No DataLoader throughput (imgs/sec)** — only approximate batch/s via epoch heartbeat.
