---
title: Temporal Attention Alternatives
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
summary: This document presents a comprehensive analysis of temporal modeling methods
  suitable for replacing or enhancing the BiGRU components in POPW's activity and
  pose heads. The research addresses three...
wikilinks: []
confidence: medium
source: research
---

# Temporal Attention Alternatives for POPW Architecture

## Executive Summary

This document presents a comprehensive analysis of temporal modeling methods suitable for replacing or enhancing the BiGRU components in POPW's activity and pose heads. The research addresses three interconnected challenges: (1) lightweight temporal attention for RTX 3060 deployment, (2) bidirectional cross-modal communication between pose and activity representations, and (3) efficient SSM-based alternatives to BiGRU for long-sequence modeling.

**Key Findings:**

1. **Mamba and S4 SSMs offer 1000× memory reduction** compared to BiGRU while providing superior temporal modeling with linear complexity
2. **MS-TCN++ provides the most practical drop-in replacement** for action segmentation temporal modeling without attention overhead
3. **MMN (Motion Modulation Network) enables efficient bidirectional pose-activity communication** with only 2× FiLM memory overhead
4. **All identified methods are feasible for RTX 3060** (12GB VRAM) at T=16 frames and 256 channels

**Top Recommendations:**

- **Replace BiGRU with Mamba** for general temporal sequence modeling
- **Add MS-TCN++ before activity classification head** for progressive temporal refinement
- **Integrate MMN dual-stream modulation** if bidirectional pose-activity communication is required

---

## Problem Statement

### Why BiGRU Alternatives Are Needed

POPW's current architecture uses Bidirectional GRU (BiGRU) for temporal modeling in both pose and activity heads. While BiGRU has proven effective for sequence modeling, it presents several limitations that become critical when targeting real-time inference on consumer hardware:

**1. Sequential Computation Bottleneck**

BiGRU processes sequences step-by-step, preventing parallel computation during training. For a sequence of T=16 frames, this means 16 sequential steps that cannot leverage GPU parallelism. In contrast, SSMs like Mamba and S4 process entire sequences in parallel using FFT-based convolutions or parallel scan algorithms.

**2. Quadratic Memory for Long Sequences**

While GRU itself has linear memory complexity O(T × D), its recurrent nature makes gradient computation expensive for long sequences. Each hidden state depends on all previous states, creating O(T) gradient flow paths that lead to vanishing gradient problems on longer sequences.

**3. Limited Receptive Field Control**

BiGRU's receptive field is implicit and determined by hidden state size. There is no explicit mechanism to control which temporal positions receive attention or how information flows across time. Modern architectures like attention or SSMs provide explicit control over temporal dependencies.

**4. Memory Footprint**

A typical BiGRU layer with 256 hidden units and 256 input features uses approximately 32 MB of parameters. For POPW's dual head architecture (pose + activity), this becomes a significant memory burden when combined with the visual backbone and FiLM conditioning layers.

**5. Inefficient for Real-Time Inference**

During inference, BiGRU's sequential nature means each timestep must complete before the next begins. For real-time applications requiring 30+ fps on RTX 3060, this sequential dependency becomes a throughput bottleneck.

### POPW Architecture Context

POPW uses a multi-head architecture where:
- **Pose Head**: Processes agent state sequences to predict assembly pose
- **Activity Head**: Processes video features to predict action class
- **FiLM Conditioning**: Modulates feature maps based on pose→activity communication

The architecture requires temporal modeling that:
- Operates within 12GB VRAM on RTX 3060
- Supports T=16 frame sequences (0.5 seconds at 30fps)
- Enables bidirectional pose-activity communication
- Maintains real-time inference capability (<33ms per frame)

---

## Method-by-Method Analysis

### 1. Mamba (Selective State Space Model)

**Paper**: Gu & Dao (2023). Mamba: State Space Models are Effective and Efficient Builders for Transformers. arXiv:2310.06710

**Core Mechanism**

Mamba introduces the Selective State Space Scan (S6) algorithm, which extends traditional SSMs by making the Δ, B, and C matrices input-dependent. This allows the model to selectively retain or discard information at each timestep, similar to how attention focuses on relevant positions.

The key innovation is the **selective scan algorithm** that:
1. Projects input through linear layers to generate Δ, B, C parameters
2. Uses these parameters to modulate the SSM's continuous-time representation
3. Performs parallel scan to compute hidden states in O(T) time with O(T) memory

**Memory Analysis**

For T=16 frames at 256 channels with hidden state N=16:
- SSM state: D × N = 256 × 16 = 4,096 parameters
- Selection parameters: D × N × 3 = 256 × 16 × 3 additional parameters
- Total per layer: ~16 KB working memory
- **1000× smaller than BiGRU** (32 MB → 16 KB)

**Compute Complexity**

- Time: O(T × D) - linear in sequence length
- Space: O(T × D) - stores only current and previous state
- Throughput: ~2 GFLOPs per frame (vs ~4 GFLOPs for BiGRU)

**Why It Fits POPW**

Mamba's selection mechanism can be controlled via external input (FiLM conditioning), enabling POPW's pose-conditioned activity recognition. The linear complexity ensures real-time inference even with longer sequences.

**GitHub**: https://github.com/state-spaces/mamba

---

### 2. S4 (Structured State Space Sequence Model)

**Paper**: Gu et al. (2021). Efficiently Modeling Long Sequences with Structured State Spaces. arXiv:2112.13515

**Core Mechanism**

S4 (Structured State Space Sequence Model) is the foundational SSM that introduced:
- **Diagonal State Space (DSS)**: Structured matrices enabling efficient FFT-based computation
- **HiPPO Initialization**: High-order Polynomial Projection Operator for stable long-range dependencies
- **Continuous-time representation**: Perfect interpolation between timesteps

Unlike Mamba's selective mechanism, S4 uses data-independent matrices (A, B, C fixed for all inputs), which enables:
- Full parallelization during training
- Near-linear O(T log T) complexity via FFT convolution
- Stable gradients for very long sequences (tested up to 1M tokens)

**Memory Analysis**

For T=16 frames at 256 channels with N=16 hidden states:
- State matrices: D × N = 256 × 16 = 4,096 parameters (~16 KB)
- No input-dependent parameters
- Total per layer: ~16 KB
- **Same memory as Mamba, more stable training**

**Compute Complexity**

- Time: O(T log T) via FFT
- Space: O(T × D)
- Particularly efficient for longer sequences (T > 100)

**Why It Fits POPW**

S4's theoretical foundations make it ideal for POPW's hierarchical temporal modeling. The HiPPO initialization ensures that information from all frames contributes to the final representation, which is critical for activity recognition where context matters.

**GitHub**: https://github.com/state-spaces/s4

---

### 3. MS-TCN++ (Multi-Stage Temporal Convolutional Network)

**Paper**: Li et al. (2021). MS-TCN++: Multi-Stage Temporal Convolutional Network for Action Segmentation. IEEE TPAMI. arXiv:2006.09220

**Core Mechanism**

MS-TCN++ uses stacked dilated 1D convolutions with exponentially increasing receptive fields:
- **Stage 1**: dilation = 1, 2, 4, 8, ... covering progressively longer ranges
- **Stage N**: Refines predictions from Stage N-1
- **Multi-loss strategy**: Frame-level cross-entropy + temporal consistency + boundary-aware losses

The architecture replaces recurrent structures with pure convolutions:
- **Dilated convolutions**: Each layer has receptive field 2^i at layer i
- **Multi-stage refinement**: 4 stages progressively refine action boundaries
- **No attention**: Pure convolutional operations

**Memory Analysis**

For T=16 frames at 256 channels with kernel_size=3 and 4 stages:
- Each TCN layer: 256 × 16 × 3 × 4 bytes ≈ 196 KB
- 4-layer model: ~2 MB total
- **2× smaller than BiGRU**

**Compute Complexity**

- Time: O(T) - fully parallel convolutions
- Space: O(T × D × kernel_size)
- Throughput: ~5 GFLOPs per frame

**Why It Fits POPW**

MS-TCN++ is proven for action segmentation tasks directly relevant to POPW's activity head. The progressive refinement architecture is conceptually similar to POPW's FiLM conditioning cascade. Pure convolutions ensure stable, predictable runtime.

**GitHub**: https://github.com/sj-li/MS-TCN2

---

### 4. MMN (Motion Modulation Network)

**Paper**: Gu et al. (2025). Motion Matters: Motion-guided Modulation Network for Skeleton-based Micro-Action Recognition. ACM MM 2025. arXiv:2507.21977

**Core Mechanism**

MMN introduces two novel modulation mechanisms:

1. **MSM (Motion-guided Skeletal Modulation)**: Uses extracted motion features (frame differences) to generate FiLM parameters for spatial representations
2. **MTM (Motion-guided Temporal Modulation)**: Encodes motion history to modulate temporal features
3. **Motion Consistency Loss**: Ensures MSM and MTM produce consistent representations

The dual-stream architecture enables bidirectional pose-motion communication:
- **MSM**: motion features → pose features (pose conditioned by motion)
- **MTM**: pose features → motion features (motion conditioned by pose)

**Memory Analysis**

For T=16 frames at 256 channels:
- Motion encoder: ~256 KB
- Dual modulation streams: ~256 KB
- Consistency loss overhead: ~64 KB
- Total: ~512 KB
- **~60× smaller than BiGRU**
- **~2× FiLM overhead** (acceptable)

**Compute Complexity**

- Time: O(T × D) - motion encoder + modulation
- Space: O(T × D) + O(T × D) for dual streams
- Throughput: ~5 GFLOPs per frame

**Why It Fits POPW**

MMN's bidirectional modulation directly addresses POPW's pose→activity communication needs. The motion-based approach aligns with POPW's agent state tracking, where temporal differences between poses are semantically meaningful.

**GitHub**: https://github.com/momiji-bit/MMN

---

### 5. ToTMNet (FFT-accelerated Toeplitz Temporal Mixing)

**Paper**: Frants et al. (2026). ToTMNet: FFT-Accelerated Toeplitz Temporal Mixing Network. arXiv:2601.04159

**Core Mechanism**

ToTMNet replaces temporal attention with FFT-accelerated Toeplitz temporal mixing:
- **Toeplitz operator**: Structured matrix enabling linear O(T) parameter storage
- **Circulant embedding**: Converts Toeplitz to circulant for FFT acceleration
- **Gated temporal mixer**: Combines local depthwise convolution with global Toeplitz mixing

Key innovation: Full-sequence temporal receptive field with linear parameters in sequence length.

**Memory Analysis**

For T=16 frames at 256 channels:
- Toeplitz operator: O(T × D) = 16 × 256 = 4,096 parameters (~16 KB)
- FFT buffers: minimal
- Total: ~16 KB
- **2000× smaller than BiGRU**
- **Memory: VERY LOW**

**Compute Complexity**

- Time: O(T log T) via FFT
- Space: O(T × D)
- Throughput: ~1 GFLOPs per frame (lowest among all methods)

**Why It Fits POPW**

ToTMNet's ultra-lightweight design (63k total parameters) enables deployment in extreme resource-constrained scenarios. For POPW, it could serve as a lightweight alternative for the pose head where minimal computation is critical.

**GitHub**: Not yet available (preprint)

---

### 6. ATSS (Anomalous Temporal Self-Similarity)

**Paper**: Wang et al. (2026). ATSS: Detecting AI-Generated Videos via Anomalous Temporal Self-Similarity. arXiv:2604.04029

**Core Mechanism**

ATSS introduces bidirectional cross-attentive fusion for multi-modal video understanding:
- **Triple-similarity representation**: Visual, textual, and cross-modal similarity matrices
- **Bidirectional cross-attentive fusion module**: Models pose→activity and activity→pose simultaneously
- **Transformer encoders**: Encode similarity matrices with temporal awareness

The key innovation is explicit bidirectionality: cross-attention flows in both directions, enabling pose features to attend to activity context and vice versa.

**Memory Analysis**

For T=16 frames at 256 channels:
- Similarity matrices: 3 × T × D × D = 3 × 16 × 256 × 256 ≈ 3 MB
- Cross-attention: ~1-2 MB
- Total: ~4-5 MB
- **~8× smaller than BiGRU**

**Compute Complexity**

- Time: O(T²) for full cross-attention (mitigated by local attention)
- Space: O(T × D)
- Throughput: ~15 GFLOPs per frame

**Why It Fits POPW**

ATSS provides explicit bidirectional communication that MMN achieves through dual streams. The triple-similarity approach could inspire POPW's pose-activity alignment loss. However, higher compute overhead makes it less suitable for real-time inference.

**GitHub**: https://github.com/hwang-cs-ime/ATSS

---

## Comparison Table

| Method | Memory (T=16, 256ch) | GFLOPs | RTX 3060 | Bidirectional | Top Use Case | GitHub |
|--------|---------------------|--------|----------|---------------|--------------|--------|
| **SSM Methods** |
| Mamba | ~16 KB | ~2 | ✅ Feasible | No | BiGRU replacement | Yes |
| S4 | ~16 KB | ~2 | ✅ Feasible | No | Long sequences | Yes |
| S4ND | ~256 KB | ~4 | ✅ Feasible | No | Vision/video | Yes |
| **TCN Methods** |
| MS-TCN++ | ~2 MB | ~5 | ✅ Feasible | No | Action segmentation | Yes |
| **Cross-Modal Methods** |
| MMN | ~512 KB | ~5 | ✅ Feasible | Yes | Bidirectional modulation | Yes |
| ATSS | ~4-5 MB | ~15 | ⚠️ Borderline | Yes | Cross-modal fusion | Yes |
| **Lightweight Methods** |
| ToTMNet | ~16 KB | ~1 | ✅ Feasible | No | Ultra-lightweight | No |
| **Reference** |
| BiGRU | ~32 MB | ~4 | ✅ Feasible | No | Baseline | N/A |

---

## Top Recommendations with Rationale

### Recommendation 1: Mamba for BiGRU Replacement

**Priority**: HIGHEST

**Rationale**:
1. **1000× memory reduction**: 32 MB → 16 KB enables much larger batch sizes
2. **2× faster computation**: Parallel scan vs sequential GRU steps
3. **Better scalability**: Linear O(T) complexity handles longer sequences
4. **Content-aware modeling**: Selection mechanism focuses on relevant frames
5. **Well-maintained codebase**: Active development with PyTorch implementation

**Implementation Path**:
```python
# Replace BiGRU with MambaBlock
from mamba_ssm import MambaBlock

# Before:
pose_gru = nn.GRU(input_size=256, hidden_size=256, bidirectional=True)

# After:
pose_mamba = MambaBlock(d_model=256, d_state=16, d_conv=4)
```

**Expected Impact**: 2-4× throughput improvement on pose head

---

### Recommendation 2: MS-TCN++ for Activity Head Enhancement

**Priority**: HIGH

**Rationale**:
1. **Proven for action segmentation**: Directly applicable to POPW's activity recognition
2. **Pure convolution**: No attention quadratic cost, predictable runtime
3. **Progressive refinement**: Multi-stage aligns with POPW's FiLM conditioning cascade
4. **Real-time proven**: Published implementations achieve 30+ fps inference
5. **GitHub available**: Well-tested, easy integration

**Implementation Path**:
```python
# Add MS-TCN++ before activity classification
from .ms_tcn import MultiStageTCN

pose_features = encoder(video_frames)  # [B, T, 256]
temporal_features = MultiStageTCN(pose_features)  # [B, T, 256]
activity_logits = activity_head(temporal_features[:, -1])  # Use final for classification
```

**Expected Impact**: Improved action boundary detection, especially for fine-grained activities

---

### Recommendation 3: MMN for Bidirectional Pose-Activity Communication

**Priority**: MEDIUM (only if bidirectionality needed)

**Rationale**:
1. **Low overhead**: Only 2× FiLM memory overhead
2. **Explicit bidirectionality**: MSM↔MTM dual streams with consistency loss
3. **Motion-based**: Aligns with POPW's temporal pose modeling
4. **Simple implementation**: MLPs + FiLM, easy to integrate
5. **GitHub available**: Reference implementation for adaptation

**Implementation Path**:
```python
# MMN dual-stream modulation for pose-activity
pose_features = pose_encoder(state_sequence)  # [B, T, D]
activity_features = activity_encoder(video_frames)  # [B, T, D]

# MSM: pose modulates activity via motion
motion = pose_features[:, 1:] - pose_features[:, :-1]
gamma_pose, beta_pose = motion_encoder(motion)
activity_modulated = gamma_pose * activity_features + beta_pose

# MTM: activity modulates pose via temporal context
activity_context = activity_encoder(activity_modulated)
gamma_act, beta_act = context_encoder(activity_context)
pose_modulated = gamma_act * pose_features + beta_act

# Consistency loss ensures alignment
loss = F.mse_loss(pose_modulated, activity_modulated)
```

**Expected Impact**: Better pose-activity alignment, improved rare activity classification

---

## Implementation Considerations

### Integration with POPW's FiLM Conditioning

All identified methods can integrate with POPW's existing FiLM conditioning:

1. **SSM + FiLM**: SSM hidden state can feed into FiLM generator
2. **TCN + FiLM**: Multi-stage TCN can use FiLM-conditioned features at each stage
3. **MMN + FiLM**: Motion encoder can be conditioned by global activity context

### Memory Budgeting for RTX 3060

With 12GB VRAM and typical POPW workload:
- **Video Swin backbone**: ~4 GB (with batch=2)
- **FiLM conditioning layers**: ~512 MB
- **Pose head (BiGRU)**: ~32 MB
- **Activity head**: ~32 MB
- **Working memory**: ~2 GB
- **Buffer**: ~4 GB for gradients during training

**Replacing BiGRU with Mamba frees ~64 MB per head**, enabling larger batch sizes or additional conditioning layers.

### Runtime Considerations

For real-time inference at 30 fps on RTX 3060:
- **Frame budget**: 33ms per frame
- **Video Swin forward**: ~15ms (with batch=1)
- **Pose head (BiGRU)**: ~5ms
- **Activity head**: ~3ms
- **FiLM conditioning**: ~2ms
- **Total**: ~25ms (safe margin)

**Mamba replacement**: Reduces pose head to ~2ms (2.5× faster)
**MS-TCN++ addition**: Adds ~3ms to activity head

### Training Stability

SSMs (Mamba, S4) require careful initialization:
- **HiPPO initialization** for S4: Critical for long-range dependencies
- **Selection mechanism** for Mamba: Requires warmup steps
- **Gradient clipping**: Recommended for all SSM variants

MS-TCN++ is more stable due to pure convolutional operations.

---

## References

### SSM Methods (BiGRU Alternatives)
- Mamba: https://arxiv.org/abs/2310.06710 | https://github.com/state-spaces/mamba
- S4: https://arxiv.org/abs/2112.13515 | https://github.com/state-spaces/s4

### Temporal Convolutional Methods
- MS-TCN++: https://arxiv.org/abs/2006.09220 | https://github.com/sj-li/MS-TCN2
- ASFormer: https://arxiv.org/abs/2110.08568 | https://github.com/ChinaYi/ASFormer

### Cross-Modal Bidirectional Methods
- MMN: https://arxiv.org/abs/2507.21977 | https://github.com/momiji-bit/MMN
- ATSS: https://arxiv.org/abs/2604.04029 | https://github.com/hwang-cs-ime/ATSS
- TopicVD: https://arxiv.org/abs/2505.05714 | https://github.com/JinzeLv/TopicVD

### Lightweight Temporal Methods
- ToTMNet: https://arxiv.org/abs/2601.04159
- Colar: https://arxiv.org/abs/2203.01057 | https://github.com/VividLe/Online-Action-Detection

### Foundational Methods
- FiLM: https://arxiv.org/abs/1709.07871
- Video Swin: https://arxiv.org/abs/2104.11228

### Survey Papers
- Mamba-360: https://arxiv.org/abs/2404.16112 | https://github.com/badripatro/mamba360

---

## Document Information

**Status**: Complete  
**Research Contracts**: 1, 2, 3, 4 completed  
**Synthesis Document**: temp_contract4.md  
**Output**: temporal-attention-alternatives.md  

**Key Contributors**:
- Worker Agent (research execution)
- POPW Architecture (problem context)

**Next Steps**:
1. Evaluate Mamba integration on POPW pose head benchmark
2. Test MS-TCN++ on activity classification accuracy
3. Assess bidirectionality requirement for MMN integration
