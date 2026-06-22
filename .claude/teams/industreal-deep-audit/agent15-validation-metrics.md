# Agent 15: Validation Loop and Evaluation Metrics

## 1. Validation Loop Structure

### Frequency
- **Per-epoch validation**: `VAL_EVERY = 1` (config.py:341) -- validates every epoch.
- **Intra-epoch (step-based) validation**: `VAL_EVERY_N_STEPS = 1000` (config.py:342). Runs a gated ~200-batch eval every 1000 global steps. This uses a **separate, pre-built DataLoader** (`_step_val_loader`) with `batch_size=1` to avoid pin_memory/re-prefetch issues inside the training loop.
- **Ordering fix** (train.py:4154-4155): TRAIN_MAX_STEPS break check was moved to AFTER the validation block; previously it skipped val entirely on the last epoch/step.

### Data Subset
- **Full dataset**: `EVAL_MAX_BATCHES = -1` means the entire validation set is processed (config.py:343).
- **Gated eval**: `GATE_EVAL_MAX_BATCHES = 200` batches is used for non-full-det-mAP epochs and step-based intra-epoch eval. Controlled by `DET_METRICS_EVERY_N` -- if set, every `N`th epoch gets full mAP; intermediate epochs use gated eval.
- **OOM retry**: If validation fails (OOM, ENOMEM, or non-OOM exception), `max_batches` is halved and the loader is rebuilt (train.py:3870-3913). Up to 3 retries.
- **DET_GT_FRAME_FRACTION sampler**: Used for validation as well (train.py:273) so val batches contain GT frames. Without this, only ~6.6% of val frames have boxes, making mAP always 0.

### Metrics Computation
Validation calls `evaluate_all()` (evaluate.py:2849) which runs the model in eval mode with `torch.no_grad()`, collects predictions across batches, and computes metrics in 4+ categories.

---

## 2. Detection Metrics (mAP)

### IoU Thresholds
- **mAP@0.5**: Single IoU threshold of 0.5. The primary training metric.
- **mAP@[0.5:0.95]**: 10 evenly spaced thresholds `np.arange(0.5, 1.0, 0.05)`. Computed via `compute_ap_multi_thresh` (evaluate.py:1400) which vectorizes the computation to be ~9x faster than calling `compute_ap_per_class` 11 times. The IoU matrix is computed once per (class, frame) and replayed across thresholds.

### Area Ranges
- No separate area-range grouping (small/medium/large). Standard COCO-style mAP without area stratification.
- Boxes are clipped to `[0, IMG_WIDTH] x [0, IMG_HEIGHT]` = `[0, 1280] x [0, 720]`.

### Max Detections
- `DET_EVAL_MAX_PER_IMAGE = 300` (config.py:399). If raw predictions exceed 300, top-300 by score are kept.
- `DET_EVAL_SCORE_THRESH = 0.001` (config.py:398). Very low threshold tuned through 6+ iterations (was 0.5, 0.0, 0.05, 0.03, 0.1, 0.02, finally 0.001).
- `DET_EVAL_NMS_IOU_THRESH = 0.5` for NMS.

### Precision/Recall/mAP
- `compute_ap_multi_thresh` (evaluate.py:1400): Per-class, per-threshold AP using COCO all-point interpolation (`_coco_ap`, evaluate.py:1313). The PR curve uses 101-point interpolation (concatenates [0] and [1.0] endpoints, then runs max-envelope backward pass). This matches YOLO/COCO standard.
- **Per-class-present mAP** (`det_mAP50_pc`, `det_mAP_50_95_pc`): Averages only over classes with GT > 0 in this eval split. Added 2026-06-04 to prevent dilution by 20 empty classes when val batches have sparse coverage.
- **Full-video mAP** (`compute_det_metrics_all_frames`): Includes frames with no GT and no predictions. Uses the corrected protocol (Bug #2 fix: removed spurious "correct rejection" TP injection that inflated mAP > 1.0).
- **Box decoding**: `decode_boxes` (evaluate.py:1218) applies exp(dw/dh) with clip to [-4, 4] for numerical stability.
- **IoU computation**: `compute_iou_matrix` (evaluate.py:1207) with 1e-6 epsilon to prevent division by zero.

### 24 Detection Classes
`NUM_DET_CLASSES = 24` (background + 22 assembly states + error_state).

---

## 3. Detection Pipeline

### Detection Pipeline (evaluate_all)
1. Get `cls_preds` [B, N, 24] and `reg_preds` [B, N, 4] from model.
2. Sigmoid -> max score per anchor -> threshold at 0.001.
3. Top-300 by score if >300.
4. Per-class NMS at IoU 0.5 for remaining predictions.
5. Collect `dp_boxes`, `dp_scores`, `dp_labels` across batches.
6. At epoch-end, compute extended detection metrics.

### PROBE (self-diagnostics)
`probe_detection_batch` (evaluate.py:93) runs silently on first 5 eval batches to detect detection collapse (flat scores, zero predictions, all-negative logits). Self-throttling by `_state["n"]` counter.

---

## 4. Pose Metrics (Head Pose)

### 9-DoF Structure
```
0-2: forward_vector (forward_x, forward_y, forward_z)  -- unit vectors
3-5: position (pos_x, pos_y, pos_z)                     -- raw values (unit unconfirmed)
6-8: up_vector (up_x, up_y, up_z)                       -- unit vectors
```

### Computation (`compute_head_pose_metrics`, evaluate.py:1632)
- **Abs diff MAE**: Mean absolute error per DoF, overall MAE, overall std.
- **Angular MAE** for directional vectors (forward + up): Normalizes to unit vectors (1e-8 epsilon to prevent div-by-zero), computes `arccos(dot)` in degrees. Only reported when BOTH pred AND gt have mean norm > 0.5 (guards against early-training non-unit outputs).
- **Fallback**: When vectors are not unit-norm (early training), emits `head_pose_angular_MAE_deg = nan` and raw MAE in separate `forward_raw_MAE` / `up_raw_MAE` keys.
- **Position MAE**: L2 norm of position diff, multiplied by 1000 for mm. **CAUTION**: comment (evaluate.py:1729-1734) explicitly warns that pose.csv units are UNVERIFIED -- possibly decimetres, 0.1m-normalized or dataset-specific. `position_MAE_mm` is unreliable.
- **Empty guard**: Returns all NaN if `pred.shape[0] == 0`.
- **Angular function**: Uses both forward and up errors averaged; `head_pose_status` key indicates `unit_vectors_ok` vs `non_unit_vectors`.

---

## 5. Activity Metrics

### Computation (`compute_activity_metrics`, evaluate.py:885)
- **Frame accuracy** (all classes): Standard `accuracy_score`.
- **Frame accuracy** (no NA, class 0 excluded): Accuracy on non-background frames.
- **Macro-F1**: Uses `f1_score(average='macro', zero_division=0)` excluding class 0 (NA) via `present_labels` filter. This aligns with MViTv2 eval protocol.
- **Weighted-F1**: Weighted average F1 (accounts for class imbalance).
- **Macro-Recall**: Macro recall excluding NA class.
- **Mean per-class accuracy**: From confusion matrix diagonal / row sums (rows clipped to min=1 to prevent div-by-zero).
- **Top-5 accuracy**: From raw logits via `argsort`. Falls back to 0.0 if logits unavailable or shape mismatch.
- **Clip-level accuracy**: `_compute_clip_level_accuracy` -- majority vote per clip, excludes NA. Falls back to frame accuracy if clip_ids not provided.
- **Segment-level accuracy** (GAP-B, evaluate.py:850): MViTv2-comparable protocol -- 16 uniformly sampled frames per segment, majority vote. Only runs when `TRAIN_ACT=True` and `DET_GT_FRAME_FRACTION < 0.9`. Protected by SIGALRM 600s timeout to prevent CUDA kernel hang. Wrapped in try/except.
- **Empty array guard** (evaluate.py:914): Returns all-0 metrics if all_gt/all_pred is empty.
- **Length mismatch guard** (evaluate.py:3362): If `act_clip_ids` length != `all_act_gt` length, truncates to minimum. This indicates a masking bug in `act_valid` filtering.

### Collapse Detection
- If <5 predicted classes seen, logs `[EVAL COLLAPSE]` warning with top-1 class and frequency (evaluate.py:3349).

---

## 6. PSR Metrics

### Computation (`compute_psr_metrics`, evaluate.py:2302)
PSR is multi-label: 11 assembly components, each binary (done=1, not done=0).

- **Per-component F1**: TP/(TP+FP) and TP/(TP+FN) per component. NaN if all masked, 0.0 if TP+FP==0 or TP+FN==0.
- **Overall F1**: `np.nanmean` over valid components.
- **F1@T**: Symmetric bi-directional greedy matching of state-change edges within tolerance (default +/-3 frames, also computed for +/-5). Uses **GPU-fused** `_compute_psr_f1_at_t_fused_cuda` (evaluate.py:2120) for both tolerances in single pass when CUDA available; falls back to numpy vectorized version. The GPU version builds adjacency matrices on GPU, transfers small matrices back to CPU for matching.
- **Edit Score**: Normalized Damerau-Levenshtein OSA distance on binary sequences per component. Detects adjacent transpositions that Hamming distance misses.
- **POS (Percentage of Ordering Success)**: Runs-based ordering metric, vectorized across components.
- **Both tolerances**: Always computes both t=3 and t=5 metrics.
- **-1 labels masked out**: GT of -1 (unknown/error) is zeroed and excluded from metrics via `valid_mask`.

### Transition Decoder (evaluate.py:3516-3552)
When `USE_PSR_TRANSITION = True`, applies `MonotonicDecoder` (fill-forward + state order) before scoring. Groups per-recording and decodes via `decode_and_score_psr`.

### Collapse Detection
If <3 unique binary patterns across all frames, logs `[EVAL COLLAPSE]` for PSR head.

---

## 7. Combined Metric Weighting

### IMPORTANT DISCREPANCY: Two different combined score formulas exist:

**metrics.py:189-198 (used by `compute_metrics` -- single-batch dispatcher)**
```
combined = mAP50 * 0.25 + F1_action * 0.25 + max(0.0, 1.0 - MAE/10.0) * 0.25 + F1_psr * 0.25
```
- Equal 0.25 weights (uniform)
- MAE normalized linearly: `1.0 - MAE/10.0`, clamped to [0, 1]
- This is NOT used in training -- it is the single-batch compute_metrics path in metrics.py

**train.py:135-138, 2021-2030 (_compute_combined_metric -- used for model selection)**
```
_W_DET  = 0.30
_W_ACT  = 0.35
_W_POSE = 0.15
_W_PSR  = 0.20

combined = _W_DET * mAP50 + _W_ACT * macro_f1_act + _W_POSE * (1.0/(1.0+MAE)) + _W_PSR * macro_f1_psr
```
- Unequal weights: act (0.35) > det (0.30) > psr (0.20) > pose (0.15)
- MAE normalized via inverse sigmoid: `1.0 / (1.0 + MAE)` with MAE clamped to min 1e-6
- This is the actual model selection metric

**Potential issue**: metrics.py uniform 0.25 weight formula uses a linear MAE normalization, while train.py's `_compute_combined_metric` uses `1/(1+MAE)`. The difference means metrics.py and train.py would disagree on combined scores for identical data. However, metrics.py's compute_metrics is NOT called during training -- the validation loop uses evaluate_all() which calls the individual metric functions and consolidates results for train.py's `_compute_combined_metric`.

---

## 8. Empty Prediction Handling

### No GT boxes
- evaluate.py:3632-3641: If `gt_box_total == 0`, detection metrics return all-0 (not NaN) with `det_mAP50=0.0, det_mAP_50_95=0.0, det_mAP50_all_frames=0.0`. Logs warning.
- Activity: Returns all-0 (not NaN) metrics when GT is empty (evaluate.py:914).
- Head pose: Returns all NaN when no predictions (evaluate.py:1654).

### All boxes suppressed
- Empty per-image predictions are appended as `np.zeros((0, 4))` for boxes, `np.zeros(0)` for scores/labels (evaluate.py:3181-3182).
- These empty arrays propagate through `compute_ap_multi_thresh` correctly (total_gt check handles zero-GT classes).

### No predictions in any batch
- `empty_guard_failed` (evaluate.py:3258-3293): If ALL batches have empty act_preds, returns safe fallback metrics (non-NaN, zero or 1e-4). Prevents infinite val loop.
- Partial empty (some batches empty): Logs warning, proceeds with remaining data.

### Score threshold edge cases
- `DET_EVAL_SCORE_THRESH = 0.001` is very low. With bias=-3.4 init (sigmoid ~0.03), most early predictions pass through.
- Flat scores (std < 0.01) trigger `[EVAL COLLAPSE]` warning (evaluate.py:3675).
- Excessive predictions (>100x GT count) also trigger collapse warning (evaluate.py:3681).

### NaN/Inf metrics
- All NaN/Inf float metrics are logged with `[EVAL NaN/Inf]` warning but PRESERVED (evaluate.py:3762-3768). Not silently converted.
- train.py NaN guard (train.py:4005): If `_task_nan` (det_mAP50, act_macro_f1, psr_macro_f1, head_pose_MAE), skips checkpoint saving and patience update.
- Non-finite components clamped to neutral values (0.0 for F1/mAP, 360.0 for MAE) for combined metric computation (train.py:4034).

---

## 9. Validation Batch Size and OOM Risk

### Current setting
- **config.py**: `VAL_BATCH_SIZE = 4` (RTX 3060 12GB). Was 16, then reduced due to FP32 OOM.
- **benchmark checkpoints**: `VAL_BATCH_SIZE = 16` (these runs have more headroom).
- **Step-based val**: Uses `batch_size=1` via `_build_loader(val_ds, 'val', 1, ...)` (train.py:861).

### OOM Risk Assessment
- Comment (config.py:328): "4x is safe with no_grad" compared to train batch=2.
- Evaluate step-based val with batch_size=1 is very safe.
- OOM handling: Halves batch size on retry, sets workers to 0, reduces max_batches. Up to 3 retries.
- `_flush_before_val` (train.py:402): Calls `psutil` RSS tracking, `gc.collect()`, `torch.cuda.empty_cache()`.
- `CUDA_MEMORY_FRACTION = 0.95`: Allows near-full VRAM.
- GPU memory logging every 10 batches in eval (evaluate.py:2973).
- CPU RAM watchdog warns if < 2GB available (train.py:1806).
- Per-image GPU memory cleanup in eval loop (evaluate.py:3224-3228): deletes intermediate tensors, calls `empty_cache`.

### Same GPU vs Separate
- Validation runs on the **same GPU** as training. No `model.to('cpu')` swap. This is the pattern for RTX 3060 single-GPU setup.
- `torch.cuda.synchronize()` before val to ensure all training ops complete.
- IN_EVALUATION_PHASE flag prevents DDP signal handlers from killing ranks during eval.

---

## 10. Best Model Selection

### Metric
- `combined = 0.30*mAP50 + 0.35*act_macro_f1 + 0.15*(1/(1+MAE)) + 0.20*psr_f1_at_t`
- Uses `psr_f1_at_t` (symmetric +/-3 frame F1) NOT `psr_macro_f1` (= `psr_overall_f1`, which was all-ones predictions). Fix applied 2026-05-31.

### Checkpoint Logic
- If `combined > best_metric`, saves best checkpoint (both model and EMA weights).
- `PATIENCE = 10` epochs.
- NaN guard: If core task metrics contain NaN/Inf, skips checkpoint saving and patience update but does NOT burn patience.
- Stage 3: Also runs raw-model validation comparison vs EMA via `_compare_raw_vs_ema` (train.py:2593).

### Efficiency Metrics
- Skipped most epochs (`LOG_EFFICIENCY_EVERY = 10`, `SKIP_EFFICIENCY_METRICS = True`).
- GFLOPs, FPS, Params computed on-demand only.

---

## Key Issues Found

1. **Weight discrepancy (metrics.py vs train.py)**: metrics.py:189 uses uniform 0.25 weights with `max(0, 1-MAE/10)` normalization, while train.py:135 uses (0.30, 0.35, 0.15, 0.20) with `1/(1+MAE)` normalization. The metrics.py function is NOT called in training (it's a standalone dispatcher), but the discrepancy is confusing and risks incorrect ad-hoc usage.

2. **position_MAE_mm unreliable** (evaluate.py:1729-1734): Self-documented as unverified -- unit multiplier (x1000) may produce meaningless values. TODO: confirm from IndustReal documentation.

3. **Act_clip_ids length mismatch** (evaluate.py:3362): The truncation guard masks a race condition where `act_valid` filtering produces inconsistent counts between act_preds/act_labels and act_clip_ids. The 2026-06-15 fix added per-sample filtering, but the guard still fires.

4. **Activity segment eval** uses a full pass through the dataset (not batched), which is slow. Protected by 600s SIGALRM timeout.

5. **Detection evaluation skipped** when `DET_METRICS_EVERY_N` is active: Returns NaN for det metrics, which triggers the NaN guard in train.py. This is intentional but means the combined metric on non-full-det epochs uses NaN components, requiring the neutral-value clamping logic.
