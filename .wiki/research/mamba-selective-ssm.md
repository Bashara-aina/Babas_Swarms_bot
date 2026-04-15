---
title: Mamba Selective Ssm
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
summary: '- **arXiv**: [2312.00752](https://arxiv.org/abs/2312.00752)'
wikilinks: []
confidence: medium
source: research
---

# Mamba: Linear-Time Sequence Modeling with Selective State Spaces

## Paper Info
- **arXiv**: [2312.00752](https://arxiv.org/abs/2312.00752)
- **Authors**: Albert Gu, Tri Dao
- **Institution**: Carnegie Mellon / Princeton
- **Venue**: arXiv 2023, updated 2024

## Core Contribution

Mamba introduces **selective state space models** — making the four SSM parameters (A, B, C, Δ) functions of the input token, rather than fixed per layer. This enables content-aware sequence modeling that prior SSMs lacked.

### The SSM Foundation

A continuous-time SSM maps a 1D input $x(t)$ to a state $h(t)$ via:

$$h'(t) = Ah(t) + Bx(t)$$
$$y(t) = Ch(t) + Dx(t)$$

Where A, B, C are learned parameters and D is the skip connection. The discrete version uses a step size Δ:

$$h_t = \bar{A}_t h_{t-1} + \bar{B}_t x_t$$
$$y_t = \bar{C}_t h_t + D x_t$$

**Prior SSM limitation**: $\bar{A}, \bar{B}, \bar{C}$ were input-independent — the same for every token. The model couldn't selectively attend to or forget information based on content.

**Mamba's innovation**: Makes Δ, B, C functions of the input via projection:

$$\Delta_t = \tau(\text{Linear}(x_t))$$
$$B_t = \text{Linear}_B(x_t)$$
$$C_t = \text{Linear}_C(x_t)$$

This is the "selective" mechanism — the SSM can now choose what to keep, forget, and emit based on the current input.

### Hardware-Aware Parallel Scan

Making parameters input-dependent breaks the efficient convolution property of SSMs. Mamba addresses this with a hardware-aware parallel scan algorithm in recurrent mode — avoids materializing the expanded state in slow GPU memory tiers (HBM) by keeping only the compact hidden state in SRAM.

Result: **5× higher throughput than Transformers**, **linear scaling in sequence length**, validated up to **1M token sequences**.

## Architecture

```
x_t → Linear(Δ) → σ → Δ
x_t → Linear(B) → B
x_t → Linear(C) → C
x_t → Linear(D) → D (skip)

SSM: h_t = Ā_t ⊙ h_{t-1} + B̄_t ⊙ x_t
y_t = C_t ⊙ h_t + D ⊙ x_t
```

No attention. No MLP blocks. Pure SSM recurrence with selective gating.

## Relevance to POPW

1. **Temporal pose modeling**: Mamba's recurrence over 17-keypoint sequences could model skeleton dynamics without quadratic attention
2. **Selective forgetting**: The model learns to suppress redundant pose frames, focus on action-critical frames
3. **Linear complexity**: Enables processing of full 685K-frame IKEA ASM videos without O(n²) memory

## Bidirectional Communication (Pose ↔ Activity)

Mamba in bidirectional mode (forward + backward SSM scans) enables:
- **Forward pass**: `pose_t → hidden_state → future_pose_prediction`
- **Backward pass**: `future_pose_context → hidden_state → current_activity_belief`
- **Activity → Pose modulation**: Backward pass hidden state carries activity context that can modulate pose encoding
- **Pose → Activity modulation**: Forward pass carries pose state that constrains activity recognition

The bidirectional selective SSM can be formulated as two Mamba blocks operating in opposite directions, with their outputs concatenated or merged. The backward block's hidden state at time t encodes the future context (what pose typically follows the current configuration), which directly informs activity recognition.

## Why Not Use Mamba in POPW (Current Version)

1. **POPW uses BiGRU** — Mamba was not yet published when POPW was designed
2. **BiGRU is simpler and well-understood** — the baseline validation should be BiGRU before upgrading to Mamba
3. **Mamba requires more training data** — POPW's 254 videos may be insufficient to train a selective SSM from scratch
4. **POPW's PoseFiLM is the key innovation** — the pose-conditioned feature modulation is more novel than the temporal head choice

## Future Extension: Mamba replacing BiGRU

For POPW v2, Mamba could replace BiGRU as the temporal head:

```
C5_mod_t → Project(2304→512) → Mamba Forward(C5_mod_t) → h_f[t]
C5_mod_t → Project(2304→512) → Mamba Backward(C5_mod_t) → h_b[t]
H_t = Concat(h_f[t], h_b[t]) ∈ R^512  (bidirectional context)
AttentionPool(H) → Classifier
```

This would give:
- Linear-time processing of T=8 frames (vs O(T²) for attention)
- Selective focus on relevant pose frames (vs uniform attention)
- Better long-range temporal modeling for full video inference

## References

- Gu, A., & Dao, T. (2023). "Mamba: Linear-time Sequence Modeling with Selective State Spaces." arXiv:2312.00752