---
title: Temp Contract4
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
summary: 'This document synthesizes research from Contracts 1-3 into a unified comparison
  table for POPW architecture decisions. The goal is to identify the best methods
  for:'
wikilinks: []
confidence: medium
source: research
---

# Contract 4 Synthesis: Comparison Table and Novelty/Contribution Analysis

## Overview

This document synthesizes research from Contracts 1-3 into a unified comparison table for POPW architecture decisions. The goal is to identify the best methods for:
1. **Temporal modeling** in the activity/pose heads (Contract 1)
2. **Bidirectional cross-modal communication** between pose and activity (Contract 2)
3. **BiGRU replacement** with more efficient SSM alternatives (Contract 3)

---

## Comparison Table

| Method | Memory (T=16, 256ch) | Compute (GFLOPs est.) | RTX 3060 Feasibility | Bidirectional Support | Novelty Score (1-5) | Research Contribution (1-5) |
|--------|----------------------|----------------------|----------------------|----------------------|---------------------|---------------------------|
| **Temporal Attention Methods** |
| MS-TCN++ | ~2 MB | ~5 GFLOPs | ✅ Feasible | No | 3 | 3 |
| ASFormer | ~64 KB | ~3 GFLOPs | ✅ Feasible | No | 4 | 4 |
| EffiDiffAct | ~256 KB | ~8 GFLOPs | ✅ Feasible | No | 3 | 3 |
| Colar | ~256 KB | ~4 GFLOPs | ✅ Feasible | No | 3 | 3 |
| Hierarchical Attn | ~256 KB | ~6 GFLOPs | ✅ Feasible | No | 4 | 3 |
| ToTMNet | ~16 KB | ~1 GFLOPs | ✅ Feasible | No | 5 | 4 |
| **SSM Methods (BiGRU Alternatives)** |
| Mamba | ~16 KB | ~2 GFLOPs | ✅ Feasible | No | 5 | 5 |
| S4 | ~16 KB | ~2 GFLOPs | ✅ Feasible | No | 5 | 5 |
| S4ND | ~256 KB | ~4 GFLOPs | ✅ Feasible | No | 4 | 4 |
| **Cross-Modal Bidirectional Methods** |
| ATSS | ~1-2 MB | ~15 GFLOPs | ⚠️ Borderline | Yes | 4 | 4 |
| LTX-2 | ~2-4 MB | ~20 GFLOPs | ⚠️ Borderline | Yes | 5 | 5 |
| TopicVD | ~512 KB | ~8 GFLOPs | ✅ Feasible | Yes | 3 | 3 |
| MMN (MSM+MTM) | ~512 KB | ~5 GFLOPs | ✅ Feasible | Yes | 4 | 4 |
| **Reference Methods** |
| Video Swin Transformer | ~4 GB | ~50 GFLOPs | ⚠️ Needs careful batching | No | 5 | 5 |
| BiGRU (baseline) | ~32 MB | ~4 GFLOPs | ✅ Feasible | No | 1 | 1 |

---

## Novelty/Contribution Analysis

### Tier 1: Highest Research Contribution (Score 5)

**1. Mamba (SSM)**
- **Novelty**: First选择性 state space model with input-dependent selection mechanism
- **Contribution**: Demonstrates SSMs can match Transformers with linear complexity
- **Impact**: Enabled new research direction in efficient sequence modeling
- **Limitation**: Long-range dependency handling still being researched

**2. S4 (Structured State Space Sequence Model)**
- **Novelty**: First parallelizable SSM with HiPPO initialization for long-range dependencies
- **Contribution**: Theoretical foundation for continuous-time sequence modeling
- **Impact**: Proved SSMs viable for NLP and genomics benchmarks
- **Limitation**: Data-independent matrices limit content-aware modeling

**3. LTX-2 (Bidirectional Audio-Visual)**
- **Novelty**: First unified audio-visual model with bidirectional cross-attention
- **Contribution**: 14B+5B parameters with efficient cross-modal fusion
- **Impact**: State-of-the-art audiovisual generation
- **Limitation**: Very high compute requirements, pre-trained only

### Tier 2: High Novelty (Score 4)

**4. Video Swin Transformer**
- **Novelty**: 3D shifted window attention for video
- **Contribution**: Unified spatial-temporal modeling without quadratic complexity
- **Impact**: SOTA on Kinetics-400, Something-Something-v2
- **Limitation**: Memory intensive for large batches

**5. ATSS (Cross-modal Detection)**
- **Novelty**: Bidirectional cross-attentive fusion with triple-similarity matrices
- **Contribution**: Novel approach to cross-modal anomaly detection
- **Impact**: Strong generalization on video generation detection
- **Limitation**: Higher memory overhead than simpler methods

**6. ToTMNet (FFT-based Temporal Mixing)**
- **Novelty**: Replaces attention with FFT-accelerated Toeplitz matrices
- **Contribution**: 63k parameter ultra-lightweight temporal modeling
- **Impact**: Enables real-time rPPG on edge devices
- **Limitation**: Domain-specific (rPPG), may not generalize

**7. MMN (Motion Modulation)**
- **Novelty**: Dual-stream motion-guided modulation with consistency loss
- **Contribution**: Explicit bidirectional pose-motion communication
- **Impact**: SOTA on micro-action recognition
- **Limitation**: Skeleton-specific, needs adaptation for POPW

### Tier 3: Moderate Novelty (Score 3)

**8. ASFormer**
- **Novelty**: Lightweight transformer with local attention for action segmentation
- **Contribution**: Combines TCN multi-stage refinement with transformer
- **Impact**: 86.7% on 50 Salads (SOTA at time)
- **Limitation**: Less novel than pure SSM approaches

**9. TopicVD**
- **Novelty**: Cross-modal bidirectional attention for video-text
- **Contribution**: Video-guided multimodal translation
- **Impact**: Demonstrates video context improves translation
- **Limitation**: Domain-specific (translation)

**10. MS-TCN++**
- **Novelty**: Multi-stage dilated convolutions for action segmentation
- **Contribution**: Established multi-stage TCN architecture
- **Impact**: Foundation for many follow-up methods
- **Limitation**: Less novel than attention-based approaches

---

## Top 3 Ranked Recommendations for POPW

### Recommendation 1: Mamba for BiGRU Replacement

**Why**: Mamba provides the best combination of:
- **Memory efficiency**: ~16 KB for T=16, 256 channels (vs 32 MB for BiGRU)
- **Compute efficiency**: ~2 GFLOPs (vs ~4 GFLOPs for BiGRU)
- **Scalability**: Linear O(T) complexity - handles longer sequences easily
- **Parallelism**: Full GPU parallelization during training
- **Content-awareness**: Selection mechanism focuses on relevant temporal features

**Implementation**: Replace BiGRU layers with MambaBlock from `mamba-ssm` library

### Recommendation 2: MS-TCN++ for Activity Head Temporal Modeling

**Why**: MS-TCN++ offers:
- **Proven real-time capability**: Established in action segmentation
- **Pure convolution**: No attention overhead
- **Progressive refinement**: Multi-stage architecture aligns with POPW's FiLM conditioning
- **Memory**: ~2 MB fits easily in RTX 3060
- **GitHub available**: Well-tested implementation

**Implementation**: Use as temporal encoder before activity classification head

### Recommendation 3: MMN (MSM+MTM) for Bidirectional Pose-Activity Communication

**Why**: MMN provides:
- **Low overhead**: ~2× FiLM memory overhead (~512 KB)
- **Low complexity**: Simple MLPs, easy to implement
- **Explicit bidirectionality**: MSM↔MTM with consistency loss
- **Motion-based**: Aligns with POPW's agent state modeling
- **GitHub available**: Reference implementation

**Implementation**: Dual-stream modulation where pose features modulate activity features and vice versa

---

## Feasibility Assessment for RTX 3060

### Fully Feasible (✅) - No concerns:
- Mamba (~16 KB)
- S4 (~16 KB)
- ToTMNet (~16 KB)
- MS-TCN++ (~2 MB)
- ASFormer (~64 KB)
- Colar (~256 KB)
- Hierarchical Attn (~256 KB)
- TopicVD (~512 KB)
- MMN (~512 KB)
- BiGRU (~32 MB)

### Borderline (⚠️) - Requires careful batching:
- Video Swin Transformer (~4 GB) - reduce batch size to 2
- ATSS (~1-2 MB) - depends on implementation
- LTX-2 (~2-4 MB) - only if using as feature extractor, not training

### Not Recommended (❌):
- LTX-2 full training (14B+5B parameters - requires A100)

---

## Key Insights

1. **SSMs (Mamba, S4) are the most efficient** for pure temporal modeling
2. **Cross-modal bidirectionality adds overhead** - worth it only if POPW needs pose↔activity communication
3. **MS-TCN++ is the practical choice** for action segmentation without attention
4. **ToTMNet's FFT approach** is promising for ultra-lightweight applications
5. **Video Swin is proven but memory-heavy** - use only if temporal modeling is critical bottleneck

---

## References

- Contract 1: `.wiki/research/temp_contract1.md`
- Contract 2: `.wiki/research/temp_contract2.md`
- Contract 3: `.wiki/research/temp_contract3.md`
- Video Swin: `.wiki/research/014-video-swin-transformer-liu-2022.md`
