---
title: Temporal Action Segmentation Survey Ding 2022
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
summary: '**Ding & Sener** | TPAMI 2024 (arXiv:2210.10352, 2022) | [arXiv:2210.10352](https://arxiv.org/abs/2210.10352)'
wikilinks: []
confidence: medium
source: research
---

# Temporal Action Segmentation: An Analysis of Modern Techniques

**Ding & Sener** | TPAMI 2024 (arXiv:2210.10352, 2022) | [arXiv:2210.10352](https://arxiv.org/abs/2210.10352)

## Overview

This **comprehensive survey** analyzes temporal action segmentation (TAS) — the task of densely predicting action labels for each frame in long, untrimmed videos containing multiple action classes. Unlike action recognition which classifies entire videos, TAS requires frame-level predictions maintaining temporal consistency.

The survey categorizes modern TAS methods into:
1. ** CTC-based** (Connectionist Temporal Classification) — frame-wise decoding
2. **Attention-based** — temporal context aggregation
3. **Temporal Convolutional Networks (TCN)** — dilated convolutions for long-range modeling
4. **Graph-based** — action transitions as graph structures

## Key Findings

### Dataset Overview

| Dataset | Videos | Classes | Avg. Actions | Notes |
|---------|--------|---------|--------------|-------|
| 50 Salads | 50 | 17 | ~7 | Academic, controlled |
| Breakfast | 171 | 10 | ~6 | Egocentric |
| YouTube Instructions | 150 | 27 | ~9 | Instructional |
| IKEA ASM | 3M frames | 16 | ~10 | Industrial assembly |

### State-of-the-Art Methods

| Method | Type | 50 Salads (Acc) | Breakfast (Acc) |
|--------|------|-----------------|-----------------|
| MS-TCN++ | TCN | 85.4% | 65.0% |
| ASFormer | Transformer | 86.7% | 67.1% |
| ActionFormer | Transformer | 88.3% | 68.5% |

## POPW Relevance

> [!CRITICAL]
> POPW classifies **FRAMES** in assembly sequences — this IS temporal action segmentation. The IKEA ASM task is a TAS problem where we predict atomic actions per frame (screw, attach, align). The survey's TCN-based methods (MS-TCN++) are directly applicable to WorkerNet's action recognition head.

> [!NOTE]
> MS-TCN++ (073) and ASFormer (074) are the top TCN/Transformer methods cited in this survey. Understanding this hierarchy helps position WorkerNet within the literature.

## Code Availability

- Awesome TAS GitHub: https://github.com/nus-cvml/awesome-temporal-action-segmentation
- Survey paper analysis tools often accompany the paper

## See Also

- [[research/073-ms-tcn-li-2021]] — MS-TCN++ for temporal action segmentation
- [[research/074-asformer-yi-2021]] — ASFormer Transformer approach
- [[research/068-i3d-carreira-2017]] — I3D for comparison
