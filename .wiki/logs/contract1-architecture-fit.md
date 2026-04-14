---
title: Contract1 Architecture Fit
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
summary: '- temporal-attention-alternatives.md: 6 methods with technical details'
wikilinks: []
confidence: medium
source: research
---
# Contract 1: Architecture Fit Analysis — POPW Temporal Methods

## Source Documents
- temporal-attention-alternatives.md: 6 methods with technical details
- popw-training-pipeline.md: data flow and pipeline specifics
- projects/popw-research.md: FiLM architecture context
- popw-activity-head-temporal-alternatives-2026-04-14.md: TSM vs BiGRU POPW-specific analysis

---

## Architecture Context

POPW multi-head architecture:
```
Input RGB → ResNet-50 Backbone (C2-C5) → FPN (P3-P7)
                                        ↓
                           PoseFiLM: pose_flat[B,51] → γ-net, β-net
                                        ↓
                    C5_mod = γ·C5 + β → GAP → [B,2048]
                                        ↓
                    Activity Head: GAP(C5_mod)[B,2048] + GAP(P4)[B,256]
                                    → concat [B,2304]
                                    → Residual MLP(2304→512→256→512, skip 2304→512)
                                    → 33-class CB-Focal
```

Pose Head:
```
Heatmaps [B,17,120,160] → soft-argmax → keypoints[B,17,2]
                         → max pool → sigmoid → pose_flat[B,51]
```

Current BiGRU integration (per popw-activity-head-temporal-alternatives-2026-04-14.md):
- Feature bank stores clip-level features
- BiGRU processes sequence after backbone, before activity MLP
- BiGRU hidden state flows over time — sequential, not parallel

---

## Method-by-Method Architecture Fit

### 1. Mamba (Selective State Space Model)

**Integration point**: Replace BiGRU in activity head (post-GAP(C5_mod)+GAP(P4) fusion)
OR replace pose head temporal modeling

**Data flow change**:
```
Old: [B,T,2048] → BiGRU → [B,512] → MLP → [B,33]
New: [B,T,2048] → MambaBlock(d_model=256, d_state=16) → [B,512] → MLP → [B,33]
```

**PoseFiLM compatibility**: Mamba's selection mechanism (Δ, B, C matrices) can be conditioned via FiLM.
The pose→FiLM→C5_mod chain remains intact. Mamba receives C5_mod features as input.
Paper narrative: "Assembly-aware temporal memory with content-dependent selective scanning"

**Score: 4/5** — Strong fit. Selection mechanism aligns with pose-conditioned activity recognition.
Minimal parameter overhead (~16KB vs BiGRU's 32MB). Parallel scan enables GPU utilization.

**Integration complexity**: Low. Replaces BiGRU with MambaBlock. No backbone modification required.
Requires clip-level feature loading (same as BiGRU).

---

### 2. S4 (Structured State Space Sequence Model)

**Integration point**: Same as Mamba — replace BiGRU in activity head.

**Data flow change**:
```
Old: [B,T,2048] → BiGRU → [B,512] → MLP → [B,33]
New: [B,T,2048] → S4 layer → [B,512] → MLP → [B,33]
```

**PoseFiLM compatibility**: S4 uses data-independent matrices (A,B,C fixed for all inputs).
This means less flexibility for FiLM conditioning compared to Mamba's selective mechanism.
S4 processes entire sequence in parallel via FFT — good for GPU utilization.

**Score: 3/5** — Good fit but less adaptable than Mamba. Stable training due to HiPPO init.
Linear O(T log T) complexity. More predictable than Mamba's selection mechanism.
Paper narrative: "State space model with HiPPO initialization for long-range assembly context"

**Integration complexity**: Medium. HiPPO initialization critical for long sequences.
Selection mechanism (Mamba) provides better FiLM conditioning alignment.

---

### 3. MS-TCN++ (Multi-Stage Temporal Convolutional Network)

**Integration point**: Add before activity classification head. Progressive refinement of temporal features.

**Data flow change**:
```
Old: [B,T,2048] → temporal model → [B,512] → MLP → [B,33]
New: [B,T,2048] → MS-TCN++ (4 stages) → [B,T,2048] → temporal average → [B,2048] → MLP → [B,33]
```

**PoseFiLM compatibility**: MS-TCN++ is a pure convolutional approach — no attention mechanism.
Can use FiLM-conditioned features at each of the 4 stages.
Multi-stage refinement conceptually similar to POPW's FiLM conditioning cascade.
Progressive refinement aligns with pose→activity information flow.

**Score: 4/5** — Good fit for activity head. Pure convolutions ensure stable, predictable runtime.
No attention quadratic cost. 4 stages progressively refine action boundaries.
Proven for action segmentation — directly applicable to POPW's 33 atomic assembly actions.
Paper narrative: "Multi-stage temporal convolutional network for progressive assembly action refinement"

**Integration complexity**: Medium. No backbone modification. Adds 4-stage TCN before MLP.
Pure convolution — stable training, predictable inference latency.

---

### 4. MMN (Motion Modulation Network)

**Integration point**: Pose→Activity bidirectional communication (replaces or augments BiGRU)

**Data flow change**:
```
Old: pose_features → BiGRU → activity_features → MLP → [B,33]
New: 
  MSM: motion = pose[:,1:] - pose[:,:-1] → gamma_pose, beta_pose → activity_modulated = gamma * activity + beta
  MTM: activity_context → gamma_act, beta_act → pose_modulated = gamma_act * pose + beta_act
  Consistency loss: MSE(pose_modulated, activity_modulated)
```

**PoseFiLM compatibility**: MMN's dual-stream (MSM+MTM) directly addresses POPW's pose→activity communication.
Motion-based approach aligns with POPW's agent state tracking — temporal pose differences are semantically meaningful.
Bidirectional modulation means pose conditions activity AND activity conditions pose.
Explicit dual-stream with consistency loss — aligns with POPW's multi-task optimization.

**Score: 5/5** — Best fit for POPW's pose→activity communication requirement.
Explicit bidirectional communication addresses FiLM's unidirectional limitation.
Motion-based modulation is semantically meaningful for assembly recognition.
Paper narrative: "Bidirectional motion modulation for pose-aware assembly activity recognition"
Only method with explicit bidirectional pose↔activity communication.

**Integration complexity**: Medium-High. Requires pose and activity feature streams.
Dual-stream with consistency loss — more complex than BiGRU replacement.
Memory overhead: ~512KB (~2× FiLM overhead, acceptable).

---

### 5. ToTMNet (FFT-accelerated Toeplitz Temporal Mixing)

**Integration point**: Replace BiGRU in pose head (ultra-lightweight option)

**Data flow change**:
```
Old: pose_sequence[B,T,17,2] → BiGRU → pose_hidden[B,256] → FiLM
New: pose_sequence[B,T,17,2] → ToTMNet → pose_hidden[B,256] → FiLM
```

**PoseFiLM compatibility**: ToTMNet replaces temporal attention with FFT-accelerated Toeplitz mixing.
Ultra-lightweight (63k total parameters, ~16KB working memory).
Full-sequence temporal receptive field with linear parameters in sequence length.
Could serve as lightweight alternative for pose head where minimal computation is critical.

**Score: 3/5** — Moderate fit. Ultra-lightweight design enables deployment in resource-constrained scenarios.
FFT-accelerated — fully parallel, O(T log T).
Not designed specifically for pose-activity communication.
Limited assembly-specific applicability — generic temporal mixer.

**Integration complexity**: Low. Replaces BiGRU. Minimal parameter overhead.
GitHub not yet available (preprint) — implementation risk.

---

### 6. ATSS (Anomalous Temporal Self-Similarity)

**Integration point**: Cross-modal bidirectional fusion (more complex than POPW needs)

**Data flow change**:
```
Old: features → BiGRU → MLP → [B,33]
New:
  Triple-similarity: visual, textual, cross-modal similarity matrices
  Bidirectional cross-attentive fusion: pose attends to activity, activity attends to pose
  Transformer encoders encode similarity matrices
```

**PoseFiLM compatibility**: ATSS provides explicit bidirectional communication (pose→activity AND activity→pose).
Triple-similarity (visual, textual, cross-modal) is more complex than POPW requires.
Cross-attention mechanism is heavier than needed for assembly activity recognition.
Could inspire POPW's pose-activity alignment loss.

**Score: 3/5** — Moderate fit but overkill for POPW. Higher compute overhead (~15 GFLOPs).
Explicit bidirectionality is valuable but ATSS is designed for AI-generated video detection, not assembly recognition.
Paper narrative could leverage cross-attention for pose↔activity alignment.

**Integration complexity**: High. Full cross-attention mechanism — O(T²) complexity.
RTX 3060 borderline feasible (~4-5 MB, ~15 GFLOPs).
Not ideal for real-time inference.

---

## Summary Table

| Method | Integration Point | PoseFiLM Alignment | Complexity | Architecture Score |
|--------|------------------|-------------------|------------|-------------------|
| Mamba | Activity head (replace BiGRU) | High (selective conditioning) | Low | 4/5 |
| S4 | Activity head (replace BiGRU) | Medium (data-independent) | Medium | 3/5 |
| MS-TCN++ | Activity head (pre-MLP) | High (multi-stage refinement) | Medium | 4/5 |
| MMN | Pose↔Activity bidirectional | Highest (dual-stream modulation) | Medium-High | 5/5 |
| ToTMNet | Pose head (replace BiGRU) | Low (generic mixer) | Low | 3/5 |
| ATSS | Cross-modal fusion | Medium (explicit bidirectionality) | High | 3/5 |

## Key Architecture Insights

1. **MMN provides unique bidirectional communication** that no other method offers.
   Only MMN enables mutual pose↔activity conditioning, directly addressing POPW's multi-task coordination challenge.

2. **Mamba and MS-TCN++ are best for activity head replacement** — both offer better efficiency than BiGRU
   while maintaining compatibility with POPW's FiLM conditioning.

3. **No method requires backbone modification** — all integrate at the head level.
   This preserves POPW's existing multi-task optimization (Kendall uncertainty weighting).

4. **All methods require clip-level data loading** (same as BiGRU) — no single-frame shortcut exists.

5. **PoseFiLM chain remains intact** for all methods — pose_flat[B,51] → γ-net → β-net → C5_mod
   is unaffected by temporal method choice.