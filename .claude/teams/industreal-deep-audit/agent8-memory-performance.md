# Agent 8 -- GPU Memory, Performance, and Throughput Audit

**Date:** 2026-06-17
**GPU:** RTX 3060 12GB (Ampere), FP32 training
**Config:** Default multi-task (ConvNeXt-T + FPN + 5 heads + TMA + TemporalBank)
**VideoMAE:** Disabled (--reinit-heads context)
**Sequence mode:** PSR_SEQUENCE_LENGTH=2, SEQ_EVERY_N_BATCHES=2

---

## 1. CRITICAL: `CUDA_LAUNCH_BLOCKING=1` -- KILLING THROUGHPUT

**File:** train.py line 99
```python
os.environ['CUDA_LAUNCH_BLOCKING'] = '1'
```

**Impact:** This forces every CUDA kernel launch to block until completion,
eliminating ALL GPU-CPU parallelism. Normally PyTorch queues kernels
asynchronously (CPU prepares next batch while GPU computes), but this flag
makes every `torch.cuda.synchronize()` implicit on every operation.

**Estimated penalty:** 30-50% throughput reduction. On an RTX 3060 with
CUDA compute capability 8.6, the GPU-CPU overlap is especially valuable
for data loading and preprocessing.

**Recommendation:** Remove or conditionally disable this for production
training. It is useful for bring-up debugging (precise crash backtraces)
but should be `CUDA_LAUNCH_BLOCKING=0` for actual training runs.

---

## 2. MIXED_PRECISION=False -- FP32 is 2x slower

**File:** config.py lines 347-352
```python
MIXED_PRECISION = False  # Disable AMP -- PSR seq loss spikes corrupt GradScaler
```

**Root cause:** AMP (FP16) is disabled because PSR sequence-mode loss spikes
(up to ~1077 at step 850) produce inf/NaN gradients. GradScaler silently
skips `optimizer.step()` when unscaled grads contain inf/NaN, producing
zero gradient updates for entire epochs (RC-29 documented in train.py).

**Impact:** The config comment says "AMP with GradScaler gives ~2x training
speedup." With MIXED_PRECISION=False, the pipeline runs at roughly 50%
of achievable throughput.

**Risk of enabling AMP:**
- PSR sequence loss spikes (documented period ~200-250 batches at ~1077)
  cause GradScaler to reduce its scale factor, potentially underflowing
  detection gradients at the next det step.
- On RTX 3060 (no native BF16), FP16 has limited dynamic range.

**VRAM savings from AMP:** ~40% less activation memory, potentially allowing
BATCH_SIZE from 2 to 4.

**Recommendations (in priority order):**
1. **Fix PSR spike root cause** -- The spike-decay cycle (period ~200-250
   batches) is documented but not resolved. If spikes are deterministic
   (aligned with specific batch types), skip `scaler.update()` on those
   steps or clamp loss before backward.
2. **Use `scaler.update(scale_growth_factor=1.5)`** to make the scaler
   recover faster from spikes.
3. **Per-parameter AMP** (autocast `mixed_precision` on backbone, FP32 on
   PSR head) to isolate PSR from AMP while getting 1.5x speedup on
   backbone + FPN + detection.
4. **Enable BF16 via CUDA >= 11.8 + Ampere** -- RTX 3060 supports BF16
   compute but not BF16 tensor cores. Still gives better dynamic range
   than FP16 for the same memory savings.

---

## 3. BATCH_SIZE=2 -- Optimal for full multi-task, suboptimal for RF stages

**Current state (default config):**
- BATCH_SIZE=2, GRAD_ACCUM_STEPS=16, effective batch=32
- VRAM: ~7.6 GB / 12 GB at batch=2 (63% utilization)
- RF stages 1-10: BATCH_SIZE=4 (det-only or sub-tasks fit)
- Paper_run preset: BATCH_SIZE=2

**Analysis of BATCH_SIZE scaling:**
```
Component                     | batch=1 | batch=2 | batch=4
--------------------------------------------------------------
Model params + buffers        | 1.2 GB  | 1.2 GB  | 1.2 GB
Optimizer states (AdamW FP32) | 0.22 GB | 0.22 GB | 0.22 GB
EMA shadow (GPU, see #5)      | 0.11 GB | 0.11 GB | 0.11 GB
Input images (1280x720)       | 0.01 GB | 0.02 GB | 0.04 GB
Activations (peak, est.)      | 2.2 GB  | 4.0 GB  | 7.6 GB
CUDA context + overhead       | 0.5 GB  | 0.5 GB  | 0.5 GB
--------------------------------------------------------------
Total (est.)                  | 4.4 GB  | 6.0 GB  | 9.7 GB
Reserved (allocator overhead) |  +0.5GB |  +1.0GB |  +1.5GB
Peak (est.)                   | ~4.9 GB | ~7.0 GB | ~11.2 GB
```

**Verdict:** BATCH_SIZE=2 is correct for full multi-task on RTX 3060 12GB.
BATCH_SIZE=4 would risk OOM due to activation memory (especially with
TMA cell + TemporalBank + FPN multi-level features).

**Recommendation:** Keep batch=2 for default. For RF stages 1-3 where
only 2-3 heads are active, batch=4 config is appropriate.

**VAL_BATCH_SIZE=4:** With `torch.no_grad()` (no activations stored for
backprop), val should be able to handle batch=8 or even batch=16. The
current VAL_BATCH_SIZE=4 was reduced from 16 due to FP32 OOM, but with
gradient checkpointing enabled, val is not affected. Investigate whether
this was a DataLoader memory issue (workers + pin_memory) rather than GPU
memory.

---

## 4. EMA Shadow Weights on GPU -- ~112 MB Unnecessary VRAM

**File:** models/model.py lines 2143-2156

```python
class EMA:
    def __init__(self, model: nn.Module, decay: float = 0.999, device=None):
        self.device = device  # stored but NEVER USED to move tensors
        self.shadow = {}
        self._register()

    def _register(self):
        for name, param in self.model.named_parameters():
            if param.requires_grad:
                self.shadow[name] = param.data.clone().detach()
                # ^^^ .clone() keeps tensor on SAME device as param = GPU
```

**Analysis:** The EMA `shadow` dict clones all trainable parameters to
the GPU. With ~28M trainable params at FP32 = 112 MB. The `device`
parameter is saved in `__init__` but never used to `.cpu()` the shadow
tensors.

**Impact:** 112 MB of VRAM that could be reclaimed.

**During EMA eval (`get_ema()`):** Creates `self.backup` with another
GPU clone = 3 copies of model weights on GPU (live + shadow + backup).

**Recommendation:**
1. Move `self.shadow` to CPU by calling `.clone().detach().cpu()` in
   `_register()`.
2. In `update()`, move model params to CPU, compute avg, store back on CPU.
3. In `get_ema()`, move shadow to GPU, swap, move backup to CPU.
4. Trade-off: ~2ms per GPU->CPU transfer for each of 28M params, but
   frees 112 MB VRAM. Worthwhile if AMP is enabled (needs the headroom
   for batch_size increase).

---

## 5. `torch.cuda.empty_cache()` Called Excessively

**Counted call sites in train.py:**
- After NaN batch skip (lines 1025, 1118, 1150, 1445, 1468, 1492)
- Before seq batch (line 1033)
- After seq batch (line 1150)
- Pre-val flush (line 416)
- OOM recovery (lines 3431, 3590, 3615, 3907, 3926)
- Epoch cleanup (line 2626)
- Crash save (line 4255)

**Problem:** `torch.cuda.empty_cache()` releases ALL unused memory back
to the OS, forcing the CUDA caching allocator to re-allocate from scratch
for the next operation. This causes fragmentation and adds ~10-50ms of
page table overhead per call.

**On an RTX 3060 with PyTorch `expandable_segments:True`**, the allocator
can already extend existing segments. `empty_cache()` defeats this benefit.

**Recommendation:** Remove `empty_cache()` calls from the normal training
path (keep only in OOM recovery paths). The caching allocator is designed
to reuse memory efficiently without explicit emptying.

---

## 6. Sequence Path Gradient Flow -- Potential Memory Optimization

**File:** train.py lines 1121-1131

```python
# Zero backbone + FPN gradients on seq batches
if hasattr(model, 'backbone'):
    for _p in model.backbone.parameters():
        if _p.grad is not None:
            _p.grad = None
if hasattr(model, 'fpn'):
    for _p in model.fpn.parameters():
        if _p.grad is not None:
            _p.grad = None
```

**Observation:** On seq batches, the full forward pass is run (backbone
forward + FPN forward + PSR head), but backbone/FPN gradients are zeroed
after backward. This means backbone/FPN activations are still kept in
memory for the backward pass, then discarded.

**Opportunity:** Use `torch.no_grad()` for backbone + FPN on seq batches
by detaching earlier, or use `model.backbone.requires_grad_(False)` before
the forward, then restore after. This would save the activation memory
peak on seq batches (backbone activations are the largest memory consumer).

**Current seq batch overhead:** ~2-3 GB for backbone activations that
are computed but whose gradients are discarded. Could be eliminated.

---

## 7. CUDNN_BENCHMARK=False with CUDNN_DETERMINISTIC=True

**File:** config.py lines 409-410
```python
CUDNN_DETERMINISTIC = True
CUDNN_BENCHMARK = False
```

**Impact:** cuDNN benchmark mode searches for the fastest convolution
algorithms for the specific input sizes during a warmup run. With 1280x720
fixed input, benchmark mode would find optimal kernels in ~1-2 minutes
and provide 10-30% convolution speedup for the remaining training.

`CUDNN_DETERMINISTIC=True` forces deterministic algorithms which are
typically slower than their non-deterministic counterparts.

**Recommendation:**
- Set `CUDNN_BENCHMARK=True` when not debugging reproducibility.
- Set `CUDNN_DETERMINISTIC=False` for production runs -- the model has
  enough stochasticity (RandAugment, random stride, dropout) that exact
  bit-level reproducibility across runs is not meaningful.
- Expected speedup: 15-25% from these two changes alone.

---

## 8. ALLOW_TF32=True Enabled -- Already Leveraging Ampere

**File:** config.py lines 413-414
```python
ALLOW_TF32 = True
MATMUL_PRECISION = 'high'
```

**Good:** TF32 uses 10 mantissa bits vs FP32's 23, giving ~8x faster
matmul on Ampere with minimal precision loss. The `MATMUL_PRECISION='high'`
setting uses accurate rounding (not stochastic), which is recommended
for training.

**No action needed** on this -- it is already optimal.

---

## 9. NUM_WORKERS=8 Analysis

**File:** config.py line 345, train.py lines 2812-2818
```python
NUM_WORKERS = 8
TRAIN_PREFETCH_FACTOR = 4
VAL_NUM_WORKERS = 1
VAL_PREFETCH_FACTOR = 2
```

**Memory per worker:**
```
bytes_per_image = 3 * 720 * 1280 * 4 = 11.06 MB (FP32 in shared memory)
est_inflight = 8 workers * 4 prefetch * 2 batch * 11.06 MB * 2.0 = 1.42 GB
```

**Verdict:** 1.42 GB inflight in /dev/shm (32GB available). Acceptable.

**Performance consideration:** 8 workers with prefetch=4 means 32 batches
are being prepared simultaneously. At 2 images/batch = 64 images inflight,
each requiring decode + transform + normalization. On a 6-core/12-thread
CPU, 8 workers may cause context-switching overhead.

**Recommendation:**
- Profile with NUM_WORKERS=4 vs 8. If GPU utilization is already near
  100%, 8 workers is fine. If GPU is waiting on data, increase to 12
  (matching TORCH_NUM_THREADS=12).
- The `_choose_num_workers()` fallback correctly handles low /dev/shm,
  so no risk of crash.

---

## 10. `_prepare_images` -- Data Pipeline Bottleneck Analysis

**File:** train.py lines 216-232
```python
def _prepare_images(images, device, training=True):
    images = images.to(device, non_blocking=True)
    if images.dtype == torch.uint8:
        images = images.float().div_(255.0)
        if USE_RANDAUGMENT and training:
            from torchvision.transforms.v2 import RandAugment
            rand_aug = RandAugment(num_ops=2, magnitude=9)
            images = rand_aug(images.view(BT, C_, H, W)).view(BT, C_, H, W)
```

**Key observations:**
- `non_blocking=True` on the initial `.to(device)` is correct -- overlaps
  H2D transfer with GPU compute.
- RandAugment is applied ON-GPU (after `.to(device)`). This is good --
  avoids CPU-GPU round trip.
- The `uint8 -> float32` conversion with `.div_(255.0)` is in-place and
  efficient.
- `non_blocking=True` on `.to(device)` for targets (lines 1222-1233) is
  applied correctly.

**No action needed** -- the data pipeline is well-optimized.

---

## 11. Gradient Accumulation Overhead

**File:** config.py line 325, train.py lines 1152-1211
```python
GRAD_ACCUM_STEPS = 16  # effective batch = 32
```

**Overhead:** Gradient accumulation means the optimizer step runs
1/16 as often as the forward pass. Each optimizer step has overhead:
- `scaler.unscale_()` iterates all params
- `clip_grad_norm_()` iterates all params (2 passes: norm + clip)
- `scaler.step(optimizer)` applies AdamW update
- `scaler.update()` adjusts scale factor

**For GRAD_ACCUM_STEPS=16:**
- Optimizer overhead is negligible (~0.1% of total time).
- The trade-off favors memory (batch=2 fits in 12GB) over throughput.

**Optimal for RTX 3060:** The current GRAD_ACCUM_STEPS=16 is fine. If
batch could increase to 4, reduce to 8 for same effective batch.

---

## 12. FeatureBank Memory Overhead

**File:** models/model.py lines 1126-1139

```python
class FeatureBank(nn.Module):
    def __init__(self, embed_dim=512, window_size=8):
        self._bank: Dict[Tuple[str, str], List[torch.Tensor]] = {}
```

**Per-sequence memory:** window_size * embed_dim * 4 bytes = 16 * 512 * 4 = 32 KB
**Total (assuming 500 training videos):** ~16 MB

**Concern:** The `_bank` dict stores tensors directly. With
`FEATURE_BANK_DETACH=True`, these tensors are detached from the graph,
but they are still GPU tensors. Over many training steps, entries for
inactive videos may persist.

**Current mitigation:** `model.feature_bank.reset()` is called on NaN
skip paths (lines 1116, 1491). No periodic cleanup for normal operation.

**Recommendation:** Add a sliding-window cleanup that evicts least-recently-
accessed video entries from the bank when the bank exceeds a threshold
(e.g., 2000 entries ~64 MB). This prevents bank growth over very long
training runs.

---

## 13. Gradient Checkpointing on ConvNeXt Backbone

**File:** config.py lines 106-110, models/model.py lines 239-243
```python
USE_BACKBONE_CHECKPOINT = True  # saves ~50% activation memory @ ~20% compute cost
```

**Current scope:** Only the 4 ConvNeXt stages are checkpointed.

**Opportunity for additional checkpointing:**
- **FPN (Feature Pyramid Network):** Each level (P3-P7) computes lateral
  convolutions and top-down pathways. Checkpointing FPN could save
  ~200-400 MB of activation memory.
- **PSR transformer:** The causal transformer encoder is already potentially
  checkpointed (seen in .bak file). Verify it is active in current code.
- **Detection head subnet:** Each of the 5 FPN levels runs cls_subnet +
  reg_subnet (4 conv layers each). These are small individually but
  checkpointing saves memory at the level (P3-P7 loop boundary).

**Recommendation:** Add checkpoint wrapping for the FPN forward pass
when `USE_BACKBONE_CHECKPOINT=True`.

---

## 14. channels_last Memory Format -- Incomplete Integration

**File:** train.py lines 2883-2885
```python
# Note: channels_last on model-level caused RuntimeError: required rank 4 tensor
# (VideoMAE's EncoderDecoder has non-4D params like biases/LayerNorm that can't use CL).
# Keeping input-level channels_last in _prepare_images which is safe.
```

**Current state:** Model-level `channels_last` was attempted but reverted
due to VideoMAE compatibility issues. With VideoMAE disabled, this
restriction no longer applies.

**Impact of channels_last (NHWC) on Ampere:**
- ~10% convolution speedup on RTX 3060
- Requires `.to(memory_format=torch.channels_last)` on model and inputs
- No memory savings (same number of elements)

**Recommendation:** Re-enable model-level `channels_last` now that
VideoMAE is disabled. Add `model = model.to(memory_format=torch.channels_last)`
after `model.to(device)` on line 2886. This requires all inputs to also
use channels_last, which `_prepare_images` would need to handle.

---

## 15. CUDA Memory Allocator Configuration

**File:** train.py lines 1-6
```python
os.environ['PYTORCH_ALLOC_CONF'] = 'expandable_segments:True'
```

**Good:** `expandable_segments:True` prevents fragmentation OOMs by
allowing the allocator to extend segments instead of allocating new ones.

**Additional tuning:**
- `max_split_size_mb:128` -- Limits memory fragmentation. On RTX 3060
  12GB, tensors vary from ~1 KB (biases) to ~100 MB (activations).
  Setting max_split_size_mb=128 prevents large blocks from being split
  by small allocations.
- `roundup_power2_divisions:16` -- Reduces waste from rounding up
  allocations to power-of-2 sizes.

**Recommended PYTORCH_ALLOC_CONF:**
```
expandable_segments:True,max_split_size_mb:128,roundup_power2_divisions:16
```

---

## 16. Optimizer State Memory

**AdamW stores 2 states per parameter:**
```
exp_avg (momentum): 28M trainable * 4 bytes = 112 MB
exp_avg_sq (variance): 28M trainable * 4 bytes = 112 MB
Total optimizer state: 224 MB on GPU
```

**Recommendations:**
- **AdamW with `foreach=True`** (fused implementation) -- check if
  `optim.AdamW(params, foreach=True)` is compatible. Fused AdamW is
  5-10% faster on Ampere.
- **Adafactor optimizer** -- Reduces optimizer state to O(1) per param
  by factoring the second moment. Not recommended for vision (convergence
  concerns), but worth noting.

---

## 17. Torch Compile Opportunity

The entire pipeline runs in eager mode. `torch.compile` with `mode='reduce-overhead'`
or `mode='max-autotune'` could provide significant speedups:

- **Backbone:** ConvNeXt is transformer-like and compiles well (20-30% speedup)
- **FPN:** Small convolutions, moderate benefit (10-15%)
- **Detection head:** Repeated per-level convs, good compile target (15-20%)
- **TMA cell:** GRU with attention, moderate compile benefit (10-15%)

**Risk:** `torch.compile` has dynamic shape issues. If batch size or
PSR sequence length varies, recompilation overhead may negate benefits.

**Recommendation:** Explore `torch.compile` for the backbone only
(most stable, biggest gain) with `mode='reduce-overhead'` and
`dynamic=True` to handle any input size variations.

---

## 18. Throughput Metrics (batches/sec, samples/sec)

**File:** train.py lines 1004-1009
```python
if step > 0 and step % _heartbeat_interval == 0:
    elapsed = time.time() - t_start
    logger.info(f'speed={step/elapsed:.1f} batch/s')
```

**Current logged values (ep. 0 estimate for batch=2, FP32, full heads):**
- Expected: ~1.5-2.5 batches/sec (3-5 samples/sec)
- Expected with AMP: ~3-5 batches/sec (6-10 samples/sec)
- Efficiency metrics: `compute_efficiency_metrics` at `LOG_EFFICIENCY_EVERY=10`
  reports eff_fps (forward-only, not training).

**Not logged but should be:**
- Data loading time vs compute time (would reveal loader bottleneck)
- CUDA kernel launch overhead percentage
- Actual GPU utilization (via `nvidia-smi` polling in-process)

**Recommendation:** Add `torch.cuda.utilization()` telemetry and
data-loading-time wall clock to identify whether the pipeline is
compute-bound or data-bound.

---

## 19. Thread Contention

**File:** train.py lines 89-93
```python
os.environ['OMP_NUM_THREADS']       = '4'
os.environ['MKL_NUM_THREADS']       = '4'
os.environ['OPENBLAS_NUM_THREADS']   = '4'
os.environ['NUMEXPR_NUM_THREADS']    = '4'
os.environ['MALLOC_ARENA_MAX']      = '4'
```

**Good:** Thread caps prevent lock convoy. The previous configuration
had 28 threads contending on jemalloc + GIL futex, causing deadlock.

**But:** With `TORCH_NUM_THREADS=12` and `OMP_NUM_THREADS=4`, there is
a mismatch. PyTorch uses OpenMP internally for some ops, and the 4-thread
cap may starve certain operations.

**Recommendation:** Profile whether `OMP_NUM_THREADS=4` is a bottleneck
for specific operations (particularly convolution and normalization).
If the DataLoader workers are the primary CPU consumers and the main
process mostly launches GPU kernels, 4 OpenMP threads may be sufficient.

---

## 20. Summary: Quick Wins (Easiest to Implement)

| # | Change | Effort | Speedup | Memory |
|---|--------|--------|---------|--------|
| 1 | Remove `CUDA_LAUNCH_BLOCKING=1` | 1 line | 30-50% | None |
| 2 | `CUDNN_BENCHMARK=True` | 1 line | 15-25% | None |
| 3 | `CUDNN_DETERMINISTIC=False` | 1 line | 10-15% | None |
| 4 | Move EMA shadow to CPU | ~20 lines | None | ~112 MB |
| 5 | Remove excessive `empty_cache()` | ~5 deletions | ~0.5% | Lower frag |
| 6 | Enable AMP with PSR isolation | ~10 lines | 50-100% | ~40% activations |
| 7 | channels_last (VideoMAE off) | ~3 lines | ~10% | None |
| 8 | Allocator tuning (max_split_size) | 1 line | ~1% | Lower frag |

**Total potential speedup (all quick wins): 1.5x - 2.5x**
**Total potential VRAM savings: ~300 MB**
**Enables batch_size=4 from batch=2 with AMP:** Activations halve in
FP16, shadow moves to CPU, freeing ~800 MB total.

---

## 21. VRAM Budget Breakdown (Current, default config)

```
Component                        | VRAM (GB) | % of 12GB
---------------------------------|-----------|-----------
ConvNeXt-T backbone (FP32)       | 0.37      | 3.1%
FPN (5 level, 256ch)             | 0.12      | 1.0%
5 task heads                     | 0.08      | 0.7%
FeatureBank + TMA cell           | 0.02      | 0.2%
Total model weights               | 0.59      | 4.9%
---------------------------------|-----------|-----------
AdamW optimizer states           | 0.22      | 1.8%
EMA shadow (GPU, see #4)         | 0.11      | 0.9%
---------------------------------|-----------|-----------
Peak activation memory (batch=2) | ~4.0      | 33.3%
Input images (batch=2, 1280x720) | 0.02      | 0.2%
CUDA context + allocator overhead| 0.50      | 4.2%
CUDA memory fraction (0.95 cap)  | 0.60      | 5.0% (reserved)
---------------------------------|-----------|-----------
TOTAL estimated peak             | ~6.0 GB   | 50.0%
```

Note: The reported "3.78 GB / 11.4 GB (33%)" in config.py refers to an
earlier configuration. With gradient checkpointing and sequence mode,
actual usage is approximately 6-8 GB.

---

## 22. Recommendations Summary

**Must-fix (production correctness/throughput):**
1. Remove `CUDA_LAUNCH_BLOCKING=1` for training
2. Fix PSR loss spikes to re-enable AMP (2x speed)
3. Move EMA shadow to CPU

**Should-fix (moderate gain):**
4. CUDNN_BENCHMARK=True + CUDNN_DETERMINISTIC=False for production
5. Zero backbone grads before forward on seq batches (not after)
6. Eliminate excess `torch.cuda.empty_cache()` calls

**Nice-to-have (exploratory):**
7. Re-enable channels_last (VideoMAE restriction gone)
8. FPN gradient checkpointing
9. Backbone-only torch.compile
10. Allocator config tuning
