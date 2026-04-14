---
paper_id: 085
title: "OpenPose: Realtime Multi-Person 2D Pose Estimation using Part Affinity Fields"
authors: "Zhe Cao, Gines Hidalgo, Tomas Simon, Shih-En Wei, Yaser Sheikh"
year: 2017
venue: "CVPR 2017"
arxiv: "1812.08008"
github: "https://github.com/CMU-Perceptual-Computing-Lab/openpose"
tags:
  - pose-estimation
  - bottom-up
  - part-affinity-fields
  - multi-person
  - realtime
  - open-source
popw_relevance: HIGH
---

## Why This Paper Matters for POPW

OpenPose established the **bottom-up paradigm** for multi-person pose estimation using Part Affinity Fields (PAFs). As the first open-source realtime system for multi-person 2D pose estimation (including body, foot, hand, facial keypoints), it set the standard that POPW's pose estimation must match or exceed. The PAF mechanism for association is still widely used.

## Core Contribution

OpenPose introduced **Part Affinity Fields (PAFs)** — a nonparametric representation encoding both keypoint locations AND their association into persons. Unlike previous detection-then-group approaches, OpenPose uses a two-stage process:
1. **Stage 1**: Predict keypoint heatmaps (confidence maps)
2. **Stage 2**: Predict PAFs (2D vector fields per limb) for association

## Key Technical Details

### Part Affinity Fields

PAFs encode the position and orientation of body limbs:
- For each pixel in a limb region, store a 2D unit vector pointing from keypoint A to keypoint B
- During inference, integrate PAFs along line between detected keypoints
- Result: confidence that two keypoints belong to the same person

### Two-Branch Architecture

The VGG-based network jointly predicts:
- **Branch 1**: Keypoint confidence maps (where are the joints?)
- **Branch 2**: PAFs (which joints belong together?)

### Greedy Parsing

After prediction, a greedy parsing algorithm:
1. Detect all keypoints above confidence threshold
2. For each keypoint pair, compute association score via PAF integration
3. Link keypoints into persons using bipartite matching

## Critical Results

| Metric | Result |
|--------|--------|
| COCO keypoints AP | ~60% (2017 baseline) |
| MPII multi-person AP | Set new SOTA |
| Runtime | 22 fps on 640×480 (2017 GPU) |
| Realtime capability | Yes — first system to achieve this |

OpenPose won first place in the COCO 2016 Keypoints Challenge and significantly exceeded prior state-of-the-art on MPII Multi-Person benchmark.

## What POPW Can Steal Directly

1. **PAF-like association mechanism**: For POPW's multi-person scenarios
2. **Multi-keypoint types**: OpenPose handles body (17), foot (6), hand (21), face (70) keypoints
3. **Bottom-up advantage**: Scales to many people without per-person computation increase

## Connection to POPW Architecture

POPW's pose head predicts 17 COCO keypoints. OpenPose shows:
- **Association is critical** for multi-person scenarios
- **PAFs provide learnable association** without explicit geometry
- **Heatmap + association** is more scalable than detection + grouping

For POPW's action recognition task, OpenPose's approach suggests:
- Keypoint locations (heatmaps) provide pose structure
- Association fields could help track persons across frames
- Realtime inference is achievable with optimized networks

## Key Innovations Not in Paper

Practical implementation details:
- **Confidence threshold tuning**: Lower thresholds catch more keypoints but increase false positives
- **PAF refinement stages**: Multiple refinement passes improve accuracy
- **Foot keypoint dataset**: Released 15K annotated foot keypoints (CMP dataset)
- **Body + foot + hand + face**: Combined model increases inference time but provides complete pose

## Limitations

1. **PAF quality determines association accuracy**: Poor PAFs = incorrect person assignment
2. **Limited to 2D**: No depth information from single camera
3. **Occlusion handling**: Greedy association fails with heavy occlusion
4. **Computational cost**: Real-time requires GPU; CPU inference is much slower

## Key Equations

**PAF definition:**
$$L_c^*(p) = \frac{1}{Z_c(p)} \int_0^1 \text{exp}\left(-\frac{\|p - u(d)\|^2}{\sigma^2}\right) v \cdot (p - u(d)) \, dd$$

where:
- $p$ is pixel location
- $u(d)$ is point on limb from keypoint 1 to 2
- $v$ is unit vector in limb direction
- $Z_c(p)$ is normalization factor

**Association score via line integral:**
$$E = \int_0^1 L_c(p(u)) \cdot \frac{p_{t2} - p_{t1}}{\|p_{t2} - p_{t1}\|} du$$

## Researcher Intelligence

- **Zhe Cao**: PhD at Carnegie Mellon University
- **Yaser Sheikh**: Associate Professor at CMU — Perceptual Computing Lab
- **Gines Hidalgo**: PhD student at CMU
- **Tomas Simon**: PhD at CMU
- **Lab**: CMU Perceptual Computing Lab — leading in pose estimation research

---

*Recorded: 2026-04-11 | Source: arXiv:1812.08008 | CVPR 2017 (journal version)*
