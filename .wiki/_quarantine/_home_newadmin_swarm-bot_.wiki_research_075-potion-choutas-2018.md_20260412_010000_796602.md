---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/research/075-potion-choutas-2018.md",
  "reason": "daily_fast_scan: score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-12T01:00:00.796622"
}
---

---
tags: [video-understanding, pose-based, action-recognition, motion, cvpr-2018]
sources: [arxiv:1711.09799]
created: 2026-04-11
updated: 2026-04-11
---

# PoTion: Pose MoTion Representation for Action Recognition

**Choutas, Weinzaepfel** | CVPR 2018 | [arXiv:1711.09799](https://arxiv.org/abs/1711.09799)

## Overview

PoTion is a **pose-based action recognition** method that encodes body keypoint motion as a compact visual representation. Instead of processing raw RGB video, PoTion first extracts OpenPose keypoints and then creates a 2D heatmap representation where each channel encodes the motion (velocity) of a specific body joint over the video clip.

The key insight is that pose motion is more robust to appearance changes and backgrounds than raw RGB processing, making it ideal for cluttered industrial environments like IKEA assembly.

## Architecture

### Key Innovation: Joint Motion as Color Channels

1. **Pose extraction**: OpenPose detects 18 body keypoints (head, shoulders, elbows, wrists, hips, knees, ankles)
2. **Motion computation**: Track keypoint positions over clip, compute velocity vectors
3. **Heatmap encoding**: For each keypoint j and time t, encode velocity as color in channel j

```
Video Clip (T frames)
  └── OpenPose extraction → 18 keypoints × (x, y, confidence)
        └── Velocity computation → v_j(t) for each joint j
              └── Color heatmap → C(x, y, j) = v_j(color)
                    └── Shallow CNN → Action label
```

### Compact Representation

PoTion produces a **fixed-size 2D heatmap** (H × W × 18) representing entire clip, enabling classification with a shallow CNN (much smaller than video understanding models).

## Performance

| Dataset | PoTion | Previous Pose-based | RGB SOTA |
|---------|--------|---------------------|----------|
| J-HMDB | 72.0% | 63.6% | 73.1% |
| MPII Cooking | 55.2% | 45.4% | — |
| IKEA ASM | TBD | — | 57.57% (I3D RGB) |

## POPW Relevance

> [!CRITICAL]
> PoTion is highly relevant to POPW's **multi-task design** (pose + action). WorkerNet already extracts pose as a task; PoTion's pose-motion encoding could inspire a fusion mechanism. However, PoTion is single-clip classification, not frame-wise segmentation like TAS.

> [!NOTE]
> For industrial assembly, pose-based methods are attractive because they focus on the worker's body motion rather than the cluttered scene. PoTion-style representation could complement WorkerNet's FiLM conditioning by providing explicit pose motion features.

## Code Availability

- Official: https://github.com/social sensing/poTion (verify exact repo)
- OpenPose integration required for keypoint extraction

## See Also

- [[068-i3d-carreira-2017]] — I3D (RGB two-stream)
- [[075-potion-choutas-2018]] — PoTion (this paper)
