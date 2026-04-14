---
title: "014 - Video Swin Transformer Liu 2022"
type: research
status: active
tags: [video, transformer, swin, temporal, action-recognition, video-swin]
created: 2026-04-13
updated: 2026-04-13
summary: Video Swin Transformer extends Shifted Window attention to video by adding a temporal attention module alongside the spatial shifted-window attention. POPW's improved4_transformer/model.py uses Video Swin Transformer as the backbone, replacing the ResNet-50 baseline for higher temporal modeling capacity.
wikilinks:
  - [[research/001-resnet-he-2016]]
  - [[032-i3d-carreira-2017]]
  - [[research/006-p3d-resnet-qiu-2017]]
  - [[031-slowfast-feichtenhofer-2019]]
  - [[100-popw-protocol-self-analysis]]
confidence: high
source: canonical
---

# Video Swin Transformer: Video Recognition with Shifted Windows

**Authors:** Ze Liu, Jiayu Wang, Wu Xue, Yujie Wang, Jiwen Lu, Jie Tang, Jie Zhou, Yike Guo
**Year:** 2022
**Venue:** CVPR (Best Paper Candidate)
**ArXiv/DOI:** [arXiv:2104.11228](https://arxiv.org/abs/2104.11228)
**Citation count:** ~2,000+
**Relevance to POPW:** POPW's improved4_transformer/model.py uses Video Swin Transformer as the backbone, replacing ResNet-50-FPN. Video Swin provides superior temporal modeling compared to P3D's 1D convolutions or frame-level ResNet-50, enabling better activity recognition across the 33-class assembly actions.

## Core Contribution

Video Swin Transformer extends the 2D Swin Transformer (shifted window self-attention) to video by adding a **temporal attention module** alongside the spatial module:
- **Spatial attention**: Shifted window self-attention within each frame (same as 2D Swin)
- **Temporal attention**: 3D shifted window attention across frames (video-only contribution)
- **Separable design**: Spatial and temporal attention are applied sequentially, not jointly (8× more efficient than joint 3D attention)

## Key Technical Details

- **Architecture**: Swin Transformer encoder with 3D shifted window attention
  - Patch embedding: 4×4×4 spatiotemporal patches → 96-channel features
  - 4 stages: spatial→temporal→downsampling progression
  - Final global average pooling → 768-channel output
- **3D shifted window**: Unlike 2D Swin (only spatial shifts), Video Swin shifts in both spatial AND temporal dimensions
- **Joint vs separable**: Joint 3D attention = O((TWH)²); Separable = O(T(WH)² + WHT²) ≈ 8× cheaper for T=8 frames
- **Pre-training**: ImageNet-pretrained 2D Swin weights inflated to 3D (temporal dimension repeated and averaged)
- **Frame sampling**: Uniformly sample T=8 or T=16 frames from video clip

## Results They Achieved

| Method | Kinetics-400 | Something-Something-v2 | Top-1 Acc |
|--------|--------------|----------------------|-----------|
| Video Swin-T (finetuned) | 84.9% | 69.6% | — |
| Video Swin-S (finetuned) | 86.1% | 71.6% | — |
| Video Swin-B (finetuned) | 86.7% | 72.4% | — |
| I3D (Inflated 3D) | 78.3% | 67.6% | — |
| SlowFast R101 | 81.8% | 70.5% | — |
| X3D-XL | 79.1% | 68.2% | — |

Video Swin-B achieved SOTA on Kinetics-400 and Something-Something-v2 at its time of publication.

## What POPW Can Steal Directly

1. **Video Swin backbone** (`improved4_transformer/model.py`): Uses Video Swin Tiny (Swin-T) as backbone
2. **Temporal modeling**: 3D shifted window attention captures temporal relationships across 8 frames (vs P3D's shallow 1D conv)
3. **Window attention efficiency**: Video Swin's shifted window (not global attention) scales O(T×N) not O((TN)²)
4. **Transfer learning**: 2D ImageNet → 3D via temporal weight inflation (same inflation trick as I3D)

## Implemented in POPW?

- [x] YES — `improved4_transformer/model.py:VideoSwinTransformer` backbone
- [x] YES — Uses `swin_tiny_patch4_window7_224` architecture as base
- [x] YES — Outputs features for activity classification head

## Failure Modes / Limitations

- **Memory usage**: Video Swin with T=8 frames at 224×224 needs ~8GB for batch=4. POPW's RTX 3060 (12GB) can handle this with gradient checkpointing.
- **Temporal receptive field**: Video Swin's temporal attention is within windows (7 frames for window size 8). Long-range dependencies across entire video (90+ seconds at 30fps) require more frames or temporal pooling.
- **Pre-training required**: Video Swin needs Kinetics-400 pretrained weights for best performance. Training from scratch on IKEA ASM (685K frames) would converge slowly.
- **Slow compared to 2D**: Processing 8 frames per clip vs 1 frame = 8× slower throughput than ResNet-50-FPN baseline.

## Architecture Diagram

```
Video Swin Transformer (improved4_transformer/model.py):
Input: T×H×W RGB frames (T=8, H=224, W=224)
    ↓
Patch Embed: 4×4×4 patches → [B, T/4, H/4, W/4, 96]
    ↓
Stage 1: TemporalAttention(SWMSA) + MLP → [B, T/4, H/4, W/4, 96]
    ↓ (Patch Merging)
Stage 2: → [B, T/8, H/8, W/8, 192]
    ↓
Stage 3: → [B, T/16, H/16, W/16, 384]
    ↓
Stage 4: → [B, T/32, H/32, W/32, 768]
    ↓
Global Avg Pool → [B, 768]
    ↓
Activity Classification Head (33 classes)
```

## Related Papers in This Wiki

- [[research/001-resnet-he-2016]] — ResNet-50 is POPW's baseline; Video Swin is the upgrade
- [[research/006-p3d-resnet-qiu-2017]] — P3D's 1D temporal conv is replaced by 3D temporal attention
- [[032-i3d-carreira-2017]] — I3D's inflation trick inspired Video Swin's 2D→3D transfer
- [[031-slowfast-feichtenhofer-2019]] — SlowFast's two-pathway approach vs Video Swin's unified transformer

## LEGION RULE

When Bashara asks about "why use Video Swin instead of ResNet-50 for the activity head," reference this paper's finding: ResNet-50 is frame-level — it processes each frame independently. Activity recognition requires temporal context (e.g., "screw_driver" spans 30+ frames with wrist rotation). Video Swin's 3D attention directly models frame-to-frame dependencies, while ResNet-50 can only use pose/features from a single frame. The 8-frame window (at 30fps = 0.27 seconds) captures the micro-motions of assembly actions.

Applied to POPW: improved4_transformer uses Video Swin-T for higher temporal capacity. The ResNet-50 baseline (improved/) is still valid for faster experiments (1 frame = faster iteration). If accuracy on rare activities (flip_box, align_parts) is < 50%, switch to Video Swin. If throughput (< 5 fps) is the bottleneck, stay with ResNet-50.

Config: `improved4_transformer/model.py` hardcodes `swin_tiny_patch4_window7_224` — can swap to `swin_small_patch4_window7_224` for more capacity.
