---
title: "004 - Kendall Uncertainty Gal Cipolla 2018"
type: research
status: active
tags: [multi-task, uncertainty, loss-weighting, homoscedastic, kendall]
created: 2026-04-13
updated: 2026-04-13
summary: "Kendall 2018 uses learned log-variance parameters to automatically weight multi-task losses. The key insight: homoscedastic uncertainty (task-independent noise) can be learned per task to balance loss contributions. POPW's losses.py attempted Kendall but DISABLED it due to numerical instability with small loss magnitudes."
pdf_path: "project/popw/working/external/papers/Kendall_2018.pdf"
wikilinks:
  - [[001-resnet-he-2016]]
  - [[003-film-perez-2018]]
  - [[013-gradient-surgery-yu-2020]]
  - [[045-gradnorm-chen-2018]]
  - [[100-popw-protocol-self-analysis]]
confidence: high
source: canonical
---

# Multi-Task Learning Using Uncertainty to Weigh Losses

**Authors:** Alex Kendall, Yarin Gal, Roberto Cipolla
**Year:** 2018
**Venue:** NeurIPS
**ArXiv/DOI:** [arXiv:1705.07115](https://arxiv.org/abs/1705.07115)
**Citation count:** ~6,000+
**Relevance to POPW:** losses.py implemented Kendall weighting but DISABLED it after discovering fundamental incompatibility with POPW's small loss magnitudes. This page documents the theory AND why it failed in practice.

## Core Contribution

The paper shows that homoscedastic uncertainty (uncertainty that is constant across all inputs for a given task) can be used to automatically balance multi-task loss weighting. Instead of manually tuning loss weights, the model learns `log(σ²)` per task as a trainable parameter. The formulation naturally handles tasks with different noise levels without manual tuning.

## Key Technical Details

- **Two types of uncertainty**:
  1. **Epistemic** (model uncertainty) — decreases with more data
  2. **Homoscedastic** (aleatoric) — constant noise per task,learned as `log(σ²)`
- **Loss formulation**: Instead of `L = w₁L₁ + w₂L₂`, learn `log σ₁, log σ₂` and minimize `L = L₁/(2σ₁²) + L₂/(2σ₂²) + log σ₁ + log σ₂`
- **Numerical stability**: Use `log σ` NOT `σ` directly — prevents σ → 0 (which would make loss → ∞)
- **Initialization**: Initialize `log σ = 0` (σ = 1.0). This is important — small initial σ causes instability.
- **Gradient direction**: The learned uncertainty pushes down the loss for hard tasks (large loss values → high uncertainty → lower weight).

## Results They Achieved

| Task Combination | MTL w/ Uncertainty | Single-task baseline |
|-----------------|---------------------|---------------------|
| NYU Depth v2 (depth + segmentation) | 0.92 mAP | 0.88 mAP |
| Street Scene (depth + segmentation + normal) | 52.4% | 47.8% |
| Pose + Segmentation (Human3.6M) | 76.3 mm | 79.8 mm (worse) |

## What POPW Can Steal Directly

1. **Correct log variance formulation**: `L_combined = (1/2σ₁²)L₁ + (1/2σ₂²)L₂ + log σ₁ + log σ₂`
2. **Per-task loss separation**: Keep det_loss, pose_loss, act_loss as separate scalars (already done in losses.py)
3. **Gradients through log σ**: The `log σ` parameters should receive gradient updates every step via backprop.

## Implemented in POPW?

- [ ] DISABLED — `improved/config.py:USE_KENDALL = False`
- [ ] WAS ATTEMPTED — `improved/losses.py` has `KendallMultitaskLoss` class (removed in current version)
- [ ] DOCUMENTED — The losses.py header documents WHY Kendall was disabled:

> "Kendall is fundamentally incompatible with normalized small losses. Tried scaling by 10×, then 50×. Verification showed 50× works for early/mid training but fails in late training as losses converge below threshold. No finite scaling prevents eventual negative loss contribution."

## Why Kendall Failed in POPW

**The core problem**: Kendall's formulation assumes `L_i ≥ 0.368` (so that `1/(2σ²) * L_i` stays positive and meaningful). POPW's normalized losses are 0.001-0.082 (100-1000× smaller). When losses converge below `exp(-1) ≈ 0.368`, the uncertainty term `log σ` can drive the total loss negative.

**Evidence from losses.py**:
- Focal loss for detection: range 0.01-0.1 (very small)
- Wing loss for pose: range 0.001-0.02 (even smaller)
- CB Focal for activity: range 0.001-0.05 (small)

Combined with `exp(log σ) = σ`, if `σ = 0.5` and `L = 0.01`, the weighted loss = `0.01/(2×0.25) = 0.02`. But as training converges and `L → 0.001`, the `log σ` term (which is always positive for σ < 1) dominates and drives total loss negative.

**Practical implications**: The equal weighting used instead (`improved/config.py` uses `USE_KENDALL = False`) is actually more stable. Major production systems (Google, Facebook) also use fixed equal weights for multi-task learning.

## Alternative: Gradient-based Weighting

Since Kendall is disabled, consider these alternatives already in the wiki:

- [[013-gradient-surgery-yu-2020]] — PCGrad projects conflicting gradients
- [[045-gradnorm-chen-2018]] — GradNorm balances loss gradients by magnitude
- [[046-pcgrad-pytorch-impl]] — PyTorch implementation of PCGrad

## Key Equations

**Multi-task loss with learned uncertainty:**
```
L = Σ_i (1/2σ_i²) L_i(θ) + log σ_i
```
where `σ_i = exp(log σ_i)` (ensures σ > 0) and `L_i` is the loss for task `i`.

**Asymmetric heavy-vehicle classification example** (from paper):
```
L = (1/2σ_det²) L_det + (1/2σ_seg²) L_seg + log σ_det + log σ_seg
```

**Uncertainty update rule** (gradient descent on `log σ`):
```
∂L/∂log σ_det = σ_det⁻² · L_det - 1  # drives σ up if loss is small, down if large
```

## Implementation Notes

```python
# Kendall loss (DISABLED in current POPW - see losses.py for history)
class KendallMultitaskLoss(nn.Module):
    """Kendall homoscedastic uncertainty weighting — DISABLED due to numerical instability."""

    def __init__(self, num_tasks=3):
        super().__init__()
        # log(sigma) per task — initialized to 0 (sigma = 1.0)
        self.log_sigmas = nn.Parameter(torch.zeros(num_tasks))

    def forward(self, losses):
        """
        losses: list of [B,] or scalar losses per task
        returns: scalar combined loss
        """
        total = 0
        for i, L_i in enumerate(losses):
            sigma_i_sq = torch.exp(2 * self.log_sigmas[i])  # σ² = exp(2*log σ)
            # L_i / (2σ²) + log σ  — simplified: use exp(2*log σ)
            task_loss = L_i / (2 * sigma_i_sq) + self.log_sigmas[i]
            total = total + task_loss
        return total
```

**Key bug to avoid**: If using `torch.exp(self.log_sigmas)` without the `2*`, then `σ = exp(log σ)` and `σ² = exp(2 log σ)`. The original paper uses `log σ` where `σ = exp(log σ)` implicitly. The formula `1/(2σ²) = 1/(2exp(2log σ))` is correct.

## Related Papers in This Wiki

- [[003-film-perez-2018]] — FiLM conditions features; Kendall conditions loss weights — different approaches
- [[013-gradient-surgery-yu-2020]] — PCGrad solves gradient conflicts directly
- [[045-gradnorm-chen-2018]] — GradNorm balances by gradient magnitude
- [[100-popw-protocol-self-analysis]] — Documents Kendall disable decision

## LEGION RULE

When Bashara asks about "should we re-enable Kendall for the activity head loss," reference this paper's finding: Kendall works best when tasks have genuinely different noise levels (e.g., depth estimation is inherently noisier than classification). For POPW, the problem is NOT different noise levels — the problem is that all three losses are small normalized values. Kendall would work IF the losses were unnormalized (e.g., raw cross-entropy with large values).

Applied to POPW: Instead of re-enabling Kendall, consider [[045-gradnorm-chen-2018]] (GradNorm) which balances by gradient magnitude rather than loss scale. Or use [[013-gradient-surgery-yu-2020]] (PCGrad) if gradient conflicts between tasks are the primary problem.
