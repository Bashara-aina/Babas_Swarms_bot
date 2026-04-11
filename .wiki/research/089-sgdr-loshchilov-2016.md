---
title: "089 — SGDR: Stochastic Gradient Descent with Warm Restarts (Loshchilov & Hutter, 2016)"
subtitle: "Cosine Annealing Learning Rate Scheduling with Periodic Restarts"
category: training-optimization
subcategory: learning-rate-schedule
tags: [cosine-annealing, warm-restarts, learning-rate, sgdr, scheduler, cyclic-lr]
authors: ["Ilya Loshchilov", "Frank Hutter"]
venue: "ICLR 2017"
arXiv: "1608.03983"
date: 2016-08-12
cited: "~3000+"
implementation: "PyTorch CosineAnnealingWarmRestarts", "TensorFlow"
status: verified
tier: 9
hardware: "RTX 3060 12GB VRAM"
---

# Quick Summary

SGDR combines cosine annealing with periodic warm restarts, enabling faster convergence and better final performance. The warm restarts help escape local minima and find flatter regions of the loss landscape.

## Core Contribution

Simple modification to cosine annealing: periodically "warm restart" the learning rate to allow the optimizer to escape local minima.

---

# Abstract (from paper)

> In this paper, we propose a simple warm restart technique for stochastic gradient descent to improve its anytime performance when training deep neural networks. The technique is based on periodically warming up the learning rate to explore the loss landscape more thoroughly...

---

# Key Technical Details

## Cosine Annealing (without restarts)

Standard cosine annealing decays learning rate as:

```
η_t = η_min + (η_max - η_min) * (1 + cos(π * t / T)) / 2
```

Where:
- `η_t`: learning rate at step t
- `T`: total number of steps
- `η_max`: maximum (initial) learning rate
- `η_min`: minimum learning rate (often 0)

## SGDR: With Warm Restarts

```python
# SGDR schedule (conceptual)
def sgdr_schedule(epoch, T_0, T_mult, eta_max, eta_min):
    """
    T_0: period of first cycle
    T_mult: period multiplication factor after each restart
    """
    t_cur = epoch
    T_i = T_0
    
    while t_cur >= T_i:
        t_cur -= T_i
        T_i *= T_mult  # Next cycle is longer
    
    # Cosine annealing within current cycle
    eta_t = eta_min + (eta_max - eta_min) * (1 + cos(π * t_cur / T_i)) / 2
    
    return eta_t
```

## Cycle Patterns

```
Example: T_0=10, T_mult=2, eta_max=1e-3, eta_min=1e-6

Cycle 1: epochs 0-9,  full cosine decay
Restart: back to eta_max at epoch 10
Cycle 2: epochs 10-29 (T_0*2=20), slower cosine decay
Restart: back to eta_max at epoch 30
Cycle 3: epochs 30-69 (T_0*4=40), even slower decay
...
```

---

# Why Warm Restarts Work

## Loss Landscape Exploration

| Without Restarts | With Warm Restarts |
|------------------|-------------------|
| Converges to nearest local minimum | Periodically escapes local minima |
| Stuck in sharp minima | Explores loss landscape more broadly |
| Poor generalization | Finds flatter minima (often better) |

## The "AnyTime" Property

SGDR naturally provides good solutions at any point during training — useful if you need to stop early.

---

# RTX 3060 Relevance

## WorkerNet LR Schedule

```python
# WorkerNet training schedule
from torch.optim.lr_scheduler import CosineAnnealingWarmRestarts

# Configuration for ~100 epoch training
T_0 = 20        # First cycle length (epochs)
T_mult = 2      # Multiply by 2 after each restart
eta_max = 1e-3  # Initial LR (for backbone)
eta_min = 1e-6  # Final LR

optimizer = AdamW(model.parameters(), lr=eta_max, weight_decay=0.01)
scheduler = CosineAnnealingWarmRestarts(
    optimizer, 
    T_0=T_0, 
    T_mult=T_mult,
    eta_min=eta_min
)

# Training loop
for epoch in range(num_epochs):
    scheduler.step()  # Updates LR
    train_epoch(model, dataloader, optimizer)
```

## Multi-LR Configuration

For WorkerNet, different components may benefit from different LR schedules:

```python
# Separate schedulers for backbone vs heads
optimizer = AdamW([
    {"params": model.backbone.parameters(), "lr": 1e-3},
    {"params": model.neck.parameters(), "lr": 1e-3},
    {"params": model.heads.parameters(), "lr": 5e-4},  # Smaller LR for heads
], weight_decay=0.01)

scheduler_backbone = CosineAnnealingWarmRestarts(
    optimizer, T_0=20, T_mult=2, eta_min=1e-6
)
```

---

# Results from Paper

CIFAR-10 with 110-layer ResNet:

| Schedule | Final Accuracy | Best Accuracy (anytime) |
|----------|---------------|------------------------|
| Fixed LR | 93.8% | 93.8% |
| Step decay | 94.4% | 94.4% |
| SGDR | 95.5% | 94.7% (at epoch 45) |

SGDR achieves best final accuracy and provides good intermediate solutions.

---

# Combining with Other Techniques

## Complete WorkerNet Training Recipe

```python
# 086 + 087 + 088 + 089 combined
from torch.optim import AdamW
from torch.cuda.amp import autocast, GradScaler
from torch.optim.lr_scheduler import CosineAnnealingWarmRestarts
from torch.utils.checkpoint import checkpoint_sequential

model = MemoryEfficientWorkerNet().cuda()
optimizer = AdamW(model.parameters(), lr=1e-3, weight_decay=0.01)
scheduler = CosineAnnealingWarmRestarts(optimizer, T_0=20, T_mult=2)
scaler = GradScaler()

for epoch in range(num_epochs):
    scheduler.step()
    for batch in dataloader:
        with autocast():
            outputs = model(batch["image"])
            loss = multi_task_loss(outputs, batch)
        
        scaler.scale(loss).backward()
        scaler.step(optimizer)
        scaler.update()
        optimizer.zero_grad()
```

---

# Limitations

1. **Cycle length tuning**: T_0 and T_mult are problem-dependent
2. **LR range**: eta_max and eta_min require tuning
3. **Cold start**: Learning rate jumps discontinuously at restarts
4. **May need warmup**: Very aggressive restarts can destabilize early training

---

# Citation

```bibtex
@article{loshchilov2016sgdr,
  title={SGDR: Stochastic Gradient Descent with Warm Restarts},
  author={Loshchilov, Ilya and Hutter, Frank},
  journal={arXiv:1608.03983},
  year={2016},
  note={ICLR 2017}
}
```

---

# POPW-PROTOCOL Research Wiki — Tier Index

**Part of**: Training Optimization for RTX 3060 (Tier 9)  
**Related**: 086 Mixed Precision FP16 | 087 Gradient Checkpointing | 088 AdamW

**Owner**: Bashara | SIT Thesis | 2026
