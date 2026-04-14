---
title: BiGRU Contract 3 — RTX 3060 Practical Feasibility Analysis
type: research
status: active
tags:
- bigru-replacement
- rtx-3060
- practical-feasibility
- implementation
created: '2026-04-14'
updated: '2026-04-14'
summary: Practical RTX 3060 implementation feasibility for 6 temporal methods
contracts: [3]
---

# BiGRU Contract 3: RTX 3060 Practical Feasibility Analysis

## RTX 3060 Specifications (Reference)

- **VRAM**: 12 GB GDDR6
- **Compute**: 3584 CUDA cores, 12 TFLOPS FP32
- **Architecture**: NVIDIA Ampere (GA106)
- **Memory Bandwidth**: 360 GB/s

**Typical POPW workload on RTX 3060**:
- Video Swin backbone: ~4 GB (batch=2)
- FiLM conditioning: ~512 MB
- Pose head (BiGRU): ~32 MB
- Activity head: ~32 MB
- Working memory: ~2 GB
- **Total**: ~7 GB, leaving ~5 GB buffer

---

## Method-by-Method Practical Analysis

### 1. Mamba — Feasibility: ✅ RECOMMENDED

**VRAM Usage (T=8 frames, 256 channels)**:
- SSM state: 256 × 16 = 4,096 parameters (~16 KB)
- Selection parameters: 256 × 16 × 3 = 12,288 parameters (~48 KB)
- Activation memory: O(T × D) = 8 × 256 = 2,048 values
- **Total working memory**: ~64 KB per MambaBlock
- **Compared to BiGRU**: 32 MB → 64 KB (500× reduction)

**Inference Time Estimate**:
- Parallel scan: O(T) with high parallelism
- Per-frame latency: ~1-2 ms
- Throughput: ~2 GFLOPs per frame
- **Estimated total**: 2-3 ms for full temporal processing

**Training Stability**:
- Warmup recommended for selection mechanism
- Gradient clipping advised
- Initialized with standard SSM initialization
- **Status**: Stable with proper warmup

**Implementation Complexity: LOW**
- `pip install mamba-ssm` available
- PyTorch native integration
- Well-documented examples

**Feasibility Rating: ✅ (Recommended)**
- 500× memory reduction enables larger batch sizes
- Fast inference within real-time budget
- Stable training with proper initialization
- Well-maintained implementation

---

### 2. S4 — Feasibility: ✅ RECOMMENDED

**VRAM Usage (T=8 frames, 256 channels)**:
- Diagonal state matrices: 256 × 16 = 4,096 parameters (~16 KB)
- No input-dependent parameters
- FFT buffers: minimal additional memory
- **Total working memory**: ~32 KB per S4 layer
- **Compared to BiGRU**: 32 MB → 32 KB (1000× reduction)

**Inference Time Estimate**:
- FFT-based convolution: O(T log T)
- Per-frame latency: ~2 ms
- Throughput: ~2 GFLOPs per frame
- **Estimated total**: 2-3 ms for full temporal processing

**Training Stability**:
- HiPPO initialization critical for long sequences
- Well-studied stability properties
- **Status**: Stable with proper HiPPO initialization

**Implementation Complexity: MEDIUM**
- Requires careful HiPPO initialization
- Library support less mature than Mamba
- Available in `s4` package

**Feasibility Rating: ✅ (Recommended)**
- Excellent memory efficiency
- More stable than Mamba for long sequences
- Slightly higher implementation complexity

---

### 3. MS-TCN++ — Feasibility: ✅ RECOMMENDED

**VRAM Usage (T=8 frames, 256 channels)**:
- Per TCN layer: 256 × 16 × 3 × 4 bytes ≈ 196 KB
- 4-layer model: ~2 MB total
- **Compared to BiGRU**: 32 MB → 2 MB (16× reduction)

**Inference Time Estimate**:
- Pure convolution: fully parallel
- Per-frame latency: ~1-2 ms
- Throughput: ~5 GFLOPs per frame
- **Estimated total**: 3-4 ms for full temporal processing

**Training Stability**:
- Pure convolutional operations (no recurrence)
- No vanishing/exploding gradient issues
- **Status**: Highly stable

**Implementation Complexity: LOW**
- GitHub implementation available (MS-TCN2)
- Well-tested architecture
- Easy integration as drop-in

**Feasibility Rating: ✅ (Recommended)**
- Excellent stability (no RNN gradient issues)
- Proven for action segmentation task
- Simple implementation path

---

### 4. MMN — Feasibility: ✅ RECOMMENDED (with consideration)

**VRAM Usage (T=8 frames, 256 channels)**:
- Motion encoder: ~256 KB
- Dual modulation streams: ~256 KB
- Consistency loss overhead: ~64 KB
- **Total**: ~512 KB
- **Compared to BiGRU**: 32 MB → 512 KB (64× reduction)
- **Additional FiLM overhead**: 2× normal FiLM (~512 KB)

**Inference Time Estimate**:
- Motion encoder: O(T × D)
- Dual-stream modulation: 2 × O(T × D)
- **Estimated total**: 5-8 ms for full modulation

**Training Stability**:
- Dual-stream architecture adds complexity
- Consistency loss requires careful weighting
- **Status**: Stable with proper loss balancing

**Implementation Complexity: MEDIUM**
- Requires motion encoder implementation
- Dual-stream coordination
- Custom consistency loss

**Feasibility Rating: ✅ (Recommended)**
- Acceptable memory overhead
- Adds bidirectional capability
- Moderate implementation complexity

---

### 5. ToTMNet — Feasibility: ✅ RECOMMENDED

**VRAM Usage (T=8 frames, 256 channels)**:
- Toeplitz operator: O(T × D) = 8 × 256 = 2,048 parameters (~8 KB)
- FFT buffers: minimal
- Gated mixer: additional ~8 KB
- **Total**: ~16 KB
- **Compared to BiGRU**: 32 MB → 16 KB (2000× reduction)

**Inference Time Estimate**:
- FFT-accelerated mixing: O(T log T)
- Ultra-low compute: ~1 GFLOPs per frame
- **Estimated total**: 1-2 ms for full temporal processing

**Training Stability**:
- Novel architecture (preprint)
- Limited stability data
- **Status**: Uncertain (preprint only)

**Implementation Complexity: HIGH (Risk)**
- No public GitHub implementation
- Preprint code not available
- Integration risk significant

**Feasibility Rating: ⚠️ (Borderline — Implementation Risk)**
- Excellent memory/compute characteristics
- No available implementation
- Cannot verify claims without code

---

### 6. ATSS — Feasibility: ⚠️ BORDERLINE

**VRAM Usage (T=8 frames, 256 channels)**:
- Similarity matrices: 3 × T × D × D = 3 × 8 × 256 × 256 ≈ 1.5 MB
- Cross-attention: ~1-2 MB
- Transformer encoders: ~1 MB
- **Total**: ~4-5 MB
- **Compared to BiGRU**: 32 MB → 5 MB (6× reduction)

**Inference Time Estimate**:
- Full cross-attention: O(T²)
- Transformer encoding: ~10 ms
- **Estimated total**: 15-20 ms for cross-modal processing
- **This exceeds real-time budget for activity head**

**Training Stability**:
- Cross-attention can be unstable
- Similarity matrices require careful initialization
- **Status**: Stable with standard transformer techniques

**Implementation Complexity: MEDIUM**
- GitHub implementation available
- Cross-modal fusion is well-studied

**Feasibility Rating: ⚠️ (Borderline)**
- Memory acceptable but compute exceeds budget
- 15-20 ms vs 5 ms budget for temporal processing
- Would impact overall frame processing time

---

## Practical Feasibility Summary

| Method | VRAM (T=8, 256ch) | GFLOPs/frame | Inference Time | Training Stability | Implementation | Rating |
|--------|------------------|--------------|----------------|-------------------|----------------|--------|
| **Mamba** | ~64 KB | ~2 | 2-3 ms | Warmup needed | Low | **✅** |
| **S4** | ~32 KB | ~2 | 2-3 ms | Stable (HiPPO) | Medium | **✅** |
| **MS-TCN++** | ~2 MB | ~5 | 3-4 ms | Highly stable | Low | **✅** |
| **MMN** | ~512 KB | ~5 | 5-8 ms | Stable | Medium | **✅** |
| **ToTMNet** | ~16 KB | ~1 | 1-2 ms | Uncertain | **High (Risk)** | **⚠️** |
| **ATSS** | ~5 MB | ~15 | 15-20 ms | Stable | Medium | **⚠️** |

---

## Key Findings

1. **All methods except ATSS are feasible** for RTX 3060 at T=8 frames
2. **Mamba, S4, MS-TCN++** are the most practical choices with excellent memory efficiency
3. **MMN** adds capability at acceptable cost (~512 KB, 5-8 ms)
4. **ToTMNet** has best specs but no implementation available (risky)
5. **ATSS** compute (15-20 ms) exceeds real-time budget

---

## Recommendation

For **RTX 3060 deployment**, the recommended order is:
1. **Mamba** — best memory/speed ratio, available implementation
2. **MS-TCN++** — proven for action segmentation, stable
3. **S4** — excellent theoretical properties, slightly more complex

**Avoid**: ToTMNet (no implementation), ATSS (compute too high)

**Next**: See bigru_contract4.md for unified comparison table.