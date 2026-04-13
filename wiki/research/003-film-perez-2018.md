---
title: "003 - FiLM Perez Strub de Vries 2018"
type: research
status: active
tags: [film, conditioning, multi-task, visual-reasoning, feature-modulation]
created: 2026-04-13
updated: 2026-04-13
summary: FiLM (Feature-wise Linear Modulation) learns an affine transformation γ/β to condition neural network features on auxiliary input. POPW's Phase 2 goal is FiLM conditioning from pose→activity head, enabling pose-guided action recognition.
wikilinks:
  - [[001-resnet-he-2016]]
  - [[004-kendall-uncertainty-2018]]
  - [[025-cross-stitch-misra-2016]]
  - [[026-mtan-liu-2019]]
  - [[063-pose-guided-action-2021]]
  - [[100-popw-protocol-self-analysis]]
confidence: high
source: canonical
---

# FiLM: Visual Reasoning with a General Conditioning Layer

**Authors:** Ethan Perez, Florian Strub, Harm de Vries, Pieter Abbeel
**Year:** 2018
**Venue:** ICLR / CVPR (featured)
**ArXiv/DOI:** [arXiv:1709.07871](https://arxiv.org/abs/1709.07871)
**Citation count:** ~4,000+
**Relevance to POPW:** POPW's Phase 2 plan is FiLM conditioning between the pose head and activity head (poseFiLMModule in improved4_transformer/model.py). The pose heatmaps would provide γ/β parameters to modulate activity features.

## Core Contribution

FiLM learns to modulate intermediate neural network features using an auxiliary conditioning input. The modulation is a simple affine transform: `FiLM(x) = γ ⊙ x + β`, where `γ,β` are predicted from the conditioning signal. This is mathematically equivalent to batch norm with predicted scale/shift — but applied anywhere in the network, not just after a specific normalization layer.

## Key Technical Details

- **FiLM equation**: `f_out = γ · f_in + β`
  - `γ,β` are predicted by a small conditioning network (e.g., 2-layer FC)
  - `⊙` is element-wise multiplication (Hadamard product)
- **Where to inject FiLM**: After normalization (BN), before activation (ReLU)
- **Initialization**: `γ ≈ 1.0`, `β ≈ 0.0` (near-identity at start) is critical for stable training
- **Conditioning network**: Takes auxiliary input (e.g., pose coordinates, scene context) → outputs γ,β vectors
- **Multi-FiLM**: Multiple FiLM layers at different depths capture different aspects of conditioning
- **Relation to other conditioning**: FiLM is more expressive than skip connections (linear add) or feature concat (quadratic param growth)

## Results They Achieved

| Task | Method | Accuracy |
|------|--------|----------|
| Visual Reasoning ( CLEVR ) | FiLM + ResNet | 98.7% |
| VQA | FiLM + LSTM | 68.5% |
| Captioning | FiLM + ResNet | 41.5 CIDEr |
| Baseline (no conditioning) | ResNet only | 52.3% (CLEVR) |

## What POPW Can Steal Directly

1. **γ/β initialization** (CRITICAL): Initialize `γ = 1.0, β = 0.0`. This is the single most important implementation detail. If γ starts near 0, features are zeroed; if β starts large, features are shifted randomly. Check: `improved/config.py:USE_FILM = False` (not yet enabled).
2. **FiLM injection location**: After BatchNorm, before ReLU. This is the standard placement.
3. **Conditioning network design**: Small 2-layer MLP from pose features → γ,β vectors matching feature dimension (256 for FPN features, 2048 for C5).
4. **Multi-FiLM at different depths**: Consider injecting FiLM at both C5 level and after the activity head's hidden layer.

## Implemented in POPW?

- [ ] NO — `improved/config.py:USE_FILM = False`. Aspirational for Phase 2.
- [ ] PARTIAL — `improved4_transformer/model.py` has `PoseFiLMModule` class defined but `USE_FILM` is `False` in config, so it is not trained.

## Failure Modes / Limitations

- **γ/β explosion**: Without careful initialization or regularization, γ can grow large causing feature scale instability. Fix: clip γ values, use stronger weight decay on conditioning network.
- **Conditioning signal quality**: If pose estimates are noisy (wrong keypoint locations), the γ/β will be junk. This is why POPW should only enable FiLM after pose head achieves ≥85% PCK@0.1.
- **Information bottleneck**: The conditioning network must compress pose info into γ/β vectors. If pose features are 256-dim and output is 256-dim, no compression. If pose features → 64-dim → γ/β, information is lost.
- **Competing conditioning signals**: If both pose and detection features condition the activity head simultaneously, they may conflict. Use separate FiLM layers with separate conditioning networks.

## Key Equations

**FiLM modulation:**
```
γ, β = C(z)  # conditioning network output
f_out = γ ⊙ f_in + β  # element-wise affine transform
```

**Conditioning network (MLP):**
```
C(z) = W_2 σ(W_1 z + b_1) + b_2
where γ, β = split(C(z), 2)  # split into scale and shift
```

## Implementation Notes

```python
# FiLM implementation for pose→activity conditioning
class PoseFiLMModule(nn.Module):
    """Predict γ/β from pose heatmaps to modulate activity features."""

    def __init__(self, pose_channels=17, film_dim=2048):
        super().__init__()
        # Pose encoder: heatmaps → compact representation
        self.pose_encoder = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Linear(pose_channels, 128),
            nn.ReLU(),
        )
        # Conditioning network: pose → γ, β
        self.conditioning = nn.Linear(128, 2 * film_dim)  # γ and β

    def forward(self, pose_heatmaps, activity_features):
        # Encode pose
        pose_emb = self.pose_encoder(pose_heatmaps)  # [B, 128]
        # Predict γ, β
        gamma_beta = self.conditioning(pose_emb)  # [B, 2*film_dim]
        gamma, beta = gamma_beta.chunk(2, dim=-1)  # each [B, film_dim]
        # FiLM modulation: γ=1, β=0 initialization via careful init
        gamma = gamma + 1  # init γ≈1 (identity)
        beta = beta + 0    # init β≈0 (identity)
        # Apply to activity features (reshape γ,β to broadcast)
        if activity_features.dim() == 2:
            return activity_features * (1 + gamma) + beta
        elif activity_features.dim() == 4:
            # [B, C, H, W] → [B, C, 1, 1] for broadcasting
            return activity_features * (1 + gamma.view(-1, gamma.size(-1), 1, 1)) \
                                        + beta.view(-1, beta.size(-1), 1, 1)
```

**Critical initialization**: After the last linear layer, add `nn.init.zeros_(self.conditioning.bias)` so that at initialization `C(z) ≈ 0`, and after `+1`/`+0` offset, `γ≈1, β≈0`.

## Related Papers in This Wiki

- [[004-kendall-uncertainty-2018]] — Kendall also conditions on task uncertainty (different mechanism)
- [[025-cross-stitch-misra-2016]] — Cross-stitch is a precursor linear combination approach
- [[026-mtan-liu-2019]] — MTAN uses learned attention masks instead of affine transforms
- [[063-pose-guided-action-2021]] — Pose-guided action recognition is POPW's application domain

## LEGION RULE

When Bashara asks about "FiLM vs other cross-task conditioning methods," reference this paper's finding: FiLM is more parameter-efficient than cross-stitch (which needs N×N parameters for N tasks) and more expressive than hard parameter sharing. The affine transform can capture complex task relationships while maintaining a single shared representation.

Applied to POPW: Pose features → γ/β conditioning → modulates activity head. The intuition: a "screwdriver twisting" activity has a distinctive wrist-elbow-shoulder alignment. FiLM would let the pose head tell the activity head "I'm seeing a ~90° elbow angle, which is characteristic of screwdriver use." Without FiLM, the activity head must infer pose information from the shared C5 features, which are also needed for detection.

Note: FiLM is NOT yet implemented in POPW's active training pipeline. Enable in `improved/config.py:USE_FILM = True` after pose head achieves ≥85% PCK@0.1.
