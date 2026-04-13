---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/research/068-i3d-carreira-2017.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-13T01:00:01.198647"
}
---

---
tags: [video-understanding, temporal-modeling, action-recognition, two-stream, 3d-cnn, kinetics]
sources: [arxiv:1705.07750]
created: 2026-04-11
updated: 2026-04-11
---

# I3D: Two-Stream Inflated 3D ConvNets

**Carreira & Zisserman** | CVPR 2017 | [arXiv:1705.07750](https://arxiv.org/abs/1705.07750)

## Overview

The **Two-Stream Inflated 3D ConvNet (I3D)** is a landmark video understanding architecture that bootstraps 3D convolutional networks from 2D image classification models. The core innovation is "inflating" 2D filters into 3D by repeating weights along the temporal dimension, enabling transfer learning from ImageNet pre-training to video tasks.

I3D established the Kinetics-400 dataset as the standard benchmark for action recognition and demonstrated that two-stream architecture (RGB + optical flow) significantly outperforms single-stream approaches.

## Architecture

### Core Innovation: 2D-to-3D Inflation

The inflation technique converts a 2D ConvNet (e.g., Inception) into a 3D equivalent:
- **2D filter**: `[H, W, in_channels, out_channels]` → **3D filter**: `[T, H, W, in_channels, out_channels]`
- Weight repetition: copy each 2D filter weight T times along temporal axis, normalize by `√T`
- This preserves the 2D model's rich feature representations while adding temporal capacity

### Two-Stream Design

1. **RGB Stream**: Raw video frames processed through 3D ConvNet
2. **Flow Stream**: Optical flow fields (horizontal U, vertical V) processed through separate 3D ConvNet

Both streams produce logits that are averaged at test time for final classification.

### Kinetics-400 Pre-training

I3D was trained on Kinetics-400 (240K training videos, 400 classes) and released as pre-trained checkpoints. This pre-training enabled significant improvements on smaller datasets like UCF-101 and HMDB-51.

## Key Results

| Dataset | I3D (two-stream) | Previous Best |
|---------|-------------------|---------------|
| Kinetics-400 | 74.2% (top-1) | — |
| UCF-101 | 93.4% | 88.0% (C3D) |
| HMDB-51 | 66.4% | 51.3% (C3D) |

## Significance for POPW

- **IKEA ASM Baseline**: I3D achieves 57.57% frame-wise accuracy on IKEA ASM vs 68.4% on Kinetics — dataset is ~10% harder
- **Two-stream is expensive**: Optical flow computation is slow; not suitable for real-time RTX 3060 deployment
- **I3D as FiLM conditioning baseline**: WorkerNet's FiLM conditioning can be compared against I3D's two-stream late fusion
- **Transfer learning insight**: Pre-training on large video datasets helps industrial assembly tasks

## POPW Relevance

> [!CRITICAL]
> POPW classifies **FRAMES** but temporal context is key for assembly sequences. I3D's two-stream design demonstrates that spatial (RGB) and temporal (flow) information are complementary. For IKEA assembly, temporal ordering of actions (screw → attach → align) is crucial — pure RGB classification misses this.

## Code Availability

- Official: https://github.com/google-deepmind/kinetics-i3d
- TensorFlow Hub: https://www.tensorflow.org/hub/modules/models/I3D-nchw/1

## See Also

- [[069-tsm-lin-2019]] — Temporal Shift Module for efficient video understanding (RTX 3060-friendly)
- [[071-slowfast-feichtenhofer-2019]] — SlowFast dual-path architecture
