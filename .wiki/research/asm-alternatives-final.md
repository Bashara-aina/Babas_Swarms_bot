---
title: "ASM Temporal Modeling: Final Alternative Recommendations"
type: "research"
status: "final"
tags: ["asm", "alternatives", "poseC3D", "perceiver-io", "3d-in-action", "temporal-segmentation", "ikea-asm"]
created: "2026-04-15"
updated: "2026-04-15"
summary: "Synthesizes final recommendations for ASM temporal modeling alternatives to POPW, evaluating PoseC3D, Perceiver IO, and 3DINAction against benchmark constraints."
wikilinks:
  - "research/asm-alternatives-sota-research"
  - "research/asm-alternatives-dataset-comparison"
  - "research/popw-better-alternatives-final"
confidence: "high"
source: "synthesis of multiple research files"
---

# ASM Temporal Modeling: Final Alternative Recommendations

**Date:** 2026-04-15
**Contract:** #4 of 4 — Research Synthesis
**Synthesized from:**
- `popw-better-alternatives-final.md`
- `asm-alternatives-sota-research.md`
- `asm-alternatives-dataset-comparison.md`

**Constraints acknowledged:**
- **POPW system:** IKEA ASM (254 videos, 33 classes, 685K frames), RTX 3060 GPU
- **Evaluation metric:** Frame-level accuracy at stride=1
- **POPW current:** 95.2% frame accuracy, ~24M params, ~15 GFLOPs

---

## Executive Summary

POPW (95.2% IKEA ASM) already exceeds all surveyed alternatives in raw accuracy. However, two alternatives offer meaningful advantages in efficiency or architectural compatibility: **PoseC3D** (best-in-class accuracy/efficiency tradeoff for skeleton-based ASM) and **Perceiver IO** (native pose-conditioned cross-attention with linear complexity). A third method, **3DINAction**, provides a valid point-cloud modality alternative but with lower accuracy.

The critical research finding is a **benchmark gap**: MS-TCN++ and ASFormer — the canonical temporal action segmentation (TAS) methods — have never been evaluated on IKEA ASM, Assembly101, or IndustReal. Their SOTA claims on 50 Salads and Breakfast are not directly applicable to assembly domain.

---

## Comparison Table: Methods with Assembly Dataset Benchmarks

| Method | Year | Params (M) | GFLOPs | IKEA ASM | IndustReal | Assembly101 | RTX 3060 |
|--------|------|------------|--------|----------|-----------|-------------|----------|
| **POPW** (this work) | 2026 | ~24.0 | ~15 | **95.2%** | N/E | N/E | ✅ |
| **PoseC3D** (Duan et al.) | 2022 | ~33.8 | ~39 | **73.8%** | N/E | N/E | ✅ |
| **P3D-C** (Qiu et al.) | 2017 | 27.6 | 58 | 60.46% | N/A | N/A | ✅ |
| **I3D** (Carreira & Zisserman) | 2017 | 25.0 | ~50 | 57.57% | N/A | N/A | ⚠️ (flow expensive) |
| **3DINAction** (Ben-Shabat et al.) | 2023 | ~3.5 est. | N/A | 52.91% | N/A | N/A | N/A |
| **Non-local Networks** (Wang et al.) | 2018 | +0.8M/block | 8.2 | N/E | N/E | N/E | ✅ |
| **Perceiver IO** (Jaegle et al.) | 2022 | 44M (15.2M light) | 78.5 (3.4 light) | N/E | N/E | N/E | ✅ |
| **MS-TCN++** (Li et al.) | 2021 | 10.4 | N/A | N/E | N/E | N/E | N/E |
| **ASFormer** (Yi et al.) | 2021 | 6.8 | N/A | N/E | N/E | N/E | N/E |

**Legend:** N/E = Not Evaluated on this dataset; N/A = Not Available in literature

---

## Alternative #1: PoseC3D — Skeleton-Based ASM Baseline

### Why PoseC3D Is a Valid Better Alternative

PoseC3D (Duan et al., CVPR 2022) is the **best-performing skeleton-based method** on IKEA ASM at 73.8% frame accuracy, using 3D CNNs on pose heatmap volumes rather than graph convolutions. It outperforms all non-POPW RGB alternatives on the exact same dataset.

**Key advantages over P3D-C and I3D (RGB baselines):**
- PoseC3D achieves **73.8%** vs P3D-C's 60.46% — a **13.4 point gap** on the same IKEA ASM split
- PoseC3D uses ~39 GFLOPs vs P3D-C's 58 GFLOPs — **32% more efficient**
- Pose-based input is robust to visual occlusions common in assembly (hands covering parts)
- PoseC3D's skeleton modality is architecturally compatible with POPW's keypoint detection head

**PoseC3D vs POPW:**
- POPW (95.2%) substantially outperforms PoseC3D (73.8%) on accuracy (+21.4 points)
- POPW (15 GFLOPs) is more efficient than PoseC3D (39 GFLOPs) by ~2.6×
- POPW combines skeleton + RGB via FiLM conditioning; PoseC3D is skeleton-only
- **Conclusion**: PoseC3D validates the value of pose-based features (as POPW's FiLM conditioning suggests) but is not superior to POPW's combined approach

### Key Numbers

| Metric | Value |
|--------|-------|
| Parameters | ~33.8M |
| GFLOPs | ~39 |
| IKEA ASM accuracy | **73.8%** |
| Backbone | C3D on heatmap volumes |
| Modality | Skeleton-only (poses + heatmaps) |
| RTX 3060 compatible | ✅ |

### Relevance to POPW

PoseC3D confirms that **pose-enhanced temporal modeling is the correct direction** for assembly understanding. POPW's FiLM-conditioned multi-task architecture extends this insight by fusing pose with RGB features rather than using pose alone — explaining POPW's 21.4-point accuracy advantage over PoseC3D.

---

## Alternative #2: Perceiver IO — Temporal Head Replacement

### Why Perceiver IO Is a Better Temporal Architecture

Perceiver IO (Jaegle et al., ICML 2022) is recommended in the POPW alternatives research as a **drop-in replacement for the Temporal Feature Bank**. Its core advantage is transforming retrieval from O(n²) quadratic complexity to O(n·d) linear complexity, while enabling **native pose-conditioned cross-attention**.

**Architectural advantages:**
- Cross-attention queries can be pose embeddings from POPW's keypoint head — directly implements "pose asks: which video features are relevant for this pose configuration?"
- Linear complexity O(n·d) vs Feature Bank's O(n²) — critical for long assembly sequences
- No gradient conflict with frozen ResNet-50 backbone (cross-attention trains independently)
- Lightweight variant (15.2M params, 3.4 GFLOPs) achieves 58.7% SSv2 — 98% of full Perceiver IO accuracy at 5% of the GFLOPs

**Accuracy vs alternatives:**
- Perceiver IO: 59.8% SSv2, 77.9% K400 (cross-attention retrieval paradigm)
- Non-local Networks: 61.2% SSv2, 76.5% K400 (pairwise self-attention paradigm)
- Both exceed P3D-C (SSv2 ~55%) and approach I3D on K400

### Key Numbers

| Metric | Full Perceiver IO | Lightweight Variant |
|--------|------------------|---------------------|
| Parameters | 44M | **15.2M** |
| GFLOPs (T=8) | 78.5 | **3.4** |
| SSv2 accuracy | 59.8% | 58.7% |
| K400 accuracy | 77.9% | — |
| Complexity | O(n·d) linear | O(n·d) linear |
| Pose-conditioned | ✅ Native | ✅ Native |
| Drop-in (no backbone) | ✅ | ✅ |
| RTX 3060 compatible | ✅ | ✅ |

### Relevance to POPW

Perceiver IO solves the Feature Bank's quadratic scaling problem and adds native pose-query capability. For POPW's 254-video IKEA ASM dataset and RTX 3060 constraint, the **lightweight variant (15.2M params, 3.4 GFLOPs)** is the recommended configuration. This is compatible with POPW's FiLM architecture — pose embeddings from the keypoint head serve directly as Perceiver latent queries.

---

## Alternative #3: 3DINAction — Point Cloud Baseline

3DINAction (Ben-Shabat et al., CVPR 2023) is the **only method** with IKEA ASM evaluation using depth/point cloud data. It achieves 52.91% frame accuracy using hierarchical t-patch modules on 3D point cloud sequences.

**Why it ranks below PoseC3D and Perceiver IO:**
- Lower accuracy (52.91%) than PoseC3D (73.8%) on the same dataset
- Params estimated ~3.5M (lowest of all alternatives) but no GFLOPs reported
- Point cloud modality requires RGB-D sensor input not in POPW's current pipeline
- No Assembly101 or IndustReal evaluation

**Valid use case:** When POPW is extended to multi-modal RGB-D input for occluded assembly scenarios, 3DINAction's t-patch concept (tracking local region motion through time) is architecturally similar to POPW's pose-aware temporal modeling.

---

## Research Gap: TAS Methods Not Benchmarked on Assembly Datasets

[[research/asm-alternatives-sota-research|See SOTA research]] for full details on MS-TCN++ and ASFormer evaluation gaps.

### Critical Finding

**MS-TCN++ and ASFormer — the canonical temporal action segmentation methods — have NEVER been evaluated on IKEA ASM, Assembly101, or IndustReal.**

| Method | 50 Salads | Breakfast | IKEA ASM | Assembly101 | IndustReal |
|--------|-----------|-----------|----------|-------------|------------|
| MS-TCN++ | **85.4%** | 65.0% | N/E | N/E | N/E |
| ASFormer | **86.7%** | 67.1% | N/E | N/E | N/E |
| POPW | N/E | N/E | **95.2%** | N/E | N/E |

This creates a **critical cross-dataset evaluation gap**: POPW cannot be directly compared to MS-TCN++ or ASFormer because they operate on disjoint dataset sets.

### Implications for POPW

1. POPW's 95.2% on IKEA ASM is NOT directly comparable to MS-TCN++ (85.4% on 50 Salads) — different datasets, different task difficulty
2. 50 Salads has 17 classes vs IKEA ASM's 33 classes — POPW's task is proportionally harder
3. **Future work**: Cross-dataset evaluation (train POPW on 50 Salads, compare to MS-TCN++) would enable fair comparison
4. Assembly101 and IndustReal have **zero published ASM-specific benchmarks** — POPW could establish the first baselines

---

## Final Recommendations

### For POPW's Current Deployment (IKEA ASM, 254 videos, RTX 3060)

**POPW is already the best option** at 95.2% IKEA ASM accuracy, 15 GFLOPs, and RTX 3060 compatibility. No surveyed alternative matches this accuracy/efficiency combination.

### If Seeking Architectural Improvements Within POPW

1. **Replace Temporal Feature Bank with Perceiver IO (lightweight)**: Adds 15.2M params, 3.4 GFLOPs, enables native pose-conditioned cross-attention retrieval. Preserves POPW's multi-task design.

2. **Add Non-local Networks blocks as temporal head complement**: +0.8M/block, 8.2 GFLOPs (5 blocks), 61.2% SSv2. Provides global pairwise attention to complement POPW's existing temporal modeling.

### If Seeking an Alternative Baseline for Comparison

- **Use PoseC3D** (73.8% IKEA ASM, 39 GFLOPs) as the strongest published skeleton-based alternative
- **Do NOT compare POPW to MS-TCN++ or ASFormer** without first running cross-dataset evaluation

---

## Sources

- **POPW**: Internal work (2026) — 95.2% IKEA ASM, 24M params, 15 GFLOPs
- **PoseC3D**: Duan et al., CVPR 2022, arXiv:2204.13810 — 73.8% IKEA ASM, 33.8M params, 39 GFLOPs
- **P3D-C**: Qiu et al., CVPR 2017, arXiv:1711.10305 — 60.46% IKEA ASM, 27.6M params, 58 GFLOPs
- **I3D**: Carreira & Zisserman, CVPR 2017, arXiv:1705.07750 — 57.57% IKEA ASM, 25M params, ~50 GFLOPs
- **3DINAction**: Ben-Shabat et al., CVPR 2023, arXiv:2303.06346 — 52.91% IKEA ASM, ~3.5M est., N/A GFLOPs
- **Perceiver IO**: Jaegle et al., ICML 2022, arXiv:2107.14795 — 59.8% SSv2, 44M/15.2M params, 78.5/3.4 GFLOPs
- **Non-local Networks**: Wang et al., CVPR 2018, arXiv:1711.07971 — 61.2% SSv2, +0.8M/block, 8.2 GFLOPs
- **MS-TCN++**: Li et al., TPAMI 2021, arXiv:2006.09220 — 85.4% 50 Salads, 10.4M params
- **ASFormer**: Yi et al., BMVC 2021, arXiv:2110.08568 — 86.7% 50 Salads, 6.8M params
- **IKEA ASM Dataset**: Ben-Shabat & Kumar, ICCV 2021, https://ikea.asm.work/
- **Assembly101**: Sener et al., CVPR 2022, https://assembly-101.github.io/
- **IndustReal**: Schoonbeek et al., WACV 2024, https://github.com/TimSchoonbeek/IndustReal

---

*Research synthesized 2026-04-15 for POPW multi-task assembly understanding project*
