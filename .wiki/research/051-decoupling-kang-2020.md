---
title: Decoupling Kang 2020
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
summary: '**Kang, Xie, Rohrbach, Yan, Gordo, Feng & Kalantidis** | ICLR 2020 | [arXiv:1910.09217](https://arxiv.org/abs/1910.09217)'
wikilinks: []
confidence: medium
source: research
---

# Decoupling Representation and Classifier

**Kang, Xie, Rohrbach, Yan, Gordo, Feng & Kalantidis** | ICLR 2020 | [arXiv:1910.09217](https://arxiv.org/abs/1910.09217)

## Overview

This landmark paper demonstrates a surprising finding: **data imbalance may NOT be a problem for learning high-quality representations**. The key is to decouple representation learning from classifier learning.

The paper systematically explores how different balancing strategies affect representation vs. classifier learning, establishing that:
1. Representations learned with standard instance-balanced sampling can be excellent
2. Classifier performance on long-tail data is primarily a classification head problem, not a representation problem

## Key Findings

### Representation Learning

Using simple instance-balanced (natural) sampling:
- Learn representations normally with standard cross-entropy loss
- Representations generalize well to tail classes
- No re-balancing needed during representation stage

### Classifier Learning

After fixing learned representations, adjust only the classifier:
- **Classifier Re-training**: Train new classifier head with re-balanced sampling
- **Class-Balanced Classifier**: Normalize classifier weights by class frequency
- **Logit Adjustment**: Add class-prior adjustment to logits

## Two-Stage Framework

```
Stage 1: Representation Learning
  └─ Standard CE loss + instance-balanced sampling
  └─ Output: Fixed feature extractor

Stage 2: Classifier Learning  
  └─ Fix features, train classifier with re-balancing
  └─ Options: Re-weight, re-sample, or normalize classifier
```

## Key Results

| Dataset | Decoupled + Balance | Joint Best |
|---------|-------------------:|-----------|
| ImageNet-LT | 58.7% | 52.7% |
| Places-LT | 45.2% | 40.6% |
| iNaturalist | 68.0% | 64.3% |

## POPW Relevance

> [!CRITICAL]
> POPW's 2545:1 imbalance means most training iterations see only head-class activities. This paper proves this doesn't corrupt representations — the problem is the classifier head.
>
> **Recommended POPW Pipeline**:
> 1. Learn features with all data using standard CE
> 2. Re-train classifier head with LDAM or logit adjustment
> 3. Optionally fine-tune last few layers with re-balancing

## Combinability

- ✅ **Decoupling + LDAM (049)**: Natural combination — learn features, apply LDAM to classifier
- ✅ **Decoupling + BBN (050)**: BBN implements this internally; can be viewed as a specific architecture for decoupled learning
- ✅ **Decoupling + MiSLAS (053)**: MiSLAS builds on this framework with calibration improvements
- ✅ **Decoupling + Logit Adjustment (055)**: Use logit adjustment as the classifier re-training method

## Code Availability

- Official: https://github.com/facebookresearch/classifier-balancing

## See Also

- [[research/049-ldam-cao-2019]] — LDAM for classifier re-training
- [[research/050-bbn-zhou-2020]] — Bilateral-branch architecture implementing similar ideas
- [[research/055-logit-adjustment-menon-2021]] — Logit adjustment as classifier method
