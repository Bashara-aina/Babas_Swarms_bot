---
title: POPW v14 Ground Truth — improved4_film Reference
type: research
status: active
tags: [popw, ground-truth, v14, improved4_film, reference, architecture, computer-vision]
created: 2026-04-13
updated: 2026-04-13
summary: "POPW v14 is the ground-truth reference for improved4_film (WorkerNet). Every fact, tensor shape, and number in the Professor Hub HTML visualization is verified against model.py/losses.py/config.py source code. Key verified facts: P3 shape [B,256,80,60] (corrected from v13's [B,256,60,80]), all tensor dimensions, FiLM module parameters, and loss configurations."
wikilinks:
  - [[architecture/worker-net-improved4]]
  - [[architecture/popw-training-pipeline]]
  - [[projects/popw-research]]
confidence: high
source: research
project: popw
---

# POPW v14 Ground Truth — improved4_film Reference

## TL;DR

POPW v14 is the audited ground-truth reference aligned to `improved4_film` source code. Every tensor shape, fact, and number in the `film-popw-viz.html` Professor Hub has been verified against `model.py`, `losses.py`, `config.py`, `train.py`, and `ikea_dataset.py`. **Critical correction from v13**: P3 tensor shape is `[B, 256, 80, 60]` (matching C3 `[B, 512, 80, 60]` from input `[B, 3, 640, 480]`), NOT `[B, 256, 60, 80]` as incorrectly documented in v13.

---

## 1. Critical Correction: P3 Tensor Shape

### The Bug (v13)

```
❌ P3 shape was [B, 256, 60, 80]
   This does NOT match C3 = [B, 512, 80, 60] from input [B, 3, 640, 480]
   ResNet C3 has spatial 80 (H) × 60 (W) — height is 80, width is 60
   The P3 lateral conv takes C3 [B, 512, 80, 60] → lateral [B, 256, 80, 60]
   So P3 must also be [B, 256, 80, 60], NOT [B, 256, 60, 80]
```

### The Fix (v14)

```
✅ P3 shape is [B, 256, 80, 60]
   C3 = [B, 512, 80, 60]  (height=80, width=60 from input 640×480)
   FPN lateral_c3: C3 [512, 80, 60] → P3_lateral [256, 80, 60]
   P3 final = smooth_p3(P3_lateral) = [B, 256, 80, 60]
```

### Why This Matters

The stride-8 feature map P3 corresponds to the highest resolution in the FPN. If P3 were transposed to `[B, 256, 60, 80]`, it would be spatially inconsistent with the C3 feature map it was derived from, and any pose heatmap or detection head operating on P3 would have mismatched spatial coordinates.

---

## 2. Verified Architecture Facts

### 2.1 Input → Backbone → FPN

```
Input: [B, 3, 640, 480]

ResNet-50 (ImageNet pretrained):
  C1: [B, 64, 320, 240]   (after conv1 + bn1 + relu + maxpool stride-2)
  C2: [B, 256, 80, 60]   (stride 8)
  C3: [B, 512, 80, 60]   (stride 8)  ← note: H=80, W=60
  C4: [B, 1024, 40, 30]  (stride 16)
  C5: [B, 2048, 20, 15]  (stride 32)

FPN (all 256 channels):
  P3: [B, 256, 80, 60]   (from C3 via lateral + smooth)
  P4: [B, 256, 40, 30]   (from C4 via lateral + top-down + smooth)
  P5: [B, 256, 20, 15]   (from C5 via lateral + smooth)
  P6: [B, 256, 10, 8]    (from C5 via stride-2 conv)
  P7: [B, 256, 5, 4]     (from P6 via stride-2 conv)
```

### 2.2 PoseFiLMModule

```
Input to FiLM:
  keypoints: [B, 17, 3]  (x, y, confidence per COCO keypoint)
  flatten: [B, 51]       (17 × 3 = 51)
  concat confidence: [B, 68]  (51 + 17)
  gamma_net: 68 → 512 → 2048 → [B, 2048]
  beta_net:  68 → 512 → 2048 → [B, 2048]
  output: gamma * c5.unsqueeze(-1).unsqueeze(-1) + beta.unsqueeze(-1).unsqueeze(-1)
  c5 shape: [B, 2048, 20, 15]
  modulated: [B, 2048, 20, 15]
```

### 2.3 ActivityHead

```
Architecture:
  C5 features: [B, 2048, 20, 15]
  GAP → [B, 2048]
  Concat P4 features after 1×1 conv: [B, 256] → [B, 2304]
  FC: 2304 → 512 → ReLU
  FC: 512 → 33 (logits)

Total parameters (with FiLM): 42,252,117
Total parameters (without FiLM): 40,097,621
FiLM overhead: 2,154,496 params
```

---

## 3. Loss Configurations

### 3.1 Focal Loss (Detection)

```python
FocalLoss(alpha=0.25, gamma=2.0, pos_iou_thresh=0.5, neg_iou_thresh=0.4)
```

### 3.2 Wing Loss (Pose)

```python
WingLoss(wing_w=2.0, wing_warmup=10)
# warmup: first 10 epochs use MSE, then Wing Loss
```

### 3.3 CB-Focal Loss (Activity)

```python
ClassBalancedFocalLoss(beta=0.9999, gamma=2.0, num_classes=33)
```

### 3.4 Kendall MultiTaskLoss

```python
MultiTaskLoss():
  log_var_det: init=-1.0, learnable
  log_var_pose: init=-1.0, learnable
  log_var_act: init=-1.0, learnable

  L_total = 0.5 * exp(-log_var_det) * L_det
          + 0.5 * exp(-log_var_pose) * L_pose
          + 0.5 * exp(-log_var_act) * L_act
          + log_var_det + log_var_pose + log_var_act
```

---

## 4. Training Config

```python
IMG_HEIGHT = 640
IMG_WIDTH = 480
NUM_ACT_CLASSES = 33
NUM_DET_CLASSES = 7  # furniture parts
NUM_KEYPOINTS = 17    # COCO

BATCH_SIZE = 15
GRAD_ACCUM = 4  # effective batch = 60
BASE_LR = 1e-3
WEIGHT_DECAY = 1e-4
WARMUP_EPOCHS = 5
MAX_EPOCHS = 150
PATIENCE = 15
SEED = 42

NUM_WORKERS = 4
PIN_MEMORY = True
persistent_workers = True  # training loader only
VAL_BATCH_SIZE = 4
VAL_NUM_WORKERS = 2
```

---

## 5. Dataset Facts

| Stat | Value |
|------|-------|
| Total frames | 685,516 |
| Videos | 254 |
| Frame size | 640 × 480 |
| Detection classes | 7 (table top, leg, shelf, side panel, back panel, door, drawer) |
| Activity classes | 33 (atomic IKEA assembly actions) |
| Keypoints | 17 COCO keypoints |
| Activity imbalance | 2545:1 (CB-Focal active) |
| Label coverage | 100% (all 3 tasks labeled) |

---

## 6. Source Files Verified

| File | Key Verified Facts |
|------|-------------------|
| `model.py` | FPN forward pass, P3 shape [B,256,80,60], PoseFiLMModule MLP dimensions |
| `losses.py` | Focal α=0.25, γ=2.0; Wing w=2.0, warmup=10; CB-Focal β=0.9999 |
| `config.py` | IMG_H=640, IMG_W=480, NUM_ACT_CLASSES=33 |
| `train.py` | VAL_BATCH_SIZE=4, VAL_NUM_WORKERS=2, log_var init -1.0 |
| `ikea_dataset.py` | Balanced sampler, 2545:1 class counts |

---

## Related Articles

- [[architecture/worker-net-improved4]] — Full model architecture
- [[architecture/popw-training-pipeline]] — Training pipeline details
- [[research/popw-model-comparison]] — Benchmark results
