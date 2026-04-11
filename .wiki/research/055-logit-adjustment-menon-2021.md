---
tags: [long-tail-learning, logit-adjustment, class-prior, iclr-2021]
sources: [arxiv:2007.07314]
created: 2026-04-11
updated: 2026-04-11
---

# Long-Tail Learning via Logit Adjustment

**Menon, Jayasumana, Rawat, Jain, Veit & Kumar** | ICLR 2021 | [arXiv:2007.07314](https://arxiv.org/abs/2007.07314)

## Overview

Logit adjustment provides a simple, principled approach to long-tail recognition by post-hoc adjusting classifier logits based on class priors. The method unifies several recent proposals while having stronger statistical grounding.

## Core Method

Given pre-softmax logits $z$ and class frequencies $p_c$, the adjusted logit for class $c$ is:

$$s_c = z_c + \tau \log p_c$$

Where $\tau > 0$ is a temperature parameter controlling the strength of adjustment.

**Two variants**:
1. **Post-hoc**: Train with standard CE, adjust logits at test time
2. **Training-time**: Add $\tau \log p_c$ to logits during training

## Theoretical Justification

The paper provides a generalization bound showing that logit adjustment achieves lower expected risk for tail classes. The key insight:

- Standard softmax + CE implicitly assumes uniform priors
- Adjusting by $\log p_c$ corrects for non-uniform priors
- This encourages larger margins between rare vs. common classes

## Relation to Other Methods

| Method | Mathematical Form | Equivalent to Logit Adj? |
|--------|------------------|-------------------------|
| Deferred Re-weighting | Modify loss by $1/n_c$ | No (changes gradients) |
| Class-Balanced Loss | Weight loss by $1/E_n$ | No (similar effect, diff implementation) |
| Label Smoothing | Soft targets $y'_i$ | No (modifies targets) |
| Logit Adjustment | Add $\tau \log p_c$ | ✓ Base method unifies these |

## Key Results

| Dataset | Logit Adj | Deferred Re-weight | Class-Balanced |
|---------|----------:|-------------------:|---------------:|
| ImageNet-LT | 59.1% | 57.7% | 58.6% |
| Places-LT | 45.8% | 43.3% | 45.2% |
| iNaturalist | 68.8% | 66.7% | 68.0% |

## POPW Relevance

> [!CRITICAL]
> Logit adjustment is one of the simplest methods to implement for POPW's 2545:1 imbalance:
> 1. Train normally with standard CE
> 2. Add $\tau \log(\text{class\_prior})$ to logits before softmax
>
> This requires NO changes to training pipeline, only inference modification. Can be combined with any training-time method for additional gains.
>
> **Recommended $\tau$**: Start with 0.5-1.0. Higher values push more toward tail classes.

## Combinability

- ✅ **Logit Adj + Decoupling (051)**: Apply as classifier re-training method
- ✅ **Logit Adj + Any Training Method**: Post-hoc adjustment works with any trained model
- ✅ **Logit Adj + LDAM (049)**: Both push margins toward tail classes; can combine
- ✅ **Logit Adj + MiSLAS (053)**: Logit adj + LAS for calibrated classifier

## Code Availability

- Official: https://github.com/google-research/google-research/tree/master/logit_adjustment

## See Also

- [[051-decoupling-kang-2020]] — Decoupled framework (logit adj as classifier stage)
- [[052-class-balanced-cui-2019]] — Class-balanced loss (alternative approach)
- [[049-ldam-cao-2019]] — LDAM (margin-based alternative)
