---
title: POPW Training Pipeline
type: architecture
status: active
tags: [popw, training, multi-task-learning, pose-estimation, object-detection, resnet, fpn, fp16, gradient-accumulation, kendall-loss, ikea]
created: 2026-04-13
updated: 2026-04-13
summary: "Complete training pipeline for improved4/improved4_film on 685K IKEA assembly frames. RTX 3060 12GB optimized: FP16 mixed precision, gradient accumulation (effective batch 60), Kendall uncertainty weighting, cosine annealing with warmup, early stopping. 3-4 days training time, NaN skip guard, JSONL logging."
wikilinks:
  - [[architecture/worker-net-improved4]]
  - [[concepts/kendall-loss]]
  - [[concepts/multi-task-learning]]
  - [[projects/popw-research]]
confidence: high
source: research
project: popw
---

# POPW Training Pipeline

## TL;DR

Full training pipeline for WorkerNet improved4/improved4_film on 685K IKEA assembly frames. Optimized for RTX 3060 12GB with FP16 mixed precision, gradient accumulation (batch 15 × accum 4 = effective 60), Kendall uncertainty weighting, and cosine annealing. 150 epochs = 3-4 days. Comprehensive logging with per-task losses, Kendall weights, and NaN skip counter.

---

## 1. Training Loop Overview

```
Epoch loop:
  ├── Forward pass (model + PoseFiLMModule if film=True)
  ├── MultiTaskLoss: L_det + L_pose + L_act, Kendall-weighted
  ├── scaler.scale(loss_total) + backward + scaler.update
  ├── Gradient accumulation (every 4 steps)
  ├── Cosine LR scheduler step
  └── Checkpoint (best + periodic)

Validation (every N epochs):
  ├── Pre-validation memory flush
  ├── evaluate_all() → {act_F1, pose_PCK, det_mAP}
  └── Combined metric = 0.40*F1 + 0.35*PCK + 0.25*mAP (normalized)
```

### 1.1 Combined Validation Metric

```python
_W_F1  = 0.40
_W_PCK = 0.35
_W_MAP = 0.25

# If PCK is NaN (no visible keypoints), fall back:
_W_F1_NO_PCK  = _W_F1  / (_W_F1 + _W_MAP)
_W_MAP_NO_PCK = _W_MAP / (_W_F1 + _W_MAP)
```

This weighting was chosen to prioritize activity accuracy (40%) while maintaining strong pose (35%) and detection (25%). When PCK is unavailable, the weight redistributes to F1 and mAP.

---

## 2. Hardware Configuration

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Batch size | 15 | RTX 3060 max with FP16 |
| Gradient accumulation | 4 | Effective batch = 60 |
| Mixed precision | FP16 | ~2x memory savings |
| Gradient clipping | max_norm=1.0 | Training stability |
| CUDA_alloc conf | expandable_segments=True | Reduce fragmentation |
| cudnn.benchmark | True | Faster convolutions |
| allow_tf32 | True | Faster matmul on Ampere+ |

### 2.1 RTX 3060 Memory Budget

| Component | Memory |
|-----------|--------|
| Model (40M params, FP16) | ~320MB |
| Gradients (FP32) | ~640MB |
| Optimizer states (FP32, Adam) | ~640MB |
| Activations (batch 15, FP16) | ~4GB |
| Feature pyramids (P3-P7) | ~2GB |
| **Total** | **~7.6GB** (fits in 12GB with margin) |

---

## 3. Optimizer & Scheduler

### 3.1 Optimizer: SGD with Momentum

```python
optimizer = AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
# Note: code uses AdamW despite comment saying "SGD with momentum"
# Verified in train.py line ~79: from torch.optim import AdamW
```

### 3.2 Learning Rate Schedule

```python
warmup_scheduler = LinearLR(
    start_factor=0.1, end_factor=1.0, total_iters=5  # epochs
)
cosine_scheduler = CosineAnnealingLR(
    T_max=150 - 5, eta_min=1e-6
)
scheduler = SequentialLR(
    optimizer,
    [warmup_scheduler, cosine_scheduler],
    milestones=[5]  # switch after warmup
)
```

### 3.3 Early Stopping

```python
patience = 15  # epochs without improvement
best_metric = 0.0
early_stop_counter = 0
```

---

## 4. Data Loading

### 4.1 Dataset Statistics

| Stat | Value |
|------|-------|
| Total frames | 685,516 |
| Assembly videos | 254 |
| Frame-level labels | 100% (all 3 tasks) |

### 4.2 Sampler: Class-Balanced for Activity

Activity classes have extreme imbalance (2545:1). The sampler uses class-balanced sampling to ensure rare classes appear frequently enough:

```python
class_counts = [count_class_i() for i in range(33)]
# Beta = 0.9999 for class-balanced weighting
effective_samples = (1.0 - 0.9999^count) / (1.0 - 0.9999)
sampler = BalancedSampler(dataset, class_counts, beta=0.9999)
```

### 4.3 DataLoader Configuration

```python
DataLoader(
    dataset,
    batch_size=15,
    sampler=sampler,  # for train only
    num_workers=4,    # multiprocessing
    collate_fn=collate_fn,
    pin_memory=True,
    drop_last=True,    # train only
    persistent_workers=True,  # train only (avoid worker restart overhead)
)
)
```

### 4.4 Validation Loader (Memory-Optimized)

```python
# Reduced for OOM prevention at validation time
VAL_BATCH_SIZE = 4
VAL_NUM_WORKERS = 2
prefetch_factor = 1  # halve prefetch RAM vs training loader
```

---

## 5. Training Stability Fixes

### 5.1 NaN/Inf Skip Guard

Corrupt JPEG frames produce NaN losses. The training loop skips these frames:

```python
if torch.isnan(loss_total) or torch.isinf(loss_total):
    nan_skip_counter += 1
    continue  # skip backward, don't update weights
```

The counter is logged to `metrics.jsonl` per epoch.

### 5.2 Pre-Validation Memory Flush

Before validation runs (at memory peak), the pipeline clears:

```python
def _flush_before_val():
    # 1. Clear COCO cache
    del coco_cache
    # 2. Zero gradients
    optimizer.zero_grad(set_to_none=True)
    # 3. Close SQLite connections
    for conn in open_connections:
        conn.close()
    # 4. Force garbage collection
    gc.collect()
    gc.collect()  # double collect
    # 5. Empty CUDA cache
    torch.cuda.empty_cache()
```

This prevents `VM_FAULT_OOM` errors during validation.

### 5.3 Multiprocessing Strategy

```python
# Set at module top-level (before any other imports in main thread)
try:
    multiprocessing.set_start_method('spawn', force=True)
except RuntimeError:
    pass  # already set

# Sharing strategy
torch.multiprocessing.set_sharing_strategy('file_system')
```

`spawn` is required on Linux for CUDA safety. `persistent_workers=False` for val loader to avoid keeping old workers alive.

---

## 6. Checkpointing

### 6.1 Checkpoint Contents

```python
{
    'epoch': 143,
    'model_state': model.state_dict(),
    'optimizer_state': optimizer.state_dict(),
    'scheduler_state': scheduler.state_dict(),
    'scaler_state': scaler.state_dict(),
    'log_vars': {
        'log_var_det': -0.5,
        'log_var_pose': -1.2,
        'log_var_act': 0.3,
    },
    'nan_skip_count': 47,
    'best_metric': 0.8234,
}
```

### 6.2 Resume Behavior

```python
# On crash resume, log_var_pose must NOT reset to 0.0
# Correct behavior: fill_(-1.0) to preserve asymmetric Kendall init
if resume:
    checkpoint = torch.load(path)
    log_vars = checkpoint['log_vars']
    # log_var_pose starts from -1.0 (from checkpoint), not 0.0
```

---

## 7. Logging

### 7.1 metrics.jsonl Format

```json
{
  "epoch": 1,
  "timestamp": "2026-03-14T08:23:41",
  "train": {
    "loss_total": 2.341,
    "loss_det": 0.892,
    "loss_pose": 0.445,
    "loss_act": 1.004,
    "nan_skips": 0
  },
  "val": {
    "act_macro_f1": 0.234,
    "pose_pck_01": 0.892,
    "det_map_05": 0.412,
    "combined_metric": 0.523
  },
  "kendall_weights": {
    "log_var_det": -0.32,
    "log_var_pose": -1.14,
    "log_var_act": 0.28
  },
  "lr": 0.00098
}
```

### 7.2 Kendall Weights Interpretation

| log_var value | Interpretation |
|---------------|----------------|
| negative (< 0) | Task is HARD — model allocates more weight |
| positive (> 0) | Task is EASY — model allocates less weight |
| magnitude | How certain the model is about task difficulty |

Over training, `log_var_pose` typically goes very negative (pose is hard to learn well), while `log_var_det` may stabilize near zero.

---

## 8. Evaluation Script

```bash
# Full evaluation with all metrics
python improved4__evaluate.py.txt \
    --checkpoint runs/ikea_multitask_improved4_film/checkpoints/best.pth \
    --split test \
    --save_dir output/eval_improved4_film

# Segment-level temporal metrics
python improved4__temporal_metrics.py.txt \
    --checkpoint runs/.../best.pth \
    --split test
```

---

## 9. Known Issues & Fixes Timeline

| Date | Issue | Fix |
|------|-------|-----|
| 03-10 | ActivityHead dimension mismatch | Always fuse C5+P4; dedicated C5-only constructor |
| 03-10 | soft-argmax edge-pixel bias | `(IMG_W-1)/(hm_w-1)` instead of `IMG_W/hm_w` |
| 03-10 | AnchorGenerator loop order | ratios-outer / scales-inner |
| 03-13a | BrokenPipeError | `set_start_method('spawn')` at module top |
| 03-13b | Bus error / worker crash | spawn + `persistent_workers=False` |
| 03-14 | OOM at validation | Pre-validation memory flush |
| 03-14b | IndentationError line 415 | Extra space before `best_metric` |
| 03-15 | Validation OOM (VM_FAULT_OOM) | VAL_BATCH_SIZE=4, VAL_NUM_WORKERS=2 |
| 03-16 | log_var_pose reset on resume | `fill_(-1.0)` instead of `fill_(0.0)` |

---

## Related Articles

- [[architecture/worker-net-improved4]] — Full model architecture
- [[concepts/kendall-loss]] — Kendall uncertainty weighting theory
- [[projects/popw-research]] — Research context and dataset details
