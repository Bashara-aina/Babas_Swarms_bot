---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/research/057-square-loss-hui-2021.md",
  "reason": "daily_fast_scan: score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-12T01:00:00.915848"
}
---

---
tags: [loss-functions, square-loss, cross-entropy, classification, neurips-2021]
sources: [arxiv:2006.07322]
created: 2026-04-11
updated: 2026-04-11
---

# Square Loss as Alternative to Cross-Entropy

**Hui & Belkin** | NeurIPS 2021 | [arXiv:2006.07322](https://arxiv.org/abs/2006.07322)

## Overview

This paper challenges the widely held belief that cross-entropy (CE) loss is superior to square loss for neural network classification. Through extensive experiments, the authors demonstrate that **square loss performs comparably or better than CE in most tasks**, especially NLP and ASR.

## Key Claims

1. **Square loss is competitive**: With identical hyperparameters, square loss often outperforms CE
2. **Better on non-vision tasks**: Square loss significantly outperforms CE on NLP/ASR tasks
3. **Less sensitive to initialization**: Square loss shows lower variance across random seeds
4. **No clear theoretical advantage for CE**: The common belief lacks strong empirical or theoretical support

## Mathematical Formulation

**Cross-Entropy Loss**:
$$L_{CE} = -\sum_{c} y_c \log(\hat{y}_c)$$

**Square Loss**:
$$L_{SQ} = \sum_{c} (\hat{y}_c - y_c)^2$$

Where $\hat{y}_c$ is the predicted probability for class $c$ and $y_c$ is the target.

## Experimental Results

### NLP Tasks (Square > CE)
| Task | Square Loss | Cross-Entropy |
|------|------------:|---------------:|
| Language Modeling | 38.9 PPL | 43.4 PPL |
| Sentiment Analysis | 4.32% Error | 4.85% Error |
| NER | 4.12% F1 | 4.35% F1 |

### Vision Tasks (CE slightly better)
| Task | Square Loss | Cross-Entropy |
|------|------------:|---------------:|
| ImageNet | 30.2% Error | 29.8% Error |
| CIFAR-10 | 4.85% Error | 4.12% Error |

## POPW Relevance

> [!NOTE]
> This paper is relevant for POPW because:
> 1. **Loss function choice matters less than assumed**: POPW can experiment with square loss for its activity head
> 2. **Less sensitivity to initialization**: Important for training stability with limited data
> 3. **Potentially better for sequential/temporal data**: POPW's activity sequences may benefit
>
> **For POPW's extreme class imbalance**, square loss alone doesn't address the problem — it needs to be combined with class re-balancing techniques.

## Implications for Class Imbalance

**Does square loss help with imbalanced data?**

Not directly. Square loss, like CE, doesn't automatically handle class imbalance. However:
- Square loss's uniform treatment of errors may be more stable than CE's implicit emphasis on confident predictions
- Combined with logit adjustment (055), square loss + logit adjustment could be a valid approach

## Combinability

- ✅ **Square Loss + Logit Adjustment (055)**: Apply class prior adjustment to square loss logits
- ✅ **Square Loss + Effective Number (052)**: Weight square loss by class weights
- ⚠️ **Square Loss + Focal Loss**: Focal loss specifically modifies CE; square loss version would need new derivation

## Code Availability

- Official: https://github.com/l耕/SquareLossClassification

## See Also

- [[055-logit-adjustment-menon-2021]] — Logit adjustment (can be applied to square loss)
- [[052-class-balanced-cui-2019]] — Class-balanced weighting for any loss
- [[049-ldam-cao-2019]] — LDAM (margin-based approach)
