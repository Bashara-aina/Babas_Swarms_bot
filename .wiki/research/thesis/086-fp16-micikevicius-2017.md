---
title: "086 — Mixed Precision Training (Micikevicius et al., 2017)"
subtitle: "FP16 Training for Deep Neural Networks"
category: training-optimization
subcategory: memory-optimization
tags: [fp16, mixed-precision, gradient-scaling, nvidia, memory-efficient]
authors: ["Paulius Micikevicius", "Sharan Narang", "Jonah Alben", "Gregory Diamos", "Erich Elsen", "David Garcia", "Boris Ginsburg", "Michael Houston", "Oleksii Kuchaiev", "Ganesh Venkatesh", "Hao Wu"]
venue: "ICLR 2018"
arXiv: "1710.03740"
date: 2017-10-10
cited: "~5000+"
implementation: "NVIDIA APEX, PyTorch native AMP"
status: verified
tier: 9
hardware: "RTX 3060 12GB VRAM"
---

# Quick Summary

Mixed Precision Training enables training deep neural networks with **half-precision (FP16)** floating point, nearly **halving memory consumption** while maintaining accuracy. Essential for RTX 3060 12GB VRAM.

## Core Contribution

Two techniques handle FP16's limited numerical range:
1. **Master weights in FP32**: Maintain FP32 copy accumulating gradients, round to FP16 for forward/backward
2. **Loss scaling**: Scale loss appropriately to handle gradient underflow in FP16

---

# Abstract (from paper)

> Deep neural networks have enabled progress in a wide variety of applications. Growing the size of the neural network typically results in improved accuracy. As model sizes grow, the memory and compute requirements for training these models also increases. We introduce a technique to train deep neural networks using half precision floating point numbers. In our technique, weights, activations and gradients are stored in IEEE half-precision format...

---

# Key Technical Details

## Problem
- FP16 has limited range: ~6×10⁻⁵ to 65504 vs FP32's ~1.4×10⁻⁴⁵ to 3.4×10³⁸
- Gradients often underflow to zero in FP16 during training

## Solution Architecture

```
Forward/Backward: FP16 weights, activations, gradients
Optimizer step: FP32 master weights + gradients
Each iteration:
  1. Convert FP32 weights → FP16
  2. Forward pass (FP16)
  3. Backward pass (FP16)
  4. Convert gradients to FP32
  5. Update FP32 master weights (with loss scaling)
  6. Round FP32 weights → FP16 for next iteration
```

## Loss Scaling Algorithm

```python
# Automatic loss scaling (simplified from paper)
scale = 2**15  # initial scale
while True:
    loss_scaled = loss * scale
    loss_scaled.backward()
    if grads_finite():
        break  # OK, gradients valid
    scale /= 2  # reduce scale
    # Zero gradients and retry
```

---

# RTX 3060 Relevance

## Why This Matters for WorkerNet
- WorkerNet (ResNet-50 + FPN + FiLM) is memory-intensive
- Multi-task learning with pose + action heads compounds memory pressure
- FP16 effectively doubles available batch size

## ⚠️ CRITICAL: log_var Underflow Risk

WorkerNet uses **Kendall homoscedastic uncertainty** for multi-task weighting. The `log_var` parameters (one per task) are trained in FP16.

**Problem**: `log_var` values can become very negative (e.g., -10, -20) during training, which underflows to **zero in FP16** (minimum representable is ~6×10⁻⁵).

**Consequences**:
- Task weights freeze to uniform (no multi-task benefit)
- Training effectively becomes single-task on dominant task
- Model fails to learn balanced representations

**Solution**:
```python
# Keep log_var in FP32 for numerical stability
self.log_vars = nn.Parameter(torch.zeros(2, dtype=torch.float32))  # NOT float16
```

---

# Implementation in WorkerNet

## PyTorch Native (Preferred)

```python
# train.py — use PyTorch native AMP
from torch.cuda.amp import autocast, GradScaler

scaler = GradScaler()
model = build_worker_net().cuda()

for epoch in range(num_epochs):
    for batch in dataloader:
        with autocast():
            outputs = model(images)
            loss = multi_task_loss(outputs, targets)
        
        scaler.scale(loss).backward()
        scaler.step(optimizer)
        scaler.update()
```

## WorkerNet-Specific Notes

- Backbone (ResNet-50): FP16 OK
- FPN + FiLM: FP16 OK  
- Pose head output: heatmaps are FP16 OK
- **log_var parameters: MUST stay FP32**
- **Action head output: FP16 OK**

---

# Results from Paper

| Model | Memory Reduction | Speedup |
|-------|-----------------|---------|
| ResNet-50 (ILSVRC) | ~2× | ~1.5-1.8× |
| DeepSpeech 2 | ~2× | ~1.4× |
| GNMT (100M params) | ~2× | ~1.3× |

Accuracy: Within 0.5% of FP32 across all tested models.

---

# Limitations

1. **Hardware dependency**: Requires Tensor Cores (Volta+) for best speedup
2. **Not universal**: Some layers may need FP32 (e.g., softmax, batch norm in some cases)
3. **Loss scaling tuning**: May need adjustment per architecture
4. **Mixed-task interference**: log_var underflow issue (see above)

---

# Citation

```bibtex
@article{micikevicius2017mixed,
  title={Mixed precision training},
  author={Micikevicius, Paulius and others},
  journal={arXiv:1710.03740},
  year={2017}
}
```

---

# POPW-PROTOCOL Research Wiki — Tier Index

**Part of**: Training Optimization for RTX 3060 (Tier 9)  
**Related**: 087 Gradient Checkpointing | 088 AdamW | 089 SGDR

**Owner**: Bashara | SIT Thesis | 2026
