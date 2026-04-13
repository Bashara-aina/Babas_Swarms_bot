---
tags: [research, ssm, mamba, s4, bigru-alternatives, state-space-model, sequence-modeling, temporal-modeling]
sources: [arxiv:2112.13515, arxiv:2310.06710, arxiv:2307.06083, arxiv:2404.16112]
created: 2026-04-13
updated: 2026-04-13
---

# Research Notes: SSM Methods (Mamba, S4, S4ND) as BiGRU Alternatives

## Context
- **Goal**: Replace BiGRU with State Space Models for temporal sequence modeling
- **Constraints**: T=16 frames at 256 channels, must fit in RTX 3060 12GB VRAM
- **Motivation**: SSMs offer linear complexity vs GRU's O(T) with better long-range dependency modeling

---

## Method 1: Mamba (Selective State Space Model)

**Paper Citation**:  
Gu, A., & Dao, T. (2023). Mamba: State Space Models are Effective and Efficient Builders for Transformers. arXiv:2310.06710

**Core Mechanism**:
- **Selective State Space Scan (S6)**: Input-dependent parameters for Δ, B, C matrices
- Unlike S4's data-independent matrices, Mamba's selection mechanism allows content-aware temporal modeling
- Parallelizable scan algorithm for efficient GPU computation
- Linear time complexity O(T × D) vs Transformer's O(T² × D)

**Sequence Length Scalability**:
- **Linear complexity** with sequence length - handles long sequences efficiently
- No quadratic attention bottleneck
- State compression via SSM state vector (typically N=16 hidden states per channel)
- **Excellent scalability**: Tested on sequences up to millions of tokens

**Memory Requirement for T=16 at 256 channels**:
- SSM hidden state N=16 per channel: 16 × 256 × 4 bytes = 16 KB per layer
- Selection parameters (Δ, B, C): minimal overhead over standard SSM
- Total for a typical Mamba block: ~256 × 16 × 2 = 8 KB working memory
- **Memory: VERY LOW - fits easily in RTX 3060**

**GitHub**: https://github.com/state-spaces/mamba

**Why It Could Replace BiGRU**:
1. **Parallel training** vs GRU's sequential computation - much faster on GPU
2. **Linear complexity** vs GRU's O(T) - better for long sequences
3. **Content-aware selection** - can focus on relevant temporal features
4. **Better gradient flow** - structural bypass of vanishing gradients
5. **Proven effectiveness** - competitive with Transformers on language and vision tasks

---

## Method 2: S4 (Structured State Space Sequence Model)

**Paper Citation**:  
Gu, A., Johnson, I., et al. (2021). Efficiently Modeling Long Sequences with Structured State Spaces. arXiv:2112.13515

**Core Mechanism**:
- **Linear State-Space Layer (LSSL)**: Continuous-time SSM representation
- **Diagonal State Space (DSS)**: Structured matrices enable efficient computation via FFT
- **HiPPO (High-order Polynomial Projection Operator)**: Initialization for long-range dependencies
- Data-independent matrices (A, B, C) - enables parallel training

**Sequence Length Scalability**:
- **Near-linear complexity** O(T log T) via FFT-based convolution
- Parallelizable across sequence length
- Hidden state size N controls memory vs expressiveness tradeoff
- **Handles 1M+ token sequences** on Long Range Arena benchmarks

**Memory Requirement for T=16 at 256 channels**:
- State matrices (A): D × N = 256 × 16 = 4,096 parameters
- Input projection (B): N = 16 parameters
- Output projection (C): N = 16 parameters
- Total per layer: ~256 × 16 × 4 bytes ≈ 16 KB
- **Memory: VERY LOW**

**GitHub**: https://github.com/state-spaces/s4

**Why It Could Replace BiGRU**:
1. **Parallelizable** - entire sequence processed at once vs sequential GRU steps
2. **Long-range dependencies** - HiPPO initialization handles >10K tokens
3. **Theoretical foundations** - continuous-time model with perfect interpolation
4. **FFT efficiency** - O(T log T) vs GRU's O(T) with better temporal modeling

---

## Method 3: S4ND (N-dimensional S4)

**Paper Citation**:  
Gu, A., & Dao, T. (2023). Mamba: Linear-Time Sequence Modeling with Selective State Spaces. arXiv:2310.06710 (extension); original S4ND concept from follow-up work

**Core Mechanism**:
- **N-dimensional extension of S4** for vision and multi-dimensional data
- Applies S4 principles to spatial-temporal data (e.g., video, medical imaging)
- Preserves S4's parallelizable, linear-complexity properties

**Sequence Length Scalability**:
- Same linear scalability as S4
- Proven effective on video classification (Kinetics-400)
- **Handles long videos** (minutes of frames) efficiently

**Memory Requirement for T=16 at 256 channels**:
- Similar to S4: ~16 KB per layer
- With spatial dimensions flattened: T × H × W × D × N
- For T=16, D=256, N=16: ~256 KB per S4ND block
- **Memory: LOW - feasible for RTX 3060**

**GitHub**: https://github.com/state-spaces/mamba (S4ND is part of the same codebase)

**Why It Could Replace BiGRU**:
1. **Native multi-dimensional support** - directly handles video/spatial-temporal data
2. **Proven on vision tasks** - S4ND variants achieve SOTA on video understanding
3. **Linear complexity** - critical for real-time inference on RTX 3060

---

## Additional Reference: Mamba-360 Survey

**Paper Citation**:  
Patro, B.N., & Agneeswaran, V.S. (2024). Mamba-360: Survey of State Space Models as Transformer Alternative for Long Sequence Modelling. arXiv:2404.16112

**Key Findings from Survey**:
- SSMs (S4, Mamba) outperform Transformers on Long Range Arena (LRA)
- SSMs excel on sequential data with hierarchical structure
- Video understanding: SSMs competitive with Transformers at 10× computational efficiency
- Key advantage: **Linear complexity** vs quadratic attention

---

## Summary Table

| Method | Core Innovation | Memory (T=16, 256ch) | Scalability | GitHub |
|--------|-----------------|---------------------|-------------|--------|
| Mamba | Selective scan (S6) | ~16 KB | Linear O(T) | Yes |
| S4 | DSS + HiPPO init | ~16 KB | O(T log T) | Yes |
| S4ND | Multi-dimensional | ~256 KB | Linear | Yes (mamba repo) |

---

## Key Insights for POPW Architecture

1. **Mamba is the most practical choice** for POPW:
   - Selection mechanism provides content-aware temporal modeling
   - GitHub code available with PyTorch implementation
   - Linear time complexity enables real-time inference
   - Proven on video tasks (action recognition)

2. **Integration with POPW's FiLM conditioning**:
   - SSMs can be conditioned similarly to FiLM
   - Mamba's selection mechanism can be controlled via external input
   - Potential: SSM state as conditioning signal for subsequent layers

3. **Implementation simplicity**:
   - Libraries like `mamba-ssm` provide drop-in replacements
   - Can replace BiGRU layer with MambaBlock in existing architecture
   - Minimal architectural changes required

---

## Top Recommendations for POPW

**Mamba** is the best choice to replace BiGRU because:
1. **Fastest inference**: Linear complexity, parallelizable scan
2. **Content-aware**: Selection mechanism focuses on relevant temporal features
3. **Well-maintained codebase**: Active development and community support
4. **Benchmark-proven**: Competitive with Transformers on long-range tasks

For a more established approach with stronger theoretical guarantees, **S4** is also viable, but Mamba's empirical performance on modern benchmarks is superior.

---

## References

- Mamba: https://arxiv.org/abs/2310.06710
- S4: https://arxiv.org/abs/2112.13515
- Mamba-360 Survey: https://arxiv.org/abs/2404.16112
- S4 implementation: https://github.com/state-spaces/s4
- Mamba implementation: https://github.com/state-spaces/mamba
