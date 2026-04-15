---
title: Posescript
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- research
created: '2026-04-14'
updated: '2026-04-14'
summary: '- **arXiv**: [2210.11795](https://arxiv.org/abs/2210.11795)'
wikilinks: []
confidence: medium
source: research
---

# PoseScript: 3D Body Pose from 2D Images

## Paper Info
- **arXiv**: [2210.11795](https://arxiv.org/abs/2210.11795)
- **Authors**: Delmas et al.
- **Venue**: ECCV 2022

## Core Contribution

PoseScript reconstructs **3D body pose** from single 2D images using:
1. **SMPL body model**: Parametric 3D body mesh (shape + pose parameters)
2. **Neural encoder**: Image → SMPL parameters
3. **Pose prior**: Natural body configuration constraint

**Relevance to POPW**: POPW's OpenPose gives 2D keypoints. PoseScript suggests enhancing with:
1. 3D pose estimation (depth information)
2. SMPL mesh (body surface, not just keypoints)
3. Pose priors (natural body constraints)

## SMPL Model Overview

SMPL (Skinned Multi-Person Linear model) represents body pose as:
```
SMPL(β, θ) → 3D mesh with 6890 vertices
  β ∈ R^10: body shape parameters (height, weight, proportions)
  θ ∈ R^72: 24-joint pose parameters (3 angles per joint)
```

**For POPW**: SMPL gives richer pose representation than 2D keypoints:
- 3D joint positions (x, y, z)
- Body surface mesh (for occlusion reasoning)
- Shape parameters (body size affects visual features)

## Pose Prior in PoseScript

PoseScript's prior ensures **natural body configurations**:
```
Pose prior: P(θ) = probability of pose θ being natural human pose

Training loss:
  L = L_image + λ_pose · (-log P(θ))

  L_image: image reconstruction loss
  -log P(θ): encourages natural poses
```

**What the prior captures**:
- Joint angle constraints (elbows can't bend backward)
- Body symmetry (left-right proportions)
- Natural standing/sitting configurations

## POPW Enhancement: 3D Pose + Pose Prior

POPW's current 2D pose has limitations:
```
2D keypoints: No depth information, can be ambiguous
  Example: Arm reaching forward vs backward looks same in 2D

With PoseScript 3D pose:
  3D keypoints: Full depth, unambiguous pose
  SMPL mesh: Body surface for occlusion reasoning
  Pose prior: Natural body constraints enforced
```

## 3D Pose for Assembly Activities

3D pose provides critical advantages for assembly:
| Ambiguity | 2D | 3D |
|-----------|----|----|
| Reach forward | Same as reach backward | Distinguishable |
| Lean left/right | Ambiguous | Clear depth difference |
| Overhead reach | Clipped by frame | Full 3D trajectory |

**For IKEA assembly**: 3D pose enables:
- Accurate tool-use trajectory reconstruction
- Object-pose relationship reasoning (hand ↔ part in 3D)
- Better activity classification from full 3D motion

## POPW + PoseScript Integration

```
Current POPW:
  Frame → ResNet-50-FPN → C5
       → OpenPose → 2D keypoints[17] + confidence[17]
       → PoseFiLM → C5_mod

With PoseScript:
  Frame → ResNet-50-FPN → C5
       → OpenPose → 2D keypoints[17]
       → PoseScript → 3D keypoints + SMPL mesh + shape

       3D keypoints → concat with 2D → PoseFiLM
       SMPL mesh → mesh encoder → mesh features → PoseFiLM
```

**Multi-stream PoseFiLM**:
```
pose_2d = concat(2D_keypoints, confidence)
pose_3d = 3D_keypoints (from PoseScript)
pose_mesh = SMPL mesh features

pose_fused = concat([pose_2d, pose_3d, pose_mesh])

γ = MLP_γ(pose_fused)
β = MLP_β(pose_fused)

C5_mod = γ ⊙ C5 + β  # enriched with 3D pose
```

## Pose Prior as Regularization

PoseScript's pose prior can **regularize POPW's pose estimation**:
```
OpenPose → 2D keypoints (can be noisy, occluded)
     ↓
PoseScript 3D reconstruction + pose prior → refined pose
     ↓
pose_prior_loss = -log P(pose)  # encourages natural poses

Training POPW:
  Total_loss = activity_loss + λ · pose_prior_loss
```

**Benefit**: During training, POPW's pose head is encouraged to output natural poses, reducing noise in pose-conditioned features.

## Practical Considerations

PoseScript requires:
1. **SMPL model**: Predefined body model (~100MB)
2. **PoseScript encoder**: Trained on large 3D pose datasets
3. **3D supervision**: Need 3D pose labels for training

**For POPW**: Use PoseScript as frozen pose estimator:
```
OpenPose (2D) → PoseScript (3D refinement) → 3D pose for PoseFiLM
```

## Comparison with POPW's Current Pose

| Aspect | POPW (OpenPose only) | POPW + PoseScript |
|--------|---------------------|-------------------|
| Pose dimensions | 2D (x, y) | 3D (x, y, z) |
| Body mesh | No | Yes (SMPL) |
| Occlusion handling | Confidence masking | Mesh reasoning |
| Depth | Ambiguous | Clear |
| Complexity | Low | Medium |

## References

- Delmas et al. (2022). "PoseScript: 3D Body Pose from 2D Images." ECCV 2022. arXiv:2210.11795
