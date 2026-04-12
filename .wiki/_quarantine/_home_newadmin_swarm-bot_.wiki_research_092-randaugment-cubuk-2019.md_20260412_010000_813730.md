---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/research/092-randaugment-cubuk-2019.md",
  "reason": "daily_fast_scan: score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-12T01:00:00.813756"
}
---

---
title: "092 — RandAugment: Practical Automated Data Augmentation (Cubuk et al., 2019)"
subtitle: "Simplified Automated Augmentation That Works Out of the Box"
category: training-optimization
subcategory: data-augmentation
tags: [randaugment, automated-augmentation, data-augmentation, augmentation-policy, imagenet]
authors: ["Ekin D. Cubuk", "Barret Zoph", "Jonathon Shlens", "Quoc V. Le"]
venue: "NeurIPS 2020"
arXiv: "1909.13719"
date: 2019-09-30
cited: "~3000+"
implementation: "PyTorch RandAugment", "TensorFlow Augment", "timm"
status: verified
tier: 9
hardware: "RTX 3060 12GB VRAM"
---

# Quick Summary

RandAugment simplifies automated data augmentation by reducing the search space to just **2 hyperparameters** (N, M): N augmentations applied with magnitude M. Works out of the box, matching or surpassing all previous automated augmentation approaches.

## Core Contribution

Remove the separate search phase entirely. Parameterization allows tailoring regularization strength to model/dataset size.

---

# Abstract (from paper)

> RandAugment has a significantly reduced search space which allows it to be trained on the target task with no need for a separate proxy task. Furthermore, due to the parameterization, the regularization strength may be tailored to different model and dataset sizes...

---

# How RandAugment Works

## Available Transformations (14 total)

1. `identity` — no change
2. `autocontrast` — maximize contrast
3. `equalize` — histogram equalization
4. `rotate` — rotate by degrees
5. `solarize` — invert pixels above threshold
6. `posterize` — reduce colors
7. `solarize-add` — add to pixel values
8. `color` — adjust color balance
9. `contrast` — adjust contrast
10. `brightness` — adjust brightness
11. `sharpness` — adjust sharpness
12. `shear-x` — horizontal shear
13. `shear-y` — vertical shear
14. `translate-x` — horizontal translate
15. `translate-y` — vertical translate

## Algorithm

```python
def randaugment(image, n, m):
    """
    Args:
        image: PIL Image or tensor
        n: number of augmentations to apply (from 1 to len(transforms))
        m: magnitude of augmentations (0-30 scale)
    """
    ops = random.sample(AVAILABLE_TRANSFORMS, n)
    
    for op in ops:
        # Apply each operation with magnitude m
        magnitude = m / 30  # Normalize to [0, 1]
        image = apply_op(image, op, magnitude)
    
    return image
```

## Recommended Settings (from paper)

| Dataset | N | M | ImageNet Accuracy |
|---------|---|---|------------------|
| CIFAR-10 | 2 | 14 | 97.1% |
| ImageNet | 2 | 14 | 85.0% |

---

# RTX 3060 Relevance

## WorkerNet Augmentation Policy

For pose estimation + action recognition, RandAugment must be used carefully:

```python
# worker_net/augmentation.py

# PROBLEM: Some RandAugment operations BREAK pose heatmaps
# AVOID operations that change spatial correspondence

SAFE_OPERATIONS = [
    "autocontrast",  # OK: only changes contrast
    "equalize",      # OK: histogram only
    "color",         # OK: color balance only
    "brightness",    # OK: no spatial change
    "sharpness",     # OK: no spatial change
    "contrast",     # OK: no spatial change
    # Posterize might be OK depending on interpretation
]

# DANGEROUS operations (DO NOT USE):
DANGEROUS_OPERATIONS = [
    "rotate",         # ❌ ROTATION DESTROYS POSE GEOMETRY
                      #    Rotation >30° causes severe keypoint misalignment
                      #    WorkerNet uses keypoint locations → spatial structure matters
    "shear-x",       # ❌ Shearing distorts keypoint locations
    "shear-y",       # ❌ Shearing distorts keypoint locations
    "translate-x",    # ⚠️ Large translations shift keypoints outside valid regions
    "translate-y",    # ⚠️ Large translations shift keypoints outside valid regions
    "solarize",       # ⚠️ May affect heatmap gradient structure
    "posterize",      # ⚠️ Color quantization could affect fine detail in heatmaps
]

# Safe RandAugment implementation
def safe_randaugment(image, n=2, m=14):
    """Apply only safe operations for pose tasks"""
    ops = random.sample(SAFE_OPERATIONS, min(n, len(SAFE_OPERATIONS)))
    for op in ops:
        magnitude = m / 30
        image = apply_safe_op(image, op, magnitude)
    return image
```

## ⚠️ CRITICAL: Rotation Limit for Pose Tasks

```
Rotation limit: ≤ 15° for minor adjustments
               > 30° → DO NOT USE

Reason: Keypoints are defined in image coordinates.
        Rotation changes the anatomical meaning of keypoint locations.
        A "left shoulder" rotated 45° becomes misaligned.
```

## Recommended Configuration

```python
# For WorkerNet pose + action multi-task
AUGMENTATION_CONFIG = {
    # Standard image-level augmentations (always safe)
    "random_flip": True,
    "random_crop": True,
    "color_jitter": {"brightness": 0.2, "contrast": 0.2},
    
    # RandAugment-like but restricted
    "safe_ops": ["autocontrast", "equalize", "brightness", "sharpness"],
    "n_ops": 2,
    "magnitude": 10,  # Lower magnitude for safety
    
    # EXPLICITLY FORBIDDEN:
    "forbidden": ["rotate", "shear-x", "shear-y"],
}

# Action classification can use full RandAugment
# but pose branch receives pre-augmented images (augmented before heatmap generation)
```

---

# Results from Paper

| Method | ImageNet Top-1 | CIFAR-10 |
|--------|----------------|----------|
| Baseline augmentation | 84.0% | 96.0% |
| AutoAugment | 85.0% | 97.1% |
| RandAugment (N=2, M=14) | **85.0%** | **97.2%** |
| Fast AutoAugment | 84.7% | 97.1% |

RandAugment matches AutoAugment with **no search phase** and **2× faster training**.

---

# Limitations

1. **Spatial transforms dangerous for pose**: See warnings above
2. **Hyperparameter tuning**: N and M still need selection
3. **Not optimal for all tasks**: ImageNet/CIFAR optimized, may not suit industrial video
4. **Magnitude discretization**: m in {0, 1, ..., 30} discretized

---

# Citation

```bibtex
@article{cubuk2019randaugment,
  title={RandAugment: Practical automated data augmentation with a reduced search space},
  author={Cubuk, Ekin D. and Zoph, Barret and Shlens, Jonathon and Le, Quoc V.},
  journal={arXiv:1909.13719},
  year={2019},
  note={NeurIPS 2020}
}
```

---

# POPW-PROTOCOL Research Wiki — Tier Index

**Part of**: Training Optimization for RTX 3060 (Tier 9)  
**Related**: 090 Bag of Tricks | 091 CutMix | 093 GradCAM

**⚠️ CRITICAL**: For pose tasks, AVOID rotations >30°, shear, large translations

**Owner**: Bashara | SIT Thesis | 2026
