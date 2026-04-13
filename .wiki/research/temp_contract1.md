---
tags: [research, temporal-attention, lightweight, rtx-3060, video-understanding, action-segmentation]
sources: [arxiv:2006.09220, arxiv:2110.08568, arxiv:2408.02024, arxiv:2203.01057, arxiv:2005.03209, arxiv:2601.04159]
created: 2026-04-13
updated: 2026-04-13
---

# Research Notes: Lightweight Temporal Attention Methods for RTX 3060

## Context
- **Target Hardware**: NVIDIA RTX 3060 (12GB VRAM)
- **Working Set**: T=16 frames at 256 channels
- **Constraint**: Must fit in 12GB VRAM with margin for batch processing

---

## Method 1: MS-TCN++ (Multi-Stage Temporal Convolutional Network)

**Paper Citation**:  
Li, S., Farha, Y.A., Liu, Y., Cheng, M., & Gall, J. (2021). MS-TCN++: Multi-Stage Temporal Convolutional Network for Action Segmentation. IEEE TPAMI. arXiv:2006.09220

**Core Mechanism**:
- Stacked dilated 1D convolutions with exponentially increasing receptive fields
- Multi-stage progressive refinement architecture
- Replaces recurrent structures (LSTM/GRU) with pure convolutions

**Memory Estimate for T=16 at 256 channels**:
- Each TCN layer: ~256 channels × 16 frames × 4 bytes (float32) × kernel_size
- With kernel_size=3 and 4 layers: ~256 × 16 × 4 × 3 × 4 ≈ 196 KB per layer
- Total for 4-stage model: <2 MB
- **OOM Risk: LOW**

**GitHub**: https://github.com/sj-li/MS-TCN2

**Why It Fits RTX 3060**:
- Pure convolutional operations (no attention quadratic cost)
- Constant O(T) memory for temporal reasoning
- Parallelizable, efficient on GPU
- Established architecture with proven real-time inference capability

---

## Method 2: ASFormer (Transformer for Action Segmentation)

**Paper Citation**:  
Yi, F., Wen, H., & Jiang, T. (2021). ASFormer: Transformer for Action Segmentation. BMVC 2021. arXiv:2110.08568

**Core Mechanism**:
- Lightweight Transformer encoder on top of MS-TCN stages
- Locally-constrained attention (O(T × k) instead of O(T²))
- Hierarchical multi-stage refinement
- Action prototypes for constraining output space

**Memory Estimate for T=16 at 256 channels**:
- Local attention with window size k=9 reduces complexity from O(256) to O(144) per head
- With 4 attention heads: 16 × 256 × 4 × 4 bytes ≈ 64 KB for attention weights
- **OOM Risk: LOW**

**GitHub**: https://github.com/ChinaYi/ASFormer

**Why It Fits RTX 3060**:
- Local attention design prevents quadratic memory growth
- k=9 window size maintains locality for action segmentation
- Integrates with existing TCN infrastructure
- Still achieves SOTA (86.7% on 50 Salads vs 85.4% MS-TCN++)

---

## Method 3: EffiDiffAct (Efficient Diffusion Action Segmentation)

**Paper Citation**:  
Wang, S., Wang, S., Li, M., Yang, D., Kuang, H., Qian, Z., & Zhang, L. (2024). Faster Diffusion Action Segmentation. arXiv:2408.02024

**Core Mechanism**:
- Lightweight temporal feature encoder (mitigates rank collapse in self-attention)
- Adaptive skip strategy for dynamic timestep adjustment during inference
- Reduces diffusion sampling steps overhead

**Memory Estimate for T=16 at 256 channels**:
- Temporal encoder replaces full self-attention: ~256 × 16 × 16 × 4 bytes ≈ 256 KB
- No need for full diffusion backbone if using as feature encoder
- **OOM Risk: LOW**

**GitHub**: Not explicitly listed in paper abstract

**Why It Fits RTX 3060**:
- Specifically designed for "real-time applications"
- Lightweight temporal encoder is the key innovation
- Reduces computational overhead compared to standard Transformer-based approaches
- Addresses feature-smoothing issues in long video sequences

---

## Method 4: Colar (Exemplar-Consultation Mechanism)

**Paper Citation**:  
Yang, L., Han, J., & Zhang, D. (2022). Colar: Effective and Efficient Online Action Detection by Consulting Exemplars. CVPR 2022. arXiv:2203.01057

**Core Mechanism**:
- Exemplar-consultation mechanism for similarity measurement
- Aggregates features based on similarity weights (limited computations)
- Long-term dependencies via historical frames as exemplars
- Category-level modeling via representative frames

**Memory Estimate for T=16 at 256 channels**:
- Exemplar store: T × D × K exemplars (K typically small)
- 16 × 256 × 16 × 4 bytes ≈ 256 KB for exemplar store
- **OOM Risk: LOW**

**GitHub**: https://github.com/VividLe/Online-Action-Detection

**Why It Fits RTX 3060**:
- "Lightweight architecture" explicitly designed in paper
- Both similarity measurement and feature aggregation require "limited computations"
- Achieves new high performance while being efficient
- Online action detection use case aligns with real-time requirement

---

## Method 5: Hierarchical Attention Network for Action Segmentation

**Paper Citation**:  
Gammulle, H., Denman, S., Sridharan, S., & Fookes, C. (2020). Hierarchical Attention Network for Action Segmentation. Pattern Recognition Letters. arXiv:2005.03209

**Core Mechanism**:
- Multi-scale temporal attention framework
- Frame-level and segment-level embeddings
- Hierarchical recurrent attention analyzing video at multiple temporal scales

**Memory Estimate for T=16 at 256 channels**:
- Hierarchical attention at segment level: O(T²) at segment level only
- Frame-level attention: O(T × scale)
- 16 × 256 × 16 × 4 bytes ≈ 256 KB per attention layer
- **OOM Risk: LOW**

**GitHub**: Not explicitly available

**Why It Fits RTX 3060**:
- "Simple, lightweight, yet extremely effective architecture"
- Multi-scale approach allows trading off resolution for memory
- Static overhead/dynamic ego-centric camera views
- Validated on MERL Shopping, 50 salads, Georgia Tech Egocentric datasets

---

## Method 6: ToTMNet (FFT-accelerated Toeplitz Temporal Mixing Network)

**Paper Citation**:  
Frants, V., Agaian, S., & Panetta, K. (2026). ToTMNet: FFT-Accelerated Toeplitz Temporal Mixing Network for Lightweight Remote Photoplethysmography. arXiv:2601.04159

**Core Mechanism**:
- Replaces temporal attention with FFT-accelerated Toeplitz temporal mixing
- Full-sequence temporal receptive field with linear parameters in clip length
- Near-linear time using circulant embedding and FFT-based convolution
- Gated temporal mixer combining local depthwise convolution with global Toeplitz mixing

**Memory Estimate for T=16 at 256 channels**:
- Toeplitz operator: O(T × D) parameters, not O(T²)
- 16 × 256 × 4 bytes ≈ 16 KB for operator
- FFT-based computation: minimal intermediate buffers
- **OOM Risk: VERY LOW**

**GitHub**: Not yet available (preprint)

**Why It Fits RTX 3060**:
- "Only 63k parameters" - extremely lightweight
- Linear time complexity O(T log T) via FFT
- No quadratic attention memory overhead
- Replaces attention entirely with structured convolution

---

## Summary Table

| Method | Memory (T=16, 256ch) | OOM Risk | GitHub |
|--------|----------------------|----------|--------|
| MS-TCN++ | ~2 MB | Low | Yes |
| ASFormer | ~64 KB + weights | Low | Yes |
| EffiDiffAct | ~256 KB | Low | Not listed |
| Colar | ~256 KB | Low | Yes |
| Hierarchical Attn | ~256 KB | Low | No |
| ToTMNet | ~16 KB | Very Low | No |

---

## RTX 3060 Feasibility Assessment

All 6 methods are **feasible** for RTX 3060 with T=16 frames at 256 channels.

**Top Recommendations for POPW Architecture**:

1. **MS-TCN++** (Highest practicality) - Proven real-time capability, pure convolution, no attention overhead
2. **ToTMNet** (Most innovative) - 63k parameters, FFT-based, replaces attention entirely  
3. **ASFormer** (Best accuracy/compute trade) - Local attention maintains SOTA accuracy with reduced memory

---

## References

- MS-TCN++: https://arxiv.org/abs/2006.09220
- ASFormer: https://arxiv.org/abs/2110.08568
- EffiDiffAct: https://arxiv.org/abs/2408.02024
- Colar: https://arxiv.org/abs/2203.01057
- Hierarchical Attn: https://arxiv.org/abs/2005.03209
- ToTMNet: https://arxiv.org/abs/2601.04159
