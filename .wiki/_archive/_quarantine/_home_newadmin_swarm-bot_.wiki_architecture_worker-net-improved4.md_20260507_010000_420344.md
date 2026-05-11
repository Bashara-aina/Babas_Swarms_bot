---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/architecture/worker-net-improved4.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-05-07T01:00:00.420363"
}
---

---
title: WorkerNet — improved4 Architecture
type: architecture
status: active
tags: [popw, computer-vision, multi-task-learning, pose-estimation, object-detection, resnet, fpn, film, kendall-loss, ikea, assembly-understanding]
created: 2026-04-13
updated: 2026-04-13
summary: "improved4 is WorkerNet v2 with ResNet-50-FPN backbone, 3 task heads (Detection/Pose/Activity), PoseFiLMModule for pose-conditioned activity modulation, and Kendall uncertainty weighting. improved4_film adds FiLM and achieves act_top1=37.4%, det_mAP@0.5=0.600, pose_PCK@0.1=99.9%. Training: 3-4 days on RTX 3060 12GB, FP16, grad accum."
wikilinks:
  - [[concepts/multi-task-learning]]
  - [[concepts/film-modulation]]
  - [[concepts/kendall-loss]]
  - [[concepts/wise-iou]]
  - [[projects/popw-multi-task-ikea]]
  - [[projects/popw-research]]
confidence: high
source: research
project: popw
---

# WorkerNet — improved4 Architecture

## TL;DR

improved4 is the WorkerNet v2 multi-task model for IKEA assembly video understanding. ResNet-50-FPN backbone → 3 parallel heads (Detection + Pose + Activity). improved4_film adds PoseFiLMModule (`γ = MLP_pose(kp)`, `β = MLP_pose(kp)`, `modulated = γ ⊙ C5 + β`) achieving **act_top1=37.4%**, **det_mAP@0.5=0.600**, **pose_PCK@0.1=99.9%** at **26.3ms/inference** on RTX 3060. 40.1M → 42.2M trainable params with FiLM.

---

## 1. Architecture Map

### 1.1 Full Forward Pass

```
Input [B, 3, 640, 480]
  ↓
ResNet-50 (ImageNet pretrained, frozen first 20 epochs)
  → C3 [B, 512, 80, 60], C4 [B, 1024, 40, 30], C5 [B, 2048, 20, 15]
  ↓
FPN (256-ch lateral convs + smooth + P6/P7)
  → P3 [B, 256, 80, 60], P4 [B, 256, 40, 30], P5 [B, 256, 20, 15]
      P6 [B, 256, 10, 8],  P7 [B, 256, 5, 4]
  ↓
┌─────────────────────────────────────────────────────────┐
│ P5 ─────────┬─► DetectionHead (RetinaNet-style)        │
│             ├─► PoseHead (Heatmap + soft-argmax, 17 kp) │
│             └─► ActivityHead (GAP + FC → 33 classes)    │
│                    ↑                                    │
│                    └ PoseFiLMModule (if film=True) ←───┤
│                         modulates C5 with pose context  │
└─────────────────────────────────────────────────────────┘
Output: detections, keypoints [B, 17, 3], activity logits [B, 33]
```

### 1.2 Key Dimensions

| Layer | Shape | Channels |
|-------|-------|----------|
| Input | [B, 3, 640, 480] | 3 |
| C3 | [B, 512, 80, 60] | 512 |
| C4 | [B, 1024, 40, 30] | 1024 |
| C5 | [B, 2048, 20, 15] | 2048 |
| P3–P7 | [B, 256, H, W] | 256 |
| Activity features | [B, 2304] | — |
| Activity logits | [B, 33] | — |

### 1.3 PoseFiLMModule (Pose-Conditioned Feature Modulation)

```python
class PoseFiLMModule(nn.Module):
    def __init__(self, pose_dim=51, feat_channels=2048):
        self.gamma_net = nn.Sequential(
            nn.Linear(pose_dim, 512), nn.ReLU(),
            nn.Linear(512, feat_channels)  # → [B, feat_channels]
        )
        self.beta_net = nn.Sequential(
            nn.Linear(pose_dim, 512), nn.ReLU(),
            nn.Linear(512, feat_channels)  # → [B, feat_channels]
        )

    def forward(self, c5, keypoints, confidence):
        # keypoints: [B, 17, 3] (x, y, conf) — flatten to [B, 51]
        z = torch.cat([keypoints.flatten(1), confidence], dim=1)  # [B, 51+17=68]
        gamma = self.gamma_net(z)  # [B, 2048]
        beta  = self.beta_net(z)   # [B, 2048]
        return c5 * gamma.unsqueeze(-1).unsqueeze(-1) + beta.unsqueeze(-1).unsqueeze(-1)
```

**Key insight**: The pose encoder is a simple MLP (NOT a graph network or transformer). It takes raw 17×3 keypoint coordinates and produces channel-wise scale/shift for C5 features. This is the simplest possible pose-conditioned modulation — no spatial attention, no graph structure.

---

## 2. Task Heads

### 2.1 DetectionHead (RetinaNet-style)

- **9 anchors per location** (3 ratios × 3 scales)
- **Focal Loss** for classification (α=0.25, γ=2.0)
- **Smooth L1** for box regression
- **7 furniture part classes**: table top, leg, shelf, side panel, back panel, door, drawer
- Input: P5 features
- Anchor sizes: (32, 64, 128, 256, 512) at each spatial location

### 2.2 PoseHead (Heatmap Regression)

- **17 COCO keypoints** per frame
- **Wing Loss** for heatmap regression (wing_w=2.0, wing_warmup=10)
- **Multi-scale**: P3 (stride-8) for face keypoints, P4 (stride-16) for body
- **soft-argmax** for coordinate extraction (fixed edge-pixel bias on IMG_W/hm_w)
- Confidence-weighted loss: `loss *= keypoint_confidence`

### 2.3 ActivityHead

- **33 atomic action classes** (IKEA assembly actions)
- **Class-Balanced Focal Loss** (β=0.9999, γ=2.0) for 2545:1 imbalance
- Architecture: `C5_features → GAP → 2304 → 512 → 33`
- **Pending upgrade**: residual bottleneck `2304 → 768 → 256 → 768 → 33`

---

## 3. Loss Functions

### 3.1 MultiTaskLoss (Kendall Uncertainty Weighting)

```python
class MultiTaskLoss(nn.Module):
    def forward(self, det_loss, pose_loss, act_loss):
        # L_total = 0.5 * exp(-log_var_det) * L_det
        #           + 0.5 * exp(-log_var_pose) * L_pose
        #           + 0.5 * exp(-log_var_act) * L_act
        #           + log_var_det + log_var_pose + log_var_act
        #
        # 3 learned log-variance parameters (initially -1.0)
        # Auto-balances task weights during training
```

### 3.2 Task-Specific Losses

| Task | Loss | Configuration |
|------|------|---------------|
| Detection | Focal Loss | α=0.25, γ=2.0, pos_iou=0.5, neg_iou=0.4 |
| Pose | Wing Loss | wing_w=2.0, wing_warmup=10 epochs |
| Activity | CB-Focal Loss | β=0.9999, γ=2.0, class-balanced |

### 3.3 CB-Focal Loss (Class-Balanced)

```python
effective_samples = (1.0 - beta^count) / (1.0 - beta)  # β=0.9999
class_weights = 1.0 / effective_samples * num_classes
focal_loss = class_weights[targets] * (1 - p_t)^gamma * ce_loss
```

---

## 4. Training Configuration

| Parameter | Value |
|-----------|-------|
| Batch size | 15 |
| Gradient accumulation | 4 steps → effective 60 |
| Precision | FP16 (mixed) |
| Optimizer | SGD (momentum=0.9, base_lr=1e-3) |
| Scheduler | Cosine annealing + linear warmup (5 epochs) |
| Early stopping | patience=15 |
| Epochs | 150 (target) |
| Training time | 3-4 days on RTX 3060 |
| NaN guard | Skip corrupt frames, counter logged |

### 4.1 Critical Fixes (2026-03)

| Date | Issue | Fix |
|------|-------|-----|
| 03-10 | ActivityHead dim mismatch (expected 2304, got 2048) | Always fuse C5+P4; dedicated C5-only constructor arg |
| 03-10 | soft-argmax edge-pixel bias (~8px systematic underestimation) | `scale = (IMG_W-1)/(hm_w-1)` instead of `IMG_W/hm_w` |
| 03-10 | AnchorGenerator ratio/scale loop order | ratios outer / scales inner (matches RetinaNet standard) |
| 03-13a | BrokenPipeError on multiprocessing | `set_start_method('spawn')` at module top-level |
| 03-13b | Bus error / worker crash | spawn + file_system sharing + `persistent_workers=False` |
| 03-14 | OOM at validation | Pre-validation flush: clear cache, zero grads, gc.collect(), empty CUDA |
| 03-14b | IndentationError line 415 | Extra space before `best_metric` |
| 03-15 | Validation OOM (VM_FAULT_OOM) | VAL_BATCH_SIZE=4, VAL_NUM_WORKERS=2, prefetch_factor=1 |
| 03-16 | log_var_pose reset to 0.0 on resume | Corrected to `fill_(-1.0)` for asymmetric Kendall init |

---

## 5. Benchmark Results (compare_models.py)

Results from `compare_results.json.txt` (2026-03-28):

### 5.1 improved4 (no FiLM)

```
trainable_params : 40,097,621
inference_ms     : 25.61 ms
act_top1          : 37.9%
pose_PCK@0.05     : 99.53%
pose_PCK@0.1     : 99.89%
det_mAP@0.5       : 0.535
```

### 5.2 improved4_film (with PoseFiLMModule)

```
trainable_params : 42,252,117  (+2.15M for FiLM)
inference_ms     : 26.34 ms    (+0.73ms overhead)
act_top1          : 37.4%
pose_PCK@0.05     : 99.58%
pose_PCK@0.1     : 99.89%
det_mAP@0.5       : 0.600     (+12% relative vs improved4)
```

### 5.3 Comparison with improved3 variants

| Model | act_top1 | det_mAP@0.5 | pose_PCK@0.1 | params |
|-------|----------|-------------|--------------|--------|
| improved3 | 20.7% | 0.591 | 98.2% | 40.1M |
| improved3_film | 32.3% | 0.598 | 98.3% | 42.3M |
| improved4 | 37.9% | 0.535 | 99.9% | 40.1M |
| improved4_film | 37.4% | **0.600** | 99.9% | 42.3M |

**Key observation**: improved4_film achieves best detection mAP@0.5 among all variants while maintaining near-perfect pose accuracy. Activity accuracy is essentially tied with improved4 (37.4% vs 37.9%) — suggesting the FiLM module is primarily benefiting detection through improved feature learning, not through activity.

---

## 6. Evaluation Metrics

### 6.1 Activity Recognition

- Frame accuracy (all classes / excluding NA class 0)
- Macro-F1, Weighted-F1, Macro-Recall
- Mean per-class accuracy
- Top-5 accuracy (requires raw logits)
- Confusion matrix + per-class report

### 6.2 Pose Estimation

- PCK@0.05, PCK@0.1, PCK@0.2
- Per-keypoint PCK@0.1
- Mean pixel error

### 6.3 Object Detection

- mAP@0.5 (primary)
- mAP@[0.5:0.95]
- Per-class AP@0.5

### 6.4 Segment-Level Metrics (temporal_metrics.py)

Computed post-evaluation on frame-level predictions:

| Metric | Description |
|--------|-------------|
| F1@10 | Segment F1 at IoU threshold 0.10 |
| F1@25 | Segment F1 at IoU threshold 0.25 |
| F1@50 | Segment F1 at IoU threshold 0.50 |
| Edit Score | Normalized Levenshtein similarity on segment sequences |

These are the same metrics used by HVQ and View-Invariant papers for temporal action segmentation.

```bash
python improved4__temporal_metrics.py.txt --checkpoint runs/.../best.pth --split test
```

---

## 7. Hardware Profile

| Metric | Value |
|--------|-------|
| GPU | RTX 3060 12GB |
| GFLOPs | ~200 GFLOPs (estimated for full multi-task forward) |
| FPS (batch=1) | ~38 FPS |
| Latency (batch=1) | ~26 ms |
| Peak GPU memory | ~8GB |
| Throughput (batch=15) | ~150 frames/sec |

---

## 8. Key Files

| File | Purpose |
|------|---------|
| `improved4__config.py.txt` | All paths, IMG_H/W=640/480, dataset constants |
| `improved4__model.py.txt` | ResNet50-FPN + 3 heads + PoseFiLMModule |
| `improved4__losses.py.txt` | Focal, Wing, CB-Focal, Kendall MultiTaskLoss |
| `improved4__ikea_dataset.py.txt` | Multi-task dataset loader, LRU cache, balanced sampler |
| `improved4__train.py.txt` | Training loop: FP16, grad accum, early stopping, checkpointing |
| `improved4__evaluate.py.txt` | Full evaluation: mAP, PCK, accuracy, macro-F1 |
| `improved4__benchmark.py.txt` | GFLOPs, FPS, GPU memory profiler |
| `improved4__temporal_metrics.py.txt` | Segment-level F1@10/25/50, Edit Score |
| `improved4__micro_benchmark.py.txt` | Per-module latency breakdown |
| `improved4__plot_kendall.py.txt` | Kendall uncertainty weight visualization |

---

## 9. Next Steps (Priority Order)

1. **Apply FiLM `.detach()` fix** — remove `keypoints.detach()` to restore bidirectional gradient flow (expected +2-5% activity)
2. **Residual ActivityHead** — replace `2304→512→33` with `2304→768→256→768→33` bottleneck (+1-2%)
3. **Object-aware FiLM** — augment FiLM conditioning with top-K detected boxes (+1-3%)
4. **Temporal attention** — add frame-to-frame attention across video sequence (planned for April 2026)

---

## Related Articles

- [[projects/popw-multi-task-ikea]] — High-level POPW research overview
- [[projects/popw-research]] — Full research narrative (685K frames, 254 videos, 3 tasks)
- [[concepts/multi-task-learning]] — Multi-task learning theory (Kendall, GradNorm, PCGrad)
- [[concepts/film-modulation]] — FiLM as conditional normalization
- [[concepts/kendall-loss]] — Kendall homoscedastic uncertainty weighting
- [[concepts/wise-iou]] — Wise-IoU loss (alternative detection loss)
