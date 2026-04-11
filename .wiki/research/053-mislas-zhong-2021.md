---
tags: [long-tail-learning, mixup, label-smoothing, calibration, cvpr-2021]
sources: [arxiv:2104.00466]
created: 2026-04-11
updated: 2026-04-11
---

# MiSLAS: Mixup Shifted Label-Aware Smoothing

**Zhong, Cui, Liu & Jia** | CVPR 2021 | [arXiv:2104.00466](https://arxiv.org/abs/2104.00466)

## Overview

**MiSLAS (Mixup Shifted Label-Aware Smoothing)** builds on the decoupled representation/classifier framework (Paper 051) with two key innovations:

1. **Label-Aware Smoothing (LAS)**: Addresses miscalibration in long-tail recognition by adjusting label smoothing based on class frequency
2. **Shifted Batch Normalization (SBN)**: Addresses dataset bias between representation and classifier training stages due to different samplers

## Two Key Innovations

### Label-Aware Smoothing (LAS)

Standard label smoothing distributes confidence evenly across classes:
$$y'_i = (1 - \epsilon) \cdot y_i + \epsilon/K$$

LAS adjusts smoothing based on class frequency — tail classes get less smoothing:
$$y'_i = (1 - \alpha \cdot \epsilon) \cdot y_i + \alpha \cdot \epsilon/K$$

Where $\alpha$ is inversely related to class frequency.

**Intuition**: Head classes are over-confident (due to more samples), so they need more smoothing. Tail classes are under-confident, so they need less.

### Shifted Batch Normalization (SBN)

When switching from representation learning (instance-balanced) to classifier training (class-balanced sampling):
- BatchNorm statistics shift due to different data distributions
- SBN recalculates running statistics using the new sampler
- This prevents the "representation shift" problem

## Two-Stage Framework

```
Stage 1: Representation Learning
  └─ Mixup + Instance-balanced sampling
  └─ Learn robust features

Stage 2: Classifier Learning
  └─ Label-Aware Smoothing + Shifted BN
  └─ Train calibrated classifier
```

## Key Results

| Dataset | MiSLAS | Previous Best |
|---------|-------:|-------------|
| CIFAR-10-LT (100:1) | 64.4% | 59.1% |
| CIFAR-100-LT (100:1) | 48.1% | 44.4% |
| ImageNet-LT | 61.4% | 58.7% |
| Places-LT | 48.4% | 45.2% |
| iNaturalist 2018 | 71.6% | 68.0% |

## POPW Relevance

> [!IMPORTANT]
> MiSLAS directly addresses POPW's calibration problem. With 2545:1 imbalance:
> - Head classes (assemble) will be over-confident → needs more smoothing
> - Tail classes (inspect, adjust) will be under-confident → needs less smoothing
>
> The **Shifted BN** is particularly relevant for POPW where representation and classifier training may happen in different phases (pre-training vs. fine-tuning).

## Combinability

- ✅ **MiSLAS + LDAM (049)**: Replace LAS with LDAM loss in Stage 2
- ✅ **MiSLAS + Decoupling (051)**: MiSLAS IS built on decoupled framework
- ✅ **MiSLAS + Remix (054)**: Use Remix instead of vanilla Mixup in Stage 1
- ✅ **MiSLAS + Effective Number (052)**: Use effective number for class weights in LAS

## Code Availability

- Official: https://github.com/Jia-Research-Lab/MiSLAS

## See Also

- [[051-decoupling-kang-2020]] — Base decoupling framework
- [[054-remix-chou-2020]] — Remix mixup variant
- [[049-ldam-cao-2019]] — LDAM for classifier training
