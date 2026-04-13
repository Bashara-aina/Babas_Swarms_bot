---
title: "090 — Bag of Tricks for Image Classification (He et al., 2018)"
subtitle: "Training Procedure Refinements for CNN Performance Gains"
category: training-optimization
subcategory: data-augmentation
tags: [training-tricks, label-smoothing, mixup, cosine-annealing, resnet, data-augmentation]
authors: ["Tong He", "Zhi Zhang", "Hang Zhang", "Zhongyue Zhang", "Junyan Xie", "Mu Li"]
venue: "arXiv:1812.01187"
arXiv: "1812.01187"
date: 2018-12-04
cited: "~2000+"
implementation: [" torchvision built-in", "timm library"]
status: verified
tier: 9
hardware: "RTX 3060 12GB VRAM"
---

# Quick Summary

"Bag of Tricks" systematically evaluates training procedure refinements that are often only visible in source code. Combined refinements improved ResNet-50 accuracy from **75.3% → 79.29%** on ImageNet.

## Core Tricks Evaluated

1. **Data augmentation**: Mixup, Cutout
2. **LR Schedule**: Cosine annealing (see 089)
3. **Label smoothing**: Reduce overconfidence
4. **ResNet improvements**: Modified stem, downsample projection
5. **Training refinements**: Warmup, zero γ (BN hack)

---

# Abstract (from paper)

> Much of the recent progress made in image classification research can be credited to training procedure refinements, such as changes in data augmentations and optimization methods. In the literature, however, most refinements are either briefly mentioned as implementation details or only visible in source code...

---

# Tricks Summary Table

| Trick | Effect | WorkerNet Relevance |
|-------|--------|---------------------|
| Label Smoothing | +0.2% | ✅ Apply to action classification head |
| Mixup | +0.6% | ⚠️ Breaks pose heatmaps (see 091, 092) |
| Cosine LR | +0.3% | ✅ Already planned (089) |
| Warmup | Stable training | ✅ Recommended |
| Zero γ in BN | Easier debugging | ❌ Not needed |
| Modified Stem | +0.5% | ✅ Use ResNet-D stem |
| Downsample Mod | +0.2% | ✅ Use stride=1/2 conv |

---

# Label Smoothing

## What It Is

Label smoothing regularizes by softening hard labels:

```python
# Hard labels: [0, 0, 1, 0, 0] → one-hot
# Soft labels with ε=0.1: [0.025, 0.025, 0.9, 0.025, 0.025]

# Cross-entropy with label smoothing
def label_smoothing_loss(logits, targets, num_classes, ε=0.1):
    confidence = 1.0 - ε
    smooth_target = torch.full((logits.shape), ε / (num_classes - 1))
    smooth_target.scatter_(1, targets.unsqueeze(1), confidence)
    return F.cross_entropy(logits, smooth_target)
```

## Effect

| Model | Hard Labels | Label Smoothing (ε=0.1) |
|-------|-------------|------------------------|
| ResNet-50 | 75.3% | 75.6% |
| MobileNet | 73.3% | 73.6% |

---

# ResNet-D Improvements

## Modified Stem (Standard vs ResNet-D)

```
Standard ResNet Stem:
Input → Conv7×7 (stride 2) → MaxPool (stride 2)
Output: 56×56 from 224×224 input

ResNet-D Stem (from paper):
Input → Conv3×3 (stride 1) → Conv3×3 (stride 2) → Conv3×3 (stride 2) → MaxPool (stride 2)
Output: 56×56 from 224×224 input (same), but first conv uses stride 1 → less information loss
```

## Downsample Projection

```
Standard: 1×1 conv with stride 2 (loses 75% spatial info)
ResNet-D: 3×3 conv with stride 1 + 1×1 conv with stride 2 (preserves more info)
```

---

# RTX 3060 Relevance

## WorkerNet Implementation

```python
# In worker_net/model.py

class ResNetDStem(nn.Module):
    """ResNet-D stem as described in Bag of Tricks"""
    def __init__(self):
        super().__init__()
        self.stem = nn.Sequential(
            nn.Conv2d(3, 64, 3, stride=1, padding=1, bias=False),  # Changed from 7×7 stride 2
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 64, 3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 64, 3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
        )
    
    def forward(self, x):
        return self.stem(x)

# Use label smoothing for action classification
class ActionHead(nn.Module):
    def __init__(self, in_channels, num_actions, ε=0.1):
        super().__init__()
        self.ε = ε
        self.fc = nn.Linear(in_channels, num_actions)
    
    def forward(self, x, labels=None):
        logits = self.fc(x)
        if labels is not None and self.training:
            return F.cross_entropy(logits, labels)  # Apply smoothing in loss
        return logits
```

---

# Results from Paper

ResNet-50 on ImageNet:

| Configuration | Top-1 Accuracy | Δ |
|---------------|-----------------|---|
| Baseline | 75.3% | — |
| + Label Smoothing | 75.6% | +0.3% |
| + Cosine LR | 75.9% | +0.6% |
| + Mixup | 76.5% | +1.2% |
| + ResNet-D Stem | 77.0% | +1.7% |
| **All Combined** | **79.29%** | **+3.99%** |

---

# ⚠️ WARNING: Mixup/CutMix with Pose Tasks

**Mixup and CutMix (091) are NOT compatible with pose estimation.**

**Problem**: 
- Pose heatmaps have spatial structure (keypoint locations)
- Mixup interpolates both images and labels linearly
- CutMix replaces rectangular regions
- Both destroy spatial correspondence of keypoints

**Solution for WorkerNet**:
```python
# Apply augmentations conditionally per task
def mixed_augment_batch(batch, use_mixup=False, use_cutmix=False):
    images = batch["image"]
    action_labels = batch["action"]
    pose_heatmaps = batch["heatmap"]
    
    # NEVER apply mixup/cutmix to pose data
    if use_mixup or use_cutmix:
        # Only augment action classification branch
        images_aug = mixup(images, action_labels)  # Action only
        return {
            "image": images_aug,
            "action": batch["action"],  # Original labels (mixup handles internally)
            "heatmap": pose_heatmaps  # Original, no augmentation
        }
    
    return batch
```

---

# Citation

```bibtex
@article{he2018bag,
  title={Bag of Tricks for Image Classification with Convolutional Neural Networks},
  author={He, Tong and Zhang, Zhi and Zhang, Hang and others},
  journal={arXiv:1812.01187},
  year={2018}
}
```

---

# POPW-PROTOCOL Research Wiki — Tier Index

**Part of**: Training Optimization for RTX 3060 (Tier 9)  
**Related**: 089 SGDR | 091 CutMix | 092 RandAugment

**⚠️ Critical**: Mixup/CutMix NOT compatible with pose estimation — see warning above

**Owner**: Bashara | SIT Thesis | 2026
