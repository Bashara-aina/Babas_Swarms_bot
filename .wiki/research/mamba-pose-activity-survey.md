---
title: "Mamba & MMN for Pose-Aware Activity Recognition: Comprehensive Survey"
created: 2026-04-14
modified: 2026-04-14
tags: [mamba, mmn, pose-activity, bidirectional-communication, temporal-modeling, motion-modulation, survey, ssM, pose-conditioned, feature-modulation]
authors: [Bashara]
type: research
summary: "Comprehensive survey of 20 papers covering Mamba SSM for video/pose modeling (8 papers) and Motion Modulation Networks for bidirectional pose↔activity communication (10 papers). Provides POPW v1/v2/v3 roadmap and architecture selection guide for POPW's temporal head upgrade path."
wikilinks:
  - [[mamba-selective-ssm]]
  - [[vision-mamba]]
  - [[video-mamba]]
  - [[bigru-temporal-action-recognition]]
  - [[pose-aware-feature-bank]]
  - [[pose-conditioned-temporal-modeling]]
  - [[projects/popw-multi-task-ikea]]
---

# Mamba & MMN for Pose-Aware Activity Recognition

## Survey Scope

This survey covers two complementary research threads for POPW's temporal modeling upgrade:

1. **Mamba SSM Papers** (8 papers): State space models for video/pose temporal modeling
2. **Motion Modulation Papers** (10 papers): Bidirectional pose↔activity communication via motion-guided feature modulation

Both threads converge on POPW v2/v3 architecture decisions.

---

## Part 1: Mamba SSM for Video/Pose Modeling

### 1.1 Mamba Selective SSM (Foundation)

**Paper**: Gu & Dao, arXiv 2312.00752

**Core**: Selective state space models — SSM parameters (A,B,C,Δ) are functions of input, enabling content-aware sequence modeling with linear-time inference.

**POPW Relevance**:
- Foundation for all subsequent Mamba papers
- Temporal pose modeling: Mamba recurrence over 17-keypoint sequences
- Selective forgetting: suppress redundant pose frames, focus on action-critical frames

### 1.2 Vision Mamba (Vim)

**Paper**: Zhu et al., arXiv 2401.09417

**Core**: First pure SSM vision backbone — no attention. Bidirectional Mamba blocks process image patches with 2D position embeddings.

**POPW Relevance**:
- Per-frame backbone replacement: ResNet-50-FPN → Vim
- 2.8× faster inference, 86.8% less GPU memory
- Bidirectional SSM captures spatial context before pose decoding

### 1.3 VideoMamba

**Paper**: Li et al., arXiv 2403.06977

**Core**: Direct Mamba adaptation for video with 4 abilities: scalable self-distillation, short-term sensitivity, long-range modeling, multi-modal fusion.

**POPW Relevance**:
- Multi-modal fusion (ability 4): fuse pose features with RGB for assembly recognition
- Temporal Mamba Block: Δ controls hidden state evolution rate

### 1.4 Video Mamba Suite

**Paper**: Chen et al., arXiv 2403.09626

**Core**: Comprehensive benchmarking — Mamba in 4 roles: Temporal Modeler, Spatio-Temporal Modeler, Backbone, **Memory Modeler**.

**POPW Relevance**:
- **Role 4 (Memory Modeler)**: Mamba as pose-activity memory buffer — highest relevance
- Architecture selection guide for POPW v2 temporal head

### 1.5 Motion Mamba

**Paper**: Zhang et al., arXiv 2403.07487

**Core**: Hierarchical bidirectional SSM for skeleton-based motion generation. Most directly relevant to POPW's pose sequence modeling.

**POPW Relevance**:
- **Same input domain**: 17-keypoint skeleton → bidirectional Mamba
- POPW v2: Replace BiGRU with Motion Mamba temporal head
- Selective mechanism: Δ decides pose info to propagate vs. suppress

### 1.6 SpikMamba

**Paper**: Chen et al., arXiv 2410.16746

**Core**: SNN + Mamba for event camera action recognition. Event cameras capture per-pixel brightness changes asynchronously.

**POPW Relevance**:
- Future edge deployment with event cameras
- Energy efficiency: spike coding + Mamba
- 1kHz temporal resolution vs 30fps RGB

### 1.7 MS-Temba

**Paper**: Sinha et al., arXiv 2501.06138

**Core**: Multi-scale temporal SSM for action detection — captures short actions (0.5-2s) and long phases (30-60s) simultaneously.

**POPW Relevance**:
- Multi-scale for IKEA assembly: hammer strike (fine) vs full phase (coarse)
- Scale fusion: learns which temporal scale matters per frame

### 1.8 VL-Mamba

**Paper**: Qiao et al., arXiv 2403.13600

**Core**: Mamba as fusion backbone for vision-language multimodal LLM — no cross-attention needed.

**POPW Relevance**:
- Demonstrates Mamba can fuse multimodal inputs (pose + RGB + activity)
- Future POPW v3: unified SSM fusion for all feature streams

---

## Part 2: Motion Modulation Networks for Bidirectional Communication

### 2.1 MMN — Motion Modulation Network (Foundation)

**Paper**: Gu et al., ACM MM 2025, arXiv 2507.21977

**Core**: Motion-guided Skeletal Modulation (MSM) + Motion-guided Temporal Modulation (MTM). Enables **bidirectional** pose↔activity communication.

**POPW Relevance**:
- **Critical**: POPW's PoseFiLM is unidirectional (pose→activity). MMN adds activity→pose feedback.
- MSM: motion modulates skeleton features
- MTM: activity state gates temporal context

### 2.2 MANs / TARM

**Paper**: Xie et al., PR 2018, arXiv 1804.08254

**Core**: Motion attention networks — motion-based attention weights for skeleton sequences. TARM combines with recurrent modules.

**POPW Relevance**:
- Motion as attention: relevant frames get high attention
- Foundation for MMN's motion-guided approach

### 2.3 PSUMNet

**Paper**: Trivedi et al., BMVC 2022, arXiv 2208.05775

**Core**: Part-wise semantic understanding — decompose body into semantic parts (upper/lower body, left/right arms) with per-part motion streams.

**POPW Relevance**:
- Per-part pose modulation instead of global
- "Screw" → right arm modulation high
- POPW enhancement: part-wise PoseFiLM

### 2.4 LSTA-Net

**Paper**: Chen et al., arXiv 2111.00823

**Core**: Long-term spatial-temporal attention — captures dependencies across full video, not just local window.

**POPW Relevance**:
- Long assembly phases (minutes) not captured by T=8 window
- Hybrid BiGRU + LSTA: local + global temporal context

### 2.5 EPAM-Net

**Paper**: Abdelkawy et al., arXiv 2408.05421

**Core**: Evolutionary pose-aware modulation — pose modulation parameters evolved via CMA-ES to optimize pose→activity alignment.

**POPW Relevance**:
- POPW's PoseFiLM could use evolutionary fine-tuning
- Pose modulation parameters optimized directly for activity

### 2.6 DMM — Deep Motion Modulation

**Paper**: Yu et al., ICCV 2023, arXiv 2307.07754

**Core**: Multi-scale motion (velocity + acceleration + jerk) for skeleton modulation.

**POPW Relevance**:
- Jerk: high = abrupt (hammer strike), low = smooth (aligning)
- Motion at multiple scales: frame-level, 2-frame, 4-frame

### 2.7 Just Add π

**Paper**: Reilly et al., WACV 2024, arXiv 2311.18840

**Core**: Discovered motion prior π from unlabeled skeleton data — pretrained encoder for motion patterns.

**POPW Relevance**:
- Pretrained motion prior reduces overfitting on 254 videos
- π frozen, only γ, β fine-tuned

### 2.8 POGARS

**Paper**: Thilakarathne et al., arXiv 2108.04186

**Core**: Pose-graph attention — skeleton as graph with attention-based message passing between body parts.

**POPW Relevance**:
- Graph attention learns action-specific pose relationships
- Alternative to predefined body part decomposition

### 2.9 PoseScript

**Paper**: Delmas et al., ECCV 2022, arXiv 2210.11795

**Core**: 3D pose reconstruction from 2D images using SMPL model + pose priors.

**POPW Relevance**:
- 3D pose from OpenPose 2D keypoints
- Depth information resolves 2D ambiguities
- SMPL mesh for body surface reasoning

### 2.10 ST-GCN

**Paper**: Yan et al., AAAI 2018, arXiv 1801.07455

**Core**: Spatial-temporal graph convolution on skeleton — foundational skeleton-based action recognition.

**POPW Relevance**:
- POPW's pose input source
- Graph CNN on skeleton vs FiLM-based modulation

---

## Part 3: Architecture Selection Guide for POPW

### POPW v1 (Current)

```
Frame → ResNet-50-FPN → C5
     → OpenPose → keypoints[17] + confidence[17]
     → PoseFiLM → C5_mod
     → Feature Bank (deque T=8)
     → BiGRU → Activity Classification
```

### POPW v2 (Near-term: Replace BiGRU with Mamba)

**Option A: Motion Mamba as Temporal Head**
```
C5_mod[0:8] → Motion Mamba Forward → h_f[t]
C5_mod[0:8] → Motion Mamba Backward → h_b[t]
H_t = Concat(h_f[t], h_b[t]) ∈ R^512
→ Activity Classification
```
**Benefit**: Selective SSM, linear complexity, motion-aware

**Option B: MS-Temba Multi-Scale**
```
C5_mod → Scale 1 (fine) → Mamba_S1
        → Scale 2 (medium) → Mamba_S2
        → Scale 3 (coarse) → Mamba_S3
Scale Fusion → H_t ∈ R^512
→ Activity Classification
```
**Benefit**: Multi-scale temporal context

### POPW v2 Enhancement: Add Motion Modulation (MMN)

**Add MSM (Motion-guided Skeletal Modulation)**
```
velocity_t = keypoints[t+1] - keypoints[t]
γ_motion, β_motion = MLP(velocity_t)
C5_mod_motion = γ_motion ⊙ C5 + β_motion
```

**Add MTM (Motion-guided Temporal Gating)**
```
motion_magnitude = ||velocity_t||
gate_t = sigmoid(Linear(motion_magnitude))
h_t = gate_t ⊙ BiGRU_output + (1-gate_t) ⊙ h_{t-1}
```

### POPW v3 (Long-term: Unified Multimodal Mamba)

```
Vision Tokens = ResNet-50-FPN features
Pose Tokens = OpenPose keypoints
Activity Tokens = C5_mod features

→ VL-Mamba-style fusion through unified bidirectional SSM
→ Unified multimodal context
→ Task-specific heads (pose, detection, activity)
```

---

## Part 4: Dataset Alignment

| Dataset | Temporal Resolution | Pose | Activities | POPW Extension |
|---------|-------------------|------|------------|---------------|
| Kinetics-400 | 30fps, 10s | 2D keypoints | 400 | Pretrain Vim/Vision Mamba |
| Something-Something | 30fps, 2-10s | None | 174 | Motion reasoning |
| Charades | 30fps, 30s | None | 157 | Multi-label |
| AVA | 30fps, 15min | 2D boxes | 80 | Spatio-temporal detection |
| NTU RGB+D | 30fps, 10s | 3D joints | 60/120 | Pretrain motion prior π |
| IKEA ASM | 30fps, 2-5min | 2D keypoints | 33 | POPW target dataset |
| Ego4D | FPS varies | None | ego | Assembly tutorials |
| assembly_evidence | ? | 2D/3D | ? | Complementary assembly |

---

## Part 5: Research Gaps & Future Directions

### Gap 1: No SSM + Pose-FiLM Combination
- All Mamba papers use either pure vision backbones or skeleton inputs
- No work combines SSM backbone with FiLM-style pose conditioning
- **POPW opportunity**: PoseFiLM + Mamba temporal head

### Gap 2: Limited Assembly-Specific Motion
- Most motion modulation papers validate on generic actions (NTU, Kinetics)
- Assembly-specific motions (screw, hammer, align) understudied
- **POPW opportunity**: Assembly motion taxonomy + specialized motion prior

### Gap 3: Bidirectional Communication Not Fully Explored
- MMN proposes bidirectional, but only validates skeleton→activity
- Activity→pose feedback (MTM) not ablated separately
- **POPW opportunity**: Full ablation of bidirectional vs unidirectional

### Gap 4: Event Cameras for Assembly
- SpikMamba validates on gesture, not assembly
- High-speed assembly events (hammer strikes) ideal for event cameras
- **POPW opportunity**: DVS event camera + SpikMamba temporal head

---

## Summary: POPW Upgrade Roadmap

| Version | Change | Expected Gain | Complexity |
|---------|--------|-------------|------------|
| v1.1 | Add motion features (DMM-style) | +1-2% | Medium |
| v2.0 | Replace BiGRU with Motion Mamba | +2-3% | High |
| v2.1 | Add MS-Temba multi-scale | +1-2% | Medium |
| v2.2 | Add MSM + MTM (MMN) | +2-3% | High |
| v3.0 | Unified multimodal Mamba fusion | +3-5% | Very High |

**Recommended path**: v1.1 (motion features) → v2.0 (Motion Mamba) → v2.2 (bidirectional MMN)

---

## References (Complete List)

### Mamba Papers
- Gu & Dao (2023). "Mamba: Linear-time Sequence Modeling with Selective State Spaces." arXiv:2312.00752
- Zhu et al. (2024). "Vision Mamba: Efficient Visual Representation Learning with Bidirectional State Space Model." arXiv:2401.09417
- Li et al. (2024). "VideoMamba: State Space Model for Efficient Video Understanding." arXiv:2403.06977
- Chen et al. (2024). "Video Mamba Suite: State Space Model as a Versatile Alternative for Video Understanding." arXiv:2403.09626
- Zhang et al. (2024). "Motion Mamba: Hierarchical Bidirectional State Space Models for Efficient Motion Generation." arXiv:2403.07487
- Chen et al. (2024). "SpikMamba: Combining Spiking Neural Networks with State Space Models for Event-based Action Recognition." arXiv:2410.16746
- Sinha et al. (2025). "MS-Temba: Multi-Scale Temporal Modeling with State Space Models for Action Detection." arXiv:2501.06138
- Qiao et al. (2024). "VL-Mamba: Exploring State Space Models for Multimodal Learning." arXiv:2403.13600

### Motion Modulation Papers
- Gu et al. (2025). "MMN: Motion Modulation Network for Skeleton-based Action Recognition." ACM MM 2025. arXiv:2507.21977
- Xie et al. (2018). "Motion Attention Networks for Skeleton-based Action Recognition." Pattern Recognition. arXiv:1804.08254
- Trivedi et al. (2022). "PSUMNet: Part-wise Semantic and Motion Understanding Network." BMVC 2022. arXiv:2208.05775
- Chen et al. (2021). "LSTA-Net: Long-term Spatial-Temporal Attention Network for Skeleton-based Action Recognition." arXiv:2111.00823
- Abdelkawy et al. (2024). "EPAM-Net: Evolutionary Pose-aware Modulation Network." arXiv:2408.05421
- Yu et al. (2023). "Deep Motion Modulation for Skeleton-based Action Recognition." ICCV 2023. arXiv:2307.07754
- Reilly et al. (2024). "Just Add π: Discovering Motion Prior for Action Recognition." WACV 2024. arXiv:2311.18840
- Thilakarathne et al. (2021). "POGARS: Pose-Graph Attention for Activity Recognition." arXiv:2108.04186
- Delmas et al. (2022). "PoseScript: 3D Body Pose from 2D Images." ECCV 2022. arXiv:2210.11795
- Yan et al. (2018). "ST-GCN: Spatial Temporal Graph Convolutional Networks." AAAI 2018. arXiv:1801.07455
