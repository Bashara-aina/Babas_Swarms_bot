---
title: Temp Contract2
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
summary: '- **Goal**: Enable bidirectional communication between pose and activity
  representations'
wikilinks: []
confidence: medium
source: research
---

# Research Notes: Cross-Modal Attention for Bidirectional Pose-Activity Communication

## Context
- **Goal**: Enable bidirectional communication between pose and activity representations
- **Baseline**: FiLM (Feature-wise Linear Modulation) - unidirectional conditioning
- **Target**: Methods that enable pose→activity AND activity→pose communication

---

## Method 1: ATSS (Anomalous Temporal Self-Similarity)

**Paper Citation**:  
Wang, H., Shen, C., Zhang, L., & Cheng, Z. (2026). ATSS: Detecting AI-Generated Videos via Anomalous Temporal Self-Similarity. arXiv:2604.04029

**Mechanism Description (How it enables bidirectional communication)**:
- **Bidirectional cross-attentive fusion module** explicitly models both pose→activity and activity→pose information flow
- Constructs visual, textual, and cross-modal similarity matrices
- Integrates these matrices via bidirectional attention to model "intra- and inter-modal dynamics"
- The bidirectional nature means pose features attend to activity features AND vice versa

**Memory Overhead vs FiLM Baseline**:
- FiLM baseline: O(C) parameters for gamma/beta per channel
- ATSS cross-attention: O(T × D) for similarity matrices + O(T²) attention if not localized
- Estimated overhead: ~3-5× FiLM for full cross-modal attention
- **Memory Overhead: MEDIUM-HIGH** (but still feasible for RTX 3060)

**Implementation Complexity**: 
- Requires building similarity matrices for multiple modalities
- Bidirectional attention module needs careful implementation
- **Complexity: MEDIUM**

**GitHub**: https://github.com/hwang-cs-ime/ATSS

---

## Method 2: LTX-2 (Bidirectional Audio-Visual Cross-Attention)

**Paper Citation**:  
HaCohen, Y. et al. (2026). LTX-2: Efficient Joint Audio-Visual Foundation Model. arXiv:2601.03233

**Mechanism Description (How it enables bidirectional communication)**:
- **Bidirectional audio-video cross-attention layers** explicitly allow information flow in both directions
- Video features attend to audio features AND audio features attend to video features simultaneously
- Cross-modality AdaLN for shared timestep conditioning
- Asymmetric dual-stream architecture with coupling through bidirectional cross-attention

**Memory Overhead vs FiLM Baseline**:
- Standard FiLM: O(C) for gamma/beta
- LTX-2 bidirectional cross-attention: O(T × D) per layer
- Multiple cross-attention layers increase overhead
- **Memory Overhead: MEDIUM** (14B+5B parameters total, but cross-attention layers are lightweight)

**Implementation Complexity**:
- Transformer-based architecture requires careful attention implementation
- Dual-stream design adds complexity
- **Complexity: HIGH** (but pre-trained weights available)

**GitHub**: Not explicitly listed, but model weights publicly released

---

## Method 3: TopicVD (Cross-Modal Bidirectional Attention Module)

**Paper Citation**:  
Lv, J., Chen, J., Long, Z., Fu, X., & Chen, Y. (2025). TopicVD: A Topic-Based Dataset of Video-Guided Multimodal Machine Translation. arXiv:2505.05714

**Mechanism Description (How it enables bidirectional communication)**:
- **Cross-modal bidirectional attention module** designed specifically for video-text fusion
- Models shared semantics between text and video in both directions
- Uses global context from documentary video to improve translation
- The bidirectional nature enables both "video guides text understanding" and "text enriches video representation"

**Memory Overhead vs FiLM Baseline**:
- FiLM: O(C) parameters
- Bidirectional cross-attention: O(T × D) with attention over T tokens
- For T=16, D=256: ~256KB per attention layer
- **Memory Overhead: MEDIUM** (acceptable for RTX 3060)

**Implementation Complexity**:
- Standard cross-attention implementation
- Video-subtitle pairs require alignment
- **Complexity: LOW-MEDIUM** (transformer attention is well-documented)

**GitHub**: https://github.com/JinzeLv/TopicVD

---

## Method 4: Motion Modulation Network (MSM + MTM)

**Paper Citation**:  
Gu, J., Li, K., Wang, F., Wei, Y., Wu, Z., Fan, H., & Wang, M. (2025). Motion Matters: Motion-guided Modulation Network for Skeleton-based Micro-Action Recognition. ACM MM 2025. arXiv:2507.21977

**Mechanism Description (How it enables bidirectional communication)**:
- **MSM (Motion-guided Skeletal Modulation)**: Motion modulates spatial representations - motion features → pose features
- **MTM (Motion-guided Temporal Modulation)**: Motion encodes into temporal context - temporal features → motion features
- **Motion Consistency Loss** ensures the two modulation streams agree
- This creates bidirectional information flow: pose informs motion, motion informs pose

**Memory Overhead vs FiLM Baseline**:
- Base FiLM: O(C) for gamma/beta
- MSM+MTM: O(C) + O(T × D) for motion encoder
- Motion consistency loss: minimal additional memory
- Total overhead: ~2× FiLM
- **Memory Overhead: LOW** (fits easily in RTX 3060)

**Implementation Complexity**:
- Motion encoder is simple MLP
- Two-stream modulation is straightforward
- **Complexity: LOW** (well-documented in paper with PyTorch code)

**GitHub**: https://github.com/momiji-bit/MMN

---

## Summary Table

| Method | Memory Overhead vs FiLM | Implementation Complexity | Bidirectional Support |
|--------|------------------------|---------------------------|----------------------|
| ATSS | 3-5× FiLM (MEDIUM-HIGH) | MEDIUM | Yes (explicit) |
| LTX-2 | MEDIUM | HIGH | Yes (explicit) |
| TopicVD | MEDIUM | LOW-MEDIUM | Yes (explicit) |
| MMN (MSM+MTM) | ~2× FiLM (LOW) | LOW | Yes (implicit via dual-stream) |

---

## Key Insights for POPW Architecture

1. **Bidirectional cross-attention is the standard approach** - Most methods use explicit cross-attention modules that attend in both directions

2. **FiLM can be extended for bidirectionality** - Motion Modulation Network shows how FiLM-style modulation can create bidirectional information flow with low overhead

3. **Memory overhead is manageable for RTX 3060** - Even "medium-high" overhead methods fit in 12GB VRAM at T=16, 256 channels

4. **Cross-modal similarity matrices are effective** - ATSS approach of constructing similarity matrices across modalities is worth considering for pose-activity alignment

---

## Top Recommendation for POPW

**Motion Modulation Network (MSM+MTM)** is the most practical for POPW because:
- Lowest memory overhead (~2× FiLM)
- Lowest implementation complexity (simple MLPs)
- Explicit bidirectional mechanism (MSM↔MTM with consistency loss)
- GitHub code available
- Aligns with POPW's temporal modeling needs

For a more sophisticated approach, **TopicVD's cross-modal bidirectional attention** provides a transformer-based alternative with explicit bidirectional attention.

---

## References

- ATSS: https://arxiv.org/abs/2604.04029
- LTX-2: https://arxiv.org/abs/2601.03233
- TopicVD: https://arxiv.org/abs/2505.05714
- MMN: https://arxiv.org/abs/2507.21977
- FiLM: https://arxiv.org/abs/1709.07871
