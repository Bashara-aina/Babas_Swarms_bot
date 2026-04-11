---
paper_id: 079
title: "Deep Learning-Based Human Pose Estimation: A Survey"
authors: "Zheng, Ce; Zhu, Zheng; Yang, Mengjia; Zhu, Feng; Huang, Guan; Du, Dalong"
year: 2020
venue: "arXiv"
arxiv: "2012.13392"
citations: 850
tier: 8
tags: [pose, survey, deep-learning, 2D, 3D, heatmap, regression]
popw_relevance: HIGH
---

# Deep Learning-Based Human Pose Estimation: A Survey

## Why This Paper Matters for POPW

POPW's pose head predicts 17 COCO keypoints using heatmap regression. This survey provides the taxonomy and evaluation protocols that define best practices — essential for understanding whether POPW should use heatmap-based or regression-based pose estimation.

## Core Contribution

A comprehensive survey of deep learning-based 2D and 3D human pose estimation methods published up to 2020. Covers the full spectrum: single-person, multi-person, 2D, 3D, heatmap-based, regression-based, top-down, bottom-up approaches. Provides unified evaluation protocol discussion (COCO Keypoint Detection, MPII).

## Key Technical Details

- **Taxonomy**: Single-person vs Multi-person; 2D vs 3D; Top-down vs Bottom-up
- **Heatmap vs Regression**: Heatmap (Softmax + argmax) dominates — better spatial awareness
- **COCO Keypoint Detection**: 17 keypoints, OKS-based evaluation, PCK@0.1/0.05/0.2
- **Top-down approach**: Person detector + single-person pose estimator — higher accuracy but cascaded
- **Bottom-up approach**: Detect all keypoints then group — faster but lower accuracy on overlapping people
- **Network architectures**: Hourglass, CPM, OpenPose, SimpleBaseline, HRNet

## Critical Results (Exact Numbers)

| Metric | Method | Value | Notes |
|--------|--------|-------|-------|
| COCO mAP (keypoints) | HRNet-W48 | 76.7% | Top-down, official |
| COCO mAP (keypoints) | HigherHRNet | 74.3% | Bottom-up |
| MPII Accuracy | Hourglass | 92.0% | Single person |

## What POPW Can Steal Directly

- **ikea_dataset.py**: Use COCO-format keypoint annotations for POPW's 17-keypoint pose head
- **model.py**: SimpleBaseline-style deconvolutional head for heatmap generation (papers 008, 009 already cover)
- **Evaluation**: Use OKS (Object Keypoint Similarity) for pose head evaluation, not just accuracy

## Failure Modes and Known Limitations

- Survey is from 2020 — misses recent advances (Transformer-based pose estimation)
- 3D pose estimation is still poorly solved — POPW uses 2D heatmaps only
- Domain gap: most methods tested on MPII/COCO, not on assembly furniture context

## Key Equations

Equation 1 — Object Keypoint Similarity (OKS):
$$\text{OKS} = \sum_i \frac{\exp(-d_i^2 / 2s_i^2 \sigma_i^2)}{\sum_i \delta_i}$$
where $d_i$ is Euclidean distance, $s_i$ is person scale, $\sigma_i$ is keypoint-specific constant

## Researcher Intelligence

**Ce Zheng** (now at Meituan) and **Zheng Zhu** (JD.com) led this survey during 2019-2020. Motivation: standardize the rapidly fragmenting HPE landscape where different papers used different evaluation protocols, making comparison impossible.

**Key papers that cite this / build on it:**
- Later HPE surveys (2022-2024) extend this taxonomy
- PoseConv3D (011) uses 2D projection onto heatmap volumes — informed by HPE survey findings

## Engineer's Implementation Notes

- COCO keypoint ordering: nose, eyes, ears, shoulders, elbows, wrists, hips, knees, ankles — POPW uses same 17-keypoint COCO format
- OKS uses per-keypoint $\sigma$ values: eyes/ears are harder (σ~0.026) than shoulders/hips (σ~0.079)
- For POPW: compute per-keypoint accuracy separately to diagnose which keypoints fail (likely wrists due to small scale)
- Heatmap decoding (argmax vs mouse mean) matters: use mouse mean for sub-pixel accuracy

## Connections to Other Wiki Papers

- [[008-simple-baseline-xiao-2018]] — SimpleBaseline is reference method in survey
- [[009-hrnet-wang-2020]] — HRNet is the top-performing method cited
- [[080-higherhrnet-cheng-2020]] — HigherHRNet achieves strong bottom-up results

## POPW Action Item

> **PRIORITY HIGH:** Implement OKS-based evaluation for pose head in `train.py` — current accuracy metric is insufficient for diagnosing keypoint-specific failures. Track wrist/elbow accuracy separately to identify scale-related issues with small furniture parts.
