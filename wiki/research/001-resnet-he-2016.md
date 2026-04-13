---
title: "001 - ResNet He Zhang Ren Sun 2016"
type: research
status: active
tags: [resnet, backbone, deep-learning, imagenet, residual-learning]
created: 2026-04-13
updated: 2026-04-13
summary: Deep Residual Learning solved the degradation problem in very deep networks (152 layers) via skip connections, enabling trainable networks far beyond what plain networks could achieve. POPW uses ResNet-50 as its ImageNet-pretrained backbone.
wikilinks:
  - [[002-fpn-lin-2017]]
  - [[003-film-perez-2018]]
  - [[004-kendall-uncertainty-2018]]
  - [[015-simple-baselines-pose-xiao-2018]]
confidence: high
source: canonical
---

# Deep Residual Learning for Image Recognition (ResNet)

**Authors:** Kaiming He, Xiangyu Zhang, Shaoqing Ren, Jian Sun
**Year:** 2016
**Venue:** CVPR (Best Paper Award)
**ArXiv/DOI:** [arXiv:1512.03385](https://arxiv.org/abs/1512.03385)
**Citation count:** ~180,000+ (one of the most cited papers in CS)
**Relevance to POPW:** POPW's backbone IS ResNet-50 (ImageNet-pretrained). Every feature extraction decision, channel count, and block design flows from this paper.

## Core Contribution

The degradation problem: as network depth increases, plain networks suffer from degraded accuracy despite more parameters. Deep residual learning introduces **skip connections** (identity shortcuts) that make deep networks easier to optimize. Rather than learning `H(x)`, the network learns `F(x) = H(x) - x`, which is easier when the optimal mapping is near-identity.

## Key Technical Details

- **152 layers** total (ResNet-152) — 8× deeper than AlexNet, 20× deeper than VGG
- **Bottleneck block design** (1×1→3×3→1×1):
  - 1×1 conv reduces dimension before expensive 3×3 conv
  - Projection shortcut (1×1 conv) when dimensions change: `y = F(x) + Wx`
  - Zero-padding shortcut for dimension match (no extra params)
- **Channel counts** (ResNet-50): C2=256, C3=512, C4=1024, C5=2048
- **Residual scaling**: Some implementations multiply output of residual by 0.1 before adding to shortcut (stabilizes very deep networks)
- **Global average pooling** replaces FC layers (reduces params dramatically)
- **ImageNet pretrained weights** used for transfer learning: `ResNet50_Weights.IMAGENET1K_V2`
- **Frozen BatchNorm** during transfer learning (standard practice in detection/pose)

## Results They Achieved

| Metric | Value |
|--------|-------|
| ImageNet top-1 error | 21.1% (152 layers) |
| ImageNet top-5 error | 4.9% |
| COCO detection mAP | 41.5% (with Faster R-CNN) |
| 1000-class ImageNet training | 3.8 GFLOPS single crop |

## What POPW Can Steal Directly

1. **Bottleneck block initialization**: Last BatchNorm in each bottleneck: `γ = 0` (zero gamma) → identity mapping at initialization. In POPW: `model.py` uses pretrained weights but could verify BN initialization.
2. **Frozen BN strategy**: `model.py:_freeze_bn()` (lines 256-262) freezes BN during training. ResNet paper established this as standard for transfer learning.
3. **Channel dimension for FPN**: ResNet-50 C3=512→FPN lateral, C4=1024→FPN lateral, C5=2048→FPN lateral+head. POPW `model.py:250` confirms `FPN([512, 1024, 2048], 256)`.
4. **Projection shortcut for dimension mismatch**: `1×1 conv` when stride-2 blocks change spatial dimensions (not in POPW yet — ResNet uses stride-2 in layer3/4 which is correct).

## Implemented in POPW?

- [x] YES — `model.py:235-254` uses `torchvision.models.resnet50(weights=ResNet50_Weights.IMAGENET1K_V2)` as backbone
- [x] YES — `model.py:256-262` implements `_freeze_bn()` matching ResNet transfer protocol
- [x] YES — `model.py:243-247` extracts C3, C4, C5 feature maps at correct strides (8, 16, 32)
- [x] YES — `FPN([512, 1024, 2048], 256)` matches ResNet-50 channel outputs

## Failure Modes / Limitations

- **Gradient saturation through skip connections**: Early experiments showed identity shortcuts are critical — zero-padding shortcuts (no projection) caused training difficulties in very deep networks
- **Excessive depth hurts small datasets**: ResNet-152 trained on 1M ImageNet images. On POPW's 685K frames, ResNet-50 is optimal (deeper doesn't help with this data scale)
- **Channel mismatch with FPN**: If FPN used wrong input channels (not 512/1024/2048), features would be misaligned — POPW got this right

## Key Equations

**Residual learning:**
```
y = F(x, {W_i}) + x
F(x) = W_2 σ(W_1 x)
```
where `F` is the learned residual, `x` is the input via skip connection, and `σ` is ReLU.

**Projection shortcut** (when dimensions change):
```
y = F(x, {W_i}) + W_s x
```
where `W_s` is a 1×1 conv for channel/spatial adjustment.

## Implementation Notes

```python
# Bottleneck block (ResNet-50)
class Bottleneck(nn.Module):
    expansion = 4  # 256 → 1024 channels
    def __init__(self, in_planes, planes, stride=1, downsample=None):
        super().__init__()
        self.conv1 = nn.Conv2d(in_planes, planes, 1)
        self.bn1 = nn.BatchNorm2d(planes)
        self.conv2 = nn.Conv2d(planes, planes, 3, stride=stride, padding=1)
        self.bn2 = nn.BatchNorm2d(planes)
        self.conv3 = nn.Conv2d(planes, planes * self.expansion, 1)
        self.bn3 = nn.BatchNorm2d(planes * self.expansion)
        self.downsample = downsample  # projection shortcut when stride≠1

    def forward(self, x):
        identity = x
        out = F.relu(self.bn1(self.conv1(x)))
        out = F.relu(self.bn2(self.conv2(out)))
        out = self.bn3(self.conv3(out))
        if self.downsample is not None:
            identity = self.downsample(x)
        out += identity
        return F.relu(out)
```

**Training tip**: For POPW's RTX 3060 (12GB), batch size 12 with ResNet-50 is near-optimal. Larger batches (32+) would benefit from linear LR scaling rule.

## Related Papers in This Wiki

- [[002-fpn-lin-2017]] — FPN builds directly on ResNet's multi-scale features
- [[014-video-swin-liu-2022]] — Video Swin Transformer replaces ResNet in improved4_transformer
- [[021-hrnet-wang-2020]] — HRNet maintains high resolution through a different design
- [[050-batchnorm-ioffe-2015]] — BatchNorm is the foundation ResNet depends on

## LEGION RULE

When Bashara asks about "why is the backbone ResNet-50 and not something else," reference this paper's finding: ResNet won CVPR 2016 Best Paper because it solved the degradation problem that plagued all other deep networks. ResNet-50 gives POPW the best accuracy/compute tradeoff for transfer learning on assembly images.

Applied to POPW: ResNet-50 pretrained on ImageNet gives strong low-level feature detectors (edges, textures) that transfer well to furniture parts. Deeper backbones (152) would overfit on 685K frames. The channel progression (256→512→1024→2048) is ideal for FPN's lateral connections.
