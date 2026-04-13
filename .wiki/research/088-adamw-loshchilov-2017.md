---
title: "088 — Decoupled Weight Decay Regularization (AdamW, Loshchilov & Hutter, 2017)"
subtitle: "Fixing Adam's Weight Decay Implementation for Better Generalization"
category: training-optimization
subcategory: optimizer
tags: [adamw, weight-decay, l2-regularization, optimization, generalization]
authors: ["Ilya Loshchilov", "Frank Hutter"]
venue: "ICLR 2019"
arXiv: "1711.05101"
date: 2017-11-14
cited: "~4000+"
implementation: ["PyTorch optim.AdamW", "TensorFlow"]
status: verified
tier: 9
hardware: "RTX 3060 12GB VRAM"
---

# Quick Summary

AdamW decouples weight decay from the optimization step, fixing a fundamental flaw where L2 regularization and weight decay behave differently in adaptive gradient methods. Improves Adam's generalization to match SGD+momentum on image classification.

## Core Contribution

L2 regularization ≠ weight decay in adaptive gradient algorithms (Adam, RMSprop, etc.). AdamW properly decouples them, substantially improving Adam's generalization.

---

# Abstract (from paper)

> L2 regularization and weight decay regularization are equivalent for standard stochastic gradient descent (when rescaled by the learning rate), but as we demonstrate this is NOT the case for adaptive gradient algorithms, such as Adam. While common implementations of these algorithms employ L2 regularization (often calling it "weight decay" in what may be misleading), we propose a simple modification to recover the original formulation of weight decay regularization by decoupling the weight decay from the optimization steps taken w.r.t. the loss function...

---

# The Problem

## Standard Adam with "Weight Decay"

```python
# Common (incorrect) implementation in many frameworks
# This is actually L2 regularization, NOT weight decay
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-4)

# What actually happens:
# gradient += weight_decay * parameters  # L2 term added to gradient
# This interacts incorrectly with adaptive gradient scaling
```

## Why This Matters

In SGD:
```
SGD update: w = w - lr * (gradient + weight_decay * w)
           = w - lr*gradient - lr*weight_decay*w
           = (1 - lr*weight_decay)*w - lr*gradient
```
This is true weight decay — uniformly shrinks all weights.

In Adam:
```
Adam update: uses EMA of gradients and squared gradients
             L2 term gets scaled by EMA(v)/EMA(v) ratios
             → weight decay effect varies per-parameter
             → effective regularization is inconsistent
```

---

# The Solution

## Decoupled Weight Decay

```python
# Correct AdamW implementation (from paper)
def adamw_update(params, grad, exp_avg, exp_avg_sq, lr, weight_decay, beta1=0.9, beta2=0.999):
    # Decouple weight decay from optimization step
    # Weight decay applied AFTER gradient-based update
    
    # Standard Adam update for gradient-based part
    bias_correction1 = 1 - beta1 ** t
    bias_correction2 = 1 - beta2 ** (t ** 0.5)
    
    update = exp_avg / (exp_avg_sq**0.5 + eps) / bias_correction2 * bias_correction1
    # NOTE: NO weight_decay in the gradient-based update
    
    # Decoupled weight decay step
    params = params * (1 - lr * weight_decay)  # Applied separately
    
    params = params - lr * update
    
    return params
```

## Key Insight

> Weight decay should uniformly shrink all parameters, independent of the gradient scaling.

AdamW applies weight decay as: `w = w * (1 - lr * wd)` — purely multiplicative, independent of gradient history.

---

# PyTorch Implementation

```python
# Simple: use PyTorch's AdamW
from torch.optim import AdamW

optimizer = AdamW(
    model.parameters(),
    lr=1e-3,
    weight_decay=0.01,  # Now correctly decoupled
    betas=(0.9, 0.999)
)

# For WorkerNet: exclude log_vars from weight decay if needed
optimizer = AdamW(
    [
        {"params": model.backbone.parameters(), "weight_decay": 0.01},
        {"params": model.neck.parameters(), "weight_decay": 0.01},
        {"params": model.heads.parameters(), "weight_decay": 0.01},
        {"params": [model.log_vars], "weight_decay": 0.0},  # No decay on log_vars
    ],
    lr=1e-3
)
```

---

# RTX 3060 Relevance

## Why AdamW for WorkerNet

1. **Multi-task learning**: AdamW's better generalization helps balanced task learning
2. **Pose estimation**: Sensitive to overfitting; proper weight decay helps
3. **FiLM conditioning**: Parameters in FiLM layers benefit from uniform regularization

## Recommended Configuration

```python
# WorkerNet optimizer setup
optimizer = AdamW(
    [
        {"params": model.backbone.parameters(), "weight_decay": 0.01},
        {"params": model.neck.parameters(), "weight_decay": 0.01},
        {"params": model.heads.parameters(), "weight_decay": 0.01},
        {"params": model.log_vars, "weight_decay": 0.0},  # Keep log_vars in check
    ],
    lr=1e-3,
    betas=(0.9, 0.999),
    eps=1e-8
)

# Learning rate schedule: combine with cosine annealing (089)
scheduler = CosineAnnealingWarmRestarts(optimizer, T_0=10, T_mult=2)
```

---

# Results from Paper

| Optimizer | ImageNet Top-1 |
|-----------|---------------|
| Adam (standard) | 71.2% |
| SGD + momentum | 75.0% |
| AdamW | 74.6% |

AdamW closes the gap with SGD+momentum while maintaining Adam's faster convergence.

---

# Combining with Other Techniques

## AdamW + FP16 (086) + Gradient Checkpointing (087)

```python
# Full WorkerNet training setup
from torch.optim import AdamW
from torch.cuda.amp import autocast, GradScaler
from torch.utils.checkpoint import checkpoint_sequential

scaler = GradScaler()
optimizer = AdamW(model.parameters(), lr=1e-3, weight_decay=0.01)

for epoch in range(num_epochs):
    for batch in dataloader:
        with autocast():
            outputs = model(batch["image"])
            loss = multi_task_loss(outputs, batch)
        
        scaler.scale(loss).backward()
        scaler.step(optimizer)
        scaler.update()
        optimizer.zero_grad()
```

## AdamW + Cosine Annealing (089)

Standard pairing in modern training pipelines. See 089 for details.

---

# Limitations

1. **Hyperparameter sensitivity**: weight_decay and lr are now truly independent — tune both
2. **Learning rate warmup**: Still recommended for stability
3. **Not always best**: SGD+momentum may still outperform on some tasks

---

# Citation

```bibtex
@article{loshchilov2017decoupled,
  title={Decoupled Weight Decay Regularization},
  author={Loshchilov, Ilya and Hutter, Frank},
  journal={arXiv:1711.05101},
  year={2017},
  note={ICLR 2019}
}
```

---

# POPW-PROTOCOL Research Wiki — Tier Index

**Part of**: Training Optimization for RTX 3060 (Tier 9)  
**Related**: 086 Mixed Precision FP16 | 087 Gradient Checkpointing | 089 SGDR

**Owner**: Bashara | SIT Thesis | 2026
