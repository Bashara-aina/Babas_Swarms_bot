---
title: Video Swin Transformer Liu 2022
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
summary: '**Liu, Ning, Cao, Wei, Zhang, Lin, Hu** | CVPR 2022 | [arXiv:2106.13230](https://arxiv.org/abs/2106.13230)'
wikilinks: []
confidence: medium
source: research
---

# Video Swin Transformer

**Liu, Ning, Cao, Wei, Zhang, Lin, Hu** | CVPR 2022 | [arXiv:2106.13230](https://arxiv.org/abs/2106.13230)

## Overview

The **Video Swin Transformer** extends the Swin Transformer architecture to video understanding by replacing 2D windows with 3D windows (temporal × spatial) while maintaining the local attention mechanism that makes Swin efficient. The architecture achieves state-of-the-art on video classification benchmarks by treating video as a 3D volume (T×H×W) rather than separate spatial and temporal dimensions.

## Architecture

### Core Innovation: 3D Shifted Window Attention

Building on Swin Transformer's success in images, Video Swin Transformer applies **3D window-based self-attention**:

1. **3D windows**: `[T, H, W]` windows spanning time, height, and width
2. **Shifted windows**: Cross-block shifting enables cross-window communication without expensive global attention
3. **Hierarchical design**: 4-stage pyramid (similar to Swin-T/S/B/L variants)

### Key Properties

- **Locality inductive bias**: Better speed-accuracy trade-off than global attention approaches
- **Pretrained on Kinetics-400**: ImageNet-1K pre-training → Kinetics-400 video pre-training
- **Native 3D processing**: End-to-end temporal modeling unlike two-stream approaches

## Performance

| Benchmark | Video Swin (K400 pretrained) | Previous SOTA |
|-----------|------------------------------|---------------|
| Kinetics-400 | 83.1% (top-1) | 81.3% (SlowFast) |
| Kinetics-600 | 85.3% | — |
| AVA 2.2 | 39.0% (mAP) | 38.4% (SlowFast) |

## POPW Relevance

> [!NOTE]
> Video Swin Transformer's 3D window attention is compute-intensive for long assembly videos. The locality bias is interesting for assembly sequences (local temporal patterns like "screw → attach → align" occur in windows). However, the architecture is heavier than TSM — may not be RTX 3060 friendly for POPW's real-time requirements.

## Code Availability

- Official: https://github.com/SwinTransformer/Video-Swin-Transformer
- Hugging Face: https://huggingface.co/Tonic/video-swin-transformer

## See Also

- [[research/069-tsm-lin-2019]] — TSM (efficient, 2D cost)
- [[research/071-slowfast-feichtenhofer-2019]] — SlowFast for comparison
