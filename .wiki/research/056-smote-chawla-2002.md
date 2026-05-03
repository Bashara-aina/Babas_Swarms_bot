---
title: SMOTE — Synthetic Minority Over-sampling Technique
type: concept
status: active
tags: [smote, imbalanced-learning, oversampling, classification, augmentation]
created: 2026-04-13
updated: 2026-04-13
summary: '**Chawla, Bowyer, Hall & Kegelmeyer** | JAIR 2002 | [DOI:10.1613/jair.953](https://doi.org/10.1613/jair.953) | Foundational oversampling method for imbalanced classification using k-NN interpolation in feature space.'
wikilinks:
  - [[research/054-remix-chou-2020]]
  - [[research/053-mislas-zhong-2021]]
  - [[research/052-class-balanced-cui-2019]]
confidence: high
source: research
project: popw
---

# SMOTE: Synthetic Minority Over-sampling Technique

**Chawla, Bowyer, Hall & Kegelmeyer** | JAIR 2002 | [DOI:10.1613/jair.953](https://doi.org/10.1613/jair.953)

## Overview

**SMOTE (Synthetic Minority Over-sampling Technique)** is a foundational oversampling method for handling imbalanced classification. Rather than simply duplicating minority class samples, SMOTE generates synthetic examples by interpolating between minority class samples.

## Core Algorithm

For each minority class sample $x_i$:

1. Find $k$ nearest minority class neighbors (typically $k=5$)
2. Randomly select one neighbor $x_{nn}$
3. Generate synthetic sample:
   $$x_{new} = x_i + \lambda \cdot (x_{nn} - x_i)$$
   where $\lambda \in [0,1]$ is random

**Key**: Interpolation happens in feature space, not label space. For image classification, this corresponds to interpolating between actual image features.

## Variants

| Variant | Description |
|---------|-------------|
| Borderline-SMOTE | Only oversample near decision boundary |
| SMOTE-NC | For datasets with nominal features |
| SMOTE + ENN | Combine with Edited Nearest Neighbors cleaning |
| ADASYN | Adaptive synthetic sampling based on density |

## Key Results (from original paper)

| Dataset | C4.5 + SMOTE | C4.5 + Under-sampling |
|---------|------------:|----------------------:|
| Glass (7:1 imbalance) | 76.2% AUC | 68.3% AUC |
| Breast Cancer (1.8:1) | 97.2% AUC | 96.2% AUC |

## POPW Relevance

> [!IMPORTANT]
> SMOTE is a foundational method that inspired many deep learning augmentation techniques. While direct SMOTE on raw images may not be optimal for deep networks, the core idea of **interpolating between minority samples** is fundamental:
>
> - **Mixup (2017)**: Generalizes SMOTE idea to deep learning
> - **Remix (Paper 054)**: SMOTE-like oversampling + Mixup regularization
> - **SMOTE for features**: Apply SMOTE in feature space, not pixel space

## Limitations for Deep Learning

1. **Linear interpolation**: SMOTE interpolates linearly, but deep features are non-linear
2. **No label consideration**: SMOTE doesn't consider classification boundaries
3. **Over-generation**: Can create too many synthetic samples, leading to overfitting

For modern deep learning, **Remix (054)** or **Mixup-based methods** generally outperform vanilla SMOTE.

## Combinability

- ✅ **SMOTE + Under-sampling**: Original paper's approach — oversample minority, undersample majority
- ✅ **SMOTE + Ensemble**: SMOTE + bagging (SMOTEBoost)
- ⚠️ **SMOTE + Deep Learning**: Generally superseded by Mixup/Remix for neural networks

## Code Availability

- Official (JAIR): https://www.jair.org/index.php/jair/article/view/10302
- Archive: https://arxiv.org/abs/1106.1813
- scikit-learn-contrib: https://github.com/scikit-learn-contrib/imbalanced-learn

## See Also

- [[research/054-remix-chou-2020]] — Remix (deep learning evolution of SMOTE ideas)
- [[research/053-mislas-zhong-2021]] — MiSLAS (mixup + calibration for long-tail)
- [[research/052-class-balanced-cui-2019]] — Class-balanced loss (re-weighting alternative)