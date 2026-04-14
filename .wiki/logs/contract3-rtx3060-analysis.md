---
title: Contract3 Rtx3060 Analysis
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- logs
created: '2026-04-14'
updated: '2026-04-14'
summary: '- temporal-attention-alternatives.md: memory/compute per method'
wikilinks: []
confidence: medium
source: research
---
# Contract 3: RTX 3060 Practical Analysis — POPW Temporal Methods

## Source Documents
- temporal-attention-alternatives.md: memory/compute per method
- popw-training-pipeline.md: RTX 3060 budget details

---

## Current Baseline: BiGRU on RTX 3060

From popw-training-pipeline.md (RTX 3060 12GB memory budget):
- Batch size: 15 (effective 60 with gradient accumulation × 4)
- Mixed precision: FP16
- Memory breakdown:
  - Model (40M params, FP16): ~320MB
  - Gradients (FP32): ~640MB
  - Optimizer states (FP32, Adam): ~640MB
  - Activations (batch 15, FP16): ~4GB
  - Feature pyramids (P3-P7): ~2GB
  - Total: ~7.6GB (fits in 12GB with margin)

BiGRU specifically (from temporal-attention-alternatives.md):
- Memory: ~32 MB per BiGRU layer (256 hidden, 256 input)
- Two heads (pose + activity) = ~64 MB total
- GFLOPs: ~4 per frame

Inference target: 30 fps → 33ms per frame budget
Current forward pass (improved4_film): ~26ms

---

## Method-by-Method RTX 3060 Analysis

### 1. Mamba

**VRAM requirement** (T=16, 256 channels, d_state=16):
- SSM state: D × N = 256 × 16 = 4,096 parameters (~16 KB)
- Selection parameters: ~16 KB additional
- Total working memory: ~16 KB per layer
- **1000× smaller than BiGRU (32 MB → 16 KB)**

**GFLOPs**: ~2 per frame (vs BiGRU's ~4)
**Training memory overhead**: Minimal — parallel scan eliminates sequential gradient accumulation
**Inference latency**: ~2ms (vs BiGRU's ~5ms)
**RTX 3060 verdict**: ✅ Feasible — frees ~64 MB per head, enables larger batch sizes

**Training stability**:
- Selection mechanism requires warmup steps
- Gradient clipping recommended
- No HiPPO dependency (unlike S4)
- Risk: MEDIUM — needs warmup, but well-documented

**Integration impact on batch size**: Replacing BiGRU frees 64 MB — could increase batch from 15 to ~18-20.

---

### 2. S4

**VRAM requirement** (T=16, 256 channels):
- State matrices: D × N = 256 × 16 = 4,096 parameters (~16 KB)
- No input-dependent parameters
- Total: ~16 KB per layer
- **Same as Mamba — 1000× smaller than BiGRU**

**GFLOPs**: ~2 per frame (FFT-based convolution)
**Training memory overhead**: O(T log T) via FFT — efficient
**Inference latency**: ~2ms
**RTX 3060 verdict**: ✅ Feasible

**Training stability**:
- HiPPO initialization is CRITICAL for long-range dependencies
- Stable gradients for very long sequences (tested up to 1M tokens)
- Risk: LOW — more predictable than Mamba's selection mechanism

**Integration impact**: HiPPO initialization required — adds setup complexity.

---

### 3. MS-TCN++

**VRAM requirement** (T=16, 256 channels, kernel_size=3, 4 stages):
- Each TCN layer: 256 × 16 × 3 × 4 bytes ≈ 196 KB
- 4-layer model: ~2 MB total
- **2× smaller than BiGRU (32 MB → 2 MB)**

**GFLOPs**: ~5 per frame
**Training memory overhead**: Pure convolutions — O(T × D × kernel_size)
**Inference latency**: ~3ms (additional on top of backbone)
**RTX 3060 verdict**: ✅ Feasible — fully parallel, predictable runtime

**Training stability**:
- Pure convolutional operations — most stable of all methods
- No attention mechanism to destabilize
- Multi-loss strategy (frame-level CE + temporal consistency + boundary-aware)
- Risk: LOW — convolutional stability is well-established

**Integration impact**: Adds 4 stages before MLP. No modification to backbone or other heads.

---

### 4. MMN

**VRAM requirement** (T=16, 256 channels):
- Motion encoder: ~256 KB
- Dual modulation streams (MSM + MTM): ~256 KB
- Consistency loss overhead: ~64 KB
- Total: ~512 KB
- **~60× smaller than BiGRU (~32 MB → ~512 KB)**
- **~2× FiLM overhead** (acceptable)

**GFLOPs**: ~5 per frame
**Training memory overhead**: O(T × D) for dual streams
**Inference latency**: ~3-4ms (dual-stream processing)
**RTX 3060 verdict**: ✅ Feasible — low memory, moderate compute

**Training stability**:
- Dual-stream architecture — two independent modulation paths
- Consistency loss ensures alignment between streams
- Risk: MEDIUM — dual-stream adds complexity but not instability
- No special initialization requirements (unlike SSMs)

**Integration impact**: Requires pose and activity feature streams. More complex than BiGRU replacement.
Memory overhead is 2× FiLM — acceptable given 12GB budget.

---

### 5. ToTMNet

**VRAM requirement** (T=16, 256 channels):
- Toeplitz operator: O(T × D) = 16 × 256 = 4,096 parameters (~16 KB)
- FFT buffers: minimal
- Total: ~16 KB
- **2000× smaller than BiGRU (32 MB → 16 KB)**
- **Memory: VERY LOW**

**GFLOPs**: ~1 per frame (lowest among all methods)
**Training memory overhead**: O(T × D)
**Inference latency**: ~1-2ms (ultra-efficient)
**RTX 3060 verdict**: ✅ Feasible — lowest compute of all methods

**Training stability**:
- Gated temporal mixer (local depthwise + global Toeplitz) — stable
- No attention mechanism
- Risk: LOW — FFT-based approach is well-established
- GitHub not available — implementation risk is the concern, not stability

**Integration impact**: Replaces BiGRU. Lowest overhead of any method.
Risk: GitHub not available (preprint) — hard to verify implementation.

---

### 6. ATSS

**VRAM requirement** (T=16, 256 channels):
- Similarity matrices: 3 × T × D × D = 3 × 16 × 256 × 256 ≈ 3 MB
- Cross-attention: ~1-2 MB
- Total: ~4-5 MB
- **~8× smaller than BiGRU (32 MB → 4-5 MB)**

**GFLOPs**: ~15 per frame
**Training memory overhead**: O(T²) for full cross-attention (mitigated by local attention)
**Inference latency**: ~8-10ms (highest among all methods)
**RTX 3060 verdict**: ⚠️ Borderline — higher compute than other methods

**Training stability**:
- Cross-attention mechanism — can be unstable with long sequences
- Transformer encoders for similarity matrices — standard but memory-intensive
- Risk: MEDIUM-HIGH — cross-attention can be unstable

**Integration impact**: Full cross-attention — O(T²) complexity. Requires careful batching.
Not ideal for real-time inference despite being technically feasible.

---

## RTX 3060 Feasibility Summary

| Method | Memory (T=16, 256ch) | GFLOPs | Inference (ms) | Batch Impact | Stability Risk | Verdict |
|--------|---------------------|--------|---------------|--------------|----------------|---------|
| Mamba | ~16 KB | ~2 | ~2 | +3-5 (batch) | Medium (warmup) | ✅ Feasible |
| S4 | ~16 KB | ~2 | ~2 | +3-5 (batch) | Low (HiPPO) | ✅ Feasible |
| MS-TCN++ | ~2 MB | ~5 | ~3 | Neutral | Low | ✅ Feasible |
| MMN | ~512 KB | ~5 | ~3-4 | Neutral | Medium | ✅ Feasible |
| ToTMNet | ~16 KB | ~1 | ~1-2 | +3-5 (batch) | Low | ✅ Feasible |
| ATSS | ~4-5 MB | ~15 | ~8-10 | -2-3 (batch) | Medium-High | ⚠️ Borderline |
| BiGRU (baseline) | ~32 MB | ~4 | ~5 | None | Low | ✅ Baseline |

---

## Key RTX 3060 Insights

1. **All methods except ATSS are clearly feasible** on RTX 3060 12GB.
   Memory is not the bottleneck — compute and training stability are.

2. **Mamba, S4, ToTMNet free significant memory** (64 MB per head replacement).
   This could enable batch size increase from 15 to ~18-20, reducing training time.

3. **ATSS is borderline** — 15 GFLOPs vs 33ms budget leaves little margin.
   With backbone already using ~15ms, ATSS would push total to ~23-25ms.
   Manageable but tight — not recommended if real-time is critical.

4. **MS-TCN++ and MMN are the most balanced** — moderate memory, moderate compute,
   stable training. Good choices for POPW's resource constraints.

5. **Training stability concern**: SSMs (Mamba, S4) require careful initialization.
   Mamba needs warmup steps. S4 needs HiPPO initialization. This adds implementation complexity.

6. **NaN risk**: From popw-training-pipeline.md, corrupt JPEG frames produce NaN losses.
   SSM warmup requirements may interact poorly with NaN skip guard.
   Recommendation: Monitor NaN skip counter closely during SSM training.

---

## Batch Size Impact Analysis

Current training configuration:
- Batch 15, accumulation 4, effective 60
- Total VRAM: ~7.6GB / 12GB

With Mamba/S4/ToTMNet replacing BiGRU (-64 MB):
- Model: 320 MB
- Gradients: 640 MB (FP32)
- Optimizer: 640 MB (FP32, Adam)
- Activations: ~4GB (could increase batch)
- Feature pyramids: ~2GB
- Freed BiGRU memory: 64 MB

Estimated new batch size: 18-20 (8-12% increase)
Effective batch with accumulation: 72-80

This is a meaningful improvement for training stability and convergence speed.

---

## Inference Latency Budget

Current forward pass (improved4_film): ~26ms (per popw-model-comparison.md)
Target: 30 fps = 33ms per frame
Margin: ~7ms

| Method | Additional Latency | Total | Within Budget? |
|--------|-------------------|-------|----------------|
| None (baseline) | 0ms | ~26ms | ✅ Yes (7ms margin) |
| Mamba | +2ms | ~28ms | ✅ Yes (5ms margin) |
| S4 | +2ms | ~28ms | ✅ Yes (5ms margin) |
| MS-TCN++ | +3ms | ~29ms | ✅ Yes (4ms margin) |
| MMN | +3-4ms | ~29-30ms | ✅ Yes (3-4ms margin) |
| ToTMNet | +1-2ms | ~27-28ms | ✅ Yes (5-6ms margin) |
| ATSS | +8-10ms | ~34-36ms | ❌ No (exceeds budget) |

**Conclusion**: ATSS is the only method that exceeds the 33ms budget at inference time.