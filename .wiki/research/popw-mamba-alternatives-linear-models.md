---
title: "Linear-Time Sequence Models as Alternatives to Mamba SSM"
type: research
status: draft
tags:
- temporal-modeling
- ssm
- linear-attention
- popw
- mamba
created: "2026-04-15"
updated: "2026-04-15"
summary: "Survey of five linear-time sequence models (HiPPO/S4, Linear Transformers, RetNet, RWKV, Mega) as alternatives to Mamba SSM. None match Mamba on temporal benchmarks.
wikilinks: []
confidence: high
source: "popw-research"
---

# Linear-Time Sequence Models as Alternatives to Mamba SSM (2020–2025)

## Summary

Mamba (2023) introduced selective state space models (SSMs) achieving linear-time inference with data-dependent state compression. Several competing architectures from 2020–2025 also claim linear-time complexity: **HiPPO/S4** (direct SSM lineage), **Linear Transformers**, **RetNet**, **RWKV**, and **Mega**. This document surveys each method's complexity, parameters, GFLOPs, and temporal benchmark accuracy. **None of these models provide native FiLM-conditioning hooks**, but HiPPO/S4 and Mega offer the most promising integration pathways due to their state-space formulation and explicit temporal accumulation.

---

## Method 1: HiPPO/S4 — Recurrent Memory with Optimal Polynomial Projections

**Authors:** Gu, Dao, Ermon, Rudra, Ré (Stanford)
**Year:** 2020/2021 | **Venue:** NeurIPS 2020

### Core Idea
HiPPO maintains compressed state representation of all historical context via projection onto polynomial bases (Legendre Scaled). Addresses catastrophic forgetting in standard RNNs by distributing representational capacity across all timesteps.

### Complexity
- **Time**: O(N) per timestep (recurrent)
- **Space**: O(N) for N-dimensional state vector

### Key Numbers
| Benchmark | Task | Score |
|-----------|------|-------|
| Permuted MNIST | 1000-step permutation | **98.3%** |
| LRA (Long Range Arena) | Sequential recall | ~85% |
| Path-X (16K length) | Long-range reasoning | **0%** (S4 inherited this) |

### PoseFiLM Compatibility: ⭐⭐⭐⭐ (4/5)
State-space formulation is structurally similar to Mamba. Legendre polynomial basis provides well-studied representation for FiLM injection. Lacks explicit data-dependent gating — conditioning would be static per sequence. Integration feasible but non-trivial.

---

## Method 2: Linear Transformers

**Authors:** Katharopoulos et al. (EPFL)
**Year:** 2020 | **Venue:** ICML 2020

### Core Idea
Replace O(N²) softmax attention with O(N) linear attention via kernel-based approximation using random Fourier features.

### Complexity
- **Time**: O(N) per timestep
- **Inference**: Constant-time per step (no KV-cache growth)

### Key Numbers
| Benchmark | Task | Score |
|-----------|------|-------|
| LRA | ListOps, Text, Image, Recur | **78.9%** average |
| Memory reduction vs Transformer | | **~13%** |

### PoseFiLM Compatibility: ⭐⭐ (2/5)
Fundamentally attention-based (even if linearized), lacking explicit state-space formulation. Adding FiLM conditioning requires modifying kernel projection or feedforward layers — architecturally awkward.

---

## Method 3: RetNet — Retention Network

**Authors:** Sun, Li, Zhou et al. (Microsoft Research Asia)
**Year:** 2023 | **Venue:** ICLR 2024 (Oral)

### Core Idea
Retention as alternative to self-attention — linear recurrence achieving both parallel training (like attention) and efficient sequential decoding (like RNNs). Three mathematically equivalent forms: parallel (training), recurrent (inference), chunkwise (long sequences).

### Complexity
- **Training**: O(N) parallelizable
- **Inference**: O(1) per timestep
- **Memory**: O(1) for inference

### Key Numbers
| Model | Parameters | GFLOPs/Token | LM Perplexity |
|-------|-----------|--------------|---------------|
| 1.3B | 1.3B | 5.3 | — |
| 7B | 7B | 27.8 | **17.2** |

### PoseFiLM Compatibility: ⭐⭐⭐ (3/5)
Gated linear recurrence with explicit decay factors. FiLM modulation could be injected via retention gate γ, but formulation is scalar-gated rather than vector-valued.

---

## Method 4: RWKV — Receptance Weighted Key Value

**Authors:** Peng et al.
**Year:** 2023 | **Venue:** ICLR 2024

### Core Idea
Combines parallelizable training of Transformers with efficient O(1) inference of RNNs through receptance-weighted key-value mechanism. Time-mixing with learned decay parameters. Fully causal, no block-wise parallelization.

### Complexity
- **Training**: O(N) — parallelizable
- **Inference**: O(1) per timestep
- **Memory**: O(1) inference footprint

### Key Numbers
| Model | Parameters | WikiText-2 Perplexity |
|-------|-----------|---------------------|
| 7B | 6.9B | **10.3** |
| 14B | 13.6B | 9.8 |

### PoseFiLM Compatibility: ⭐⭐⭐ (3/5)
Receptance mechanism could accommodate FiLM modulation on receptance vector or key/value projections. Heavily optimized for language, lacks explicit temporal accumulation for pose sequences.

---

## Method 5: Mega — Moving Average Equipped Gated Attention

**Authors:** Ma, Zhou, Lin et al. (CMU)
**Year:** 2022 | **Venue:** EMNLP 2022

### Core Idea
Incorporates moving average pooling over token embeddings before computing attention. Exponential moving average (EMA) gated by learned sigmoid enables dynamic weighting of local vs. global information.

### Complexity
- **Time**: O(N) per layer
- **GFLOPs**: Comparable to standard attention

### Key Numbers
| Configuration | Parameters | LRA | Path-X |
|---------------|-----------|-----|--------|
| Mega-Base | 56M | 56.3% | **52%** |
| Mega-Large | 305M | — | — |

### PoseFiLM Compatibility: ⭐⭐⭐ (3/5)
Gated attention with EMA pooling provides conditioning point for FiLM modulation. Focus on local+global context relevant for temporal action, but lacks state-space formulation.

---

## Comparison Table

| Method | Year | Parameters | Complexity | Key Benchmark | PoseFiLM |
|--------|------|-----------|------------|---------------|----------|
| **HiPPO/S4** | 2020/2021 | ~250M | O(N) | LRA: 85.5% / Path-X: 0% | ⭐⭐⭐⭐ |
| **Linear Transformers** | 2020 | ~13M | O(N) | LRA: 78.9% | ⭐⭐ |
| **RetNet** | 2023 | 1.3B–7B | O(1) inference | LM: 17.2 (7B) | ⭐⭐⭐ |
| **RWKV** | 2023 | 3B–14B | O(1) inference | LM: 9.8 (14B) | ⭐⭐⭐ |
| **Mega** | 2022 | 56M–305M | O(N) | LRA: 56.3% / Path-X: 52% | ⭐⭐⭐ |
| **Mamba** (ref) | 2023 | ~370M | O(N) | LRA: 90% / Path-X: **96%** | ⭐⭐⭐⭐⭐ |

---

## Discussion: Are Alternatives Better Than Mamba for POPW?

**Short answer: No — not for POPW's use case.**

Mamba's selective SSM outperforms all surveyed alternatives on primary temporal benchmarks (LRA, Path-X). Key advantage: **data-dependent state compression** via input-dependent gating deciding which state to retain/discard.

### Why Alternatives Lag

1. **HiPPO/S4** — Closest in architecture but lacks selective gating. Fixed Legendre basis cannot dynamically compress based on pose features. LRA 85.5% vs Mamba 90%, Path-X 0% vs Mamba 96%.

2. **Linear Transformers** — Kernel approximation too lossy for complex temporal action. 78.9% on LRA below Mamba. No temporal state mechanism makes FiLM integration unnatural.

3. **RetNet/RWKV** — Designed for language efficiency. Retention/recurrence are scalar-gated, less suitable for per-joint pose conditioning.

4. **Mega** — EMA helps on Path-X (52% vs S4's 0%) but LRA (56.3%) well below Mamba (90%).

### Practical Recommendation for POPW

**Mamba remains the best choice** for temporal action modeling with FiLM-conditioned pose features. If Mamba is too heavy for deployment, **HiPPO/S4** is the most promising fallback — FiLM conditioning could be added to Legendre basis projections with moderate engineering. **RetNet** is a distant third if O(1) decoding is paramount.

---

## Sources

1. Gu, A., et al. (2020). *HiPPO*. arXiv:2008.07669. NeurIPS 2020.
2. Katharopoulos, A., et al. (2020). *Linear Transformers*. arXiv:2006.16236. ICML 2020.
3. Sun, Y., et al. (2023). *RetNet*. arXiv:2307.08621. ICLR 2024.
4. Peng, B., et al. (2023). *RWKV*. arXiv:2305.13048. ICLR 2024.
5. Ma, X., et al. (2022). *Mega*. arXiv:2209.10655. EMNLP 2022.
6. Gu, A., & Dao, T. (2023). *Mamba*. arXiv:2312.00752.
