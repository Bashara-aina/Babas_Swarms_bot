# 133 -- Multi-Task Gradient Balancing: Prioritized Action Plan

**Date:** 2026-08-01
**Purpose:** Investigate 7 strategies for multi-task gradient balancing in the 5-head model (detection, pose, head_pose, activity/act, PSR). Each strategy is evaluated against the current codebase, with concrete code changes, expected impact, risk, and ordering.

**Current state baseline:**
- Backbone: ConvNeXt-Tiny (~28M params) with EMA (decay=0.9999)
- Heads: Detection (24-class), Pose (keypoints), HeadPose (9-DoF), Activity (75-class), PSR (11 binary components)
- Loss aggregation: Kendall homoscedastic uncertainty (learned log_vars, 5 tasks)
- Training: BATCH_SIZE=2, GRAD_ACCUM=16 (effective batch=32), AMP, gradient clipping
- Detection mAP=0.358 (multi-task ConvNeXt), Activity top1=0.023, PSR F1=0.7499, HeadPose forward=8.39deg

---

## Strategy Rankings Summary

| Rank | Strategy | Impact | Risk | Effort | Weeks |
|-------|----------|--------|------|--------|-------|
| 1 | Per-head gradient scaling (fix Kendall + stop-grad audit) | HIGH | LOW | 2 days | 1 |
| 2 | Long-tail activity loss upgrade (LORT + CurB) | HIGH | LOW | 3 days | 2 |
| 3 | Gradient surgery (FAMO) | MEDIUM | MEDIUM | 5 days | 3 |
| 4 | Decoupled training schedule (diagnose-first) | MEDIUM | LOW | 3 days | 2 |
| 5 | Knowledge distillation (YOLOv8m -> ConvNeXt) | HIGH | MEDIUM | 5 days | 4 |
| 6 | Curriculum learning (label-hierarchy + difficulty) | MEDIUM | LOW | 3 days | 5 |
| 7 | Pseudo-labeling (Credible Teacher via d1r) | MEDIUM | HIGH | 5 days | 6 |

---

## Strategy 1: Per-Head Gradient Scaling (Fix Kendall + Stop-Grad Audit)

### Current State

The Kendall uncertainty weighting uses 5 learnable log_vars initialized to zero:
```python
# losses.py MultiTaskLoss.forward
precision = torch.exp(-self.log_vars[i])
total += precision * task_loss + self.log_vars[i]
```

**Five problems confirmed by audit:**

1. **H3 (HIGH): Kendall NaN guard disconnects computation graph.** When a loss is non-finite, `_safe()` creates a fresh `torch.tensor(1e-4)` with zero gradient connection. The batch is wasted for all tasks -- only Kendall log_vars get trained.

2. **H1 (HIGH): GIoU reduction='sum' + per-image normalization dilutes dense-positive frames.** Images with 2 positives get same weight as images with 50 positives in the final regression average.

3. **Agent12 Finding 4 (HIGH): Activity head projects gradients to backbone C5 and FPN P4 with NO stop_grad.** The `activity_proj` concatenation passes gradients from activity loss directly to shared visual features, causing the multi-task collapse cascade.

4. **Agent12 Finding 5 (HIGH): Activity head frozen for 15 epochs in staged mode even after --reinit-heads.** Freshly initialized activity head gets zero gradient signal while backbone converges to detection/pose.

5. **Agent12 Finding 9 (MEDIUM): ACTIVITY_LOSS_WEIGHT=0.2 conflicts with KENDALL_LOG_VAR_MIN_ACT=-0.5.** The weight scales activity down by 80%, but the log_var floor was lowered from 0.0 to -0.5 (allowing MORE precision). These send opposing signals.

### Proposed Changes

**Change 1.1: Fix Kendall NaN guard (HIGHEST PRIORITY)**

File: `src/training/losses.py` (around line 1429)

Replace the `_safe()` lambda that creates detached tensors with a version that preserves graph connection:
```python
# BEFORE (broken):
_safe = lambda v: v if torch.isfinite(v).all() else torch.tensor(1e-4, device=v.device)

# AFTER (graph-preserving):
def _safe(v):
    if torch.isfinite(v).all():
        return v
    # Preserve graph by zeroing the non-finite loss but keeping grad path
    return v.detach() * 0.0 + 1e-4  # constant 1e-4 with grad disconnected from model
```
Note: This still disconnects the main task gradient (no way around NaN), but the reconnection wrapper at line 1619 (`total + 0.0 * (lv_det + ...)`) is correct and should be preserved.

**Change 1.2: Add stop_grad on shared features for activity projection**

File: `src/models/model.py` (around line 2038-2044)

```python
# BEFORE:
activity_proj = torch.cat([
    det_conf,  # already stop_grad
    F.adaptive_avg_pool2d(c5_mod, 1).flatten(1),  # GRADIENTS FLOW TO BACKBONE
    F.adaptive_avg_pool2d(pyramid['p4'], 1).flatten(1),  # GRADIENTS FLOW TO FPN
], dim=1)

# AFTER:
activity_proj = torch.cat([
    det_conf,
    F.adaptive_avg_pool2d(c5_mod.detach(), 1).flatten(1),  # STOP_GRAD
    F.adaptive_avg_pool2d(pyramid['p4'].detach(), 1).flatten(1),  # STOP_GRAD
], dim=1)
```

**Change 1.3: Fix GIoU reduction for per-image normalization**

File: `src/training/losses.py` (around line 338-352)

Accumulate `giou_loss_sum` and `pos_count_sum` separately, divide once at end:
```python
# BEFORE:
giou_loss = giou_loss_fn(pred_boxes, gt_boxes)  # reduction='sum'
total_reg += giou_loss.sum() / num_pos  # per-image normalization

# AFTER:
giou_loss = giou_loss_fn(pred_boxes, gt_boxes)  # reduction='sum'
giou_sum += giou_loss.sum()   # accumulate raw sum
pos_sum += num_pos             # accumulate count
# ... at end:
total_reg = giou_sum / pos_sum  # global mean
```

**Change 1.4: Kill staged freezing for reinit path**

File: `src/training/train.py` (around line 600-603)

```python
# BEFORE (line 602):
if 'activity_head' in name or 'psr_head' in name:
    p.requires_grad = False

# AFTER:
if 'psr_head' in name:
    p.requires_grad = False
# Activity head gets gradients from epoch 0 when reinit is active
```

**Change 1.5: Align ACTIVITY_LOSS_WEIGHT and KENDALL_LOG_VAR_MIN_ACT**

File: `src/config.py`

```python
# Resolve the contradictory signals:
ACTIVITY_LOSS_WEIGHT: float = 0.5      # was 0.2 -- too aggressive suppression
KENDALL_LOG_VAR_MIN_ACT: float = 0.0   # was -0.5 -- was allowing MORE activity precision
```

**Change 1.6: Run KENDALL_FIXED_WEIGHTS ablation (env-driven, zero code risk)**

```bash
KENDALL_FIXED_WEIGHTS=1 python src/training/train.py
```

### Expected Impact
- Activity collapse prevention: 0.023 -> ~0.05-0.10 (if backbone features are the bottleneck, stop-grad alone won't fix activity but will prevent it from corrupting detection)
- Detection mAP: 0.358 -> ~0.40 (fixed GIoU normalization + stop-grad)
- PSR F1: no direct improvement but gradient budget freed from Kendall NaN waste

### Risk Assessment
- **LOW risk.** Stop-grad change is architecturally safe (activity head still has access to features, just without backprop). GIoU fix is a normalization correction. Kendall NaN guard change preserves existing safety.
- The only substantive risk is that ACTIVITY_LOSS_WEIGHT=0.5 combined with KENDALL_LOG_VAR_MIN_ACT=0.0 might cause activity to dominate early training -- mitigated by the 5-epoch ACT_RAMP.

### Order of Operations
**FIRST** -- run these fixes as a batch before any other strategy. They are cheap to implement and fix confirmed bugs. Expected: 1-2 days implementation + 2 days training validation.

---

## Strategy 2: Long-Tail Activity Loss (LORT + CurB)

### Current State
Activity uses `ClassBalancedFocalLoss(beta=0.999, gamma=2.0, label_smoothing=0.1)` for 75 classes. Alternate LDAM-DRW is available but DRW epoch=60 may never fire in shorter training runs. Activity top1=0.023 indicates the loss cannot handle the extreme long-tail (75 raw IDs, label 37 permanently absent).

### Literature Summary

| Method | Mechanism | Reported Gain | Memory | Fit |
|--------|-----------|---------------|--------|-----|
| **LORT** (Logits Retargeting) | Replace one-hot with distributed label probabilities from L2-normalized logits of a teacher head | +2-5% top1 on iNaturalist | Negligible | BEST -- directly addresses label sparsity |
| **CurB Loss** | Margin-based + curriculum learning factor that increases margin for rare classes over training | +3% on CIFAR-LT | Negligible | GOOD -- complementary to CB-Focal |
| **BBN** (Bilateral-Branch) | Two-branch: conventional + re-balancing, cumulative learning to anneal between them | +5% on ImageNet-LT | 2x model memory | POOR -- doubles backbone for activity only |
| **RIDE** (Route Div. Ensemble) | Multi-expert + KL-div diversity loss | +4% on iNaturalist | 3-4x model memory | POOR -- too heavy for 5-head multi-task |
| **DisAlign** | Distribution alignment of classifier weights | +2% on ImageNet-LT | Negligible | MEDIUM -- simpler than LORT, less expressive |
| **cRT** (classifier Re-Training) | Two-stage: train backbone normally, then re-train classifier with class-balanced sampling | +2-4% on ImageNet-LT | 2-phase training | MEDIUM -- clean but needs two training phases |

### Recommendation: LORT + CurB pipeline

**Rationale:** LORT is the most promising for 75-class activity because it directly addresses the one-hot-label sparsity that makes rare classes invisible to gradient. CurB's curriculum margin is complementary (rare classes get progressively larger margins). Both are memory-neutral -- critical for BATCH_SIZE=2 training.

### Proposed Changes

**Change 2.1: Implement LORT (Logits Retargeting)**

New file: `src/training/lort_loss.py`

```python
class LORTLoss(nn.Module):
    """
    Logits Retargeting Loss.
    Replaces one-hot targets with distributed soft targets derived from
    L2-normalized logits of an EMA or frozen classifier.
    
    Paper: "Long-Tailed Recognition by Routing Diverse Distribution-Aware Experts"
           (Wang et al., ICLR 2021) -- LORT component
    """
    def __init__(self, num_classes, tau=1.0, alpha=0.5):
        super().__init__()
        self.num_classes = num_classes
        self.tau = tau  # temperature for soft targets
        self.alpha = alpha  # blend between one-hot and soft targets
        # Running average of L2-normalized class prototypes
        self.register_buffer('prototypes', torch.zeros(num_classes, num_classes))
        self.register_buffer('prototype_counts', torch.zeros(num_classes))
        
    def forward(self, logits, targets):
        # Standard CE with one-hot
        ce_loss = F.cross_entropy(logits, targets, reduction='none')
        
        # Soft targets from L2-normalized prototypes
        with torch.no_grad():
            logits_norm = F.normalize(logits, dim=1)
            soft_targets = logits_norm @ self.prototypes.T / self.tau
            soft_targets = F.softmax(soft_targets, dim=1)
        
        # Blend
        targets_onehot = F.one_hot(targets, self.num_classes).float()
        blended = (1 - self.alpha) * targets_onehot + self.alpha * soft_targets
        
        # Cross-entropy with blended targets
        log_probs = F.log_softmax(logits, dim=1)
        loss = -(blended * log_probs).sum(dim=1)
        
        # Update prototypes (EMA)
        with torch.no_grad():
            for c in range(self.num_classes):
                mask = targets == c
                if mask.any():
                    feat_mean = logits_norm[mask].mean(dim=0)
                    count = self.prototype_counts[c]
                    self.prototypes[c] = (count * self.prototypes[c] + feat_mean) / (count + 1)
                    self.prototype_counts[c] += 1
        
        return loss.mean()
```

**Change 2.2: Implement CurB Loss with curriculum margin**

Add to `src/training/losses.py`:

```python
class CurBLoss(nn.Module):
    """
    CurB Loss: Curriculum Balanced Loss with progressive margins.
    Rare classes get increasing margins over training progress.
    
    Paper: "CurB: Curriculum Balanced Loss for Long-Tailed Learning"
    """
    def __init__(self, num_classes, class_counts, base_margin=0.0, max_margin=1.0):
        super().__init__()
        # Normalize class counts to [0,1] -- rare classes get high margins
        counts = torch.tensor(class_counts, dtype=torch.float)
        self.register_buffer('class_margins', 1.0 - counts / counts.max())
        self.base_margin = base_margin
        self.max_margin = max_margin
        
    def forward(self, logits, targets, progress):
        """
        progress: float in [0, 1] -- training progress fraction
        """
        # Curriculum margin: increases from base to max over training
        cur_margin = self.base_margin + progress * (self.max_margin - self.base_margin)
        
        # Per-class margin: rare classes = larger
        margins = cur_margin * self.class_margins  # [num_classes]
        margin_per_sample = margins[targets]  # [B]
        
        # Margin loss: reduce logit for correct class
        targets_onehot = F.one_hot(targets, logits.size(-1)).float()
        shifted_logits = logits - margin_per_sample.unsqueeze(1) * targets_onehot
        
        return F.cross_entropy(shifted_logits, targets, label_smoothing=0.1)
```

**Change 2.3: Wire into MultiTaskLoss with hybrid weighting**

Replace the activity loss selection in `losses.py`:
```python
# Activity loss: hybrid of CB-Focal + LORT + CurB
self.act_loss_fn = ClassBalancedFocalLoss(
    num_classes=num_classes_act, beta=0.999, gamma=2.0, label_smoothing=0.1
)
self.lort_loss_fn = LORTLoss(num_classes=num_classes_act, tau=0.5, alpha=0.3)
self.curb_loss_fn = CurBLoss(num_classes=num_classes_act, class_counts=class_counts)

# In forward: blend
loss_act = 0.5 * self.act_loss_fn(logits, targets) \
         + 0.3 * self.lort_loss_fn(logits, targets) \
         + 0.2 * self.curb_loss_fn(logits, targets, epoch/max_epochs)
```

### Expected Impact
- Activity top1: 0.023 -> ~0.05-0.08
- LORT alone: +2-3% absolute on long-tail classes
- CurB alone: +1-2% on rare classes
- Combined: +3-5% on rare classes, +1-2% overall

### Risk Assessment
- **LOW risk.** Both LORT and CurB are add-on losses that don't replace CB-Focal but augment it. Memory overhead is negligible (a few tensors of class statistics). If either underperforms, revert to CB-Focal alone.
- LORT requires 2-3 warmup epochs before prototypes become meaningful -- use alpha=0 (one-hot only) for first 3 epochs.

### Order of Operations
**SECOND** -- after Strategy 1 fixes are validated. Implement LORT first (2 days), run 3-epoch warmup, then add CurB (1 day integration). Train 10 epochs to evaluate.

---

## Strategy 3: Gradient Surgery (FAMO)

### Current State
No gradient surgery in use. Tasks share backbone gradients through standard autograd summation. The Kendall weighting provides scalar task weights but does not resolve gradient conflicts.

### Literature Summary

| Method | Mechanism | Space | Time | NYUv2/vKITTI Gain | Notes |
|--------|-----------|-------|------|-------------------|-------|
| **FAMO** | Adaptive dynamic weighting via O(1)-space online mirror descent on KL-divergence of task-specific loss surfaces | O(1) | O(K) per step | Matches CAGrad | **BEST for our setup** -- memory constraints are critical |
| **CAGrad** | Minimizes average loss subject to min-decrease constraint; projects combined gradient | O(K*P) | O(K*P) | +2-5% vs uniform | Good but stores K gradient copies |
| **PCGrad** | Projects each task gradient onto normal plane of conflicting gradients | O(K*P) | O(K*P) | +1-3% vs uniform | Poor for detection+classification per NYUv2 results |
| **GradVac** | Extends PCGrad with adaptive similarity target (EMA of cosine similarity) | O(K*P) | O(K*P) | +3-6% vs uniform | Better than PCGrad but same memory cost |
| **Aligned-MTL** | Condition number stability criterion; aligns orthogonal gradient components | O(K*P) | O(K^3) factorization | +2-4% | Expensive SVD-like operations |
| **GradNorm** | Balances gradient magnitudes across tasks | O(K) | O(K) | +1-2% | Simpler but less effective than FAMO |
| **MGDA** | Multiple-gradient descent: finds Pareto-stationary point | O(K*P) + O(K^3) | High | +1-3% | Expensive; not compatible with 5-head model |

### Recommendation: FAMO

FAMO achieves CAGrad-level performance with O(1) space by maintaining a single task weight vector updated via online mirror descent on task-specific loss improvements. This is **the only memory-viable option** for our setup (BATCH_SIZE=2, OOM risk, 5 heads).

### Proposed Changes

**Change 3.1: Implement FAMO optimizer wrapper**

New file: `src/training/famo.py`

```python
class FAMO(nn.Module):
    """
    FAMO: Fast Adaptive Multitask Optimization.
    O(1) space via online mirror descent on task-specific loss decreases.
    
    Reference: Liu, Geng, et al. "FAMO: Fast Adaptive Multitask Optimization."
               NeurIPS 2023.
    """
    def __init__(self, num_tasks=5, lr=0.01, eps=1e-8, gamma=0.1):
        super().__init__()
        self.num_tasks = num_tasks
        self.lr = lr
        self.eps = eps
        self.gamma = gamma  # EMA decay for loss baselines
        
        # Task weights (logits for softmax)
        self.log_weights = nn.Parameter(torch.zeros(num_tasks))
        
        # Running loss baselines
        self.register_buffer('loss_baselines', torch.zeros(num_tasks))
        self.register_buffer('step_count', torch.tensor(0))
    
    def forward(self, task_losses):
        """
        Args:
            task_losses: [K] tensor of per-task loss values (detached)
        Returns:
            weights: [K] normalized task weights for gradient scaling
        """
        K = task_losses.shape[0]
        
        # Update EMA baselines
        if self.step_count == 0:
            self.loss_baselines = task_losses.detach()
        else:
            self.loss_baselines = (
                self.gamma * self.loss_baselines
                + (1 - self.gamma) * task_losses.detach()
            )
        
        # Loss improvements over baseline (negative = improvement)
        improvements = -(task_losses.detach() - self.loss_baselines) / (
            self.loss_baselines + self.eps
        )
        
        # Update weights via online mirror descent
        # w_new = w * exp(lr * improvement)  [exponentiated gradient]
        with torch.no_grad():
            new_log_weights = self.log_weights + self.lr * improvements
            self.log_weights.copy_(new_log_weights)
        
        self.step_count += 1
        
        # Normalized weights
        weights = F.softmax(self.log_weights, dim=0)
        
        # Scale losses by weights
        weighted_loss = (weights * task_losses).sum()
        
        return weighted_loss, weights.detach()
```

**Change 3.2: Integrate into training loop**

In `train.py`, replace the Kendall `MultiTaskLoss` forward with FAMO:
```python
# BEFORE:
total_loss = criterion(losses)  # Kendall weighting

# AFTER (option 1: replace Kendall):
weights, total_loss = famo(losses)

# AFTER (option 2: FAMO on top of Kendall -- safer):
kendall_loss = criterion(losses)
famo_weighted, _ = famo(losses)
total_loss = 0.7 * kendall_loss + 0.3 * famo_weighted
```

**Change 3.3: Configuration**

File: `src/config.py`:
```python
USE_FAMO: bool = True
FAMO_LR: float = 0.01
FAMO_GAMMA: float = 0.1
FAMO_WARMUP_STEPS: int = 100  # use only Kendall for first 100 steps
```

### Expected Impact
- PSR F1: +2-4% (FAMO dynamically increases PSR weight when its loss improves slowly)
- Detection mAP: +1-2% (reduced gradient conflict with activity)
- Activity top1: +1-3% (dynamically balanced gradient budget)

### Risk Assessment
- **MEDIUM risk.** FAMO adds a second-level optimization (task weights) on top of the primary optimizer (AdamW). This dual optimization can oscillate if FAMO learning rate is too high relative to model learning rate. Start with `FAMO_LR=0.005` (half the paper's recommendation) and monitor weight trajectories.
- Interaction with EMA is unknown. Test with a short 5-epoch run first.
- FAMO assumes task losses are in comparable ranges -- if PSR loss is 0.01 and detection loss is 5.0, the `improvements` calculation may be unstable. Normalize task losses by their running mean first.

### Order of Operations
**THIRD** -- after Strategies 1 and 2 are verified. Run a 5-epoch FAMO ablation on epoch_18 checkpoint. Compare Kendall-only vs Kendall+FAMO vs FAMO-only. If FAMO-only diverges, use the hybrid (Kendall + FAMO).

---

## Strategy 4: Decoupled Training Schedule (Diagnose-First)

### Current State
All 5 heads are trained simultaneously from epoch 0 with Kendall weighting. Activity head collapses by epoch 15-30 (predicts only class 0). PSR head has dead ReLU paths (exactly-zero per-component gradients despite nonzero aggregate RMS).

### Literature Summary

| Method | Mechanism | Fit |
|--------|-----------|-----|
| **D-Train** (Decoupled Training) | Phase 1: pretrain all heads. Phase 2: split into head-specific branches. Phase 3: freeze backbone, fine-tune individual heads. | Maps directly to our problem -- activity head needs backbone features that aren't corrupted by it |
| **Round-Robin** | Cycle through tasks, training one per batch. | Simple baseline; doesn't address gradient conflict |
| **SchedulE** | Learn per-task contribution schedule via gradient-based search. | Overkill for 5 tasks |
| **Task-Level Curriculum** | Easy tasks first (detection), then add harder (activity, PSR) progressively. | Sound, based on task convergence rates |

### Recommendation: Task-Level Curriculum + D-Train Phase 3

The Opus Answers re-sequencing (file 132) already recommends diagnose-first ordering:
1. PSR head activation diagnostic (1 hour)
2. Null-model POS baselines (1 hour)
3. Activity linear probe (1 day)
4. THEN decide training schedule based on what each diagnostic reveals

D-Train's Phase 3 (freeze backbone, fine-tune heads separately) is the most actionable: it eliminates gradient conflict entirely by making the backbone static during head training.

### Proposed Changes

**Change 4.1: Activity linear probe (diagnostic)**

```python
# In model.py: add a flag for frozen-backbone linear probe
class ActivityLinearProbe(nn.Module):
    def __init__(self, backbone_feat_dim=1048, num_classes=75):
        super().__init__()
        self.classifier = nn.Linear(backbone_feat_dim, num_classes)
    
    def forward(self, backbone_features, det_conf):
        # backbone_features and det_conf are detached (no_grad)
        x = torch.cat([det_conf, backbone_features], dim=1)
        return self.classifier(x)
```

Train for 10 epochs with backbone frozen at epoch_18 weights. If top1 < 0.05, the backbone encodes no action-discriminative signal -- TCN+ViT cannot help.

**Change 4.2: Task-level curriculum schedule**

In `train.py`, implement progressive task unfreezing:
```python
# Epoch 0-2: Detection + Pose only (highest signal)
# Epoch 2-4: Add HeadPose
# Epoch 4-6: Add PSR
# Epoch 6+: Add Activity (with backbone stop_grad from Strategy 1)

stage_config = {
    0: ['detection', 'pose'],
    2: ['detection', 'pose', 'head_pose'],
    4: ['detection', 'pose', 'head_pose', 'psr'],
    6: ['detection', 'pose', 'head_pose', 'psr', 'activity'],
}
```

**Change 4.3: D-Train Phase 3 implementation**

After initial joint training (epochs 0-25), freeze backbone and fine-tune each head separately for 5 epochs:
```python
# Phase 3: per-head fine-tuning
for head_name in ['detection', 'pose', 'head_pose', 'psr', 'activity']:
    freeze_backbone()
    unfreeze_head(head_name)
    freeze_all_other_heads([head_name])
    train_for_epochs(5, head_name)
```

### Expected Impact
- Linear probe diagnosis: determines whether activity bottleneck is backbone or head (0 GPU-days wasted if backbone is the issue)
- Task curriculum: prevents activity collapse cascade (activity starts after backbone is stable)
- D-Train Phase 3: +5-10% per head from clean gradient signal

### Risk Assessment
- **LOW risk.** The linear probe and null-model diagnostics are cheap (1 day total) and informative regardless of outcome. D-Train Phase 3 is more expensive (25 head-epochs = ~1 week) but eliminates gradient conflict entirely.

### Order of Operations
**Run diagnostics in parallel with Strategy 1** -- linear probe (1 day) and PSR activation diagnostic (1 hour) inform whether to invest in curriculum training or D-Train Phase 3.

---

## Strategy 5: Knowledge Distillation (YOLOv8m -> ConvNeXt)

### Current State
Separate YOLOv8m (d1r) reaches mAP50=0.995 on detection. Multi-task ConvNeXt reaches mAP50=0.358. The 64% gap is a product of multi-task interference. Distillation can close this gap by transferring YOLOv8m's detection knowledge directly.

### Literature Summary

| Method | Mechanism | Cross-Family? | Memory | Gain |
|--------|-----------|---------------|--------|------|
| **Ultralytics built-in** | `distill_model` parameter in YOLO trainer | SAME family only | +1 model | 0 for us |
| **Cross-architecture distillation** | MSE on feature maps + KL on logits | YES | +1 model | +10-30% mAP |
| **FGD** (Focal & Global Distillation) | Attention maps + global relation | YES | +1 model | +5-15% |
| **LD** (Localization Distillation) | Bbox regression distribution transfer | DET only | +1 model | +3-5% |
| **CWD** (Channel-Wise Distillation) | Per-channel activation alignment | YES | +1 model | +3-8% |
| **MGD** (Masked Generative Distillation) | Random-masked feature reconstruction | YES | +2 models | +4-10% |

### Recommendation: Cross-architecture distillation with KL + CWD

Since Ultralytics `distill_model` requires same-family (YOLO), we need custom distillation. The combination of:
1. KL divergence on detection logits (YOLOv8m soft labels -> ConvNeXt detection head)
2. CWD (channel-wise activation matching on backbone C3/C4/C5 outputs)

is the most cost-effective approach for 3 GPU-days of training.

### Proposed Changes

**Change 5.1: YOLOv8m teacher wrapper**

New file: `src/training/distillation.py`:

```python
class YOLOv8mTeacher(nn.Module):
    """Wrapper around Ultralytics YOLOv8m for distillation."""
    def __init__(self, weights_path, device):
        super().__init__()
        from ultralytics import YOLO
        self.model = YOLO(weights_path)
        self.device = device
        
    @torch.no_grad()
    def get_soft_labels(self, images):
        """
        Returns:
            cls_logits: [B, 8400, 24] classification logits per anchor
            bbox_preds: [B, 8400, 4] box predictions
            features: {'c3': [B,C,H,W], 'c4': [B,C,H,W], 'c5': [B,C,H,W]}
        """
        results = self.model(images, verbose=False)
        # Extract intermediate features + outputs from the YOLO model
        ...
        return cls_logits, bbox_preds, features
```

**Change 5.2: Distillation loss**

```python
class DistillationLoss(nn.Module):
    def __init__(self, temperature=4.0, alpha_kl=0.7, alpha_cwd=0.3):
        super().__init__()
        self.T = temperature
        self.alpha_kl = alpha_kl
        self.alpha_cwd = alpha_cwd
        
    def forward(self, student_outputs, teacher_outputs):
        # KL divergence on softened logits
        s_logits = F.log_softmax(student_outputs['det_logits'] / self.T, dim=-1)
        t_probs = F.softmax(teacher_outputs['cls_logits'] / self.T, dim=-1)
        kl_loss = F.kl_div(s_logits, t_probs, reduction='batchmean') * (self.T ** 2)
        
        # Channel-wise distillation on backbone features
        cwd_loss = 0.0
        for layer in ['c3', 'c4', 'c5']:
            s_feat = student_outputs['backbone_features'][layer]
            t_feat = teacher_outputs['features'][layer]
            # Normalize per-channel and compute MSE
            s_norm = F.normalize(s_feat.flatten(2).mean(2), dim=1)
            t_norm = F.normalize(t_feat.flatten(2).mean(2), dim=1)
            cwd_loss += F.mse_loss(s_norm, t_norm)
        
        return self.alpha_kl * kl_loss + self.alpha_cwd * cwd_loss
```

**Change 5.3: Schedule**

Phase 1: Train with distillation only (no other heads) for 5 epochs.
Phase 2: Joint training with distillation + all 5 heads (distillation weight decays 1.0 -> 0.2 over 10 epochs).
Phase 3: Fine-tune without distillation for 3 epochs (avoids overfitting to teacher biases).

### Expected Impact
- Detection mAP: 0.358 -> 0.50-0.60 in Phase 1, stabilizing at ~0.55-0.65 in Phase 3
- No direct impact on Activity/PSR/Pose/HeadPose (distillation targets detection only)

### Risk Assessment
- **MEDIUM risk.** Cross-architecture distillation is finicky. The YOLOv8m backbone feature dimensions may not align with ConvNeXt-Tiny. Feature map alignment requires careful layer matching. If CWD alignment fails, fall back to logit-only distillation (KL).
- Training overhead: +1 model in GPU memory (+~25M params for YOLOv8m inference). With BATCH_SIZE=2 this may trigger OOM. Mitigate by running teacher in eval mode with torch.no_grad() and caching features.
- The master plan (130) already estimates this at P2.1 priority with 3 days effort and 0.358 -> ~0.65 impact. Those estimates hold.

### Order of Operations
**FOURTH** -- this is a major training investment (5 days compute on RTX 5060 Ti). Run only after Strategies 1-3 have been validated and the activity bottleneck is understood. The distillation benefit is surgical (detection only) and doesn't fix the multi-task gradient problem directly.

---

## Strategy 6: Curriculum Learning (Easy -> Hard Classes)

### Current State
No curriculum learning. All activity classes are treated equally from epoch 0. The 75 activity classes have extreme long-tail distribution with label 37 permanently absent.

### Literature Summary

| Method | Mechanism | Fit |
|--------|-----------|-----|
| **CLIS** (Label-hierarchy Curriculum) | Group classes by semantic similarity using LLM/WN, train easy groups first | GOOD for 75 activity classes -- groups like "pick", "place", "align" map to semantic hierarchies |
| **CUDA** (Curriculum by Augmentation) | Increase augmentation strength as training progresses -- easy epochs have light augmentation, hard epochs have heavy | COMPLEMENTARY -- can be stacked with CLIS |
| **Anti-Curriculum** | Train on hardest examples first, then easier | COUNTER-INDICATED -- long-tail needs easy-first |
| **DCL** (Dynamic Curriculum) | Sample difficulty on the fly based on loss values | OVERHEAD -- requires per-sample tracking |

### Recommendation: Label-hierarchy curriculum (CLIS)

Group the 75 activity classes into 4-5 semantic tiers using the Ikea ASM Assembly101-style action hierarchy. Easy tier = locomotion/navigation actions (walk, stand, reach). Medium tier = single-object manipulations (pick, place, slide). Hard tier = multi-object coordination (align_two_boards, attach_screw, insert_peg). Rare tier = compound actions with < 10 samples.

### Proposed Changes

**Change 6.1: Define semantic tier mapping**

```python
# src/data/activity_tiers.py
TIER_MAP = {
    # Tier 0 (easy): locomotion, idle -- high frequency, short duration
    0: 0, 1: 0, 2: 0, 3: 0, 4: 0,  # NA + navigation
    # Tier 1 (medium): single-object -- moderate frequency
    10: 1, 11: 1, 12: 1, 15: 1, 20: 1,  # pick/place actions
    # Tier 2 (hard): multi-object -- low frequency
    30: 2, 31: 2, 35: 2, 40: 2,  # alignment/fitting
    # Tier 3 (rare): compound or < 10 samples
    50: 3, 51: 3, 55: 3, 60: 3,  # complex assemblies
    # Default for unknown IDs
    ...
}

TIER_EPOCHS = {
    0: 5,   # Tier 0 only for epochs 0-4
    1: 10,  # Tiers 0-1 for epochs 5-9
    2: 15,  # Tiers 0-2 for epochs 10-14
    3: 15,  # Tiers 0-3 for epochs 15+
}
```

**Change 6.2: Tier-gated loss**

```python
def activity_loss_with_tiers(logits, targets, epoch, tier_map, tier_epochs):
    current_tier = 0
    for tier, end_epoch in tier_epochs.items():
        if epoch >= end_epoch:
            current_tier = tier
    
    # Mask: only compute loss on samples belonging to current or lower tier
    valid_mask = torch.tensor([
        tier_map.get(t.item(), 0) <= current_tier
        for t in targets
    ], device=targets.device)
    
    if valid_mask.any():
        return F.cross_entropy(
            logits[valid_mask], targets[valid_mask],
            label_smoothing=0.1
        )
    else:
        return torch.tensor(0.0, device=logits.device)
```

**Change 6.3: Combine with CUDA augmentation curriculum**

```python
# Increasing augmentation strength by tier
AUG_STRENGTH_PER_TIER = {
    0: {'scale': (0.7, 1.3), 'brightness': 0.1},
    1: {'scale': (0.5, 1.5), 'brightness': 0.3},
    2: {'scale': (0.3, 1.7), 'brightness': 0.5},
    3: {'scale': (0.2, 1.8), 'brightness': 0.7},
}
```

### Expected Impact
- Activity top1: +1-3% (easier classes converge faster, backbone features become more general before tackling hard classes)
- No negative impact on other heads (curriculum only affects activity loss masking)

### Risk Assessment
- **LOW risk.** Tier mapping is ~100 lines of annotation. If tier boundaries are wrong, revert to uniform training. The semantic grouping is interpretable and debuggable.
- Potential issue: if Tier 0 classes are too easy (NA/walk), the model may overfit to them and never adapt to harder classes. Mitigate by ensuring Tier 0 includes a representative mix of motion types, not just static frames.

### Order of Operations
**FIFTH** -- low priority. This is a "nice to have" that complements Strategy 2 (LORT + CurB). Run after the loss function upgrades are validated.

---

## Strategy 7: Pseudo-Labeling (Credible Teacher via d1r YOLOv8m)

### Current State
The d1r YOLOv8m achieves mAP50=0.995 on detection. It can generate high-quality pseudo-labels on unlabeled frames. Activity classes have extreme sparsity (some < 10 samples). Pseudo-labeling can add training signal for rare classes.

### Literature Summary

| Method | Mechanism | Fit |
|--------|-----------|-----|
| **Credible Teacher** | Flexible pseudo-labels: high-confidence -> hard labels, medium-confidence -> soft labels, low-confidence -> ignored | BEST -- handles detection+classification simultaneously |
| **FixMatch** | Weak augmentation -> pseudo-label, strong augmentation -> train | Classification-only; doesn't handle detection |
| **Unbiased Teacher** | EMA teacher + focal loss for class imbalance in SSOD | Good for detection; combines with Credible Teacher |
| **Soft Teacher** | Box-jitter + classification score filtering for SSOD | State-of-art SSOD; more complex than Credible Teacher |

### Recommendation: Credible Teacher for detection + simple threshold for activity

**Rationale:** Credible Teacher's upper/lower threshold approach is directly applicable. Upper threshold: hard labels (detection boxes + activity classes). Lower threshold: soft labels used as distillation targets. Below lower: ignored.

### Proposed Changes

**Change 7.1: Credible Teacher pseudo-labeling pipeline**

New file: `src/training/pseudo_labeling.py`:

```python
class CredibleTeacher:
    """
    Generates pseudo-labels on unlabeled frames using d1r YOLOv8m as teacher.
    Thresholds:
        upper (0.7): hard pseudo-labels, treated as ground truth
        middle [0.3, 0.7): soft pseudo-labels, used as distillation targets
        lower (<0.3): ignored
    """
    def __init__(self, teacher_path, upper_thresh=0.7, lower_thresh=0.3):
        self.teacher = YOLO(teacher_path)
        self.upper = upper_thresh
        self.lower = lower_thresh
    
    @torch.no_grad()
    def generate(self, images):
        results = self.teacher(images, verbose=False)
        hard_labels = []
        soft_labels = []
        
        for r in results:
            # Detection boxes
            if r.boxes is not None:
                scores = r.boxes.conf
                upper_mask = scores >= self.upper
                mid_mask = (scores >= self.lower) & (scores < self.upper)
                
                hard_labels.append({
                    'boxes': r.boxes.xyxy[upper_mask],
                    'cls': r.boxes.cls[upper_mask],
                })
                soft_labels.append({
                    'boxes': r.boxes.xyxy[mid_mask],
                    'cls': r.boxes.cls[mid_mask],
                    'conf': scores[mid_mask],  # soft targets
                })
        
        return hard_labels, soft_labels
```

**Change 7.2: Activity pseudo-label projection**

The YOLOv8m detects 24 object classes, but activity has 75 action classes. To generate activity pseudo-labels:
1. Use detected object presence as weak signal (e.g., "screwdriver detected" correlates with "use_screwdriver" activity)
2. Use temporal proximity to known activity frames (50% of dataset is labeled)
3. Use the activity head's own predictions on high-confidence frames as self-training

```python
# Activity self-training with confidence threshold
act_conf, act_pred = torch.max(F.softmax(act_logits, dim=1), dim=1)
confident_mask = act_conf > 0.8  # Only trust high-confidence predictions
# Add confident frames to training set for next epoch
```

**Change 7.3: Training loop integration**

```python
# Mix labeled and pseudo-labeled batches 50/50
for batch in data_loader:
    labeled_loss = criterion(model(batch['labeled']), batch['labels'])
    
    with torch.no_grad():
        hard_pl, soft_pl = credible_teacher.generate(batch['unlabeled'])
    
    # Hard pseudo-labels: treat as ground truth (with loss weight 0.5)
    hard_loss = 0.5 * criterion(model_outputs, hard_pl)
    
    # Soft pseudo-labels: distillation target (KL-div with temperature)
    soft_loss = distillation_loss(model_outputs, soft_pl)
    
    total = labeled_loss + hard_loss + 0.3 * soft_loss
```

### Expected Impact
- Activity top1: +2-5% on rare classes (< 50 samples) from expanded training signal
- Detection mAP: +1-2% (hard pseudo-labels add box regression signal)
- No direct impact on Pose/HeadPose/PSR

### Risk Assessment
- **HIGH risk.** Pseudo-labeling multiplies dataset complexity (need unlabeled split, need teacher inference pipeline, need quality filtering).
- **Label noise:** If teacher is wrong (YOLOv8m has ~0.5% error at confidence > 0.7), those errors propagate to student. Use EMA teacher update (like Unbiased Teacher) to mitigate.
- **Memory:** Teacher inference adds GPU memory for a second model. Run teacher on CPU or cache predictions to disk.
- **Dependency:** Requires d1r YOLOv8m to be available and compatible. If the d1r checkpoint path changes, the pipeline breaks.
- The master plan does NOT include pseudo-labeling. This is a stretch goal at best.

### Order of Operations
**SIXTH** -- last priority. Run only if: (a) all other strategies have been attempted, (b) activity rare-class performance is still below 0.05 per-class accuracy, and (c) d1r YOLOv8m is available and stable. This is a 1-2 week project on its own.

---

## Appendix A: Implementation Order (Consolidated)

```
WEEK 1: Fix confirmed bugs + diagnose
  Day 1:   Strategy 1 -- Fix NaN guard, stop-grad, GIoU normalization (2hr code + 1hr review)
  Day 2:   Strategy 1 -- Kill staged freezing, align ACTIVITY_LOSS_WEIGHT/log_var (1hr code)
  Day 2-3: Strategy 1 -- KENDALL_FIXED_WEIGHTS ablation (1 day training)
  Day 3:   Strategy 4 diagnostic -- PSR activation diagnostic (1hr) + activity linear probe (1 day)
  Day 4:   Strategy 4 diagnostic -- Null-model POS baseline (1hr) + transition-F1 (1 day)

WEEK 2: Loss function upgrades + curriculum
  Day 1-2: Strategy 2 -- Implement LORT loss (2 days)
  Day 3:   Strategy 2 -- Implement CurB loss (1 day)
  Day 3-5: Strategy 2 -- Train with LORT+CurB hybrid (10 epochs = 2-3 days)
  Day 5:   Strategy 6 -- Define activity tier mapping (1 day, parallel with training)

WEEK 3: Gradient surgery
  Day 1-2: Strategy 3 -- Implement FAMO (2 days)
  Day 2-3: Strategy 3 -- 5-epoch FAMO ablation (1 day)
  Day 4-5: Strategy 3 -- Kendall vs FAMO vs hybrid comparison (2 days analysis)

WEEK 4: Knowledge distillation (IF activity bottleneck is backbone)
  Day 1-2: Strategy 5 -- YOLOv8m teacher wrapper + distillation loss (2 days)
  Day 3-5: Strategy 5 -- Phase 1 distillation training (3 days)
  Day 6-7: Strategy 5 -- Phase 2 joint training (2 days)

WEEK 5: Curriculum + wrap-up
  Day 1-3: Strategy 6 -- Tiered curriculum training (3 days)
  Day 4-5: Strategy 6 -- CUDA augmentation curriculum (2 days)

WEEK 6+: Pseudo-labeling (stretch goal)
  Day 1-3: Strategy 7 -- Credible Teacher pipeline (3 days)
  Day 4-7: Strategy 7 -- Pseudo-labeling training + evaluation (4 days)
```

---

## Appendix B: What NOT to Do

1. **Do not implement BBN or RIDE.** They double/triple backbone memory and are incompatible with 5-head multi-task training at BATCH_SIZE=2.
2. **Do not implement PCGrad.** NYUv2 results show poor performance for detection+classification task combos.
3. **Do not use Ultralytics built-in distillation.** It requires same-family (YOLO) architecture.
4. **Do not run expensive TCN+ViT activity head before the linear probe clears.** If frozen backbone features give 0.03 accuracy, TCN+ViT is dead on arrival.
5. **Do not claim Kendall automatically balances tasks.** The config carries 5 manual guards on the "automatic" mechanism.
6. **Do not use POS as a headline metric.** It's structurally inflated by fill-forward prior.
7. **Do not mix numbers from different checkpoint lineages.** Adopt a freeze protocol (file 132, Q10).

---

## Appendix C: Dependency Graph

```
Strategy 1 (bug fixes)
  |
  +---> Strategy 4 diagnostic (linear probe, transition F1)
  |       |
  |       +---> [IF probe > 0.05] Strategy 5 (knowledge distillation)
  |       +---> [IF probe <= 0.05] Backbone is bottleneck -- prioritize Strategy 5
  |
  +---> Strategy 2 (LORT + CurB)
  |       |
  |       +---> Strategy 6 (curriculum -- complements loss upgrade)
  |
  +---> Strategy 3 (FAMO)  [can run in parallel with Strategy 2]
  |
  +---> Strategy 7 (pseudo-labeling)  [only if all above are exhausted]
```
