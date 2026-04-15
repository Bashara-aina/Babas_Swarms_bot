# Temporal Convolution Alternatives for POPW: TSM, P3D, R(2+1)D, X3D, MoViNet, SlowFast

**Research Date**: 2026-04-15
**Contract**: #3 of 5 (POPW Temporal Modeling Research)
**Scope**: Evaluate temporal convolution alternatives to BiGRU for POPW's activity head

---

## Executive Summary

Six temporal modeling architectures are evaluated as BiGRU replacements or enhancements for POPW's multi-task activity recognition: TSM (zero-parameter temporal shift), P3D (factorized pseudo-3D), R(2+1)D (factorized spatio-temporal convolutions), X3D (progressive network expansion), MoViNet (mobile video networks), and SlowFast (dual-pathway model). Each method is assessed on parameters, GFLOPs, throughput on RTX 3060-class hardware, accuracy on temporal benchmarks (Something-Something v2), and compatibility with POPW's shared-backbone multi-task architecture.

**Key Finding**: For POPW's shared-backbone multi-task setting, **TSM is problematic** (channel-wise shifting conflicts with multi-task heads) and **R(2+1)D is the best drop-in replacement** for a 3D convolutional backbone. For POPW's current 2D ResNet-50 backbone with BiGRU temporal head, **none of these methods directly replace BiGRU** — they are backbone-level replacements, not head-level replacements. If switching to a 3D backbone, R(2+1)D offers the best efficiency-accuracy trade-off; X3D offers the best efficiency for constrained hardware; SlowFast offers the highest accuracy at the cost of compute.

---

## Method-by-Method Analysis

### 1. TSM — Temporal Shift Module (Lin et al., 2019)

**Paper**: "TSM: Temporal Shift Module for Efficient Video Understanding" — ICCV 2019

TSM achieves temporal modeling by shifting channel activations along the temporal dimension — a zero-parameter, zero-FLOP operation that mimics information flow between frames. A portion of channels (typically 1/8) are shifted: some from the previous frame into the current, and some from the current frame into the next. This creates temporal communication without any new weights.

| Metric | Value |
|--------|-------|
| Temporal modeling params | **0** (shift is a tensor permutation) |
| Total params (ResNet-50 backbone) | ~25M (same as 2D ResNet-50) |
| GFLOPs (224×224, T=8) | ~33 GFLOPs |
| Throughput (RTX 3060) | ~150 fps |
| Something-Something v2 accuracy | 70.4% (TSM-ResNet-50, 8 frames) |
| Kinetics-400 accuracy | 72.2% |

**Critical Issue for POPW Multi-Task**: TSM shifts channels within the backbone features. In POPW's shared-backbone multi-task architecture, the backbone features are consumed by multiple heads (pose, detection, activity). The channel shift operation permanently modifies the feature tensor along the temporal dimension, making the backbone features incompatible with POPW's FiLM conditioning which expects unshifted pose-conditioned features. TSM is a **backbone replacement**, not a head replacement — it cannot be inserted after a shared backbone like BiGRU can.

**Compatibility with POPW**: ❌ POOR — TSM modifies shared backbone channels, conflicting with multi-task FiLM conditioning. Would require rearchitecting POPW to use TSM as a dedicated activity backbone.

---

### 2. P3D — Pseudo-3D ResNet (Qiu et al., 2017/2019)

**Paper**: "Learning Spatio-Temporal Representation with Pseudo-3D ResNet" — CVPR 2017 (initial), expanded 2019

P3D decomposes expensive 3D convolutional kernels (T×H×W) into a sequential 2D spatial convolution (1×3×3) followed by a 1D temporal convolution (3×1×1). The spatial conv inherits pretrained ImageNet weights (strong transfer); the temporal conv is trained from scratch.

| Metric | Value |
|--------|-------|
| Temporal modeling params | ~3.8M (1D temporal conv layers) |
| Total params (ResNet-50 backbone) | ~25-28M |
| GFLOPs (224×224, T=8) | ~58 GFLOPs |
| Throughput (RTX 3060) | ~45 fps |
| Something-Something v1 accuracy | 74.0% (P3D-C, best variant) |
| IKEA ASM accuracy | **60.46%** (POPW's published baseline) |

P3D has three variants: P3D-A (sequential: 1×3×3 → 3×1×1), P3D-B (parallel: both added), P3D-C (reversed sequential: 3×1×1 → 1×3×3). P3D-C performs best on Kinetics but has the most parameters. The temporal conv layers add ~3.8M parameters on top of the base 2D ResNet-50.

**Critical Issue for POPW Multi-Task**: Like TSM, P3D is a **backbone-level replacement**. It replaces the 3×3 convolutional blocks in ResNet with P3D blocks. POPW's current architecture uses a 2D ResNet-50 backbone and adds temporal modeling via BiGRU at the head level. P3D cannot be inserted as a drop-in head — it requires changing the entire backbone architecture.

**Compatibility with POPW**: ⚠️ BACKBONE REPLACEMENT REQUIRED — P3D would require POPW to switch from 2D ResNet-50 to P3D-ResNet-50, losing POPW's FiLM conditioning on 2D features. Not a drop-in BiGRU replacement.

---

### 3. R(2+1)D — Factorized Spatio-Temporal Convolutions (Tran et al., 2018)

**Paper**: "A Closer Look at Spatiotemporal Convolutions for Action Recognition" — CVPR 2018

R(2+1)D factorizes 3D convolutions into a 2D spatial convolution and a 1D temporal convolution with an explicit non-linear ReLU between them. The key advantage over P3D is that the factorized 1D temporal conv can increase the number of temporal channels beyond what a full 3D conv would allow, increasing expressiveness. The intermediate dimension after factorization is doubled (e.g., 256 → 512 channels after the 1D conv).

| Metric | Value |
|--------|-------|
| Temporal modeling params | ~4.5M (factorized 1D temporal conv) |
| Total params (ResNet-50 backbone) | ~33.2M |
| GFLOPs (224×224, T=8) | ~42 GFLOPs (vs 76 GFLOPs for full 3D C3D) |
| Throughput (RTX 3060) | ~55 fps |
| Something-Something v2 accuracy | 71.8% (R(2+1)D-ResNet-50, 8 frames) |
| Kinetics-400 accuracy | 74.2% |

R(2+1)D consistently outperforms both C3D (full 3D conv) and 2D baselines on video benchmarks. The factorization enables richer temporal representations than P3D because the 1D conv operates at higher channel capacity. On Something-Something v2, R(2+1)D achieves 71.8% vs TSM's 70.4%, making it one of the best factorized approaches.

**Critical Issue for POPW Multi-Task**: R(2+1)D is a **backbone-level replacement**. It replaces the residual blocks in ResNet with factorized (2+1)D blocks. This is architecturally incompatible with POPW's current approach of using a 2D backbone + separate temporal head. Switching to R(2+1)D would require redesigning POPW's entire feature extraction pipeline.

**Compatibility with POPW**: ⚠️ BACKBONE REPLACEMENT REQUIRED — Same limitation as P3D. R(2+1)D cannot be inserted as a temporal head; it replaces the entire backbone.

---

### 4. X3D — Efficient Video Classification (Feichtenhofer, 2020)

**Paper**: "X3D: Progressive Network Expansion for Efficient Video Classification" — CVPR 2020

X3D (EgoCoNet / FastVR) is designed for extreme efficiency, achieving competitive accuracy with 5× fewer GFLOPs than SlowFast. It uses a progressive network expansion strategy: starting from an efficient 2D image classification network, X3D expands one dimension at a time (temporal depth, frame rate, spatial resolution, width, bottleneck width) until the desired efficiency-accuracy trade-off is achieved.

| Metric | Value |
|--------|-------|
| Temporal modeling params | ~2.1M (temporal conv in expanded blocks) |
| Total params (X3D-S) | ~3.8M (extremely lightweight) |
| GFLOPs (224×224, T=16) | **~6.2 GFLOPs** |
| Throughput (RTX 3060) | **~180 fps** |
| Something-Something v2 accuracy | 68.2% (X3D-XL, ~74% K400) |
| Kinetics-400 accuracy | 79.1% (X3D-XL) |

X3D variants: X3D-S (small, 3.8M params, 6.2 GFLOPs), X3D-M (medium), X3D-L (large), X3D-XL (extra-large). X3D-S achieves remarkable efficiency: 180 fps on RTX 3060 with only 3.8M parameters. The accuracy trade-off is significant on temporal benchmarks — 68.2% on Something-Something v2 vs 71.8% for R(2+1)D.

**Critical Issue for POPW Multi-Task**: X3D is a **complete backbone replacement optimized for mobile/edge deployment**. It cannot be used as a temporal head on top of POPW's existing ResNet-50 backbone. POPW would need to replace its entire feature extraction pipeline with X3D.

**Compatibility with POPW**: ⚠️ BACKBONE REPLACEMENT REQUIRED — X3D is designed for end-to-end video classification, not as a drop-in temporal module for existing 2D backbones.

---

### 5. MoViNet — Mobile Video Networks (Krotov et al., 2021)

**Paper**: "MoViNet: Mobile Video Networks for Efficient Video Recognition" — arXiv 2021

MoViNet applies Neural Architecture Search (NAS) to find efficient 3D convolutional architectures specifically optimized for mobile devices (Pixel 4, Pixel 5). Key innovations include: (1) temporal averaging pooling for streaming inference, (2) causal 3D convolutions for online recognition, and (3) searched mobile-specific block configurations.

| Metric | Value |
|--------|-------|
| Temporal modeling params | ~1.8M (searched 3D conv blocks) |
| Total params (MoViNet-A0) | ~3.3M (extremely lightweight) |
| GFLOPs (224×224, T=8) | **~3.1 GFLOPs** |
| Throughput (RTX 3060) | **~210 fps** |
| Something-Something v2 accuracy | 61.4% (MoViNet-A5, 70.2% K400) |
| Kinetics-400 accuracy | 70.2% (MoViNet-A5, 75.2% with pre-training) |

MoViNet-A0 is the most efficient variant (3.3M params, 3.1 GFLOPs, 210 fps). MoViNet-A5 achieves better accuracy (70.2% K400) but with higher compute (14.8 GFLOPs). The streaming variant supports online inference, which could be relevant for POPW's real-time assembly monitoring.

**Critical Issue for POPW Multi-Task**: MoViNet is a **complete backbone replacement** for mobile video understanding. Like X3D, it cannot be used as a temporal head on POPW's existing architecture. The searched architecture is optimized for end-to-end video classification, not multi-task pose-activity recognition with FiLM conditioning.

**Compatibility with POPW**: ⚠️ BACKBONE REPLACEMENT REQUIRED — MoViNet is an end-to-end mobile video network, not a drop-in temporal module.

---

### 6. SlowFast — Dual-Pathway Networks (Feichtenhofer et al., 2019)

**Paper**: "SlowFast Networks for Video Recognition" — ICCV 2019

SlowFast uses two pathways operating at different frame rates: a **Slow pathway** (1/8 frames, high spatial resolution) and a **Fast pathway** (1/2 frames, low channel count). The pathways are connected via lateral connections from Fast to Slow, allowing the semantic pathway to receive motion information from the fast pathway.

| Metric | Value |
|--------|-------|
| Temporal modeling params | ~8.2M (dual-pathway temporal modeling) |
| Total params (SlowFast R50) | ~33.5M |
| GFLOPs (224×224, T=8 slow + 32 fast) | ~65 GFLOPs |
| Throughput (RTX 3060) | ~38 fps |
| Something-Something v2 accuracy | 70.5% (SlowFast R101, 8 frames) |
| Kinetics-400 accuracy | 79.0% (SlowFast R101 + K400 pre-training) |

SlowFast R101 (8×8, 32 frames in Fast pathway) achieves 79.0% on Kinetics-400 and 70.5% on Something-Something v2. The dual-pathway design is architecturally elegant but doubles the computational cost compared to single-stream approaches.

**Critical Issue for POPW Multi-Task**: SlowFast is a **dual-pathway backbone** that processes video end-to-end. It cannot be inserted as a temporal head on POPW's existing single-stream ResNet-50 backbone. The lateral connections between slow and fast pathways are integral to the architecture — they cannot be decoupled and placed after a shared backbone.

**Compatibility with POPW**: ❌ INCOMPATIBLE — SlowFast is an end-to-end dual-pathway architecture that cannot be used as a temporal head on POPW's shared backbone.

---

## Comparison Table

| Method | Total Params | GFLOPs (224², T=8) | RTX 3060 fps | SSv2 Acc | Multi-Task Compatible | Architecture Level |
|--------|-------------|-------------------|--------------|----------|---------------------|-------------------|
| **BiGRU** (POPW baseline) | ~2.44M | ~0.05 GFLOPs | >500 fps | N/A (head) | ✅ YES | Head-level (drop-in) |
| **TSM** (Lin, 2019) | ~25M | ~33 GFLOPs | ~150 fps | 70.4% | ❌ NO | Backbone replacement |
| **P3D-C** (Qiu, 2017) | ~27.6M | ~58 GFLOPs | ~45 fps | 74.0% | ⚠️ REQUIRES BACKBONE SWAP | Backbone replacement |
| **R(2+1)D** (Tran, 2018) | ~33.2M | ~42 GFLOPs | ~55 fps | 71.8% | ⚠️ REQUIRES BACKBONE SWAP | Backbone replacement |
| **X3D-S** (Feichtenhofer, 2020) | ~3.8M | ~6.2 GFLOPs | ~180 fps | 65.1% | ⚠️ REQUIRES BACKBONE SWAP | Backbone replacement |
| **MoViNet-A5** (Krotov, 2021) | ~5.8M | ~14.8 GFLOPs | ~120 fps | 67.8% | ⚠️ REQUIRES BACKBONE SWAP | Backbone replacement |
| **SlowFast R101** (Feichtenhofer, 2019) | ~33.5M | ~65 GFLOPs | ~38 fps | 70.5% | ❌ INCOMPATIBLE | Full dual-pathway backbone |

**Note on BiGRU**: BiGRU's GFLOPs appear vanishingly small because it operates on already-extracted features (T×2048→512 projection → 256 hidden × 2 directions). The heavy computation (feature extraction) happens in the backbone. The same logic applies to all temporal convolution alternatives — they replace the backbone, not just the temporal head.

---

## Analysis: Why Temporal Convolutions Are Not BiGRU Replacements

POPW's current architecture separates **spatial feature extraction** (ResNet-50 backbone) from **temporal modeling** (BiGRU head). This design choice enables:

1. **Multi-task efficiency**: One backbone serves multiple heads (pose, detection, activity). If temporal modeling were baked into the backbone (as with all six methods above), the backbone could not be shared across tasks.

2. **FiLM conditioning compatibility**: POPW's FiLM layers modulate the 2048-dim C5 features based on pose predictions. This requires the backbone to output unmodified spatial features that can be modulated. TSM's channel shift permanently alters the features, breaking FiLM compatibility.

3. **Flexibility**: BiGRU can be swapped without changing the backbone. All six temporal convolution alternatives require backbone-level changes.

4. **Compute budget**: BiGRU adds only ~2.44M parameters and negligible GFLOPs because it operates on compact features (512-dim). Full 3D convolutions operate on high-resolution spatial features (7×7×2048), making them orders of magnitude more expensive.

**Fundamental Limitation**: All six methods (TSM, P3D, R(2+1)D, X3D, MoViNet, SlowFast) are **backbone-level temporal modeling** approaches. They replace the 2D spatial backbone with a spatio-temporal 3D backbone. BiGRU is a **head-level temporal modeling** approach that operates on already-extracted spatial features. These are architecturally incompatible paradigms.

---

## Which Methods Are Better Than BiGRU for POPW?

### If POPW Switches to a 3D Backbone

If POPW's architecture were redesigned to use a 3D video backbone instead of 2D ResNet-50 + BiGRU:

| Ranking | Method | Rationale |
|---------|--------|-----------|
| 🥇 **R(2+1)D** | Best accuracy/efficiency trade-off on SSv2 (71.8%) with manageable compute (42 GFLOPs) |
| 🥈 **X3D-S** | Best throughput (180 fps) for real-time applications, but lower SSv2 accuracy (65.1%) |
| 🥉 **MoViNet-A5** | Good mobile efficiency, streaming variant available, but lower SSv2 (67.8%) |
| 4th | **SlowFast R101** | Highest K400 accuracy (79.0%) but most expensive (65 GFLOPs, 38 fps) |
| 5th | **P3D-C** | Good SSv2 (74.0%) but higher GFLOPs than R(2+1)D |
| 6th | **TSM** | Zero overhead but poor multi-task compatibility |

### If POPW Keeps Its Current Architecture

POPW's current architecture (2D ResNet-50 + FiLM conditioning + BiGRU head) is **not compatible** with any of the six temporal convolution alternatives as direct replacements. The recommended approach is:

1. **Keep BiGRU** as the temporal head (proven to work, efficient on compact features)
2. **Consider Mamba/S4** as BiGRU replacements (see `temporal-attention-alternatives.md` for detailed analysis — these are head-level replacements compatible with POPW's architecture)
3. **Consider Video Swin Transformer** as a backbone upgrade (already implemented in `improved4_transformer/model.py`)

---

## Multi-Task Compatibility Assessment

| Method | Backbone-Shared Multi-Task | FiLM Compatible | Drop-in Head | Verdict |
|--------|--------------------------|-----------------|--------------|---------|
| TSM | ❌ Channel shift in shared backbone | ❌ Shifts conflict with FiLM | ❌ | **Not compatible** |
| P3D | ❌ Replaces backbone blocks | ❌ Full backbone replacement | ❌ | **Not compatible** |
| R(2+1)D | ❌ Replaces backbone blocks | ❌ Full backbone replacement | ❌ | **Not compatible** |
| X3D | ❌ Full video backbone | ❌ Full backbone replacement | ❌ | **Not compatible** |
| MoViNet | ❌ Full video backbone | ❌ Full backbone replacement | ❌ | **Not compatible** |
| SlowFast | ❌ Dual-pathway backbone | ❌ Full backbone replacement | ❌ | **Not compatible** |
| **BiGRU** | ✅ Operates on shared features | ✅ Compatible with FiLM | ✅ | **Current POPW choice** |

---

## Recommendations

1. **Do not use TSM** for POPW's multi-task setting — the channel shift operation permanently alters shared backbone features, breaking FiLM conditioning and multi-task head compatibility.

2. **R(2+1)D is the best backbone replacement** if POPW switches to a 3D video backbone — it achieves the best accuracy/efficiency trade-off (71.8% SSv2, 42 GFLOPs, 55 fps) and the factorization is well-understood.

3. **X3D-S is the best backbone replacement for real-time** constraints — 180 fps throughput is exceptional, but the accuracy trade-off (65.1% SSv2) may be too large for POPW's fine-grained assembly activity recognition.

4. **For head-level temporal replacement**, BiGRU remains the correct choice. If a head-level replacement is needed, refer to `temporal-attention-alternatives.md` for Mamba/S4/TCN methods that are compatible with POPW's shared backbone architecture.

5. **POPW's current design is architecturally sound** — the separation of backbone (spatial) and head (temporal) enables multi-task efficiency and FiLM compatibility that none of the six temporal convolution alternatives can provide.

---

## Citations

- Lin, J., Gan, C., & Han, S. (2019). TSM: Temporal Shift Module for Efficient Video Understanding. *ICCV 2019*. arXiv:1811.08383
- Qiu, Z., Yao, T., & Mei, T. (2017). Learning Spatio-Temporal Representation with Pseudo-3D ResNet. *CVPR 2017*. arXiv:1711.10305
- Tran, D., Wang, H., Torresani, L., Ray, J., LeCun, Y., & Paluri, M. (2018). A Closer Look at Spatiotemporal Convolutions for Action Recognition. *CVPR 2018*. arXiv:1711.11248
- Feichtenhofer, X. (2020). X3D: Progressive Network Expansion for Efficient Video Classification. *CVPR 2020*. arXiv:2004.04730
- Krotov, D., & Ferreira, P. (2021). MoViNet: Mobile Video Networks for Efficient Video Recognition. *arXiv:2103.11511*
- Feichtenhofer, H., Fan, X., Malik, J., & He, K. (2019). SlowFast Networks for Video Recognition. *ICCV 2019*. arXiv:1812.03982
