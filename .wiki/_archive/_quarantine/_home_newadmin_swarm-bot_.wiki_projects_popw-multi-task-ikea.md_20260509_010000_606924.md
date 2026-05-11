---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/projects/popw-multi-task-ikea.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-05-09T01:00:00.606945"
}
---

---
title: popw-multi-task-ikea
type: project
status: active
tags: [machine-learning, computer-vision, multi-task-learning, pose-estimation, object-detection, activity-recognition, pytorch, resnet, ikea, assembly-understanding]
created: 2026-04-13
updated: 2026-04-13
summary: "popw (Papers of Papers Worker?) is a multi-task learning research project for IKEA assembly video understanding. Architecture: ResNet50-FPN backbone → 3 task heads (Detection + Pose + Activity) with Kendall uncertainty weighting. Dataset: 685,516 frames from 254 IKEA assembly videos with 3 label types. Critical finding: FiLM `.detach()` blocks activity→pose gradient flow. Target: Activity >60.46%, Detection 70-80% mAP@0.5, Pose 85-90% PCK@0.1."
wikilinks:
 - [[concepts/multi-agent-orchestration]]
 - [[projects/cekwajar-id]]
 - [[projects/rumahlabuh-com]]
confidence: high
source: research
project: popw
---

# popw — Multi-Task IKEA Assembly Recognition

## TL;DR

popw is a multi-task deep learning research project for understanding IKEA furniture assembly videos. A single ResNet50-FPN backbone produces features fed into three parallel task heads: **object detection** (7 furniture-part classes), **pose estimation** (17 COCO keypoints via OpenPose pseudo-labels), and **activity recognition** (33 assembly action classes, severely imbalanced at 2545:1). Tasks are balanced via **Kendall uncertainty weighting** (learned log-variance parameters). Critical bug found: FiLM conditioning uses `.detach()` on keypoints, blocking activity→pose gradient flow. Hardware: RTX 3060 12GB, FP16, grad accum 6. Training: 3-4 days for 150 epochs.

---

## 1. Research Goal

**Problem**: Understand assembly actions in IKEA tutorial videos — which part is being picked up, where is it being placed, and what action is being performed — jointly, from raw video frames.

**Why multi-task**: Assembly actions (e.g., "insert_bracket_left") are defined by both hand pose AND object location. A shared backbone forces the model to learn features useful for all three tasks, improving generalization vs. single-task models.

**Target**: Beat baseline `P3D ResNet-50` activity accuracy of **60.46%**.

---

## 2. Dataset

### 2.1 Scale

| Stat | Value |
|------|-------|
| Total frames | 685,516 |
| Assembly videos | 254 |
| Furniture types | 4 |
| Frame-level label coverage | 100% (all 3 tasks labeled) |

### 2.2 Label Types

| Task | Format | Classes | Volume | Imbalance |
|------|--------|---------|--------|-----------|
| **Detection** | COCO boxes | 7 furniture parts | 3.69M boxes | moderate |
| **Pose** | 17 COCO keypoints (OpenPose pseudo-labels) | per-frame | 685K poses | none |
| **Activity** | 33 manual assembly action classes | per-frame | 685K labels | **2545:1** (CB-Focal active) |

### 2.3 Dataset Variants

| Directory | Purpose |
|-----------|---------|
| `IKEA/` | Raw downloaded videos |
| `IKEA_RAW/` | Extracted frames |
| `IKEA_dataset/` | Processed annotation files |
| `ikea_workernet_FULL/` | Full annotation set |
| `ikea_workernet_ULTIMATE/` | Refined annotations |
| `ikea_workernet_unified_BACKUP/` | Backup |

---

## 3. Architecture

### 3.1 Backbone: ResNet50-FPN

```
Input: [B, 3, 640, 480]
 ↓
ResNet-50 backbone (ImageNet pretrained)
 ↓
Feature Pyramid Network (FPN)
 ↓
{C2, C3, C4, C5, P3, P4, P5, P6, P7} ← multi-scale feature pyramid
```

### 3.2 Task Heads

```
P5 (2048 channels) ─────────────────┬─► DetectionHead (RetinaNet-style)
 ├─► PoseHead (Heatmap regression, 17 keypoints)
 └─► ActivityHead (GAP + FC → 33 classes)
 ↑
 PoseFiLMModule ← pose (x,y,conf) conditions activity
```

### 3.3 PoseFiLMModule (Feature-wise Linear Modulation)

```python
class PoseFiLMModule(nn.Module):
 # pose_dim = 17 * 3 = 51 (x, y, confidence per keypoint)
 # feat_channels = 2048
 #
 # gamma_net: 51 → 2048 (learns per-channel scale)
 # beta_net: 51 → 2048 (learns per-channel bias)
 # output: c5 * gamma + beta ← element-wise modulation
```

FiLM allows pose to modulate the spatial backbone features before activity classification.

### 3.4 ActivityHead (Simple, to be upgraded)

```python
# Current: 2304 → 512 → 33 (no residual)
# Recommended: 2304 → 768 → 256 → 768 → 33 (residual bottleneck)
```

---

## 4. Loss Functions

### 4.1 Multi-Task Loss (Kendall Uncertainty Weighting)

```python
class MultiTaskLoss(nn.Module):
 # L_total = 0.5 * exp(-log_var_det) * L_det
 # + 0.5 * exp(-log_var_pose) * L_pose
 # + 0.5 * exp(-log_var_act) * L_act
 # + log_var_det + log_var_pose + log_var_act
 #
 # Learned params: log_var_det, log_var_pose, log_var_act (one per task)
 # These auto-balance task weights during training
```

### 4.2 Task-Specific Losses

| Task | Loss | Notes |
|------|------|-------|
| Detection | Focal Loss | RetinaNet-style classification + smooth L1 box regression |
| Pose | Wing Loss | Horizontal wing wing modification for better small-keypoint accuracy |
| Activity | **CB-Focal Loss** | Class-balanced focal loss for 2545:1 imbalanced classes |

### 4.3 CB-Focal Loss (Class-Balanced)

```python
# Beta = 0.9999 (1 = minimal re-weighting for rare classes)
effective_samples = (1.0 - beta^counts) / (1.0 - beta)
class_weights = 1.0 / effective_samples * num_classes
focal_loss = class_weights[targets] * (1 - p_t)^gamma * ce
```

`set_class_counts()` is called explicitly in `train.py:520` — verified working.

---

## 5. Training Configuration

### 5.1 Hardware Setup (RTX 3060 12GB)

| Parameter | Value |
|-----------|-------|
| Batch size | 12 |
| Effective batch (grad accum) | 72 |
| Precision | FP16 (mixed) |
| Gradient clipping | max_norm=1.0 |
| Optimizer | SGD with momentum=0.9 |
| Base LR | 1e-3 (with warmup) |
| Scheduler | Cosine annealing |
| Early stopping | patience=15 epochs |

### 5.2 Expected Training Time

- **150 epochs** on RTX 3060 ≈ 3-4 days
- NaN skip counter monitors training stability
- `metrics.jsonl` logs per-epoch: losses, Kendall weights, nan_skips

---

## 6. Critical Issue: FiLM Gradient Blocking

### Location: `model.py` line ~482-488

```python
# BEFORE (INCORRECT — blocks activity → pose gradient flow)
if self.use_film:
 with torch.no_grad():
 confidence = ...
 c5_mod = self.film(
 c5, keypoints.detach(), confidence # ← .detach() IS THE BUG
 )
```

**Impact**:
- Activity loss CAN improve FiLM gamma/beta parameters ✅
- Activity loss CANNOT improve pose_head quality ❌
- One-way: pose → FiLM → activity, NOT: activity → pose

**Fix**: Remove `.detach()`:
```python
# AFTER (CORRECT)
c5_mod = self.film(
 c5, keypoints.nan_to_num(0.0), confidence # ✅ no .detach()
)
```

**Expected gain**: +2-5% activity accuracy

### Verification
```bash
# Check gradients flow into pose_head
python -c "
import torch
from model import MultiTaskIKEA
model = MultiTaskIKEA(use_film=True)
grads = [p.grad for p in model.pose_head.parameters() if p.grad is not None]
print(f'Pose head received {len(grads)} gradient tensors')
# Should be > 0 after fix
"
```

---

## 7. Evaluation Metrics

### Activity Recognition
- Top-1 Accuracy
- Top-5 Accuracy
- Macro-F1 (per-class average)
- Per-class accuracy
- Confusion matrix

### Pose Estimation
- PCK@0.05 (Percentage of Correct Keypoints at threshold 0.05)
- PCK@0.1, PCK@0.2
- Per-keypoint PCK
- Mean pixel error

### Object Detection
- mAP@0.5 (COCO-style)
- mAP@0.5:0.95
- Per-class AP (7 furniture part classes)

### Evaluation Script
```bash
python evaluate.py --checkpoint runs/ikea_multitask/checkpoints/best.pth --split test
```

---

## 8. Upgrade Path (Priority Order)

### Priority 1: Fix FiLM Gradient (5 min)
```bash
sed -i 's/keypoints\.detach()\.nan_to_num/keypoints.nan_to_num/g' model.py
```
Expected: +2-5% activity accuracy

### Priority 2: Residual ActivityHead (30 min)
Replace `ActivityHead` class with residual bottleneck:
```
2304 → 768 → 256 → 768 → 33 (+ residual skip)
```
Expected: +1-2% additional accuracy, especially for rare classes

### Priority 3: Object-Aware FiLM (1 hour, optional)
Add top-K detected boxes to FiLM conditioning vector:
```
pose_dim: 51 → 76 (pose 51 + top-5 boxes 25)
```
Expected: +1-3% accuracy (objects provide task context)

### Priority 4: PoseCrossAttentionModule (2 hours, experimental)
Replace FiLM with multi-head cross-attention:
```
Queries: C5 spatial features [B, HW, 256]
Keys/Values: Pose tokens + Object tokens [B, 17+K, 256]
```
Full implementation in `IMPLEMENTATION_GUIDE.md`.

---

## 9. Key Files

| File | Purpose |
|------|---------|
| `config.py` | All paths, hyperparameters, dataset constants |
| `ikea_dataset.py` | Multi-task dataset loader with LRU caching + balanced sampling |
| `model.py` | ResNet50-FPN + 3 heads + PoseFiLMModule |
| `losses.py` | Focal, Wing, CB-Focal, Kendall MultiTaskLoss |
| `train.py` | Training loop: FP16, grad accum, early stopping, checkpointing |
| `evaluate.py` | Full evaluation: mAP, PCK, accuracy, macro-F1 |
| `compare_models.py` | Side-by-side improved4 vs improved4_film comparison |
| `run_paper_evaluation.py` | Paper-style evaluation runner |

### Model Variants (directories)

| Directory | Description |
|-----------|-------------|
| `improved/` | Baseline single-task |
| `improved2/` | Multi-task version |
| `improved4/` | Further iterations |
| `improved4_film/` | **Current best** — FiLM conditioning |
| `improved4_transformer/` | Experimental transformer variant |

---

## 10. Architecture Decision Record

| Issue | Decision | Rationale |
|-------|----------|-----------|
| `.detach()` in FiLM | Remove | Restore bidirectional gradient flow |
| ActivityHead depth | Residual bottleneck 3-layer | 2545:1 imbalance needs capacity for rare classes |
| Class imbalance | CB-Focal Loss | Better than naive focal for extreme imbalance |
| Task weighting | Kendall learned uncertainty | End-to-end learned, no manual tuning |
| Backbone | ResNet50-FPN | Standard, well-tested for detection+pose |

---

## 11. Hardware Constraints

| Resource | Limit | Notes |
|----------|-------|-------|
| VRAM | 12GB (RTX 3060) | Batch 12 + grad accum 6 = effective 72 |
| Training time | 3-4 days / 150 epochs | Acceptable for research iteration |
| NaN losses | Monitored via `nan_skips` | If >10% epochs = stability issue |

---

## 12. Current Status (as of 2026-04-13)

- ✅ ResNet50-FPN backbone operational
- ✅ All 3 task heads implemented
- ✅ Kendall uncertainty weighting active
- ✅ CB-Focal Loss verified (`set_class_counts()` called)
- ✅ 685K frame dataset ready
- ⚠️ FiLM `.detach()` bug — **identified, fix not yet applied**
- ✅ Checkpointing with full state (model + optimizer + scheduler + scaler)
- ✅ Comprehensive evaluation metrics
- ✅ RTX 3060 optimization (FP16, grad accum)

**Next step**: Apply Priority 1 fix, re-train 10 epochs, verify +2-5% activity gain.

---

## Related Articles

- [[concepts/multi-agent-orchestration]] — Multi-task learning shares roots with multi-agent coordination
- [[projects/cekwajar-id]] — cekwajar.id (Indonesian data platform, separate ML project)
- [[projects/rumahlabuh-com]] — rumahlabuh.com (Indonesian rental platform, separate project)
- [[entities/gpt-researcher]] — Research automation patterns from this project
