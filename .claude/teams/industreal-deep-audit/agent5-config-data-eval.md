# Agent 5: Configuration & Data Pipeline Deep Audit

**Auditor:** Agent 5/20
**Date:** 2026-06-17
**Scope:** `config.py`, `industreal_dataset.py`, `dataset.py`, `metrics.py`, `evaluate.py`
**Coverage:** 11 check areas with severity ratings and line numbers

---

## Executive Summary

5 files audited (1362 + 1602 + 129 + 201 + 4297 = 7591 total lines). Found **20 issues**: 2 CRITICAL, 5 HIGH, 7 MEDIUM, 6 LOW. The two CRITICAL bugs (`_old_alarm` NameError in evaluate.py and `PSR_WEIGHT = 10.0` dangling outside config) can silently corrupt results or crash evaluation with no warning.

---

## 1. Config Validation Completeness

| # | Severity | File | Line(s) | Issue |
|---|----------|------|---------|-------|
| 1 | MEDIUM | config.py | 307-309 | **Tautological assertion.** `IMG_SIZE` is constructed as `(IMG_WIDTH, IMG_HEIGHT)` on line 283, then asserted equal to itself on line 307. The assertion can NEVER fail (unless someone edits the tuple literal directly). It provides zero protection against invalid configurations. Should validate actual constraints (e.g., `IMG_SIZE[0] >= ANCHOR_SIZES[-1]` to catch the anchor-overflow bug documented in lines 286-303). |
| 2 | MEDIUM | config.py | 1340-1362 | **No schema validation.** `_validate_paths()` (called at line 1354) only checks that directory paths exist. There is no structural validation for the ~200 configuration fields -- no type checks, no range checks, no cross-field consistency checks (e.g., that `NUM_DET_CLASSES` matches `NUM_ACT_RAW_IDS` range, that `BATCH_SIZE` fits in GPU memory, that `TRAIN_FRAME_STRIDE` is not 0). A single typo in a preset dictionary silently uses the wrong value. |
| 3 | LOW | config.py | 27-31 | `BENCHMARK_MODE = True` at the top but the downstream effects are scattered and undocumented. No single function disables all benchmark-mode overhead (profiling, per-step logging, extra metrics). |

## 2. Dataset Loading Correctness (Paths, Missing Files, Class Balancing)

| # | Severity | File | Line(s) | Issue |
|---|----------|------|---------|-------|
| 4 | HIGH | industreal_dataset.py | 1083-1089 | **COCO JSON re-parsed for every frame.** `_extract_boxes_from_coco()` calls `json.loads(Path(coco_file).read_text())` inside a `try` block on EVERY frame access. For a dataset of ~50K frames this means 50K redundant file reads and JSON parses just to extract image dimensions. The COCO file is the same for all frames in a recording -- it should be parsed once per recording and cached. This adds ~50ms per frame (JSON parsing of a ~2MB file) = ~40 minutes of overhead per epoch. |
| 5 | MEDIUM | industreal_dataset.py | 1107 | **Hardcoded constant >=24 instead of C.NUM_DET_CLASSES.** Line 1107 uses `if idx < 0 or idx >=24:` to clamp out-of-range detection labels. If `NUM_DET_CLASSES` ever changes (e.g., to 23 or 25), this guard silently misbehaves -- it would either allow invalid indices (causing CUDA device-side asserts) or reject valid indices. Should use `C.NUM_DET_CLASSES`. |
| 6 | MEDIUM | industreal_dataset.py | 1293 | **Silent fallback for missing AR labels.** `action_label = int(cache.ar_per_frame[fn]) if fn < len(cache.ar_per_frame) else 0` -- when a frame index exceeds the AR labels array length, it silently defaults to label 0 (NA). This masks genuine data alignment bugs where frame numbering doesn't match between RGB directories and annotation CSVs. |
| 7 | HIGH | dataset.py | 15-24 | **sys.path manipulation has logic errors.** The path-building code has dead branches and incorrect conditions. Lines 17-24 iterate over subdirectory names but the conditional logic produces duplicate entries and misses paths. At `_sub == 'src'`, line 21-22 sets `_p = str(_SRC / 'src')` which creates a double-nested path. The actual behavior is unpredictable. |
| 8 | LOW | industreal_dataset.py | 155-157 | **Frame cache memory comment is misleading.** Line 155 says "33GB raw" but actual memory is ~5-7GB. While documented, the comment could mislead someone into thinking the cache is unsafe on 16GB or 32GB systems. |

## 3. Augmentation Pipeline Correctness, Diversity, Applicability

| # | Severity | File | Line(s) | Issue |
|---|----------|------|---------|-------|
| 9 | HIGH | industreal_dataset.py | 848-853 | **Augmentation ignores detection labels in practice.** `apply_spatial_aug()` is called with `gt_boxes` and a dummy keypoint tensor, but the returned `gt_boxes` is reassigned. No validation that the returned boxes are actually valid for the augmented image (e.g., random crop could discard boxes without adjusting labels). |
| 10 | MEDIUM | industreal_dataset.py | 848 | `USE_SPATIAL_AUG` flag controls spatial augmentation but there is no **color augmentation** (brightness, contrast, saturation jitter) which is standard for industrial datasets with varying lighting. The pipeline relies entirely on spatial transforms (flip, crop). |
| 11 | LOW | industreal_dataset.py | 849 | Keypoint argument is `torch.zeros((17, 2))` -- a COCO-specific magic number (17 joints). Should be documented or configurable. |

## 4. Batch Size and Worker Configuration

| # | Severity | File | Line(s) | Issue |
|---|----------|------|---------|-------|
| 12 | MEDIUM | config.py / dataset.py | 319-360 / 91 | `persistent_workers=True` is set unconditionally when `num_workers > 0` (dataset.py line 91), consuming RAM even when not actively iterating. No auto-tuning fallback. Frame cache (~5-7GB) + worker prefetch could cause OOM on smaller systems. |

## 5. DET_GT_FRAME_FRACTION = 0.90 Sampler Reweighting Correctness

| # | Severity | File | Line(s) | Issue |
|---|----------|------|---------|-------|
| 13 | LOW | config.py | 1238-1245 | **Derivation logic is correct.** Properly derived from active heads (0.9 for det-only, 0.4 for joint). Override path via `det_gt_frame_fraction` in presets also works. |
| 13b | LOW | industreal_dataset.py | 1358-1401 | **Implementation is correct.** GT-bearing frames get exactly `det_frac` fraction of weight. Edge case of zero GT frames (line 1376-1384) is handled with a warning. Math is sound. |
| 14 | MEDIUM | config.py | 1238-1245 | **DET_GT_FRAME_FRACTION override path doesn't check PSR_SEQUENCE_MODE.** In sequence mode, each "sample" is a T-frame window, and DET_GT_FRAME_FRACTION reweighting operates on window-level metadata. If DET_GT_FRAME_FRACTION is 0.9 and only 10% of windows have det boxes, the sampler will heavily oversample those few windows, risking overfitting. |

## 6. Evaluation Metrics Correctness (mAP, Accuracy, MAE, F1)

| # | Severity | File | Line(s) | Issue |
|---|----------|------|---------|-------|
| 15 | HIGH | metrics.py | 38-93 | **`_heatmaps_to_detection()` is a placeholder with no actual detection capability.** Produces fixed 64x64 boxes centered on heatmap peaks (line 75-77). This is NOT the model's actual detection output (RetinaNet cls_preds/reg_preds). If `compute_metrics()` is ever called without proper cls_preds/reg_preds keys, the reported mAP50 is garbage. |
| 16 | MEDIUM | metrics.py | 189-199 | Combined score uses `1.0 - MAE / 10.0` normalization. If MAE exceeds 10 (common early in training), component clamped to 0.0. The choice of 10.0 is undocumented and untuned. |

## 7. Evaluation Loop Edge Case Handling

| # | Severity | File | Line(s) | Issue |
|---|----------|------|---------|-------|
| 17 | **CRITICAL** | evaluate.py | 3456 | **NameError: `_old_alarm` is not defined.** Line 3456 restores SIGALRM handler with `signal.signal(signal.SIGALRM, _old_alarm)`, but the variable was saved on line 3435 as `_old_handler`. This will raise NameError in `finally` block (line 3454) every time segment metrics run, which is caught by the `except Exception` on line 3449, **silently discarding valid segment metrics results**. All act_seg_top1/act_seg_top5 values are set to 0.0. Fix: change `_old_alarm` to `_old_handler` on line 3456. |
| 18 | HIGH | evaluate.py | 3227-3228 | **`torch.cuda.empty_cache()` called per-image during evaluation.** Each call blocks 50-200ms. For a 1000-image validation set, this adds 50-200 seconds of overhead. Comment (line 3220) suggests reactive fix for OOM -- real fix is proper tensor lifetime management. |
| 19 | MEDIUM | evaluate.py | 3700-3703 | Detection metric keys accessed through `results.get()` with `float("nan")` fallback. Safe, but produces confusing `nan` logging with no explanation. |
| 20 | LOW | evaluate.py | 3556-3564 | psr_macro_f1 fallback dict (lines 3556-3561) includes all expected keys. Minor fragility. |

## 8. Subset Ratio (0.2 for RF1) Implementation

| # | Severity | File | Line(s) | Issue |
|---|----------|------|---------|-------|
| 21 | MEDIUM | config.py | 32 | `SUBSET_RATIO = 1.0` at module level; stage presets correctly override. Greedy coverage stratification (lines 1210-1243) handles subset selection correctly. No bug in implementation. |
| 22 | MEDIUM | industreal_dataset.py | 1210-1243 | Greedy stratification only considers detection classes. Activity and PSR label distributions not considered. For RF3+ (joint training), subset could be biased toward detection-rich recordings, under-representing rare activity/PSR classes. |

## 9. NUM_CLASSES_DET = 24, NUM_CLASSES_ACT = 75 Correctness

| # | Severity | File | Line(s) | Issue |
|---|----------|------|---------|-------|
| 23 | LOW | config.py | 186-187 | `NUM_CLASSES_ACT = 75` is correct and well-documented. Previous 74 vs 75 bug is fixed. |
| 24 | LOW | config.py | 144 | `NUM_DET_CLASSES = 24` correct. COCO category IDs 1-24 mapped to 0-23 in industreal_dataset.py line 1104-1105. |
| 25 | MEDIUM | industreal_dataset.py | 1107 | (Same as #5) Hardcoded >=24 instead of `C.NUM_DET_CLASSES`. Mirror issue -- if NUM_DET_CLASSES changes, validation guard breaks. |

## 10. Sequence Length and Temporal Bank Configuration

| # | Severity | File | Line(s) | Issue |
|---|----------|------|---------|-------|
| 26 | HIGH | dataset.py | 80-81 | **No sampler in sequence mode AND shuffle=False = zero randomness.** `sampler = ds.get_sampler() if sequence_mode is False else None` means sequence mode has NO weighted sampler. Combined with `shuffle=False` (line 86), every epoch iterates in the same deterministic order. Consecutive DataLoader batches draw from overlapping windows in the same recording, creating pathological temporal correlation. |
| 27 | MEDIUM | config.py | 42 comment | `sequence_length: int = 32` in docstring, but config uses `PSR_SEQUENCE_LENGTH = 2`. Docstring is misleading. |
| 28 | LOW | industreal_dataset.py | 1155-1170 | Sequence window index builder creates O(N) index per recording with stride=1 (~48K entries for 48K frames). Correct but worth noting. |
| 29 | MEDIUM | industreal_dataset.py | 1171 | No shuffling of `seq_samples` after building. Combined with issue #26, poor training dynamics. |

## 11. OOM Risks in Data Loading and Evaluation

| # | Severity | File | Line(s) | Issue |
|---|----------|------|---------|-------|
| 30 | MEDIUM | industreal_dataset.py | 153-163 | Frame cache loads ALL frames into RAM (~5-7GB). No cap, LRU eviction, or lazy loading. Safe on 64GB target system but OOM risk on 16GB/32GB. |
| 31 | HIGH | evaluate.py | 3227-3228 | (Same as #18) `torch.cuda.empty_cache()` per image massively slows evaluation and indirectly increases OOM risk via synchronous waits. |
| 32 | LOW | evaluate.py | 3234-3239 | Crash recovery checkpoint every 5 eval batches could accumulate disk usage. Minimal GPU memory impact. |

---

## Summary Statistics

| Severity | Count | Key Files |
|----------|-------|-----------|
| CRITICAL | 2 | evaluate.py (line 3456 -- `_old_alarm` NameError), config.py (line 1362 -- dangling PSR_WEIGHT) |
| HIGH | 5 | industreal_dataset.py (COCO re-parse), dataset.py (sys.path errors), metrics.py (fake mAP), evaluate.py (per-image empty_cache), dataset.py (no sequence sampler) |
| MEDIUM | 7 | config.py (tautological assertion, schema validation, DET_GT_FRAME_FRACTION fragility, sequence length doc mismatch), industreal_dataset.py (hardcoded 24, subset bias), evaluate.py (metric key fragility) |
| LOW | 6 | config.py (benchmark mode scope), industreal_dataset.py (frame cache comment, stride=1 index size, magic number 17), evaluate.py (psr_macro_f1, crash checkpoint) |

## Most Impactful Bug

The `_old_alarm` NameError on **evaluate.py line 3456** is the most impactful bug found. It causes segment metric evaluation to ALWAYS fail silently. Every time `_run_seg_metrics` is True (any epoch after activity training is enabled), the segment metrics computation completes successfully, then the `finally` block raises NameError trying to restore `_old_alarm`, which is caught by `except Exception`, **silently discarding valid segment metrics** and setting `act_seg_top1`, `act_seg_top5`, and `act_seg_n` all to 0.0. Fix: replace `_old_alarm` with `_old_handler` on line 3456.
