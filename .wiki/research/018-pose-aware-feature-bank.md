---
title: "Pose-Aware Temporal Feature Bank"
created: 2026-04-14
modified: 2026-04-14
tags: [feature-bank, temporal-modeling, pose-conditioned, multi-task-learning, video-understanding, caching]
authors: [Bashara]
type: research
summary: "Design and rationale for POPW's Pose-Aware Temporal Feature Bank — stores T=8 frames of PoseFiLM-modulated C5 features (not raw C5), enabling temporal reasoning on pose-conditioned representations without expensive per-frame backbone recomputation."
wikilinks:
  - [[bigru-temporal-action-recognition]]
  - [[pose-conditioned-temporal-modeling]]
  - [[projects/popw-multi-task-ikea]]
---

# Pose-Aware Temporal Feature Bank

## Concept

The Feature Bank is a sliding-window memory that stores the most recent $T-1$ pose-conditioned feature vectors alongside the current frame, enabling a BiGRU to reason over a temporal context window without requiring all $T$ frames to pass through the backbone simultaneously.

## Design Decision: Cache C5_mod, Not Raw C5

The most critical design choice in POPW's feature bank is that it stores **PoseFiLM-modulated features** (C5_mod), not raw backbone features (C5). This is not an implementation detail — it is the architectural innovation that makes the temporal head aware of assembly state.

When POPW processes frame $t$, it:
1. Runs the image through ResNet-50-FPN to get raw C5 (2048 channels)
2. Decodes pose keypoints from the heatmap head
3. Computes pose_flat = [keypoints_34, confidence_17] ∈ ℝ^51
4. Generates affine parameters (γ_net, β_net) from pose_flat
5. Applies C5_mod = γ ⊙ C5 + β, where γ ∈ (0,2) via 1+tanh constraint

C5_mod is then pooled (GAP) and concatenated with GAP(P4) to form a 2304-dimensional feature vector f_t. This vector is pushed onto the feature bank deque.

**Why cache C5_mod instead of C5?**
- C5 contains only spatial-semantic information from the image
- C5_mod contains that same information *already conditioned on the current pose state*
- When the BiGRU processes C5_mod vectors over time, it sees not just "what was in the frame" but "how the worker's body pose shaped the perception of each frame"
- This creates a richer temporal signal: the pose-conditioned hidden states at time $t$ encode assembly state, not just visual content

Ablation E.2 validates this: BiGRU on C5_mod outperforms BiGRU on raw C5 by $[ABLATION\_BIGRU\_POSECOND\_DROP]\%$ in activity top-1 accuracy.

## Memory Layout

For each video sequence, POPW maintains a deque:

```
FeatureBank[video_id][camera_view] = deque(maxlen=T)

At inference, after processing frame t:
  C5_mod = PoseFiLM(C5, pose_flat)      # Pose-conditioned feature
  f_t = [GAP(C5_mod) ‖ GAP(P4)]         # 2048 + 256 = 2304 dim
  FeatureBank.append(f_t)               # Automatically evicts oldest if len>T

When BiGRU processes:
  B_t = [f_{t-T+1}, ..., f_t]            # Stack to [T, 2304]
  B_t = B_t.reshape(B, T, 2304)          # [B, T, 2304]
```

The deque is keyed by (video_id, camera_view) to support multi-camera scenarios (dev1/dev2/dev3 in IKEA ASM).

## Compute Efficiency

Alternative approaches and why POPW's feature bank is better:

| Approach | Backbone passes per frame | Memory | POPW advantage |
|----------|--------------------------|--------|----------------|
| I3D / SlowFast | T frames through full 3D backbone | High (stores T×C×H×W activations) | Single forward pass per frame |
| TSM | T frames through modified 2D backbone | Medium | POPW has no backbone modification (avoids cross-task interference) |
| Feature Bank (POPW) | 1 pass per frame + deque append | ~8KB per sequence | Task isolation preserved |

The feature bank decouples temporal reasoning from backbone compute. Only the BiGRU needs to process multiple frames — the backbone processes each frame exactly once, making POPW efficient for real-time multi-task inference.

## Temporal Stride Augmentation

During training, a random temporal stride $\tau \in \{1, 2, 4\}$ is applied when sampling frames from the training video. This is the temporal equivalent of spatial data augmentation (random crop, horizontal flip):

- $\tau=1$: Consecutive frames (full temporal density)
- $\tau=2$: Every other frame (sparser, forces model to reason over longer-range dependencies)
- $\tau=4$: Every 4th frame (maximum sparsification, tests temporal generalization)

At test time, $\tau=1$ (all consecutive frames) for maximum accuracy.

## Formal Definition

Let $F_t \in \mathbb{R}^{2048}$ be the raw C5 feature at time $t$. Let $M(\cdot)$ be the PoseFiLM modulation. Then:

**Feature bank at time t:**
$$B_t = \{ M(F_{t-T+1}), M(F_{t-T+2}), \ldots, M(F_t) \} \in \mathbb{R}^{T \times 2048}$$

**BiGRU input sequence:**
$$X_t = [LayerNorm(ReLU(W_{proj} \cdot M(F_{t-T+1}))), \ldots, LayerNorm(ReLU(W_{proj} \cdot M(F_t)))] \in \mathbb{R}^{T \times 512}$$

Where $W_{proj} \in \mathbb{R}^{2304 \times 512}$ (with GAP(P4) concatenated) and the LayerNorm + ReLU are applied per-timestep independently.

## Comparison with LFB (CVPR 2019)

Wu et al. introduced Long-term Feature Banks (CVPR 2019) for video understanding. POPW's feature bank differs in two critical ways:

1. **Scope**: LFB aggregates features from the entire video duration for video-level understanding. POPW's feature bank operates on a fixed T=8 window for real-time assembly inference.

2. **Feature source**: LFB stores raw CNN features from a pre-trained backbone. POPW's feature bank explicitly stores PoseFiLM-modulated features, conditioning each stored feature on the pose state at the time it was captured.

3. **Query mechanism**: LFB uses attention-based query against the feature bank at each timestep. POPW feeds the entire bank as a sequence to the BiGRU (full connectivity, no attention-based retrieval).

## References

- Wu et al. 2019 — "Long-term Feature Banks for Detailed Video Understanding" (CVPR 2019) — LFB
- Feichtenhofer et al. 2019 — "SlowFast Networks for Video Recognition" (NeurIPS 2019) — dual-pathway inspiration
- Wang et al. 2018 — "Non-Local Networks for Video Understanding" (CVPR 2018) — long-range dependencies