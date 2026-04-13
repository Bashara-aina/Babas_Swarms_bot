---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/research/074-asformer-yi-2021.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-13T01:00:01.178550"
}
---

---
tags: [video-understanding, temporal-action-segmentation, transformer, asformer, bmvc-2021]
sources: [arxiv:2110.08568]
created: 2026-04-11
updated: 2026-04-11
---

# ASFormer: Transformer for Action Segmentation

**Yi, Wen, Jiang** | BMVC 2021 | [arXiv:2110.08568](https://arxiv.org/abs/2110.08568)

## Overview

ASFormer is a **Transformer-based model for action segmentation** that integrates self-attention into the MS-TCN multi-stage architecture. The key innovation is adding a lightweight Transformer encoder on top of each MS-TCN stage, enabling the model to capture longer-range temporal dependencies while maintaining the progressive refinement approach.

ASFormer has three distinctive characteristics: (1) convolutional prior in self-attention, (2) hierarchical attention, and (3) guided decoding using action prototypes.

## Architecture

### Integration of Transformer + TCN

```
Input Frame Features
  └── MS-TCN Stage 1 (dilated convolutions)
        ├── MS-TCN Stage 2
        │     ├── ...
        │     └── MS-TCN Stage N
        │           └── Transformer Encoder (lightweight attention)
        └── Output: Frame-wise action labels
```

### Key Design Choices

1. **Convolutional prior**: Replaces full self-attention with locally-constrained attention (reduced complexity)
2. **Hierarchical design**: Multi-stage refinement, each with Transformer enhancement
3. **Action prototypes**: Constrains output space to valid action transitions

### Complexity

ASFormer reduces Transformer complexity from O(T²) to O(T × k) where k is local window size, making it practical for long videos.

## Performance

| Dataset | ASFormer | MS-TCN++ |
|---------|----------|----------|
| 50 Salads | 86.7% | 85.4% |
| Breakfast | 67.1% | 65.0% |
| GTVS | 84.8% | — |

## POPW Relevance

> [!NOTE]
> ASFormer represents the **Transformer alternative to pure TCN approaches**. For WorkerNet, if we implement an attention mechanism in the action head, ASFormer's efficient local attention design is worth studying. However, for RTX 3060 real-time inference, the simpler MS-TCN++ may be more practical.

## Code Availability

- Official: https://github.com/chinayi/asformer
- BMVC 2021 publication

## See Also

- [[073-ms-tcn-li-2021]] — MS-TCN++ (TCN baseline)
- [[072-temporal-action-segmentation-survey-ding-2022]] — Survey context
