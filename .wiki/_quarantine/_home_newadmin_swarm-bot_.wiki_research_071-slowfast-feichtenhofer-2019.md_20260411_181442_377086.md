---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/research/071-slowfast-feichtenhofer-2019.md",
  "reason": "daily_fast_scan: score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-11T18:14:42.377129"
}
---

---
tags: [video-understanding, dual-path, slowfast, temporal-modeling, iccv-2019]
sources: [arxiv:1812.03982]
created: 2026-04-11
updated: 2026-04-11
---

# SlowFast Networks for Video Recognition

**Feichtenhofer, Fan, Malik, He** | ICCV 2019 | [arXiv:1812.03982](https://arxiv.org/abs/1812.03982)

## Overview

SlowFast networks are dual-path video recognition models that process video at two different frame rates simultaneously:
- **Slow pathway**: Low frame rate (e.g., 1 frame per 8) — captures spatial semantics and appearance
- **Fast pathway**: High frame rate (e.g., 1 frame per 2) — captures motion and temporal dynamics

The pathways are connected via lateral connections that allow the Slow pathway to receive contextual information from the Fast pathway. This mirrors the biological concept of "what" (slow/semantic) vs "where" (fast/motion) pathways in primate vision.

## Architecture

### Dual Pathway Design

```
Video
  ├── Slow Pathway (1/8 frames) ─── Large temporal stride → Spatial semantics
  └── Fast Pathway (1/2 frames) ─── Small temporal stride → Motion details
        ↑
  Lateral Connections (from Fast to Slow)
```

### Key Properties

1. **Asymmetric design**: Slow path has more channels (C→8C); Fast path has fewer channels but higher temporal resolution
2. **Lateral connections**: Fast features aggregated into Slow pathway for context
3. **Efficient**: Reduces computation by processing most frames at low resolution
4. **End-to-end training**: Both pathways trained jointly

## Performance

| Benchmark | SlowFast (K400 pretrained) | Previous SOTA |
|-----------|----------------------------|---------------|
| Kinetics-400 | 79.0% (top-1) | 73.9% (I3D) |
| Kinetics-600 | 81.6% | — |
| AVA 2.2 (action detection) | 38.4% (mAP) | — |

## POPW Relevance

> [!NOTE]
> SlowFast's dual pathway is architecturally similar to how POPW could process RGB + depth or multi-view video. The Fast pathway captures fine-grained temporal motion (screw rotation, part alignment) while Slow pathway captures structural semantics (which assembly stage). Could inspire WorkerNet head design.

> [!CRITICAL]
> For industrial assembly on RTX 3060, SlowFast is computationally heavier than TSM. However, if we downsample frames aggressively, it may still be feasible for POPW's assembly sequence classification.

## Code Availability

- Official: https://github.com/facebookresearch/SlowFast
- FAIR research, PyTorch implementation

## See Also

- [[068-i3d-carreira-2017]] — I3D (two-stream baseline)
- [[069-tsm-lin-2019]] — TSM (efficient, single-stream)
