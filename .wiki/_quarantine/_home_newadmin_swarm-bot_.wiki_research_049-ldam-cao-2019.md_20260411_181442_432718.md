---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/research/049-ldam-cao-2019.md",
  "reason": "daily_fast_scan: score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-11T18:14:42.432740"
}
---

---
tags: [class-imbalance, long-tail-learning, margin-loss, neurips-2019]
sources: [arxiv:1906.07413]
created: 2026-04-11
updated: 2026-04-11
---

# LDAM: Label-Distribution-Aware Margin Loss

**Cao, Wei, Gaidon, Arechiga & Ma** | NeurIPS 2019 | [arXiv:1906.07413](https://arxiv.org/abs/1906.07413)

## Overview

**LDAM (Label-Distribution-Aware Margin Loss)** is a theoretically-motivated loss function designed for learning from imbalanced datasets. The key insight is that margin-based classification bounds suggest classifiers should have larger margins for minority classes to achieve better generalization.

Unlike standard cross-entropy loss which treats all samples equally, LDAM assigns different margins to different classes based on their number of training samples, with larger margins enforced for classes with fewer samples.

## Core Idea

The loss is derived from minimizing a margin-based generalization bound:

$$\text{LDAM Loss} = \log\left(1 + \sum_{j \neq y} \exp(s_j - s_y + \Delta_{y,j})\right)$$

Where $\Delta_{y,j}$ is the margin for class $y$ against class $j$, set inversely proportional to class frequency.

**Key insight**: As the number of samples $n_c$ for class $c$ increases, the effective "volume" of that class grows, meaning additional samples provide diminishing marginal benefit. LDAM accounts for this by enforcing smaller margins for high-frequency classes.

## Two-Stage Training Strategy

LDAM authors propose a two-stage training schedule:

1. **Stage 1 (Representation Learning)**: Train with standard cross-entropy loss and class-balanced sampling to learn initial representations
2. **Stage 2 (Classifier Re-training)**: Fix the feature extractor, re-train the classifier head using LDAM loss with deferred re-weighting

This avoids the "early overfitting" problem where minority classes are misrepresented early in training.

## Key Results

| Dataset | LDAM + BPN | Previous Best |
|---------|-----------:|---------------|
| CIFAR-10-LT (100:1) | 58.9% | 54.4% |
| CIFAR-100-LT (100:1) | 44.0% | 38.2% |
| iNaturalist 2018 | 68.4% | 64.3% |

## POPW Relevance

> [!CRITICAL]
> POPW has **2545:1 worst-case class imbalance** in its activity head (33 classes). LDAM's class-aware margins are directly applicable to POPW's multi-label activity classification where rare activities (e.g., "inspect", "adjust") are frequently misclassified as common ones (e.g., "assemble").
>
> **LDAM + Decoupled Classifier Re-training (Paper 051)** is a powerful combination: learn features with standard CE, then re-train classifier head with LDAM.

## Combinability

- ✅ **LDAM + Decoupled Classifier (051)**: Classic combination — learn representations with CE, re-train classifier with LDAM
- ✅ **LDAM + Focal Loss**: Can combine margin-based and loss-weighting approaches
- ✅ **LDAM + Mixup**: Mixup regularization complements LDAM's margin focus

## Code Availability

- Official: https://github.com/kaidic/LDAM-DRW

## See Also

- [[050-bbn-zhou-2020]] — Bilateral-Branch Network (complementary two-stage approach)
- [[051-decoupling-kang-2020]] — Decoupled representation/classifier learning
- [[052-class-balanced-cui-2019]] — Class-balanced loss with effective number of samples
