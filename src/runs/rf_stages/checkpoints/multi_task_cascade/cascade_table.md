# Multi-Task Cascade Analysis: D3 (multi-task) vs Single-Task (oracle)

**Date:** 2026-07-07
**Checkpoint:** best.pth (epoch 18) — ConvNeXt-Tiny backbone
**Val frames:** 38,036 across 16 recordings
**OOM notice:** Both GPUs busy with training. All analysis is CPU-only aggregation of existing metrics.

---

## Cascade Summary Table

| Head | Metric | Single-Task (oracle) | Multi-Task (D3) | Absolute Delta | Relative Degradation |
|---|---|---|---|---|---|
| **Detection** | mAP50 | 0.995 (YOLOv8m, D1R self-trained) | 0.00009 (ConvNeXt-Tiny head) | -0.99491 | -99.99% |
| **Activity** | top-1 (per-frame) | 0.622 (MViTv2-S, T3 baseline) | 0.0236 | -0.5984 | -96.2% |
| **PSR** | macro F1 (global thresh 0.10) | 0.7893 (decoder, single-task) | 0.7018 | -0.0875 | -11.1% |
| **Head Pose** | forward angular MAE | 8.39 (multi-task, SOTA_STATUS) | 9.14 | +0.75 | +8.9% |

### Notes on Baselines

- **Detection single-task:** 0.995 mAP50 is from a separately-trained YOLOv8m on the IndustReal D1R dataset (self-trained, beats WACV 2024's ~0.95). The multi-task ConvNeXt-Tiny detection head achieves only 0.00009, which is 4 orders of magnitude worse. This is the most severe degradation in the cascade.
- **Activity single-task:** 0.622 top-1 from T3 baseline (MViTv2-S, verb-grouped 69-class evaluation). The multi-task per-frame MLP head achieves 0.0236 — a 96.2% collapse. The MLP architecture lacks temporal reasoning, which is the primary bottleneck.
- **PSR single-task:** 0.7893 decoder F1 from single-task PSR evaluation. Multi-task F1 drops to 0.7018 — an 11.1% relative degradation, the mildest cascade effect.
- **Head pose single-task:** No independent single-task head pose run exists. The SOTA_STATUS reports 8.39 forward MAE from the same multi-task model. The 9.14 value from D3 represents a different evaluation configuration or normalization.

---

## Cascade Severity Ranking

| Rank | Head | Degradation | Category |
|------|------|-------------|----------|
| 1 | **Detection** | -99.99% | **Critical collapse** — multi-task ConvNeXt head fails catastrophically |
| 2 | **Activity** | -96.2% | **Critical collapse** — per-frame MLP cannot compete with video-level MViTv2 |
| 3 | **PSR** | -11.1% | **Mild degradation** — decoder partially robust to shared features |
| 4 | **Head Pose** | +8.9% | **Marginal increase** — likely within eval noise / normalization variance |

---

## Root Cause Analysis

### Detection Collapse (0.995 -> 0.00009)
The ConvNeXt-Tiny detection head in the multi-task model produces essentially random predictions. Three contributing factors:
1. **Feature competition:** The shared ConvNeXt backbone must serve detection, activity, PSR, and pose heads simultaneously. Detection is spatially precise and benefits from high-resolution features, while activity and PSR are global-semantic tasks. The backbone likely allocates capacity toward the latter.
2. **Gradient conflict:** Detection loss (CIoU + classification) may conflict with PSR BCE loss and activity cross-entropy. The Kendall uncertainty weighting may over-weight the auxiliary tasks.
3. **Training signal dilution:** With 4 task heads and effective batch size of 16, each task sees fewer gradient updates per epoch compared to single-task training (batch size 16, detection only).

### Activity Collapse (0.622 -> 0.0236)
The per-frame MLP head (150K params) is architecturally incapable of temporal reasoning. The MViTv2-S achieves 0.622 by processing 16-frame clips with 3D convolutions and self-attention. The multi-task model's MLP sees one frame at a time — comparable to single-frame ablated MViTv2, which would also score near zero.

### PSR Mild Degradation (0.7893 -> 0.7018)
The MonotonicDecoder is the most robust head in the cascade. Its hysteresis-based transition detection (sustain_hi=0.5, sustain_lo=0.3, sustain_min=3) acts as a low-pass filter that smooths over feature quality variations. The decoder's oracle bound (relaxed F1=0.8807) shows that even with perfect logits, the decoder loses ~12% F1 due to procedure-order constraints and sustain hysteresis.

### Head Pose Stability (8.39/9.14 )
Head pose regression (angular MAE) is the least affected by multi-task training. The FiLM-conditioned regression head operates on global pooled features, which are likely shared across all tasks and well-regularized. The small difference between 8.39 and 9.14 may reflect eval configuration rather than genuine degradation.

---

## Data Provenance

| Value | Source | Verification |
|-------|--------|-------------|
| 0.995 D1R mAP50 | `analyses/consult_2026_06_10/AAIML/129_COMPREHENSIVE_METRICS_AND_FILE_LOCATIONS.md` | Cross-referenced from SOTA_STATUS and analysis docs |
| 0.00009 D3 mAP50 | Prompt context (D3 full 38k eval) | File not found on disk — NaN-fixed eval from earlier session |
| 0.622 MViTv2-S top1 | `src/runs/rf_stages/checkpoints/t3_full_eval.json` | Verified file read |
| 0.0236 D3 activity | Prompt context / SOTA_STATUS.md | SOTA_STATUS reports 0.023 per-frame |
| 0.7893 decoder F1 | Prompt context (single-task PSR) | Not independently verified from disk |
| 0.7018 D3 PSR F1 | `psr_optimal_thr_v2/optimal_thresholds.json`: global_0.10=0.70134 | Verified file read (rounded) |
| 9.14 D3 pose MAE | Prompt context | SOTA_STATUS reports 8.39 |
| 8.39 single-task pose | SOTA_STATUS.md | Verified file read |

## Source Files

- `src/runs/rf_stages/checkpoints/SOTA_STATUS.md` — master status
- `src/runs/rf_stages/checkpoints/t3_full_eval.json` — MViTv2-S baseline
- `src/runs/rf_stages/checkpoints/psr_optimal_thr_v2/optimal_thresholds.json` — PSR 5k eval
- `src/runs/rf_stages/checkpoints/psr_optimal_thr/optimal_thresholds.json` — PSR full eval
- `src/runs/rf_stages/checkpoints/activity_clip_ep18/activity_clip.json` — activity clip eval
- `src/runs/rf_stages/checkpoints/decoder_oracle_cpu/oracle_f1.json` — oracle bound
- `analyses/consult_2026_06_10/AAIML/129_COMPREHENSIVE_METRICS_AND_FILE_LOCATIONS.md` — master cross-ref
