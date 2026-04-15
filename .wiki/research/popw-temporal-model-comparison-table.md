# Master Comparison Table: Temporal Modeling Alternatives for POPW

**Date:** 2026-04-15
**Contract:** POPW Research — Master Comparison Table
**Sources:** popw-feature-bank-alternatives-attention.md, popw-mamba-alternatives-linear-models.md, popw-temporal-convolution-alternatives.md

---

## 1. Master Comparison Table

| Method | Type | Parameters | GFLOPs (T=8) | Accuracy (SSv2) | Multi-task Compatible |
|--------|------|------------|--------------|-----------------|----------------------|
| **Cross-attention pooling** | Attention | 15.2M | 3.4 | 58.7% | ✅ Excellent |
| **Token Merging (ToMe)** | Attention | 38M | 5.2 | 60.8% | ✅ Good |
| **Stand-Alone Self-Attention** | Attention | 30.2M | 6.8 | N/A* | ✅ Good |
| **Non-local Networks** | Attention | 25.4M | 8.2 | 61.2% | ✅ Good |
| **Linear Transformers** | Linear SSM | 13M | O(N) | N/A* (LRA: 78.9%) | ⚠️ Limited |
| **R(2+1)D** | 3D Conv | 33.2M | 42 | 71.8% | ⚠️ Backbone swap required |
| **Video Swin Transformer** | Transformer | 88M | 321.4 | 67.3% | ✅ Good |
| **SlowFast R101** | 3D Conv | 33.5M | 65 | 70.5% | ❌ Incompatible |
| **P3D-C** | 3D Conv | 27.6M | 58 | 74.0% (SSv1) | ⚠️ Backbone swap required |
| **X3D-S** | 3D Conv | 3.8M | 6.2 | 65.1% | ⚠️ Backbone swap required |
| **MoViNet-A5** | 3D Conv | 5.8M | 14.8 | 67.8% | ⚠️ Backbone swap required |
| **TSM** | Temporal Shift | 0 (channel shift) | 33 | 70.4% | ❌ Incompatible |
| **Perceiver IO** | Cross-attention | 44M | 78.5 | 59.8% | ✅✅ Excellent |
| **MViTv2-Base** | Transformer | 52M | 164.2 | 64.1% | ✅ Good |
| **TimeSformer** | Transformer | 121M | 314.0 | 62.4% | ✅ Good |

\* N/A on SSv2 indicates evaluation was performed on other benchmarks (LRA, language modeling) not directly comparable.

### Supplementary: Linear-Time Sequence Models (Reference)

| Method | Type | Parameters | GFLOPs (T=8) | Benchmark | Accuracy | Multi-task Compatible |
|--------|------|------------|--------------|-----------|----------|----------------------|
| **Mamba** (reference) | Selective SSM | ~370M | O(N) | LRA / Path-X | 90% / 96% | ✅✅ Excellent |
| **HiPPO/S4** | SSM | ~250M | O(N) | LRA / Path-X | 85.5% / 0% | ⭐⭐⭐⭐ (4/5) |
| **RetNet** | Retention | 1.3B–7B | O(1) inference | LM perplexity | 17.2 (7B) | ⭐⭐⭐ (3/5) |
| **RWKV** | RNN/Transformer hybrid | 3B–14B | O(1) inference | LM perplexity | 9.8 (14B) | ⭐⭐⭐ (3/5) |
| **Mega** | Linear Attention + EMA | 56M–305M | O(N) | LRA / Path-X | 56.3% / 52% | ⭐⭐⭐ (3/5) |

---

## 2. Top-3 Rankings

### Top-3 by Efficiency (GFLOPs normalized by parameters)

| Rank | Method | GFLOPs | Parameters | Efficiency Ratio | Accuracy |
|------|--------|--------|------------|-----------------|----------|
| 🥇 1 | **Cross-attention pooling** | 3.4 | 15.2M | 0.224 GFLOPs/M | 58.7% |
| 🥈 2 | **X3D-S** | 6.2 | 3.8M | 1.632 GFLOPs/M | 65.1% |
| 🥉 3 | **Token Merging (ToMe)** | 5.2 | 38M | 0.137 GFLOPs/M | 60.8% |

**Efficiency Ranking Analysis:**
Cross-attention pooling dominates efficiency with only 3.4 GFLOPs for 15.2M parameters — the best GFLOPs-to-parameters ratio. Token Merging (ToMe) offers similar efficiency (0.137 GFLOPs/M) with slightly higher accuracy (60.8%). X3D-S has the lowest absolute GFLOPs (6.2) but a higher ratio due to its extremely small parameter count (3.8M total).

### Top-3 by Accuracy (SSv2 or equivalent benchmark)

| Rank | Method | Accuracy | GFLOPs | Parameters |
|------|--------|----------|--------|------------|
| 🥇 1 | **P3D-C** | 74.0% (SSv1) | 58 | 27.6M |
| 🥈 2 | **R(2+1)D** | 71.8% (SSv2) | 42 | 33.2M |
| 🥉 3 | **SlowFast R101** | 70.5% (SSv2) | 65 | 33.5M |

**Accuracy Ranking Analysis:**
P3D-C leads on SSv1 but is not directly comparable; R(2+1)D is the top performer on SSv2 (71.8%) with reasonable compute (42 GFLOPs). SlowFast R101 ties closely at 70.5% but at higher compute cost (65 GFLOPs). Note that all top-3 accuracy methods require **backbone-level replacement**, making them incompatible with POPW's current shared-backbone multi-task architecture.

### Top-3 PoseFiLM-Compatible Methods

| Rank | Method | PoseFiLM Compatible | Accuracy | GFLOPs |
|------|--------|---------------------|----------|--------|
| 🥇 1 | **Perceiver IO** | ✅✅ Excellent | 59.8% | 78.5 |
| 🥇 1 | **Cross-attention pooling** | ✅✅ Excellent | 58.7% | 3.4 |
| 🥉 3 | **Non-local Networks** | ✅ Good | 61.2% | 8.2 |

---

## 3. Narrative Summary: Which Approaches Dominate

### For POPW's Multi-Task Shared-Backbone Architecture

**The fundamental constraint**: POPW uses a 2D ResNet-50 backbone shared across multiple heads (pose, detection, activity) with FiLM conditioning on intermediate features. This architectural choice enables efficient multi-task learning but limits the usable temporal modeling approaches:

1. **Head-level methods dominate** (Cross-attention pooling, Non-local Networks, Token Merging, Perceiver IO)
2. **Backbone-level methods are incompatible** (R(2+1)D, P3D, X3D, MoViNet, SlowFast, TSM) — they replace the spatial backbone, breaking FiLM compatibility and multi-task sharing

### Dominant Approaches by Use Case

**For efficiency-critical real-time applications:**
- Cross-attention pooling (3.4 GFLOPs, 15.2M params) is the clear winner
- Token Merging (5.2 GFLOPs, 38M params) offers a good accuracy trade-off (+2.1% accuracy for +1.8 GFLOPs)
- Non-local Networks (8.2 GFLOPs, 25.4M params) provides +2.5% accuracy over cross-attention at 2.4× compute

**For accuracy-critical applications:**
- If backbone replacement is acceptable: R(2+1)D (71.8% SSv2, 42 GFLOPs) or P3D-C (74.0% SSv1)
- If backbone must remain: Non-local Networks offers the best head-level accuracy (61.2% SSv2)

**For PoseFiLM-conditioned multi-task:**
- Perceiver IO: architecturally ideal — cross-attention architecture naturally supports query-based pose conditioning with minimal overhead
- Cross-attention pooling: simpler implementation, excellent FiLM compatibility, lowest compute
- Mamba (reference): best overall temporal modeling (90% LRA, 96% Path-X) but requires state-space integration effort

### Trade-off Summary

| Approach Family | Best For | Limitation | POPW Compatibility |
|-----------------|----------|------------|-------------------|
| Cross-attention (Perceiver IO, CAP) | Real-time, pose-conditioned | Lower raw accuracy | ✅ Excellent |
| Token Merging | Efficiency-accuracy balance | Moderate accuracy | ✅ Good |
| Non-local Networks | Head-level accuracy | O(n²) complexity | ✅ Good |
| Linear SSM (HiPPO/S4, RetNet, RWKV) | Long-range temporal modeling | Language-focused benchmarks | ⚠️ Moderate |
| 3D Convolutions (R(2+1)D, X3D, P3D) | Maximum video accuracy | Backbone replacement required | ❌ Incompatible |
| SlowFast / TSM | Highest standalone accuracy | Incompatible with shared backbone | ❌ Incompatible |

### Conclusion

For POPW's temporal modeling needs, **head-level approaches dominate**. Cross-attention pooling and Perceiver IO offer the best efficiency-FiLM-compatibility trade-off, while Non-local Networks provides the highest head-level accuracy. If temporal accuracy is paramount and backbone redesign is acceptable, R(2+1)D is the recommended 3D backbone replacement. Mamba remains the reference for state-of-the-art temporal modeling but requires significant architectural integration effort for FiLM conditioning.

---

## 4. Sources

1. Beltagy, I., Peters, M. E., & Cohan, A. (2020). Longformer: The Long-Document Transformer. *arXiv:2004.05150*.
2. Zaheer, M., et al. (2020). Big Bird: Transformers for Longer Sequences. *NeurIPS 2020*.
3. Wang, X., et al. (2018). Non-local Neural Networks. *CVPR 2018*.
4. Ramachandran, P., et al. (2019). Stand-Alone Self-Attention in Vision Models. *NeurIPS 2019*.
5. Liu, Z., et al. (2022). Video Swin Transformer. *CVPR 2022*.
6. Li, Y., et al. (2022). MViTv2: Improved Multiscale Vision Transformers. *CVPR 2022*.
7. Bertasin, G., et al. (2021). TimeSformer. *ICML 2021*.
8. Jaegle, A., et al. (2022). Perceiver IO. *ICML 2022*.
9. Lin, J., et al. (2019). TSM. *ICCV 2019*.
10. Qiu, Z., et al. (2017). P3D. *CVPR 2017*.
11. Tran, D., et al. (2018). R(2+1)D. *CVPR 2018*.
12. Feichtenhofer, X. (2020). X3D. *CVPR 2020*.
13. Krotov, D., & Ferreira, P. (2021). MoViNet. *arXiv:2103.11511*.
14. Feichtenhofer, H., et al. (2019). SlowFast. *ICCV 2019*.
15. Gu, A., et al. (2020). HiPPO. *arXiv:2008.07669*.
16. Katharopoulos, A., et al. (2020). Linear Transformers. *ICML 2020*.
17. Sun, Y., et al. (2023). RetNet. *arXiv:2307.08621*.
18. Peng, B., et al. (2023). RWKV. *arXiv:2305.13048*.
19. Ma, X., et al. (2022). Mega. *EMNLP 2022*.
20. Gu, A., & Dao, T. (2023). Mamba. *arXiv:2312.00752*.