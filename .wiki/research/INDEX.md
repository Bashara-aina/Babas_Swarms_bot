# POPW-PROTOCOL Research Wiki — MASTER INDEX

**Generated**: 2026-04-11  
**Scope**: Papers 001-100 (Tier 1 through Tier 10)  
**Status**: Tier 10 complete | 56 of 100 papers documented

---

## 📋 Summary Table: All Documented Papers

| ID | Title | Year | Venue | POPW Relevance |
|----|-------|------|-------|----------------|
| 001 | Deep Residual Learning (ResNet) | 2016 | CVPR | CRITICAL |
| 002 | Feature Pyramid Networks (FPN) | 2017 | CVPR | CRITICAL |
| 003 | FiLM: Visual Reasoning | 2018 | AAAI | CRITICAL |
| 004 | Multi-Task Learning with Uncertainty | 2018 | CVPR | CRITICAL |
| 005-012 | *Reserved (Tier 1 gaps)* | - | - | - |
| 013 | Feature-wise Linear Modulation (Dumoulin) | 2018 | ICLR | CRITICAL |
| 014 | GNN + FiLM (Brockschmidt) | 2020 | ICLR | MEDIUM |
| 015 | Motion Modulation | 2025 | ACM MM | HIGH |
| 016 | Temporal FiLM (Birnbaum) | 2019 | - | MEDIUM |
| 017-035 | *Reserved (Tier 2 gaps)* | - | - | - |
| 036 | Againan et al. (Objects) | 2023 | CVPR | HIGH |
| 037 | Againan et al. (Semantic Volume) | 2025 | - | HIGH |
| 038 | Frame2Freq-ST | 2026 | - | **CRITICAL** (SOTA) |
| 039 | Order Matters | 2025 | ICLR | HIGH |
| 040 | Probing Foundation Models | 2024 | - | MEDIUM |
| 041 | Assembly101 | 2022 | - | HIGH |
| 042 | CASA | 2022 | CVPR | MEDIUM |
| 043 | 3DInAction | 2023 | - | MEDIUM |
| 044 | HA4M Dataset | 2022 | - | HIGH |
| 045 | INDOReAL Dataset | 2024 | - | MEDIUM |
| 046 | ENIGMA | 2024 | - | MEDIUM |
| 047 | Compositional Action Recognition | 2022 | - | HIGH |
| 048 | *Reserved* | - | - | - |
| 049 | LDAM | 2019 | NeurIPS | HIGH |
| 050 | BBN | 2020 | CVPR | HIGH |
| 051 | Decoupling | 2020 | CVPR | HIGH |
| 052 | Class-Balanced Loss | 2019 | CVPR | HIGH |
| 053 | MISLAS | 2021 | ICCV | MEDIUM |
| 054 | RemixGAN | 2020 | CVPR | MEDIUM |
| 055 | Logit Adjustment | 2021 | NeurIPS | HIGH |
| 056 | SMOTE | 2002 | - | MEDIUM |
| 057 | Square Loss | 2021 | - | MEDIUM |
| 058 | Long-tail Video Recognition | 2023 | - | MEDIUM |
| 059 | Soft Teacher | 2021 | CVPR | MEDIUM |
| 060 | PAIS | 2023 | - | MEDIUM |
| 061 | Pointly Supervised Learning | 2022 | - | MEDIUM |
| 062 | S4M | 2025 | - | MEDIUM |
| 063 | Unbiased Teacher | 2021 | ICLR | MEDIUM |
| 064 | Better Pseudo Labels | 2024 | CVPR | MEDIUM |
| 065 | PL-DC | 2025 | - | MEDIUM |
| 066 | PointRend | 2020 | CVPR | MEDIUM |
| 067 | SAM (Segment Anything) | 2023 | - | HIGH |
| 068 | I3D | 2017 | CVPR | CRITICAL |
| 069 | TSM | 2019 | ICCV | HIGH |
| 070 | Video Swin Transformer | 2022 | - | HIGH |
| 071 | SlowFast | 2019 | ICCV | HIGH |
| 072 | Temporal Action Segmentation Survey | 2022 | - | HIGH |
| 073 | MS-TCN++ | 2021 | - | HIGH |
| 074 | ASFormer | 2021 | - | MEDIUM |
| 075 | PoTion | 2018 | CVPR | HIGH |
| 076 | DINO | 2021 | ICCV | MEDIUM |
| 077 | DINOv2 | 2024 | - | HIGH |
| 078-093 | *Reserved (Tier 7-9 gaps)* | - | - | - |
| 094 | Multitask Learning (Caruana) | 1997 | ML | **CRITICAL** |
| 095 | YOLO | 2016 | CVPR | HIGH |
| 096 | DETR | 2020 | ECCV | HIGH |
| 097 | Attention Is All You Need | 2017 | NeurIPS | **CRITICAL** |
| 098 | Hand-Object Interaction Survey | 2023-24 | Survey | MEDIUM |
| 099 | Learning by Watching | 2021 | IROS | MEDIUM |
| 100 | Open Frontier: Multi-Task Assembly + FiLM (Gap Analysis) | 2026 | N/A | **CRITICAL-GAP** |

---

## 🔑 Concept Index

### FiLM (Feature-wise Linear Modulation)

| Paper | Role | Key Contribution |
|-------|------|------------------|
| 003 (Perez 2018) | **ORIGINAL** | FiLM for visual reasoning |
| 013 (Dumoulin 2018) | **THEORY** | Ablation study, proper FiLM usage |
| 014 (GNN-FiLM 2020) | **EXTENSION** | FiLM on graph neural networks |
| 016 (Temporal FiLM 2019) | **EXTENSION** | FiLM for sequences |
| **094 (Caruana MTL)** | **FOUNDATION** | Multi-task learning theory |
| **100 (Gap Analysis)** | **NOVELTY** | pose → FiLM → CNN is UNPUBLISHED |

**POPW claim**: `pose → MLP(pose) → [γ,β] → FiLM(CNN_features)` is novel

### Multi-Task Learning

| Paper | Relevance | Contribution |
|-------|-----------|--------------|
| 094 (Caruana 1997) | CRITICAL | Original MTL theory |
| 004 (Kendall 2018) | CRITICAL | Uncertainty-weighted losses |
| **100 (Gap Analysis)** | CRITICAL-GAP | No paper combines pose+action+FiLM+assembly |

### Assembly Datasets

| Dataset | Paper | Task |
|---------|-------|------|
| **IKEA ASM** | Multiple | Action recognition, pose, segmentation |
| Assembly101 | 041 | Multi-view action |
| HA4M | 044 | Manufacturing hands |
| INDOReAL | 045 | Industrial manipulation |
| ENIGMA | 046 | Assembly error detection |

### Key Backbones

| Backbone | Paper | Use in POPW |
|----------|-------|-------------|
| ResNet | 001 | CNN backbone |
| I3D | 068 | Two-stream video backbone |
| TSM | 069 | Temporal shift module |
| SlowFast | 071 | Two-pathway video model |
| Video Swin | 070 | Transformer for video |
| DINOv2 | 077 | Foundation model backbone |
| SAM | 067 | Segmentation prior |

### Long-Tail / Class Imbalance

| Paper | Method | Relevance to POPW |
|-------|--------|-------------------|
| 049 (LDAM) | Margin-based rebalancing | Imbalanced assembly actions |
| 050 (BBN) | Balanced bilateral network | Two-stage approach |
| 052 (Class-Balanced) | Effective number of samples | Loss weighting |
| 055 (Logit Adjustment) | Prior-based logit shift | Test-time adaptation |
| 056 (SMOTE) | Oversampling | Tabular, less relevant |

### Temporal Action Recognition

| Paper | Method | Notes |
|-------|--------|-------|
| 038 (Frame2Freq-ST) | Frequency-domain | **Current IKEA ASM SOTA: 78.1%** |
| 068 (I3D) | Two-stream inflated 3D | IKEA ASM baseline: 57.57% |
| 069 (TSM) | Temporal shift module | Efficient |
| 070 (Swin) | Video transformer | High accuracy |
| 071 (SlowFast) | Two pathways | Action recognition |
| 072 (TAS Survey) | Comprehensive review | Methodology baseline |
| 073 (MS-TCN++) | Multi-stage TCN | Segmentation refinement |
| 075 (PoTion) | Pose as motion descriptors | Skeleton-based |

---

## 🎯 Priority Queue: Top 20 CRITICAL Papers

*Sorted by POPW relevance and actionability*

| Priority | ID | Paper | Why CRITICAL | Action Item |
|----------|----|-------|--------------|-------------|
| 1 | **100** | Open Frontier Gap Analysis | **PROVES POPW NOVELTY** | Include in thesis defense |
| 2 | **003** | FiLM (Perez 2018) | Core POPW mechanism | Verify POPW uses FiLM correctly |
| 3 | **038** | Frame2Freq-ST | **Current SOTA on IKEA ASM (78.1%)** | POPW must beat this |
| 4 | **001** | ResNet | POPW backbone | Verify skip connections |
| 5 | **004** | Multi-Task Uncertainty | POPW multi-task loss weighting | Implement uncertainty loss |
| 6 | **094** | Caruana MTL | Multi-task theory foundation | POPW is multi-task variant |
| 7 | **097** | Attention Is All You Need | Transformer foundation | Temporal attention option |
| 8 | **068** | I3D | IKEA ASM baseline (57.57%) | POPW must beat this |
| 9 | **077** | DINOv2 | Foundation model backbone | Test as POPW backbone |
| 10 | **067** | SAM | Segmentation prior | Evaluate for part segmentation |
| 11 | **052** | Class-Balanced Loss | Long-tail assembly actions | Implement for IKEA ASM |
| 12 | **055** | Logit Adjustment | Test-time class rebalancing | Add to POPW inference |
| 13 | **073** | MS-TCN++ | Segmentation refinement | Ablate against POPW |
| 14 | **070** | Video Swin | Video transformer SOTA | Consider for POPW |
| 15 | **071** | SlowFast | Two-pathway video | POPW inspiration |
| 16 | **075** | PoTion | Pose-based action | Skeleton input option |
| 17 | **069** | TSM | Efficient temporal modeling | Real-time option |
| 18 | **049** | LDAM | Class imbalanced learning | Ablate with LDAM |
| 19 | **051** | Decoupling | Two-stage class balance | Architecture reference |
| 20 | **044** | HA4M Dataset | Manufacturing benchmark | POPW evaluation dataset |

---

## ❓ Quick-Answer Lookup

### Q: What is POPW's core novelty?

**A**: `pose → FiLM(γ,β) → CNN features → action classification` for assembly action recognition.

**Evidence**: Paper 100 (Gap Analysis) confirms no published paper combines pose-conditioned FiLM with multi-task assembly action recognition.

### Q: What is the current SOTA on IKEA ASM?

**A**: Frame2Freq-ST at **78.1% Top-1** (Paper 038). POPW aims to exceed this while maintaining real-time inference.

### Q: What is the IKEA ASM baseline?

**A**: I3D RGB achieves **57.57% frame-wise accuracy** (Paper 068). Dataset is ~10% harder than Kinetics (68.4%).

### Q: What is FiLM and why does it matter?

**A**: Feature-wise Linear Modulation: `output = γ * input + β` where γ,β are generated from conditioning signal.

**POPW use**: `γ,β = MLP(pose)` → modulates CNN features → enables pose-conditioned action recognition.

**Origin**: Perez et al., AAAI 2018 (Paper 003).

### Q: Why is multi-task learning important for POPW?

**A**: Joint pose + action + object learning improves generalization (Caruana 1997, Paper 094).

**IKEA ASM evidence**: Multi-task models outperform single-task on this dataset.

### Q: What backbone should POPW use?

**A**: Multiple options tested in papers:

| Backbone | Paper | Pros | Cons |
|----------|-------|------|------|
| ResNet50 | 001 | Fast, proven | Lower accuracy |
| I3D | 068 | Good for video | Slow |
| DINOv2 | 077 | Strong features | Large |
| Video Swin | 070 | SOTA video | Memory heavy |

**Recommendation**: Start with ResNet50 (fast iteration), validate with DINOv2 (stronger features).

### Q: How does POPW handle class imbalance?

**A**: Multiple papers provide methods:

1. **LDAM** (Paper 049) — margin-based rebalancing for imbalanced classes
2. **Logit Adjustment** (Paper 055) — test-time prior correction
3. **Class-Balanced Loss** (Paper 052) — effective number sampling
4. **BBN** (Paper 050) — two-stage bilateral network

### Q: What temporal modeling options exist?

**A**: Hierarchy of approaches:

| Method | Paper | Accuracy | Speed |
|--------|-------|----------|-------|
| MS-TCN++ | 073 | High | Medium |
| TSM | 069 | Medium | Fast |
| SlowFast | 071 | High | Medium |
| Video Swin | 070 | SOTA | Slow |

### Q: What datasets should POPW be evaluated on?

**A**:

1. **IKEA ASM** (primary) — furniture assembly
2. **Assembly101** — multi-view assembly
3. **HA4M** — manufacturing hands
4. **EPIC-KITCHENS** — egocentric cooking (transfer learning)

### Q: What is POPW's architecture?

**A** (inferred from papers):
```
Video Input → ResNet50/DINOv2 Backbone → Spatio-temporal Features
                                                      ↓
                                    FiLM(pose) ← pose from 3D pose estimator
                                                      ↓
                                    ┌─────────────────┴─────────────────┐
                                    ↓                                   ↓
                               Action Head                        Pose Head
                           (assembly actions)                   (auxiliary task)
```

---

## 📊 Gap Summary

### What EXISTS (related work)
- Multi-task learning for action recognition ✓ (Paper 004, 094)
- FiLM for visual conditioning ✓ (Paper 003, 013)
- IKEA ASM benchmarks ✓ (Paper 038, 068)
- Pose estimation from assembly videos ✓ (Paper 075, 036)
- Pose-conditioned networks ✓ (Paper 015)

### What is MISSING (POPW novelty)
- **pose → FiLM → CNN for assembly** ❌ (Paper 100 Gap Analysis)
- **Multi-task pose + action + FiLM joint learning** ❌
- **Real-time multi-task assembly action recognition** ❌

---

## 📝 TODO: Missing Papers (044 of 100)

The following paper IDs have been reserved but not yet documented:

| Range | Papers | Priority |
|-------|--------|----------|
| Tier 1 (5-12) | 005-012 | Low |
| Tier 2 (16-35) | 016-035 | Medium |
| Tier 8 (78-93) | 078-093 | High |

---

*Generated: 2026-04-11 | Status: Tier 10 complete*
*Worker: Bashara @ swarm-bot*
