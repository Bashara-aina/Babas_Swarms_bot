---
paper_id: 078
title: "VideoMAE V2: Scaling Video Masked Autoencoders with Dual Masking"
authors: "Wang, Limin; Huang, Bingkun; Zhao, Zhiyu; Tong, Zhan; He, Yinan; Wang, Yi; Wang, Yali; Qiao, Yu"
year: 2023
venue: "CVPR"
arxiv: "2303.16727"
citations: 450
tier: 7
tags: [video, masked-autoencoder, self-supervised, pretraining, backbone]
popw_relevance: MEDIUM
---

# VideoMAE V2: Scaling Video Masked Autoencoders with Dual Masking

## Why This Paper Matters for POPW

POPW's activity head uses frame-level RGB features from a ResNet-50 backbone. VideoMAE V2 demonstrates that video masked autoencoders are scalable foundation model pre-trainers — meaning POPW could benefit from pre-training on video data before fine-tuning on IKEA ASM frames.

## Core Contribution

VideoMAE V2 solves the scaling problem for video masked autoencoders by introducing a dual masking strategy: encoder processes a subset of tokens while decoder processes another subset, dramatically reducing compute. They successfully train a billion-parameter ViT model achieving SOTA on Kinetics (90.0% K400, 89.9% K600) and Something-Something (68.7% V1, 77.0% V2).

## Key Technical Details

- **Dual Masking**: Encoder operates on subset of video tokens (high masking ratio ~80%), decoder processes different subset
- **Progressive Training**: Initial pre-training on diverse multi-sourced unlabeled dataset → post-pre-training on mixed labeled dataset
- **Billion-parameter ViT**: Successfully scales VideoMAE to video ViT-L/16 with 1B parameters
- **Architecture**: ViT-B/16, ViT-L/16, ViT-H/14 variants with Tube Encoder + Mask Decoder design

## Critical Results (Exact Numbers)

| Metric | Dataset | Their Value | Notes |
|--------|---------|-------------|-------|
| Top-1 | K400 | 90.0% | Single clip, 32 frames |
| Top-1 | K600 | 89.9% | Single clip, 32 frames |
| Top-1 | Something-Something V1 | 68.7% | 4th best reported |
| Top-1 | Something-Something V2 | 77.0% | Strong on fine-grained |

## What POPW Can Steal Directly

- **config.py**: Consider VideoMAE V2 pre-trained ViT-L as frozen backbone for IKEA ASM probing (like Frame2Freq-ST uses DINOv2)
- **train.py**: Dual masking is a training strategy, not directly applicable to POPW's single-frame approach
- **improved3_film/**: The progressive training paradigm (unlabeled → labeled) could apply to POPW's semi-supervised detection pipeline

## Failure Modes and Known Limitations

- Requires massive data (~1M videos) for pre-training — POPW has only 254 videos
- Billion-parameter model won't fit in RTX 3060 12GB — even ViT-B/16 is tight
- Pre-training on Kinetics doesn't guarantee transfer to assembly-specific actions

## Key Equations

Equation 1 — Dual Masking:
$$x_{enc} = \text{Encoder}(x \odot M_{enc})$$
$$x_{dec} = \text{Decoder}(x \odot M_{dec})$$
where $M_{enc} \cap M_{dec} = \emptyset$

## Researcher Intelligence

**Lead Author**: Limin Wang (Shanghai AI Lab / OpenGVLab)
Wang's group has consistently pushed video representation learning from SlowFast to VideoMAE to VideoMAE V2. Motivation: build generalizable video foundation models that transfer across domains.

**Key papers that cite this / build on it:**
- InternVideo2 (2024) — extends dual masking to multi-modal video understanding
- Frame2Freq-ST (CVPR 2026) — uses DINOv2-style spectral adapters, not VideoMAE

## Engineer's Implementation Notes

- VideoMAE V2 code is in OpenGVLab/VideoMAEv2 GitHub — check for frozen backbone extraction scripts
- ViT-L/16 with 224×224 input needs ~20GB for training — POPW's RTX 3060 can't train, but can use as frozen feature extractor
- For POPW: consider VideoMAE V2 pre-trained weights as alternative to DINOv2 if more parameters help with IKEA ASM class imbalance

## Connections to Other Wiki Papers

- [[077-dinov2-oquab-2024]] — DINOv2 is the current frozen backbone choice for Frame2Freq-ST
- [[038-ponbagavathi-frame2freq-2026]] — Frame2Freq-ST achieves 78.1% with DINOv2 + spectral adapters
- [[039-thiyakesan-order-matters-2025]] — Step uses frozen DINOv2 + temporal probe

## POPW Action Item

> **PRIORITY MEDIUM:** Consider VideoMAE V2 pre-trained ViT-L as alternative frozen backbone for temporal action probing — but only if VRAM budget allows ViT-B/16 inference, otherwise stick with DINOv2.
