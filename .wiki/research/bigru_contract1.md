---
title: BiGRU Contract 1 — Architecture Fit Analysis
type: research
status: active
tags:
- bigru-replacement
- architecture-fit
- temporal-modeling
created: '2026-04-14'
updated: '2026-04-14'
summary: Architecture fit analysis of 6 temporal methods against POPW's BiGRU + feature bank
contracts: [1]
---

# BiGRU Contract 1: Architecture Fit Analysis

## POPW Activity Head Architecture (Reference)

The POPW activity head operates in three stages:

1. **Stage 1: Per-Frame Feature Extraction** — C5_mod (2048d) + P4 (256d) → concat → project to 512d
2. **Stage 2: Temporal Feature Bank** — Sliding window of T=8 frames, each 512d vectors
3. **Stage 3: BiGRU Temporal Processing** — BiGRU(512d hidden) → attention pooling → 33-class classifier

Total activity head: ~2.44M parameters
BiGRU alone: ~1.18M parameters (2 directions × 3 gates × (512×256 + 256×256))

---

## Method-by-Method Architecture Fit Analysis

### 1. Mamba — Architecture Fit: 4/5

**How it maps to POPW stages:**

| POPW Stage | Mamba Integration | Notes |
|------------|------------------|-------|
| Stage 1 (Feature Extraction) | No change needed | Keep C5_mod + P4 + projection |
| Stage 2 (Feature Bank) | Compatible | Bank stores 512d vectors, Mamba processes T×512 sequences |
| Stage 3 (BiGRU replacement) | **Direct swap** | MambaBlock(d_model=512, d_state=16) replaces BiGRU |

**Integration Complexity: LOW**

- MambaBlock is a drop-in replacement for nn.GRU
- Same input/output dimensions (T×512 → T×512)
- Selection mechanism (S6) adds input-dependent gating similar to GRU's update/reset gates
- PyTorch native: `from mamba_ssm import MambaBlock`

**Changes to existing code:**

```python
# Current (BiGRU):
self.bigru = nn.GRU(input_size=512, hidden_size=256, bidirectional=True, batch_first=True)

# Replacement (Mamba):
from mamba_ssm import MambaBlock
self.mamba = MambaBlock(d_model=512, d_state=16, d_conv=4)
# Output shape unchanged: [B, T, 512]
```

**Fit Score: 4/5**
- Excellent memory reduction (1000×)
- Selection mechanism mirrors GRU's gating behavior
- Slight warmup needed for selection mechanism stability
- No native bidirectionality (must run forward+reverse pass like unidirectional GRU)

---

### 2. S4 — Architecture Fit: 3/5

**How it maps to POPW stages:**

| POPW Stage | S4 Integration | Notes |
|------------|----------------|-------|
| Stage 1 (Feature Extraction) | No change needed | Keep existing pipeline |
| Stage 2 (Feature Bank) | Compatible | Bank feeds into S4 layer |
| Stage 3 (BiGRU replacement) | **Viable replacement** | S4 layer replaces BiGRU with different temporal semantics |

**Integration Complexity: MEDIUM**

- S4 uses diagonal state space (DSS) representation
- Requires HiPPO initialization for stable long-range dependencies
- More theoretical than practical for POPW's T=8 sequences
- Library support less mature than Mamba

**Changes to existing code:**

```python
# S4 requires careful initialization
from .s4 import S4Block
# Need to initialize with HiPPO for proper state propagation
self.s4 = S4Block(d_model=512, d_state=16, d_conv=4)
# Must use proper HiPPO initialization
```

**Fit Score: 3/5**
- Theoretically elegant for long sequences
- Less proven for short T=8 sequences (POPW's use case)
- More implementation complexity than Mamba
- No selective mechanism (data-independent A, B, C matrices)

---

### 3. MS-TCN++ — Architecture Fit: 4/5

**How it maps to POPW stages:**

| POPW Stage | MS-TCN++ Integration | Notes |
|------------|---------------------|-------|
| Stage 1 (Feature Extraction) | No change needed | Keep existing pipeline |
| Stage 2 (Feature Bank) | **Stage 2 enhancement** | TCN operates ON the bank, not replacing it |
| Stage 3 (BiGRU replacement) | **Alternative approach** | TCN replaces BiGRU as temporal processor |

**Integration Complexity: LOW**

- MS-TCN++ is pure convolution — no recurrence
- Multi-stage refinement conceptually similar to POPW's FiLM cascade
- Well-tested for action segmentation (directly matches activity head task)
- Available GitHub implementation

**Changes to existing code:**

```python
# Option A: Add before activity classifier (enhancement)
self.ms_tcn = MultiStageTCN(in_channels=512, hidden_channels=256, num_stages=4)
temporal_features = self.ms_tcn(bank_features)  # [B, T, 512]

# Option B: Replace BiGRU entirely
# TCN outputs per-frame predictions, aggregate with attention
```

**Fit Score: 4/5**
- Proven for action segmentation (POPW's exact task)
- Pure convolutions = stable, predictable runtime
- Multi-stage refinement aligns with POPW's design philosophy
- Cannot capture very long-range dependencies as effectively as SSMs

---

### 4. MMN (Motion Modulation Network) — Architecture Fit: 4/5

**How it maps to POPW stages:**

| POPW Stage | MMN Integration | Notes |
|------------|-----------------|-------|
| Stage 1 (Feature Extraction) | **Stage 1 enhancement** | Motion features from pose differences enhance extraction |
| Stage 2 (Feature Bank) | **Motion-aware bank** | Bank stores motion-modulated features |
| Stage 3 (BiGRU replacement) | Complementary | MMN works alongside BiGRU, not replacing it |

**Integration Complexity: MEDIUM**

- MMN introduces dual-stream modulation (MSM + MTM)
- Requires motion encoder (pose differences)
- Bidirectional pose-activity communication via FiLM
- Adds consistency loss for alignment

**Changes to existing code:**

```python
# MMN integration as pose-activity bridge
motion_features = pose_features[:, 1:] - pose_features[:, :-1]  # T-1 frames
# MSM: pose modulates activity via motion
gamma_pose, beta_pose = motion_encoder(motion_features)
activity_features = gamma_pose * activity_features + beta_pose

# MTM: activity modulates pose
gamma_act, beta_act = activity_encoder(activity_features)
pose_features = gamma_act * pose_features + beta_act
```

**Fit Score: 4/5**
- Native bidirectional communication (unique among methods)
- Motion-based approach aligns with POPW's temporal pose modeling
- 2× FiLM overhead is acceptable
- Does NOT replace BiGRU — enhances pose-activity coupling

---

### 5. ToTMNet (FFT-accelerated Toeplitz) — Architecture Fit: 3/5

**How it maps to POPW stages:**

| POPW Stage | ToTMNet Integration | Notes |
|------------|---------------------|-------|
| Stage 1 (Feature Extraction) | No change needed | Keep existing pipeline |
| Stage 2 (Feature Bank) | Compatible | Bank feeds into Toeplitz mixer |
| Stage 3 (BiGRU replacement) | **Viable replacement** | Toeplitz mixing replaces recurrent processing |

**Integration Complexity: MEDIUM**

- Ultra-lightweight (63k parameters total)
- FFT-based acceleration
- Gated temporal mixer combines local + global
- Not yet publicly available (preprint only)

**Changes to existing code:**

```python
# ToTMNet integration
from .totmnet import ToeplitzTemporalMixer
self.totm = ToeplitzTemporalMixer(d_model=512, T_max=16)
# Uses FFT for O(T log T) temporal mixing
```

**Fit Score: 3/5**
- Lowest memory footprint (16 KB)
- Promising for ultra-lightweight deployment
- GitHub not available — integration risk
- Missing proven benchmark on activity tasks

---

### 6. ATSS (Anomalous Temporal Self-Similarity) — Architecture Fit: 2/5

**How it maps to POPW stages:**

| POPW Stage | ATSS Integration | Notes |
|------------|-----------------|-------|
| Stage 1 (Feature Extraction) | No change needed | Keep existing pipeline |
| Stage 2 (Feature Bank) | **Major redesign** | Similarity matrices replace simple bank |
| Stage 3 (BiGRU replacement) | Not applicable | ATSS is cross-modal fusion, not temporal processor |

**Integration Complexity: HIGH**

- ATSS introduces similarity-based representation (visual, textual, cross-modal)
- Bidirectional cross-attention between pose and activity
- Requires redesign of feature bank structure
- Transformer encoders add complexity

**Changes to existing code:**

```python
# ATSS-style cross-modal attention
# Triple similarity matrices
S_visual = visual_features @ visual_features.transpose(-2, -1)
S_cross = pose_features @ activity_features.transpose(-2, -1)
# Cross-attention fusion
fused = cross_attention(query=pose_features, key=activity_features)
```

**Fit Score: 2/5**
- Provides native bidirectionality (like MMN)
- Cross-modal focus doesn't match POPW's pose→activity one-way need
- O(T²) attention complexity for full cross-attention
- Higher compute than BiGRU (15 GFLOPs vs 4 GFLOPs)
- Most invasive integration — would require rearchitecting activity head

---

## Architecture Fit Summary Table

| Method | Stage 1 | Stage 2 | Stage 3 | Integration Complexity | Fit Score |
|--------|---------|---------|---------|----------------------|-----------|
| **Mamba** | Compatible | Compatible | Direct swap | **Low** | **4/5** |
| **S4** | Compatible | Compatible | Viable replacement | **Medium** | **3/5** |
| **MS-TCN++** | Compatible | Enhancement | Alternative | **Low** | **4/5** |
| **MMN** | Enhancement | Motion-aware | Complementary | **Medium** | **4/5** |
| **ToTMNet** | Compatible | Compatible | Viable replacement | **Medium** | **3/5** |
| **ATSS** | Compatible | Major redesign | Not applicable | **High** | **2/5** |

---

## Key Findings

1. **Mamba** offers the cleanest BiGRU replacement with lowest integration risk
2. **MS-TCN++** provides enhancement opportunity as alternative/companion to BiGRU
3. **MMN** is the only method that natively supports bidirectional pose-activity communication
4. **ATSS** is too invasive — would require complete activity head redesign
5. **S4** and **ToTMNet** are viable but less proven for POPW's T=8 sequences

---

## Recommendation

For architecture fit, **Mamba** is the top choice for BiGRU replacement, with **MS-TCN++** as a secondary enhancement option.

**Next**: See bigru_contract2.md for novelty assessment and bigru_contract3.md for RTX 3060 feasibility.