---
title: "Pose-Conditioned Temporal Modeling"
created: 2026-04-14
modified: 2026-04-14
tags: [pose-conditioning, temporal-modeling, film, pose-estimation, activity-recognition, multi-task-learning]
authors: [Bashara]
type: research
summary: "The tight feedback loop between pose estimation and activity recognition — pose predictions condition semantic features which are then temporally modeled. This bidirectional relationship is POPW's core innovation vs prior work."
wikilinks:
  - [[bigru-activity-recognition]]
  - [[pose-aware-feature-bank]]
  - [[tasks/pose-estimation]]
  - [[projects/popw-multi-task-ikea]]
---

# Pose-Conditioned Temporal Modeling

## The Core Innovation

The fundamental limitation in prior multi-task pose + activity systems is that pose and activity are processed in separate tracks with no information flow between them. Pose estimation produces heatmaps → keypoints → the stream ends. Activity recognition receives raw backbone features and classifies. There is no mechanism for pose predictions to shape what the activity head "sees."

POPW closes this loop with PoseFiLM: decoded 2D keypoint predictions generate affine modulation parameters that reshape the deepest backbone feature map (C5, 2048 channels) before it enters the temporal head. This is not a weak signal — the 51-dimensional pose_flat carries precise spatial information about hand configuration and object relationships.

## Why Pose → Semantic Feedback Loop Is Novel

Prior FiLM applications (Perez et al., AAAI 2018) use FiLM for:
- Task-conditioned generation (vary output style by task ID)
- Language-guided visual reasoning (use language embeddings to modulate image features)
- Cross-modal alignment (align visual and audio representations)

All of these use **discrete or coarse conditioning signals** — task ID, language tokens, mode flags. None use **continuous perception outputs** (raw 2D keypoint coordinates) as conditioning.

The distinction matters because:
- Discrete signals categorize the world (this is class A, not class B)
- Continuous pose predictions encode continuous spatial relationships (hands are 12.3cm apart, angled at 23 degrees relative to the leg socket)

For assembly activity recognition, this continuous spatial encoding is the difference between knowing "hands are near the leg" (discrete) vs. knowing "left hand is 12.3cm above the leg socket at a 23-degree angle" (continuous). The latter directly constrains which actions are physically possible.

## The Temporal Dimension

PoseFiLM operates per-frame, but assembly activities unfold over time. POPW's second innovation is temporal modeling of pose-conditioned features rather than raw backbone features.

Consider two identical BiGRUs processing 8-frame sequences:
1. **Raw-C5 BiGRU**: Receives raw C5 features. Temporal context is visual (this chair leg was visible, now a drawer is visible)
2. **PoseFiLM BiGRU**: Receives C5_mod features. Temporal context is assembly-state (hands were positioning leg, now hands are tightening screws — the pose trajectory reveals the assembly phase)

The pose-conditioned sequence encodes not just what changed visually, but how the worker's body configuration changed to accomplish the change. This is a richer temporal signal for activity recognition.

## Mathematical Formulation

Let $k_t \in \mathbb{R}^{34}$ be the decoded keypoint coordinates at time $t$ (17 keypoints × 2 coords), and $c_t \in \mathbb{R}^{17}$ be the confidence scores. Define:

$$\text{pose\_flat}_t = [k_t; c_t] \in \mathbb{R}^{51}$$

**PoseFiLM per timestep:**
$$\gamma_t = 1 + \tanh(W_\gamma \cdot \text{pose\_flat}_t + b_\gamma) \in (0, 2)^{2048}$$
$$\beta_t = W_\beta \cdot \text{pose\_flat}_t + b_\beta \in \mathbb{R}^{2048}$$
$$C5\_mod_t = \gamma_t \odot C5_t + \beta_t$$

The key constraint is the $1 + \tanh(\cdot)$ on $\gamma_t$, which ensures:
- $\gamma_t \in (0, 2)$ always (never negative or zero scaling)
- Gradient is well-behaved (tanh is smoothly bounded)
- Unlike sigmoid gating (σ ∈ (0,1)), affine modulation can both suppress AND amplify

**Temporal feature bank:**
For a window of T frames, the feature bank B_t concatenates pose-conditioned features:
$$B_t = [GAP(C5\_mod_{t-T+1}) \Vert GAP(P4_{t-T+1}), \ldots, GAP(C5\_mod_t) \Vert GAP(P4_t)] \in \mathbb{R}^{T \times 2304}$$

**BiGRU processes pose-conditioned sequence:**
$$H_t = BiGRU(B_t; \theta_{GRU}) \in \mathbb{R}^{T \times 512}$$

## Comparison with Prior Approaches

| Approach | Pose Signal Used | Temporal Modeling | Pose-to-Activity Signal |
|----------|-----------------|-------------------|----------------------|
| ObjectInfo (Aganian 2023) | Skeleton keypoints as explicit features | None | Concatenation |
| MS-TCN (Abu Farha 2020) | No pose signal | Temporal CNN on RGB | None |
| PoseFiLM (POPW) | Pose predictions → FiLM conditioning | BiGRU on C5_mod | Affine transformation of C5 |
| TSM (Lin 2019) | No pose signal | Channel shift on raw features | None |

## Why PoseFiLM Works for Assembly Activity

Assembly activities have a tight coupling between pose configuration and action class:
- `attach_leg`: Hands must be at a specific height to reach the leg socket
- `tighten_screw`: Both hands operate perpendicular to the screw axis
- `open_drawer`: Hands grasp the handle, body leans forward

This means pose predictions carry high mutual information with activity class. When PoseFiLM modulates C5 using pose_flat, it is essentially telling the activity head: "the features in this frame should be interpreted in the context of this specific body configuration." The temporal head then tracks how that configuration evolves.

## Gradient Flow and Training Stability

One subtlety: during training, the pose head's gradients should not backpropagate through the PoseFiLM conditioning path into the backbone. POPW uses `torch.no_grad()` on the pose decoding path during the pose→FiLM step. This is deliberate:

- The backbone (ResNet-50-FPN) is shared by all three heads
- If pose predictions influenced backbone gradients, it could destabilize detection and pose training
- The PoseFiLM path is **one-way**: pose → modulates → activity head
- Detection and pose heads train on their own losses without pose-influenced gradients

The activity head, however, does receive pose-conditioned features — and the BiGRU learns to interpret them effectively because the pose signal is semantically rich (assembly-state information) not noisy.

## References

- Perez et al. 2018 — "FiLM: Visual Reasoning with Feature-wise Linear Modulation" (NeurIPS 2018) — original FiLM
- Dumoulin et al. 2018 — "A Guide to Convolution Arithmetic for Deep Learning" — FiLM extension
- Hinton et al. 2012 — "Transforming Auto-encoders" — earliest FiLM-like conditioning