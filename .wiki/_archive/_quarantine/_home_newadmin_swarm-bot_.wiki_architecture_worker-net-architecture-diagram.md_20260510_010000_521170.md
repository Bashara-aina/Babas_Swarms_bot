---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/architecture/worker-net-architecture-diagram.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-05-10T01:00:00.521191"
}
---

---
title: WorkerNet Architecture — Full Multi-Task Diagram
type: architecture
status: active
tags: [popw, worker-net, architecture, diagram, resnet, fpn, pose-estimation, object-detection, activity-recognition, film-modulation, multi-task-learning]
created: 2026-04-13
updated: 2026-04-13
summary: "WorkerNet is a multi-task CNN for IKEA assembly understanding with 3 parallel heads: Pose Estimation (P3, 17 COCO keypoints, Wing Loss), Object Detection (P5, 7 furniture parts, Focal Loss), and Activity Recognition (GAP + PoseFiLMModule, 33 actions, CB-Focal Loss). Trained end-to-end with Kendall uncertainty weighting."
wikilinks:
  - [[architecture/worker-net-improved4]]
  - [[architecture/popw-training-pipeline]]
  - [[concepts/film-modulation]]
  - [[concepts/kendall-loss]]
  - [[projects/popw-research]]
confidence: high
source: research
project: popw
---

# WorkerNet Architecture — Full Multi-Task Diagram

## TL;DR

WorkerNet processes RGB video frames (640×480) through a shared ResNet50-FPN backbone producing multi-scale feature pyramids (P3-P7). Three parallel task heads then predict: **Pose Estimation** (17 COCO keypoints via heatmap regression on P3), **Object Detection** (7 furniture part classes via RetinaNet on P5), and **Activity Recognition** (33 assembly actions via GAP + PoseFiLMModule conditioned on pose). All tasks are trained jointly with Kendall uncertainty weighting.

---

## 1. Architecture Diagram

![WorkerNet Full Architecture](popw-media/worker-net-architecture-diagram.png)

*Source: Architectural Diagram.drawio.png — generated from improved4_film source code audit*

---

## 2. Pipeline Stages

### Stage 1: Input

```
RGB Video Frame → [B, 3, 640, 480]
```

### Stage 2: Backbone — ResNet50 (ImageNet pretrained)

```
[B, 3, 640, 480]
  → conv1 (7×7, 64, stride-2)
  → maxpool (3×3, stride-2)
  → res2 (3 blocks, 256 channels, stride-1) → C2 [B, 256, 80, 60]
  → res3 (4 blocks, 512 channels, stride-2) → C3 [B, 512, 80, 60]
  → res4 (6 blocks, 1024 channels, stride-2) → C4 [B, 1024, 40, 30]
  → res5 (3 blocks, 2048 channels, stride-2) → C5 [B, 2048, 20, 15]
```

### Stage 3: Neck — Feature Pyramid Network (FPN)

```
C2 [B, 256, 80, 60]   ──────────────────────────→ P3 [B, 256, 80, 60]   (stride 8)
C3 [B, 512, 80, 60]   ──┬── lateral ──→ +upsample → P4 [B, 256, 40, 30]  (stride 16)
C4 [B, 1024, 40, 30]  ──┴── lateral ──→ +upsample → P5 [B, 256, 20, 15]  (stride 32)
C5 [B, 2048, 20, 15]  ─── lateral ─────────────→ P6 [B, 256, 10, 8]    (stride 64)
P6 [B, 256, 10, 8]    ─── stride-2 conv ────────→ P7 [B, 256, 5, 4]    (stride 128)

All FPN outputs: 256 channels (lateral 1×1 conv)
```

---

## 3. Task Heads

### 3.1 Pose Estimation Head

```
Input: P3 [B, 256, 80, 60]

Pose Encoder (MLP on keypoints):
  keypoints [B, 17, 3] (x, y, conf)
    → flatten [B, 51]
    → concat confidence [B, 17]
    → [B, 68]
    → gamma_net: Linear(68, 512) → Linear(512, 256) → [B, 256]  (for P3 channels)
    → beta_net:  Linear(68, 512) → Linear(512, 256) → [B, 256]   (for P3 channels)

Pose FiLM (modulates P3 with pose condition):
  P3_film = gamma * P3 + beta  [element-wise]

Heatmap prediction:
  3×3 Conv → BN → ReLU → 1×1 Conv → [B, 17, 80, 60]  (17 heatmaps)
  soft-argmax → [B, 17, 2]  (x, y coordinates per keypoint)

Loss: Wing Loss (horizontal wing modification)
  wing_w=2.0, wing_warmup=10 epochs
  Weighted by keypoint confidence
```

### 3.2 Object Detection Head

```
Input: P5 [B, 256, 20, 15]

Anchor Generation (per spatial location):
  3 ratios × 3 scales = 9 anchors
  Anchor sizes: (32, 64, 128, 256, 512) at each location

Classification head (per anchor):
  3×3 Conv → BN → ReLU → 1×1 Conv → [B, 9×7, 20, 15]
  7 furniture part classes

Box regression head (per anchor):
  3×3 Conv → BN → ReLU → 1×1 Conv → [B, 9×4, 20, 15]
  4 offsets per anchor (dx, dy, dw, dh)

Loss: Focal Loss (classification) + Smooth L1 (regression)
  α=0.25, γ=2.0
  positive IoU threshold: 0.5
  negative IoU threshold: 0.4
```

### 3.3 Activity Recognition Head

```
C5 features [B, 2048, 20, 15]
  ↓ GAP
[B, 2048]
  ↓ concat (P4 after 1×1 conv [B, 256] → upsampled + global pooling)
[B, 2304]
  ↓ FC (2304 → 512 → ReLU)
  ↓ FC (512 → 33)
[B, 33] logits

PoseFiLMModule (modulates activity features with pose):
  keypoints [B, 17, 3] → flatten + concat → [B, 68]
    → MLP → gamma [B, 2048], beta [B, 2048]
  modulated_C5 = gamma ⊙ C5 + beta  [applied before GAP]

Loss: Class-Balanced Focal Loss (CB-Focal)
  β=0.9999, γ=2.0
  Handles 2545:1 class imbalance (most actions are "no action")
```

---

## 4. Multi-Task Training

### 4.1 Kendall Uncertainty Weighting

```python
L_total = 0.5 * exp(-log_var_det) * L_det
        + 0.5 * exp(-log_var_pose) * L_pose
        + 0.5 * exp(-log_var_act) * L_act
        + log_var_det + log_var_pose + log_var_act

log_var_* are learned parameters (init=-1.0)
Auto-balances task weights during training
```

### 4.2 Validation Metric

```python
combined = 0.40 * normalize(F1) + 0.35 * normalize(PCK) + 0.25 * normalize(mAP)
# When PCK is NaN (no visible keypoints): combined = 0.57*F1 + 0.43*mAP
```

### 4.3 Training Loop

```
Backbone: SGD, lr=1e-3, momentum=0.9, weight_decay=1e-4
Scheduler: Cosine annealing (T_max=145) + Linear warmup (5 epochs)
Batch: 15 × grad_accum 4 = effective 60
Precision: FP16 mixed
Epochs: 150 (target)
```

---

## 5. Tensor Shapes Summary

| Stage | Tensor | Shape |
|-------|--------|-------|
| Input | image | [B, 3, 640, 480] |
| Backbone C3 | feature | [B, 512, 80, 60] |
| Backbone C5 | feature | [B, 2048, 20, 15] |
| FPN P3 | feature | [B, 256, 80, 60] |
| FPN P5 | feature | [B, 256, 20, 15] |
| Pose heatmaps | output | [B, 17, 80, 60] |
| Pose keypoints | output | [B, 17, 2] |
| Detection anchors | output | [B, 9, H, W] |
| Activity logits | output | [B, 33] |

---

## 6. Source Files

| File | Role |
|------|------|
| `model.py` | ResNet50 + FPN + 3 heads + PoseFiLMModule |
| `losses.py` | Focal, Wing, CB-Focal, Kendall MultiTaskLoss |
| `config.py` | IMG_H/W=640/480, dataset paths, class counts |
| `train.py` | Full training loop, validation, checkpointing |
| `evaluate.py` | Evaluation metrics (mAP, PCK, accuracy) |

---

## Related Articles

- [[architecture/worker-net-improved4]] — Detailed model architecture
- [[architecture/popw-training-pipeline]] — Training pipeline
- [[projects/popw-research]] — Research context and dataset
- [[concepts/film-modulation]] — FiLM as conditional normalization
- [[concepts/kendall-loss]] — Kendall uncertainty weighting
