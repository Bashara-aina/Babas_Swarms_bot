---
title: Cutmix Yun 2019
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- research
created: '2026-04-14'
updated: '2026-04-14'
summary: CutMix cuts and pastes rectangular patches between training images, mixing
  labels proportionally to patch area. Unlike Cutout (which removes information),
  CutMix uses all input pixels for training....
wikilinks: []
confidence: medium
source: research
---

# Quick Summary

CutMix cuts and pastes rectangular patches between training images, mixing labels proportionally to patch area. Unlike Cutout (which removes information), CutMix uses all input pixels for training. **⚠️ NOT compatible with pose estimation tasks.**

## Core Contribution

Combines benefits of Cutout (regularization, localization) with Mixup (efficient use of pixels), while avoiding their drawbacks.

---

# Abstract (from paper)

> Regional dropout strategies have been proposed to enhance the performance of convolutional neural network classifiers. They have proved to be effective for guiding the model to attend on less discriminative parts of objects (e.g. leg as opposed to head of a person)... We therefore propose the CutMix augmentation strategy: patches are cut and pasted among training images where the ground truth labels are also mixed proportionally to the area of the patches...

---

# CutMix vs Related Techniques

| Method | Operation | Label Handling | Pixel Efficiency |
|--------|-----------|---------------|-----------------|
| Cutout | Remove region (fill black/random) | Hard label preserved | ❌ 25-50% removed |
| Mixup | Linear interpolation of images | Soft label interpolation | ✅ 100% |
| CutMix | Cut-paste rectangular patches | Soft label interpolation | ✅ 100% |
| CutMix-regular | Cut-paste + auxiliary loss | Additional regularization | ✅ 100% |

## CutMix Algorithm

```python
def cutmix(batch_images, batch_labels, α=1.0):
    """
    Args:
        batch_images: [B, C, H, W]
        batch_labels: [B, num_classes] (one-hot or soft labels)
        α: Beta distribution parameter
    Returns:
        mixed_images, mixed_labels
    """
    B, C, H, W = batch_images.shape
    
    # Sample mixing ratio from Beta distribution
    λ = np.random.beta(α, α)
    
    # Sample bounding box coordinates
    cx = np.random.randint(0, W)
    cy = np.random.randint(0, H)
    cw = int(W * np.sqrt(1 - λ))
    ch = int(H * np.sqrt(1 - λ))
    
    # Box coordinates (ensures valid bounds)
    x1 = np.clip(cx - cw // 2, 0, W)
    y1 = np.clip(cy - ch // 2, 0, H)
    x2 = np.clip(cx + cw // 2, 0, W)
    y2 = np.clip(cy + ch // 2, 0, H)
    
    # Create mixed image
    mixed_images = batch_images.clone()
    mixed_images[:, :, y1:y2, x1:x2] = batch_images.flip(0)[:, :, y1:y2, x1:x2]
    
    # Adjust lambda based on actual box area
    λ_adj = 1 - (x2 - x1) * (y2 - y1) / (W * H)
    
    # Mix labels proportionally
    mixed_labels = λ_adj * batch_labels + (1 - λ_adj) * batch_labels.flip(0)
    
    return mixed_images, mixed_labels
```

---

# Why CutMix Works Better

## Forces Classifier to Use Less Discriminative Regions

Standard augmentation: model can learn to classify based on head/face alone
CutMix: region information is always mixed → must use whole object

## Improves Localization

CutMix trained models show better object localization (top-1 bounding box on ImageNet).

---

# RTX 3060 Relevance

## ⚠️ CRITICAL: CutMix NOT Compatible with Pose Estimation

**WorkerNet trains pose + action jointly. CutMix DESTROYS spatial correspondence.**

**Problem**:
- Pose heatmaps encode keypoint locations
- CutMix randomly swaps image regions
- Keypoint locations no longer correspond to the correct anatomical position
- Training becomes noise

**Evidence**: CutMix paper focuses on image classification ONLY. No pose estimation experiments.

## WorkerNet Decision

**Do NOT use CutMix for WorkerNet training.**

Use only:
- Standard augmentation (random flip, crop, color jitter)
- RandAugment (092) with restrictions (no rotations >30°)
- See warning in 092 for details

---

# Results from Paper

| Method | CIFAR-10 | CIFAR-100 | ImageNet Top-1 |
|--------|----------|-----------|----------------|
| Baseline (ResNet-18) | 95.6% | 77.8% | 69.6% |
| Cutout | 96.1% | 77.9% | 70.0% |
| Mixup | 96.3% | 78.4% | 71.6% |
| CutMix | **97.2%** | **79.6%** | **73.1%** |

CutMix outperforms other regional dropout methods.

---

# Limitations

1. **Spatial semantics**: Not suitable for tasks with spatial structure (pose, detection)
2. **Rectangular bias**: Only rectangular cutouts
3. **Label mixing**: Requires care in multi-task setting where tasks have different label types
4. **Hyperparameter α**: Needs tuning (α=1.0 typical)

---

# Citation

```bibtex
@article{yun2019cutmix,
  title={CutMix: Regularization Strategy to Train Strong Classifiers with Localizable Features},
  author={Yun, Sangdoo and Han, Dongyoon and Oh, Seong Joon and Chun, Sanghyuk and Choe, Junsuk and Yoo, Youngjoon},
  journal={arXiv:1905.04899},
  year={2019},
  note={ICCV 2019}
}
```

---

# POPW-PROTOCOL Research Wiki — Tier Index

**Part of**: Training Optimization for RTX 3060 (Tier 9)  
**Related**: 090 Bag of Tricks | 092 RandAugment

**⚠️ CRITICAL**: CutMix is NOT compatible with pose estimation — DO NOT USE for WorkerNet

**Owner**: Bashara | SIT Thesis | 2026
