---
title: "SpikMamba: SNN + Mamba for Event Camera Action Recognition"
created: 2026-04-14
modified: 2026-04-14
tags: [spikmamba, snn, event-camera, mamba, action-recognition, neuromorphic, energy-efficient, pose]
authors: [Chen et al.]
type: research
summary: "SpikMamba (Chen et al. 2024) combines Spiking Neural Networks (SNN) with Mamba for event camera action recognition. Event cameras capture per-pixel brightness changes asynchronously — ideal for high-speed motion capture. Validates Mamba's energy efficiency with SNN spike coding for real-time pose tracking on low-power hardware."
wikilinks:
  - [[mamba-selective-ssm]]
  - [[video-mamba]]
  - [[vision-mamba]]
  - [[mamba-pose-activity-survey]]
source: https://arxiv.org/abs/2410.16746
---

# SpikMamba: SNN + Mamba for Event Camera Action Recognition

## Paper Info
- **arXiv**: [2410.16746](https://arxiv.org/abs/2410.16746)
- **Authors**: Chen et al.
- **Venue**: arXiv Oct 2024

## Core Contribution

SpikMamba combines **Spiking Neural Networks (SNN)** with **Mamba** for event camera action recognition. Event cameras capture per-pixel asynchronous brightness changes rather than absolute intensity — making them ideal for high-speed motion capture with temporal precision.

**Relevance to POPW**: IKEA assembly involves both slow precise movements (aligning parts) and fast actions (hammering, screwing). Event cameras could capture these at microsecond resolution, and Mamba's selective SSM can process the resulting asynchronous spike sequences efficiently.

## Why Event Cameras for Assembly?

Traditional RGB cameras capture at 30fps — too slow for fast assembly actions. Event cameras:
- **Temporal resolution**: Microsecond precision (1M events/second)
- **Dynamic range**: 140dB vs RGB's 60dB — works in both bright and dark workshop conditions
- **Energy efficiency**: Only generates events on change — 10-1000× less power than traditional cameras
- **Motion blur**: None — each pixel reports the exact moment of brightness change

For POPW, this means:
- Fast hand movements (hammer strikes) captured at full temporal resolution
- Precise pose tracking even during rapid transitions
- Low-power deployment on edge devices (Jetson Nano class)

## Architecture

```
Event Stream → Polarity Normalization
           → Spiking Encoder (Leaky Integrate-and-Fire)
           → Spike Trains [T, C] → Mamba Blocks → Classification
```

**Spiking Encoder**: Converts continuous event stream into binary spike trains using Leaky Integrate-and-Fire (LIF) neuron model:
```
V_t = α·V_{t-1} + (1-α)·events_t   # membrane potential
S_t = 1 if V_t > threshold else 0   # spike output
```

**Mamba on Spikes**: The spike trains are binary (0/1) — Mamba's selective SSM processes these efficiently:
- Δ gate controls spike integration timing
- B, C transforms are applied to spike inputs
- Hidden state represents membrane potential dynamics

## POPW Enhancement: Event Camera + SpikMamba

Replacing RGB with event camera for POPW:

```
Event Camera (DVS) → Spiking Encoder → Spike trains
                                      → OpenPose-on-SNN (spike-based pose estimation)
                                      → 17 keypoints + confidence @ high temporal resolution

Pose Features → Mamba (instead of BiGRU) → Activity Classification
```

**Benefits for POPW**:
1. **Higher frame rate**: 1kHz effective vs 30fps RGB — captures fast assembly actions
2. **Better pose estimation**: Motion blur elimination improves keypoint accuracy
3. **Energy efficiency**: SpikMamba runs on low-power neuromorphic chips
4. **Mamba temporal modeling**: Same selective SSM processes spike-encoded pose sequences

## SNN + Mamba: Energy Analysis

| Component | Traditional CNN | Spiking CNN + Mamba |
|-----------|----------------|---------------------|
| Operations | FMA (floating multiply-accumulate) | Spikes (addition only) |
| Energy/bit | ~4pJ (CMOS) | ~0.1pJ (spike) |
| Temporal precision | Frame-limited | Microsecond |
| Mamba efficiency | O(T) with selectives | O(T) on spike trains |

SpikMamba achieves **3.2× better energy efficiency** than equivalent CNN+Attention while maintaining accuracy on DVS Gesture and NVGesture datasets.

## Future POPW Hardware Extension

For POPW on edge deployment (Jetson Nano, Intel Loihi):
1. Replace RGB camera with DVS event camera
2. Use spike-based pose estimation (SpikeCV or SNN-modified OpenPose)
3. Replace BiGRU with SpikMamba temporal head
4. Result: Real-time assembly recognition at <5W power

## Relevance to POPW's Temporal Modeling

SpikMamba validates that **Mamba can replace RNNs/LSTMs for pose sequences** with:
- Lower latency (parallel scan vs sequential RNN)
- Better energy efficiency (important for edge deployment)
- Selective focus on relevant temporal moments

POPW's BiGRU processes pose-conditioned features at 30fps. SpikMamba shows the same architecture can work at 1kHz with event cameras — enabling POPW to track fast assembly actions that RGB cameras miss.

## References

- Chen et al. (2024). "SpikMamba: Combining Spiking Neural Networks with State Space Models for Event-based Action Recognition." arXiv:2410.16746
