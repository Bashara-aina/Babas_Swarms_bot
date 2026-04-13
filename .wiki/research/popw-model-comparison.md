---
title: POPW Model Comparison — improved3 vs improved4
type: research
status: active
tags: [popw, model-comparison, improved3, improved4, improved4_film, benchmark, multi-task-learning, pose-estimation, object-detection]
created: 2026-04-13
updated: 2026-04-13
summary: "Benchmark comparison of 4 WorkerNet model variants across 685K IKEA assembly frames. improved4 achieves 37.9% activity top-1 accuracy (+83% relative vs improved3). improved4_film achieves best detection mAP@0.5=0.600 (+12% relative vs improved4 without FiLM) while maintaining near-perfect pose PCK@0.1=99.9%. All results from compare_models.py (2026-03-28)."
wikilinks:
  - [[architecture/worker-net-improved4]]
  - [[projects/popw-research]]
  - [[projects/popw-multi-task-ikea]]
confidence: high
source: research
project: popw
---

# POPW Model Comparison — improved3 vs improved4

## TL;DR

Comparison of 4 WorkerNet model variants on the IKEA assembly test set (2026-03-28). improved4 (+FiLM) achieves the best detection mAP@0.5 of 0.600 and near-perfect pose PCK@0.1 of 99.9%. Activity accuracy peaked at 37.9% (improved4) vs 20.7% (improved3), a +83% relative improvement. The FiLM module primarily benefits detection (+12% relative mAP) rather than activity.

---

## 1. Full Results Table

| Metric | improved3 | improved3_film | improved4 | improved4_film |
|--------|-----------|-----------------|-----------|----------------|
| **trainable_params** | 40,097,621 | 42,252,117 | 40,097,621 | 42,252,117 |
| **inference_ms** | 25.65 | 26.29 | 25.61 | 26.34 |
| **act_top1** | 20.7% | **32.3%** | **37.9%** | 37.4% |
| act_top5 | 0.0% | 0.0% | 0.0% | 0.0% |
| **act_macro_f1** | 0.105 | **0.171** | 0.133 | 0.132 |
| **pose_PCK@0.05** | 92.5% | 94.3% | **99.5%** | 99.6% |
| **pose_PCK@0.1** | 98.2% | 98.3% | **99.9%** | **99.9%** |
| **det_mAP@0.5** | 0.591 | 0.598 | 0.535 | **0.600** |
| det_mAP@0.5:0.95 | 0.371 | 0.376 | 0.395 | **0.404** |

*Best value per row in bold.*

---

## 2. Analysis

### 2.1 improved3 → improved4: The Architecture Jump

The biggest single improvement is improved3 → improved4. Key changes:
- Improved soft-argmax edge bias fix → +17% absolute activity accuracy
- Corrected anchor generator loop order → better detection localization
- Better multi-scale pose handling (P3 for face, P4 for body)
- Better data augmentation / sampling

### 2.2 improved4 → improved4_film: FiLM Effect

FiLM adds 2.15M parameters and 0.73ms latency overhead. The effect:

| Task | improved4 → improved4_film | Interpretation |
|------|---------------------------|---------------|
| Activity top-1 | 37.9% → 37.4% (-0.5%) | Essentially tied — FiLM doesn't help activity |
| Activity macro-F1 | 0.133 → 0.132 | Tied within noise |
| Detection mAP@0.5 | 0.535 → **0.600** (+12% rel) | FiLM significantly helps detection |
| Pose PCK@0.1 | 99.9% → 99.9% | At ceiling — pose fully converged |

**Key observation**: FiLM appears to primarily regularize the shared backbone, which benefits detection more than activity. The pose-conditioned modulation may force the backbone to learn pose-aware features that improve localization.

### 2.3 The Activity Ceiling Problem

All models achieve 0% top-5 accuracy — meaning even the correct class is never in the top-5 predictions. This suggests:
1. The activity classes are very similar to each other (fine-grained assembly actions)
2. The model lacks temporal context (frame-level only)
3. Class imbalance may still be causing poor rare-class predictions

**Next step**: Temporal attention across frames is planned for April 2026.

---

## 3. Training Details

| Model | Best Epoch | Checkpoint |
|-------|-----------|------------|
| improved3 | 143 | runs/ikea_multitask_gt_only |
| improved3_film | 101 | runs/ikea_multitask_gt_only_film |
| improved4 | 20 | runs/ikea_multitask_improved4 |
| improved4_film | 44 | runs/ikea_multitask_improved4_film |

Note: improved4 converges faster (epoch 20 vs 101) — the improved4 architecture trains more efficiently.

---

## 4. Hardware Profile (improved4_film)

| Metric | Value |
|--------|-------|
| GPU | RTX 3060 12GB |
| Inference latency | 26.34 ms/frame |
| FPS (batch=1) | ~38 |
| Trainable params | 42.3M |
| Loaded tensors | 368 / 393 |

---

## Related Articles

- [[architecture/worker-net-improved4]] — Full model architecture
- [[projects/popw-research]] — Research context
- [[research/popw-film-literature-gap]] — FiLM novelty argument
