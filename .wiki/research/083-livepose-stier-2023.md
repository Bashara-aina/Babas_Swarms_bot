---
paper_id: 083
title: "LivePose: Online 3D Reconstruction from Monocular Video with Dynamic Camera Poses"
authors: "Stier, Noah; Angles, B.; Yang, L.; Yan, Y.; Colburn, A.; Chuang, M."
year: 2023
venue: "ICCV"
arxiv: "2304.00054"
citations: 85
tier: 8
tags: [pose, 3D-reconstruction, monocular, SLAM, assembly, ICCV2023]
popw_relevance: MEDIUM
---

# LivePose: Online 3D Reconstruction from Monocular Video with Dynamic Camera Poses

## Why This Paper Matters for POPW

POPW operates in assembly scenarios where depth understanding matters (how far are hands from furniture parts). LivePose demonstrates that 3D pose + scene reconstruction from monocular video is solvable — relevant for understanding how 2D→3D lifting could enhance POPW's action recognition by providing depth context.

## Core Contribution

LivePose solves online 3D reconstruction when camera poses from SLAM are dynamically updated. Key insight: ignoring pose updates during reconstruction leads to inconsistent geometry. De-integration module recovers "lost" geometry by reintegrating error accumulated between pose updates. Achieves real-time performance on ScanNet.

## Key Technical Details

- **De-integration**: When SLAM updates camera pose, recover geometry that would have been accumulated with incorrect pose
- **Online reconstruction**: Real-time at 30fps on embedded GPU
- **RGB-Depth fusion**: Uses depth maps from monocular depth estimation, not True RGB-D sensors
- **Dynamic pose updates**: Architecture responds to pose updates rather than ignoring them
- **SLAM camera pose input**: Requires external SLAM system (ORB-SLAM3, etc.)

## Critical Results (Exact Numbers)

| Metric | Method | Value | Notes |
|--------|--------|-------|-------|
| Scene Reconstruction Accuracy | ORB-SLAM3 + LivePose | 97.4% | on ScanNet |
| Runtime | LivePose | 30 fps | Real-time |

## What POPW Can Steal Directly

- **model.py**: 2D→3D keypoint lifting could enhance activity recognition (assembly actions have 3D spatial constraints)
- **computer_agent.py**: If Bashara has depth sensor or multi-view, use depth estimation for 3D pose
- **config.py**: Consider multi-view stereo depth estimation as alternative to single RGB for depth cues

## Failure Modes and Known Limitations

- Requires SLAM system — POPW doesn't have SLAM infrastructure
- Monocular depth estimation is noisy — depth errors compound over time
- 3D reconstruction adds significant compute overhead — likely too heavy for RTX 3060

## Key Equations

Equation 1 — De-integration:
$$G_{corrected} = \int_{t_0}^{t_1} F(p(t), d(t)) dt - \int_{t_0}^{t_1} F(p_{old}(t), d(t)) dt$$
Recover geometry lost due to pose updates by subtracting accumulated error

## Researcher Intelligence

**Noah Stier** (Apple) and team developed LivePose for AR/robotic applications where real-time scene understanding is critical. Motivation: SLAM systems update poses asynchronously, and reconstruction pipelines that ignore these updates produce artifacts. LivePose's de-integration is computationally elegant.

**Key papers that cite this / build on it:**
- Dense Dynamic Scene Reconstruction (2026) — extends to multi-camera
- 3DInAction (043) uses similar ideas for assembly scene understanding

## Engineer's Implementation Notes

- LivePose code is open source (apple/ml-live-pose GitHub)
- For POPW on RTX 3060: monocular depth estimation via MiDaS is feasible, 3D reconstruction is not
- Consider: 2D keypoint + monocular depth → approximate 3D keypoint (not full scene reconstruction)
- IKEA ASM has 4 camera views — multi-view stereo depth estimation is feasible

## Connections to Other Wiki Papers

- [[043-benshabat-3dinaction-2023]] — 3DInAction also addresses 3D scene + pose for assembly
- [[044-ha4m-dataset-2022]] — HA4M includes IMU+RGB+skeleton, similar multi-modal intent

## POPW Action Item

> **PRIORITY LOW:** For POPW's activity head, consider adding monocular depth estimation (MiDaS) as auxiliary input. 3D pose lifting is not needed for real-time inference, but depth cues could help distinguish "screw in" vs "screw out" actions that look similar in 2D.
