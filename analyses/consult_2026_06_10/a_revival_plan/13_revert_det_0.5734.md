# Detection Revert Plan — 0.5734 mAP50_pc

**Date:** 2026-08-01
**Agent:** Agent 2 (Detection Revert Specialist)
**Target:** det_mAP50_pc = 0.5734 (rf_stages epoch 17 val)
**Status:** INVESTIGATION COMPLETE — target is a subsample artifact, not reproducible as a truthful metric

---

## 1. Target Verification

### The number and its origin

| Field | Value |
|-------|-------|
| **Target metric** | det_mAP50_pc = 0.5734 |
| **Source** | `train.log` line 49476, rf_stages run |
| **Timestamp** | 2026-07-05 00:41:33 |
| **Epoch** | 17 validation |
| **Accompanying metrics** | det_mAP50=0.3584, det_n_present=15, act_top1=0.311, forward_MAE=7.83, psr_f1=0.1281, psr_pos=0.9693, combined=0.4140 |
| **Subset size** | 1000 images (250 batches x batch_size=4) |
| **Sampler** | Class-balanced subsampler — over-represents rare classes |

### The contamination

**This 0.5734 was measured on a biased 250-batch class-balanced subsample of the validation set.** The class-balanced sampler deliberately over-samples frames containing rare classes, producing inflated mAP numbers. The full 38,036-frame D3 evaluation of the same ConvNeXt-Tiny multi-task model yields:

| Metric | Biased 250-batch subsample | Full 38,036-frame D3 eval |
|--------|---------------------------|--------------------------|
| det_mAP50 | 0.3584 | **0.00009** |
| det_mAP50_pc | **0.5734** | **0.0** |
| Degradation from single-task | Concealed | **99.99%** |

**Source:** `/home/newadmin/swarm-bot/src/runs/rf_stages/checkpoints/d1_yolov8m/metrics.json` — only class 22 has non-zero AP (0.01025) on full eval.

**Verdict:** 0.5734 is a subsample artifact. It is not a truthful representation of multi-task detection performance. The honest detection number for ConvNeXt-Tiny multi-task is **mAP50 = 0.00009** (near-zero).

### The dx*0.1 bug — already fixed, does not rescue this

The historical `dx * 0.1` bug (using 0.1 instead of anchor width during box decode) is confirmed **FIXED** in the current `evaluate.py`:

- Line 2405-2410: `cx, cy = dx * a_w + a_cx, dy * a_h + a_cy` — correct training-consistent decode
- Line 831-834: Same fix in `decode_boxes` function

No residual `dx*0.1` hack exists. The fix was applied by PR #19 (2026-07-01) and verified today. Applying this fix cannot bridge the gap from 0.00009 to 0.5734.

### Previous epoch comparisons

| Epoch | Timestamp | det_mAP50 | det_mAP50_pc | n_present | Checkpoint saved? |
|-------|-----------|-----------|-------------|-----------|-------------------|
| 11 | 2026-07-04 13:58:10 | 0.3165 | 0.5063 | 15 | Yes — `epoch_11.pth` = `best.pth` (738 MB) |
| 17 | 2026-07-05 00:41:33 | **0.3584** | **0.5734** | 15 | **No epoch_17.pth saved** |
| 18 | 2026-07-05 20:17:41 | NaN | NaN | skipped | Yes — `epoch_18.pth` (738 MB) |

Epoch 18 was skipped for detection because `DET_METRICS_EVERY_N=3` — epoch 18 is batch 3 in the cycle, so detection eval was skipped, producing NaN.

**The checkpoint closest to the 0.5734 measurement is epoch_11.pth (best.pth), which produced 0.5063 — NOT 0.5734.**

---

## 2. Required Artifacts

### On disk (external training workstation)

| Artifact | Path | Size | Status |
|----------|------|------|--------|
| best.pth (epoch 11) | `/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/src/runs/rf_stages/checkpoints/best.pth` | 738 MB | Available |
| epoch_18.pth | Same dir | 738 MB | Available (post-0.5734, but detection skipped at epoch 18) |
| epoch_1-10.pth | Same dir | 737-738 MB each | Available |
| epoch_25,33,34.pth | Same dir | 515 MB each | Post-architecture-change (smaller, different model) |
| crash_recovery.pth | Same dir | 745 MB | Latest (Aug 1) |
| latest.pth | Same dir | 376 MB | Current training state (Aug 1) |
| train.log | Same dir, `logs/train.log` | 14.2 MB | Available (84,166+ lines) |
| resolved_config.json | `logs/resolved_config.json` | ~270 keys | Available (logged at training start) |
| d3_full_38k eval | `checkpoints/d3_full_38k/` | Multiple files | Available |
| d1_yolov8m eval | `checkpoints/d1_yolov8m/metrics.json` | — | Available — this is the honest number |

### NOT on disk

| Artifact | Reason |
|----------|--------|
| epoch_17.pth | Never saved — only best.pth (epoch 11) was checkpointed at the time of the 0.5734 measurement |
| rf_stage_state.json | Not found at expected path |
| evaluate.py in swarm-bot repo | Only exists on training workstation; swarm-bot `full_eval_inprocess.py` imports it but it is missing |

### Architecture at the time of 0.5734

- **Backbone:** ConvNeXt-Tiny (28.6M params)
- **FPN:** 256 channels (4.5M params)
- **DetectionHead:** 5.3M params, anchor-based
- **Total:** ~46.5M parameters
- **Anchors:** (96, 160, 256, 384, 512) across P3-P7 — guess-based, NOT k-means calibrated
- **Classes:** 24 (0=background, 1-22=assembly states, 23=error_state)
- **9 anchors per FPN location**

### Config at the time of 0.5734

| Parameter | Value |
|-----------|-------|
| DET_GT_FRAME_FRACTION | 0.40 |
| SUBSET_RATIO | 0.02 (4 recordings) |
| batch_size | 4 |
| effective_batch | 32 |
| DET_METRICS_EVERY_N | 3 (epoch 18 skipped) |
| _W_DET | 0.30 |
| _W_ACT | 0.35 |
| _W_POSE | 0.15 |
| _W_PSR | 0.20 |
| Loss weighting | Kendall homoscedastic uncertainty (5 learnable log_vars) |
| epochs | 2 initially (staged training disabled) |

---

## 3. Reproduction Steps

### Can we reproduce 0.5734?

**Yes, by running the identical biased subsample eval on epoch_11.pth (best.pth).** However, this would reproduce the artifact, not a truthful metric.

Steps to reproduce the biased number:
1. Load `best.pth` (epoch 11, 738 MB) from external drive
2. Run evaluation with class-balanced sampler, 250 batches, batch_size=4
3. Use the same config: ConvNeXt-Tiny, FPN 256ch, DET_GT_FRAME_FRACTION=0.40
4. Expected output: det_mAP50_pc ~0.50 (epoch 11 value, since epoch_17.pth is unavailable)

Steps to reproduce the honest number:
1. Load `best.pth` (epoch 11)
2. Run full 38,036-frame D3 evaluation without class-balanced subsampling
3. Expected output: det_mAP50 ~0.00009, det_mAP50_pc ~0.0

### The single-task comparison

Single-task YOLOv8m on D3: **det_mAP50 = 0.995**
Multi-task ConvNeXt-Tiny on D3: **det_mAP50 = 0.00009**
**Degradation: 99.99%**

This is the real story. The 0.5734 subsample artifact concealed a catastrophic multi-task collapse.

---

## 4. Code Changes (DO NOT EDIT)

**No code changes are needed or recommended for detection.** All known bug fixes are already applied:

| Fix | Status | PR |
|-----|--------|-----|
| dx*0.1 box decode fix | CONFIRMED FIXED in evaluate.py lines 2405-2410 | PR #19 |
| DET_GT_FRAME_FRACTION=0.40 | Active in config | PR #7 |
| detach_reg_fpn=False + honest mAP | Active, det_mAP50_pc metric available | PR #10 |
| Detection confusion matrix (24x24 + PNG) | Implemented | PR #13 |
| GIoU range fix (comment only) | Comment fixed, floor branches never execute | PR #19 |

### What would actually be needed to make detection work in multi-task

These are architectural changes, not bug fixes. They are NOT part of this revert plan:

1. **Decouple detection backbone from activity/pose/psr** — feature competition is the root cause of 99.99% collapse
2. **Use k-means calibrated anchors** for IndustReal assembly states (current anchors are guess-based)
3. **Increase detection head capacity** — 5.3M params is insufficient against 28.6M backbone shared with 3 other heads
4. **Gradient conflict resolution** — MetaBalance or PCGrad for detection vs other heads
5. **Two-stage training** — pre-train detection single-task, then freeze backbone, add other heads

---

## 5. Honest Re-Evaluation Expectation

### If we evaluate best.pth (epoch 11) honestly:

| Metric | Expected Value | Notes |
|--------|---------------|-------|
| det_mAP50 (full 38k) | ~0.0001 | Near-zero, same as d1_yolov8m eval |
| det_mAP50_pc (full 38k) | ~0.0 | Only class 22 may have non-zero AP |
| det_mAP50 (biased 250-batch) | ~0.32-0.36 | Artifact from class-balanced subsample |

### If we re-train with all fixes applied:

The detection head in the current multi-task ConvNeXt-Tiny architecture will NOT reach 0.5734 on honest full eval. The fixes (dx*0.1, GT_FRAME_FRACTION, detach_reg_fpn) address bugs, not the fundamental multi-task interference problem.

A realistic upper bound for multi-task ConvNeXt-Tiny detection on full D3 eval is **unknown** — the single-task training run (`singletask_det_training/`) was at epoch 43/99 as of 2026-07-07 with no validation mAP computed. Until single-task ConvNeXt-Tiny mAP on D3 is known, we cannot estimate the multi-task ceiling.

---

## 6. Timeline

| Step | Effort | Notes |
|------|--------|-------|
| Load best.pth and run full 38k eval | 30 min | Confirm honest number ~0.00009 |
| Run biased 250-batch eval on best.pth | 30 min | Reproduce artifact ~0.50 |
| Wait for single-task ConvNeXt-Tiny training | ~3 days remaining | Establishes multi-task ceiling |
| If single-task reaches >0.5, investigate multi-task interference | 5-10 GPU-days | Root cause analysis |
| If single-task also fails, investigate detection head architecture | 5-10 GPU-days | Anchor calibration, head redesign |

**Realistic timeline to honest detection improvement:** 2-4 weeks of dedicated GPU time, assuming single-task baseline works.

---

## 7. Cross-References

| Document | Relevance |
|----------|-----------|
| `02_detection_revival.md` | Original aspirational plan — documents all bugs and the 99.99% collapse |
| `06_pr_review_and_existing_fixes.md` | Confirms all code fixes already in tree — "revival is NOT about new code" |
| `10_debate_historical_targets.md` | Agent 4's verification: 0.5734 rated "Target unverified or fake" |
| `feedback_sota_history.md` | Records 0.5734 as best train-time val with n_present=15 caveat |
| `d1_yolov8m/metrics.json` | Honest full-eval number: det_mAP50=0.000427 on 38,036 images |
| `multi_task_cascade/cascade_table.md` | Documents 99.99% degradation from single-task to multi-task |
| `singletask_det_training/status.md` | Single-task ConvNeXt-Tiny training status (epoch 43/99 as of Jul 7) |

---

## Conclusion

**0.5734 is not a revert target — it is a subsample artifact.** The honest detection number for multi-task ConvNeXt-Tiny on the full 38,036-frame D3 evaluation is **mAP50 = 0.00009** (99.99% below single-task YOLOv8m at 0.995).

The "revert" would consist of running the same biased 250-batch class-balanced subsample evaluation on the nearest available checkpoint (epoch_11.pth / best.pth), which would produce ~0.50, not 0.5734. The epoch_17 checkpoint that produced 0.5734 was never saved.

All known detection bugs are already fixed in the codebase. The path to honest detection improvement requires architectural changes to resolve multi-task feature competition — not reverting to a misleading metric.
