---
title: Psumnet
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
summary: '- **arXiv**: [2208.05775](https://arxiv.org/abs/2208.05775)'
wikilinks: []
confidence: medium
source: research
---

# PSUMNet: Part-wise Semantic and Motion Understanding

## Paper Info
- **arXiv**: [2208.05775](https://arxiv.org/abs/2208.05775)
- **Authors**: Trivedi et al.
- **Venue**: BMVC 2022

## Core Contribution

PSUMNet decomposes skeleton-based action recognition into **part-wise streams**:

1. **Body Part Decomposition**: Decompose 17-keypoint skeleton into semantic parts:
   - Upper body (shoulders, elbows, wrists, neck, head)
   - Lower body (hips, knees, ankles)
   - Left arm (left shoulder → left wrist)
   - Right arm (right shoulder → right wrist)

2. **Per-Part Motion Stream**: Each part has its own motion representation:
   - `motion_part = pose_{t+1} - pose_{t-1}` per body part
   - Separate temporal modeling per part

3. **Semantic Modulation**: Activity class modulates per-part features:
   - When classifying "screw", right arm gets higher weight
   - When classifying "stand", lower body gets higher weight

## Architecture

```
Skeleton [T, 17, 3] → Part Decomposer
                           ↓
  ├─ Upper Body → Motion Encoder → Motion Features Upper
  ├─ Lower Body → Motion Encoder → Motion Features Lower
  ├─ Left Arm   → Motion Encoder → Motion Features Left
  └─ Right Arm  → Motion Encoder → Motion Features Right
                           ↓
                  Semantic Modulator ← Activity Class
                           ↓
                  Part-wise Fusion → Activity Prediction
```

**Semantic Modulation**:
```
activity_embedding = ActivityEncoder(class)
γ_part = W_γ · activity_embedding + b_γ  # per-part gains
β_part = W_β · activity_embedding + b_β   # per-part biases

modulated_features[part] = γ_part ⊙ motion_features[part] + β_part
```

## Why PSUMNet Matters for POPW

POPW's PoseFiLM applies **global** pose modulation to all C5 features:
```
pose_flat → MLP → γ_global, β_global
C5_mod = γ_global ⊙ C5 + β_global  # same modulation for all spatial locations
```

PSUMNet suggests **part-wise** modulation:
```
pose_flat → Decompose → upper_pose, lower_pose, left_pose, right_pose
            ↓
part_γ = [γ_upper, γ_lower, γ_left, γ_right]  # per-part modulation
part_β = [β_upper, β_lower, β_left, β_right]  # per-part bias

C5_mod_part = γ_part ⊙ C5_part + β_part  # per-part pose conditioning
```

**Benefit for Assembly Recognition**:
- "Screw" action → right arm modulation high, lower body suppressed
- "Hammer" action → upper body modulation high, both arms active
- "Stand/wait" → lower body modulation high, upper body suppressed

## Per-Part Temporal Modeling

POPW's BiGRU processes global C5_mod features:
```
C5_mod[0:8] → BiGRU → global hidden state → Activity Classification
```

PSUMNet suggests **per-part temporal streams**:
```
Upper:    C5_mod_upper[0:8] → BiGRU_upper → h_upper
Lower:    C5_mod_lower[0:8] → BiGRU_lower → h_lower
Left:     C5_mod_left[0:8] → BiGRU_left → h_left
Right:    C5_mod_right[0:8] → BiGRU_right → h_right

Fusion:  concat([h_upper, h_lower, h_left, h_right])
       → FC → Activity Classification
```

## Comparison with POPW's PoseFiLM

| Aspect | POPW PoseFiLM | PSUMNet Part-wise |
|--------|--------------|------------------|
| Modulation scope | Global (all C5) | Per-part (4 parts) |
| Pose decomposition | No | Yes (body parts) |
| Activity modulation | Pose→Activity only | Both directions |
| Temporal modeling | Single BiGRU | Per-part BiGRU |

## Future POPW Enhancement: Part-wise PoseFiLM

```
Pose decomposition:
  keypoints[17] → Part Decomposer
     ├─ upper_body:  [neck, head, shoulders, elbows, wrists]  → 9 keypoints
     ├─ lower_body:  [hips, knees, ankles]                   → 6 keypoints
     ├─ left_arm:     [left_shoulder, left_elbow, left_wrist] → 3 keypoints
     └─ right_arm:    [right_shoulder, right_elbow, right_wrist] → 3 keypoints

Per-part modulation:
  part_pose → MLP → γ_part, β_part
  C5_part_mod = γ_part ⊙ C5_part + β_part

Per-part BiGRU:
  C5_mod_upper[0:8] → BiGRU_upper → h_upper ∈ R^128
  C5_mod_lower[0:8] → BiGRU_lower → h_lower ∈ R^128
  C5_mod_left[0:8]  → BiGRU_left  → h_left  ∈ R^128
  C5_mod_right[0:8] → BiGRU_right → h_right ∈ R^128

Fusion + Classification:
  H = concat([h_upper, h_lower, h_left, h_right]) ∈ R^512
  → Activity Classifier (33-class)
```

## References

- Trivedi et al. (2022). "PSUMNet: Part-wise Semantic and Motion Understanding Network for Skeleton-based Action Recognition." BMVC 2022. arXiv:2208.05775
