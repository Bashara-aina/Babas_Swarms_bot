---
title: "Vision Mamba (Vim): Bidirectional SSM for Visual Representation"
created: 2026-04-14
modified: 2026-04-14
tags: [vision-mamba, vim, ssbidirectional-ssm, vision-backbone, ss2d, visual-representation, mamba]
authors: [Liang, Liao, Zhang, Wang, Liu, Wang]
type: research
summary: "Vim — first pure SSM-based vision backbone with no self-attention. Flattened image patches as sequential tokens → bidirectional Mamba blocks. Outperforms DeiT on ImageNet, COCO, ADE20k. Foundation for per-frame pose encoding in Mamba-based POPW extension."
wikilinks:
  - [[mamba-selective-ssm]]
  - [[video-mamba]]
  - [[mamba-pose-activity-survey]]
source: https://arxiv.org/abs/2401.09417
---

# Vision Mamba (Vim): Efficient Visual Representation Learning with Bidirectional State Space Model

## Paper Info
- **arXiv**: [2401.09417](https://arxiv.org/abs/2401.09417)
- **Authors**: Lianghui Zhu, Bencheng Liao, Qian Zhang, Xinlong Wang, Wenyu Liu, Xinggang Wang
- **Institution**: Huazhong University of Science and Technology
- **Venue**: arXiv Jan 2024

## Core Contribution

**Vim** is the first pure SSM-based vision backbone — no Transformer, no self-attention. Uses bidirectional Mamba blocks with position embeddings to process image patches as sequential tokens. Achieves 2.8× faster inference than DeiT with 86.8% less GPU memory at 1248×1248 resolution.

## Architecture

```
Image → PatchEmbed (linear projection)
     → Flatten to sequence of patches
     → Position embedding (2D-aware)
     → Bidirectional Mamba blocks (N layers)
     → Classification / Downstream head
```

**2D Position Embedding**: Unlike language where 1D position is sufficient, Vim uses a 2D-aware position embedding to preserve spatial structure when flattening image patches to a 1D sequence.

**Bidirectional SSM**: Each Mamba block processes the patch sequence in both forward and backward directions. The backward scan provides future context (acausal) — similar to how a person can look at a body pose and infer what motion is being performed based on knowing typical assembly sequences.

## Vim Encoder for POPW Frame Encoding

For POPW's per-frame feature extraction:

```
Frame (H×W×3) → PatchEmbed → [T_patches, C] sequence
              → 2D Position Embedding
              → Vim blocks → [T_patches, C] feature
              → Global Average Pool → C-dim feature vector
```

This replaces ResNet-50-FPN as the per-frame backbone. The bidirectional SSM captures spatial relationships between patches while being more efficient than attention.

## Comparison with ResNet-50 for POPW

| Aspect | ResNet-50-FPN | Vim (Mamba backbone) |
|--------|---------------|---------------------|
| Parameters | ~25M | ~25M (similar) |
| GPU Memory | Baseline | 86.8% less at high-res |
| Inference Speed | Baseline | 2.8× faster |
| Temporal modeling | None (2D backbone) | Bidirectional SSM on patches |
| Position awareness | 2D convolutions | 2D position embedding |
| Pose encoding | Via FPN multi-scale | Via patch sequence bidirectional SSM |
| Attention | None | No self-attention |

## Bidirectional Encoding for Pose-Aware Features

Vim's bidirectional processing is key for POPW's pose-conditioned approach:

**Forward scan**: Captures causal spatial context — patch relationships in reading order
**Backward scan**: Captures anti-causal spatial context — patches inform each other in reverse order

For assembly images, the backward scan means: "knowing which parts of the image are furniture/background helps identify which patches contain human hands and body parts." This is complementary to POPW's explicit pose decoding — Vim provides richer spatial context per frame before pose decoding.

## Mamba + PoseFiLM Combination

For a Mamba-based POPW extension:

1. **Vim per-frame encoder** replaces ResNet-50-FPN
2. **Pose head** still decodes from Vim features (not from PoseFiLM output)
3. **PoseFiLM** still modulates Vim features using decoded keypoints
4. **BiGRU or Mamba temporal head** processes pose-conditioned feature sequences

The Vim backbone provides richer spatial encoding per frame; PoseFiLM then modulates it with pose predictions; the temporal head tracks assembly state.

## Key Insight for POPW v2

Vim demonstrates that SSM can replace self-attention for vision without performance loss. This validates a future POPW v2 that replaces ResNet-50-FPN with a Vim-style backbone and replaces BiGRU with bidirectional Mamba — achieving both per-frame spatial reasoning and temporal pose-activity modeling in a single SSM-based architecture.

## References

- Zhu et al. (2024). "Vision Mamba: Efficient Visual Representation Learning with Bidirectional State Space Model." arXiv:2401.09417