---
paper_id: 038
title: "Frame2Freq: Spectral Adapters for Fine-Grained Video Understanding"
authors: "Ponbagavathi, Thinesh Thiyakesan; Seibold, Constantin; Roitberg, Alina"
year: 2026
venue: "CVPR"
arxiv: "2602.18977"
citations: 12
tier: 4
tags: [spectral-methods, frequency-analysis, fine-grained-action, vision-foundation-models, peft, cvpr2026]
popw_relevance: CRITICAL
---

# Frame2Freq: Spectral Adapters for Fine-Grained Video Understanding

## Why This Paper Matters for POPW

Frame2Freq (CVPR 2026) is the **current SOTA on IKEA ASM at 78.1% Top-1**. POPW must beat this benchmark. This paper defines the competitive baseline and reveals that frequency-aware temporal modeling is key for fine-grained assembly action recognition.

## Core Contribution

Frame2Freq addresses the fundamental limitation of adapting image-pretrained Vision Foundation Models (VFMs) to video: existing time-domain adapters focus on static image cues and very fast temporal changes, missing crucial medium-speed motion patterns that distinguish fine-grained actions (e.g., opening vs. closing a bottle). Frame2Freq uses FFT along the temporal dimension to learn frequency-band specific embeddings that capture multi-scale temporal dynamics.

## Key Technical Details

- **Spectral Encoding**: Applies Fast Fourier Transform (FFT) along time dimension to learn frequency-band specific embeddings
- **PEFT Framework**: Parameter-efficient fine-tuning suitable for limited data scenarios (POPW has only 254 videos)
- **Multi-scale Temporal Modeling**: Adaptively highlights discriminative frequency ranges across different time scales
- **Architecture**: Vision Transformer backbone + spectral adapter module replacing time-domain adapters
- **FFT along time**: Captures medium-speed motion patterns that spatial or temporal convolutions miss
- **Key insight**: Time-domain adapters pick up static cues and fast flicker but miss medium-speed motion; spectral encoding captures multi-scale temporal dynamics

## Critical Results (Exact Numbers)

| Metric | Dataset | Frame2Freq | Previous SOTA | Improvement |
|--------|---------|------------|---------------|-------------|
| Top-1 | IKEA ASM | **78.1%** | 76.8% (Step) | +1.3% |
| Top-1 | FineGYM | 89.2% | 87.1% | +2.1% |
| Top-1 | Something-Something V2 | 77.0% | 74.8% | +2.2% |

**IKEA ASM Result**: 78.1% Top-1 on official cross-environment split — **POPW MUST BEAT THIS**

## What POPW Can Steal Directly

- **model.py**: Consider spectral adapter design for temporal modeling instead of pure 2D CNN
- **config.py**: Set Frame2Freq-ST as reference SOTA baseline (78.1% target)
- **improved3_film/**: FFT-based temporal encoding could complement FiLM conditioning
- **code**: https://github.com/th-nesh/Frame2Freq

## Failure Modes and Known Limitations

- Requires Vision Foundation Model (DINOv2, etc.) — adds pretraining complexity
- FFT computation adds overhead for very long videos
- Spectral adapters may overfit to specific frequency patterns in training data
- Not validated on industrial assembly with severe class imbalance (2545:1)

## Key Equations

Equation 1 — Spectral Adapter Forward:
$$F_{out} = \text{MLP}(\text{FFT}(F_{in})) \odot F_{in}$$
Apply FFT to intermediate features, learn frequency-band weights, multiply back

## Researcher Intelligence

**Thinesh Thiyakesan Ponbagavathi** (University of Toronto / University of Stuttgart) led this work with **Constantin Seibold** and **Alina Roitberg**. Motivation: Image-pretrained VFMs adapted to video typically use time-domain adapters that miss medium-speed motion patterns. The insight that FFT along time captures discriminative frequency bands is both simple and powerful. The paper is notable because it surpasses fully fine-tuned models on 4 of 5 fine-grained benchmarks using only PEFT adapters.

**Key papers that cite this / build on it:**
- Step (039) — uses frozen DINOv2 + temporal probe, achieves 76.8%
- POPW — must beat 78.1% using FiLM-conditioned RGB-CNN approach

## Engineer's Implementation Notes

- Frame2Freq code is on GitHub — check for frozen backbone extraction and IKEA ASM splits
- For POPW: Use Frame2Freq's 78.1% as the baseline to beat, not just "75% stretch goal"
- DINOv2 + spectral adapters is the winning combination — POPW uses ResNet-50 + FiLM
- Key difference: POPW uses pose-conditioned FiLM (novel), Frame2Freq uses spectral adapters (established)
- Spectral adapter adds ~0.5% parameters vs FiLM which adds ~1% but conditions on pose

## Connections to Other Wiki Papers

- [[039-thiyakesan-order-matters-2025]] — Step achieves 76.8% with frozen DINOv2 + temporal probe
- [[040-ponbagavathi-probing-foundation-2024]] — Earlier probing work establishing VFM approach
- [[077-dinov2-oquab-2024]] — DINOv2 is the VFM backbone for Frame2Freq

## POPW Action Item

> **PRIORITY CRITICAL:** Set Frame2Freq (78.1% Top-1) as POPW's competitive baseline to beat. Any POPW experiment must report Frame2Freq-ST numbers for comparison. The POPW FiLM approach is novel compared to spectral adapters — if FiLM + pose conditioning achieves competitive accuracy, that proves POPW's thesis contribution.
