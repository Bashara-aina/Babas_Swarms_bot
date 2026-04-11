---
tags: [class-imbalance, mixup, regularization, re-balancing, eccv-2020]
sources: [arxiv:2007.03943]
created: 2026-04-11
updated: 2026-04-11
---

# Remix: Rebalanced Mixup

**Chou, Chang, Pan, Wei & Juan** | ECCV 2020 Workshop | [arXiv:2007.03943](https://arxiv.org/abs/2007.03943)

## Overview

**Remix** modifies the Mixup augmentation to address class imbalance by disentangling the mixing of features and labels. The key insight is that standard Mixup treats both features and labels equally, but for imbalanced data, labels should be mixed differently than features.

## Core Idea

Standard Mixup for two samples $(x_i, y_i)$ and $(x_j, y_j)$:
$$\tilde{x} = \lambda x_i + (1-\lambda) x_j$$
$$\tilde{y} = \lambda y_i + (1-\lambda) y_j$$

Remix changes label mixing to favor minority classes:
$$\tilde{y} = \frac{\lambda \cdot w_{y_i} \cdot y_i + (1-\lambda) \cdot w_{y_j} \cdot y_j}{\lambda \cdot w_{y_i} + (1-\lambda) \cdot w_{y_j}}$$

Where $w_c$ is the class weight (inverse frequency or effective number).

**Intuition**: When mixing a head class sample with a tail class sample, give more weight to the tail class label in the mixed label.

## Disentangled Mixing

Remix disentangles two aspects:

1. **Feature mixing**: Same as standard Mixup (keeps Mixup's regularization benefits)
2. **Label mixing**: Disproportionately favors minority class

This ensures:
- Decision boundaries are pushed toward majority classes
- Minority classes receive more signal from mixed samples

## Key Results

| Dataset | Remix | Mixup | Improvement |
|---------|------:|------:|------------:|
| CIFAR-10-LT (100:1) | 62.5% | 55.9% | +6.6% |
| CIFAR-100-LT (100:1) | 45.1% | 39.2% | +5.9% |
| iNaturalist 2018 | 68.2% | 64.3% | +3.9% |

## POPW Relevance

> [!IMPORTANT]
> Remix is a simple, effective regularization for POPW's extreme imbalance. Unlike complex two-stage methods, Remix is a drop-in replacement for Mixup that automatically handles class imbalance.
>
> For POPW's activity recognition:
> - Mixing "assemble" (head) with "inspect" (tail) → label favors "inspect"
> - This helps the classifier learn to recognize tail activities even when they're partial/occluded

## Combinability

- ✅ **Remix + Decoupling (051)**: Use Remix in representation learning stage
- ✅ **Remix + Effective Number (052)**: Use effective number weights in Remix label mixing
- ✅ **Remix + MiSLAS (053)**: Replace vanilla Mixup with Remix in MiSLAS Stage 1
- ✅ **Remix + LDAM (049)**: Combine Remix regularization with LDAM classifier loss

## Code Availability

- Official: https://github.com/google-research/google-research/tree/master/remix

## See Also

- [[052-class-balanced-cui-2019]] — Effective number for class weights
- [[053-mislas-zhong-2021]] — MiSLAS framework (can use Remix)
- [[054b-cutmix-2020]] — CutMix for long-tail (if available)
