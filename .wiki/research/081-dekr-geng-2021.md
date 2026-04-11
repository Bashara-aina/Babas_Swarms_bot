---
paper_id: 081
title: "Bottom-Up Human Pose Estimation via Disentangled Keypoint Regression"
authors: "Zigang Geng, Ke Sun, Bin Xiao, Zhaoxiang Zhang, Jingdong Wang"
year: 2021
venue: "CVPR 2021"
arxiv: "2104.02300"
github: "https://github.com/HRNet/DEKR"
tags:
  - pose-estimation
  - bottom-up
  - disentangled-regression
  - keypoint-localization
  - adaptive-convolution
popw_relevance: MEDIUM-HIGH
---

## Why This Paper Matters for POPW

POPW's pose head uses heatmap regression for 17 COCO keypoints. DEKR introduces **disentangled keypoint regression** — a multi-branch architecture where each keypoint learns dedicated representations via adaptive convolutions. This approach achieves superior accuracy by focusing representation learning on each keypoint region, directly relevant to POPW's need for precise keypoint localization.

## Core Contribution

DEKR challenges the dominance of detection+grouping approaches in bottom-up pose estimation. The key insight: **keypoint regression requires spatial attention concentrated on keypoint regions**, not global feature extraction. DEKR uses pixel-wise spatial transformers and adaptive convolutions to activate only the relevant pixels for each keypoint.

## Key Technical Details

### Disentangled Architecture
Each keypoint is regressed by a dedicated branch:
- **Pixel-wise spatial transformer**: Learns where to attend for each keypoint
- **Adaptive convolution**: Extracts features from activated regions
- **Multi-branch structure**: 17 branches for COCO keypoints, each specialized for one keypoint

### Spatial Transformer Network (STN) Integration
The spatial transformer activates pixels near the keypoint location:
1. Heatmap prediction guides where to crop/transform features
2. Cropped features fed to dedicated regression head per keypoint
3. Enables focused representation learning per keypoint

### Comparison to Detection+Grouping

| Approach | Method | DEKR's Advantage |
|----------|--------|-----------------|
| Detection+Grouping | Detect keypoints, group via PAFs | DEKR directly regresses, simpler |
| Direct Regression | Inferior in prior work | DEKR outperforms by learning disentangled representations |

## Critical Results

| Metric | Result |
|--------|--------|
| COCO val AP | 68.0% (without refinement) |
| CrowdPose test AP | 66.9% |
| Outperforms detection+grouping methods | Yes |

## What POPW Can Steal Directly

1. **Multi-branch keypoint regression**: POPW could benefit from dedicated representation per keypoint
2. **Adaptive convolution**: Use spatial transformers to focus on keypoint regions
3. **Separation of keypoint-specific vs shared features**: Could reduce interference between keypoints

## Connection to POPW Architecture

POPW's pose head currently uses shared feature extraction followed by heatmap regression. DEKR suggests:
- **Dedicated per-keypoint heads** could improve accuracy
- **Spatial attention** before regression could focus on relevant regions
- **Disentangled representations** may reduce keypoint confusion

## Failure Modes

1. **Computational overhead**: 17 separate branches increases parameters
2. **Training complexity**: Multi-branch supervision requires careful balancing
3. **Small objects**: Still struggles with small persons (common to all bottom-up)
4. **Occlusion**: Disentangling becomes harder when keypoints are occluded

## Key Equations

**Adaptive convolution via spatial transformer:**
$$F_{adaptive} = \text{Conv}(\text{Affine}(F_{shared}))$$

where Affine() is the pixel-wise spatial transformation learned per keypoint.

**Multi-branch loss:**
$$L = \sum_{k=1}^{K} \|p_k - \hat{p}_k\|^2$$

where $p_k$ is ground truth position for keypoint $k$ and $\hat{p}_k$ is predicted.

## Researcher Intelligence

- **Zigang Geng**: PhD student, related to HRNet group
- **Ke Sun**: Known for HRNet and pose estimation work
- **Jingdong Wang**: Senior researcher at Baidu, extensive pose estimation work
- **Lab**: UIUC / Baidu research group

---

*Recorded: 2026-04-11 | Source: arXiv:2104.02300 | CVPR 2021*