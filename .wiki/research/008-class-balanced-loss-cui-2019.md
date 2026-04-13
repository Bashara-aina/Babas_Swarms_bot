---
title: "008 - Class-Balanced Loss Cui 2019"
type: research
status: active
tags: [class-balance, class-imbalance, effective-number, focal-loss, loss-weighting]
created: 2026-04-13
updated: 2026-04-13
summary: Class-balanced loss reweights each sample by 1/beta^(n_c-1) where n_c is the effective number of samples per class. Combined with focal loss (CB Focal), it handles both foreground-background imbalance AND class-frequency imbalance. POPW uses CB Focal for activity head (33 classes, 2545:1 imbalance).
wikilinks:
  - [[007-focal-loss-lin-2017]]
  - [[045-gradnorm-chen-2018]]
  - [[013-gradient-surgery-yu-2020]]
  - [[100-popw-protocol-self-analysis]]
confidence: high
source: canonical
---

# Class-Balanced Loss: Reweighting by Effective Number

**Authors:** Yin Cui, Menglin Jia, Tsung-Yi Lin, Yang Song, James Hays
**Year:** 2019
**Venue:** CVPR
**ArXiv/DOI:** [arXiv:1901.05555](https://arxiv.org/abs/1901.05555)
**Citation count:** ~3,000+
**Relevance to POPW:** POPW's activity head uses CB Focal Loss (class-balanced + focal combined) in `losses.py:CBFocalLoss`. The 33-class activity classification has extreme intra-class imbalance (2545:1), requiring both focal focusing AND class-frequency reweighting.

## Core Contribution

The key insight: as the number of samples per class increases, the benefit of each new sample decreases. The "effective number" of samples is defined as `(1 - beta^n_c) / (1 - beta)` where `n_c` is the actual number of samples and `beta ∈ [0,1)` is a hyperparameter. Samples are reweighted by `1/effective_number`, which naturally down-weights classes with many samples.

## Key Technical Details

- **Effective number formula**: `E_n = (1 - beta^n_c) / (1 - beta)`
  - `n_c` = number of samples in class `c`
  - `beta` = typically 0.9999 (set in `config.py:CB_BETA`)
- **Reweighting factor**: `w_c = 1 / E_n = (1 - beta) / (1 - beta^n_c)`
- **As n_c → ∞**: `E_n → 1/(1-beta)` → w_c → (1-beta), converges to constant
- **As n_c → 1**: `E_n → 1` → w_c → 1, no reweighting
- **CB Focal combines**: class-balanced weights (w_c) × focal factor `(1-p_t)^γ`
- **Why not inverse frequency**: With beta=0.9999, the weights are smoother — a class with 1000 samples doesn't get 1000× the weight of a class with 1 sample

## Results They Achieved

| Dataset | Method | mAP / Accuracy |
|---------|--------|----------------|
| CIFAR-100 (100 classes) | CB Loss + softmax | 59.1% |
| CIFAR-100 | Nominal softmax | 53.9% |
| iNaturalist 2017 (5089 classes) | CB Loss + softmax | 68.6% |
| iNaturalist 2017 | Nominal softmax | 63.3% |
| Places365 (365 classes) | CB Loss + softmax | 53.6% |

On long-tailed iNaturalist (5089 species, extreme imbalance), CB Loss improved top-1 accuracy by **5.3%**.

## What POPW Can Steal Directly

1. **CB Focal Loss implementation** (`losses.py:CBFocalLoss`): Uses `CB_BETA=0.9999` from config
2. **Per-class sample counting**: Effective number requires knowing per-class sample counts in the training set — computed from dataset stats at training start
3. **CB Focal formula**: `loss = -α_t (1 - p_t)^γ log(p_t)` where `α_t = α × w_c` — class-balanced alpha
4. **For 33 activity classes**: The imbalance ratio (2545:1) requires this approach; plain focal loss alone is insufficient

## Implemented in POPW?

- [x] YES — `improved/losses.py:CBFocalLoss` class
- [x] YES — `config.py:CB_BETA = 0.9999`, `CB_ALPHA = 0.25` (from focal loss defaults)
- [x] YES — Combined with focal loss γ=2.0 for activity head

## Failure Modes / Limitations

- **Beta tuning is dataset-specific**: beta=0.9999 works for iNaturalist (very large datasets). For smaller datasets like IKEA ASM (685K frames but 33 classes), beta=0.999 or beta=0.9999 both work — validate on held-out videos.
- **Requires per-class sample counts**: If class distribution shifts over time (e.g., new furniture types), effective numbers need recomputing.
- **Doesn't handle intra-class variance**: A class with 10,000 samples of very similar frames still gets the same weight as a class with 10,000 diverse frames. Consider per-sample difficulty weighting.
- **Memory overhead**: Storing per-class effective numbers adds negligible memory but requires recomputation if dataset changes.

## Key Equations

**Effective number:**
```
E_n = (1 - beta^n_c) / (1 - beta)
```

**Class-balanced weight:**
```
w_c = 1 / E_n = (1 - beta) / (1 - beta^n_c)
```

**CB Focal Loss:**
```
CBFL(p_t) = -w_y (1 - p_t)^γ log(p_t)
           = -(1 - beta) / (1 - beta^(n_y)) (1 - p_t)^γ log(p_t)
where w_y is the weight of the ground-truth class y
```

**Asymptotic behavior:**
```
n_c = 1    → w_c = 1
n_c = 10   → w_c ≈ 10(1-beta) for small beta
n_c → ∞    → w_c → (1-beta) = constant (capped)
```

## Implementation Notes

```python
# Class-Balanced Focal Loss (from losses.py)
class CBFocalLoss(nn.Module):
    def __init__(self, num_classes, beta=0.9999, gamma=2.0, alpha=0.25):
        super().__init__()
        self.num_classes = num_classes
        self.beta = beta
        self.gamma = gamma
        self.alpha = alpha
        self.class_counts = None  # Set via set_class_counts()
        self.class_weights = None  # Computed from class_counts

    def set_class_counts(self, counts: List[int]):
        """counts: list of sample counts per class, length=num_classes."""
        self.class_counts = counts
        # Compute effective numbers: E_n = (1 - beta^n_c) / (1 - beta)
        effective_nums = []
        for n in counts:
            if n == 0:
                effective_nums.append(0.0)
            else:
                en = (1 - self.beta ** n) / (1 - self.beta)
                effective_nums.append(en)
        # Class-balanced weights: w_c = 1 / E_n
        self.class_weights = [(1 - self.beta) / max(en, 1e-8) for en in effective_nums]
        self.class_weights = torch.tensor(self.class_weights, dtype=torch.float32)

    def forward(self, cls_preds, targets):
        p = torch.sigmoid(cls_preds)
        ce = F.binary_cross_entropy_with_logits(cls_preds, targets, reduction='none')
        p_t = p * targets + (1 - p) * (1 - targets)  # probability of correct class
        focal_weight = (1 - p_t) ** self.gamma
        # Apply class-balanced alpha (alpha * w_c)
        weights = self.alpha * self.class_weights.to(cls_preds.device)
        alpha_t = weights * targets + (1 - weights) * (1 - targets)
        return (alpha_t * focal_weight * ce).mean()
```

**Critical initialization**: Call `set_class_counts()` before training starts. This is done in the training loop when dataset is built.

## Related Papers in This Wiki

- [[007-focal-loss-lin-2017]] — Focal loss handles easy/hard, CB loss handles common/rare — combined = CB Focal
- [[045-gradnorm-chen-2018]] — GradNorm is another approach to loss weighting by gradient magnitude
- [[013-gradient-surgery-yu-2020]] — PCGrad solves gradient conflicts directly
- [[100-popw-protocol-self-analysis]] — Documents CB Focal usage in POPW activity head

## LEGION RULE

When Bashara asks about "why does activity need CB Focal but detection just uses plain focal," reference this paper's finding: Detection's 7 classes are roughly balanced (each furniture part appears equally often per frame). Activity's 33 classes have 2545:1 imbalance — some assembly actions are extremely rare. Plain focal only handles easy vs hard (p_t ≈ 1 vs p_t ≈ 0), NOT common vs rare (many samples vs few samples). CB Focal adds the per-class frequency reweighting to focal's hard-example focusing.

Applied to POPW: For 7 detection classes, focal loss with α=0.25, γ=2.0 is sufficient. For 33 activity classes, CB Focal with β=0.9999, γ=2.0 is necessary. The class_weights in CB Focal effectively upweight rare classes (screw_driver, flip_box) and downweight common ones (take_out_parts, organize_parts).

Config: `config.py:CB_BETA = 0.9999` — this can be tuned (0.999, 0.9999, 0.99999) via ablation experiments.
