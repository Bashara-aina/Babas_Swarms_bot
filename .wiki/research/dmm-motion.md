---
title: Dmm Motion
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
summary: '- **arXiv**: [2307.07754](https://arxiv.org/abs/2307.07754)'
wikilinks: []
confidence: medium
source: research
---

# DMM: Deep Motion Modulation

## Paper Info
- **arXiv**: [2307.07754](https://arxiv.org/abs/2307.07754)
- **Authors**: Yu et al.
- **Venue**: ICCV 2023

## Core Contribution

DMM introduces **deep motion modulation** — extracting rich motion representations from skeleton sequences and using them to modulate skeleton features. Unlike simple velocity (first derivative), DMM extracts:
- **Velocity**: First derivative of pose `v_t = pose_{t+1} - pose_t`
- **Acceleration**: Second derivative `a_t = v_{t+1} - v_t`
- **Jerk**: Third derivative `j_t = a_{t+1} - a_t`

This captures:
- Velocity: How fast pose is changing
- Acceleration: How the motion itself is changing (increasing/decreasing speed)
- Jerk: How acceleration is changing (smooth vs abrupt transitions)

## Multi-Scale Motion Representation

```
Skeleton [T, J, D] → Motion Encoder
                        ↓
  v_t = pose_{t+1} - pose_{t}     → velocity features
  a_t = v_{t+1} - v_{t}           → acceleration features
  j_t = a_{t+1} - a_{t}           → jerk features
                        ↓
  Motion features = concat([v, a, j]) ∈ R^[T, J, 3D]
                        ↓
  Deep motion encoder → high-level motion embedding m_t
                        ↓
  Feature Modulation: C5_mod = γ(m_t) ⊙ C5 + β(m_t)
```

## Why Jerk Matters for Assembly

Jerk (rate of change of acceleration) captures **motion smoothness**:
- High jerk → abrupt action (hammer strike, part snapping into place)
- Low jerk → smooth motion (aligning parts, careful positioning)

For IKEA assembly:
| Action | Velocity | Acceleration | Jerk |
|--------|----------|--------------|------|
| Hammer | High | High positive | Very high |
| Screw | Medium | Medium | Medium |
| Align | Low | Low | Low |
| Snap | Medium | High | High |

## POPW Enhancement with DMM Motion

POPW's current approach uses pose (position) only:
```
pose_flat = concat(keypoints[17], confidence[17]) → PoseFiLM → C5_mod
```

DMM suggests adding **motion features**:
```
velocity = keypoints[t+1] - keypoints[t]
acceleration = velocity[t+1] - velocity[t]
jerk = acceleration[t+1] - acceleration[t]

motion_features = concat([velocity, acceleration, jerk])
motion_embedding = MLP(motion_features)

γ = MLP_motion_γ(motion_embedding)
β = MLP_motion_β(motion_embedding)

C5_mod = γ ⊙ C5 + β  # pose + motion conditioned
```

**Benefit**: The activity classifier now sees:
- Static pose (what body configuration)
- Motion dynamics (how the pose is changing)
- Motion smoothness (how the action is being performed)

## Motion Temporal Scales

DMM extracts motion at **multiple temporal scales**:
```
Scale 1 (local):  v_t = pose_{t+1} - pose_{t}        # frame-level
Scale 2 (medium): v_t = pose_{t+2} - pose_{t}        # 2-frame motion
Scale 3 (coarse): v_t = pose_{t+4} - pose_{t}        # 4-frame motion
```

**For POPW's T=8 window**:
```
Motion at τ=1: velocity from consecutive frames
Motion at τ=2: velocity from every other frame
Motion at τ=4: velocity from quarter-rate sampling

All scales → concat → motion_embedding
```

## Comparison with Other Motion Approaches

| Approach | Motion Representation | Modulation | POPW Relevance |
|----------|----------------------|------------|---------------|
| MANs/TARM | Velocity only | Attention weights | Motion as attention |
| DMM | Vel + Acc + Jerk | Feature modulation | Motion as FiLM |
| MMN | Velocity | MSM + MTM | Full bidirectional |
| PSUMNet | Per-part velocity | Part-wise modulation | Body part focus |

## Future POPW Extension: DMM + BiGRU

```
Frame t:
  Pose: keypoints[t] ∈ R^[17, 3]
  Velocity: keypoints[t+1] - keypoints[t]
  Acceleration: velocity[t+1] - velocity[t]
  Jerk: acceleration[t+1] - acceleration[t]

  motion_features = concat([pose, vel, acc, jerk])
  motion_embedding = MLP(motion_features)

  γ = MLP_γ(motion_embedding)
  β = MLP_β(motion_embedding)

  C5_mod = γ ⊙ C5 + β

C5_mod[0:8] → BiGRU → h[0:8]
  → AttentionPool → Activity Classification
```

## References

- Yu et al. (2023). "Deep Motion Modulation for Skeleton-based Action Recognition." ICCV 2023. arXiv:2307.07754
