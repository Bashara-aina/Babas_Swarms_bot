---
tags: [class-imbalance, effective-number, re-weighting, cvpr-2019]
sources: [arxiv:1901.05555]
created: 2026-04-11
updated: 2026-04-11
---

# Class-Balanced Loss Based on Effective Number of Samples

**Cui, Jia, Lin, Song & Belongie** | CVPR 2019 | [arXiv:1901.05555](https://arxiv.org/abs/1901.05555)

## Overview

This paper introduces the **Effective Number of Samples** concept for class-rebalancing. The key insight is that as the number of samples for a class increases, the "effective" amount of new information provided by additional samples diminishes.

## Core Concept: Effective Number

For a class with $n$ samples and hyperparameter $\beta \in [0, 1)$, the effective number is:

$$E_n = \frac{1 - \beta^n}{1 - \beta}$$

When $\beta = 0$: $E_n = 1$ (only one effective sample regardless of count)
When $\beta \to 1$: $E_n \to n$ (all samples contribute equally)

**Intuition**: With $\beta = 0.9999$, a class with 1000 samples has effective number ≈ 63. A class with 10 samples has effective number ≈ 9.95. The ratio (9.95/63) is the re-weighting factor.

## Class-Balanced Loss

The class-balanced weight for class $c$:

$$w_c = \frac{1}{E_{n_c}} = \frac{1 - \beta}{1 - \beta^{n_c}}$$

Apply this to any loss function (softmax CE, focal loss, etc.):

$$\text{CB-Loss} = -\frac{1}{E_{n_y}} \log\left(\frac{\exp(s_y)}{\sum_j \exp(s_j)}\right)$$

## Relationship to Prior Work

| Method | Weight Formula | Issue |
|--------|---------------|-------|
| Naive re-weighting | $w_c = 1/n_c$ | Too aggressive for large classes |
| Effective Number | $w_c = (1-\beta)/(1-\beta^{n_c})$ | Smooth transition |
| sqrt re-weighting | $w_c = 1/\sqrt{n_c}$ | Heuristic, no theory |

## Key Results

| Dataset | CB-Focal Loss | Standard Focal |
|---------|-------------:|---------------|
| CIFAR-10-LT (100:1) | 59.1% | 54.4% |
| CIFAR-100-LT (100:1) | 44.4% | 38.2% |
| ImageNet-LT | 58.6% | — |

## POPW Relevance

> [!IMPORTANT]
> Effective Number provides a principled way to compute class weights for POPW's 2545:1 imbalance. Unlike naive $1/n_c$ weighting which can produce extreme weights, Effective Number smoothly interpolates based on diminishing returns.
>
> **Recommended $\beta$ for POPW**: Start with $\beta = 0.999$ (fairly gentle) since POPW has extreme imbalance — too aggressive weighting may destabilize training.

## Combinability

- ✅ **Effective Number + Focal Loss**: Standard combination, CB-Focal is baseline in paper
- ✅ **Effective Number + LDAM (049)**: Use effective number weights in LDAM loss
- ✅ **Effective Number + Mixup**: Combine sample weighting with mixup regularization
- ✅ **Effective Number + Decoupling (051)**: Use as classifier re-weighting strategy

## Code Availability

- Official: https://github.com/richardaecn/class-balanced-loss

## See Also

- [[049-ldam-cao-2019]] — LDAM margin loss
- [[054-remix-chou-2020]] — Remix for re-balanced mixup
- [[055-logit-adjustment-menon-2021]] — Logit adjustment (different re-balancing approach)
