---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/research/058-longtail-video-perrett-2023.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-13T01:00:01.206587"
}
---

---
tags: [long-tail-learning, video-recognition, feature-aggregation, cvpr-2023]
sources: [arxiv:2304.01143]
created: 2026-04-11
updated: 2026-04-11
---

# Use Your Head: Improving Long-Tail Video Recognition

**Perrett, Sinha, Burghardt, Mirmehdi & Damen** | CVPR 2023 | [arXiv:2304.01143](https://arxiv.org/abs/2304.01143)

## Overview

This paper investigates long-tail video recognition and makes two key contributions:

1. **New benchmarks**: The paper reveals that existing video benchmarks (SSv2, VideoLT) lack few-shot classes, falling short of true long-tail properties. The authors create proper long-tail versions: SSv2-LT and VideoLT-LT.

2. **LMR (Long-Tail Mixed Reconstruction)**: A novel method that reconstructs tail-class samples as weighted combinations of head-class samples to reduce overfitting.

## Key Problem: Missing Few-Shot Classes

Previous video long-tail benchmarks don't properly represent the long-tail:
- Head classes have many samples
- Tail classes have few samples
- **Missing**: Few-shot classes (5-20 samples) in the "tail"

LMR addresses this by using head class knowledge to help tail classes.

## LMR: Long-Tail Mixed Reconstruction

### Method

```
For each tail class sample x_t:
1. Find k-nearest head class samples {x_h1, ..., x_hk}
2. Learn weights {α_1, ..., α_k} via reconstruction
3. x_reconstructed = Σ α_i · x_hi
4. Mix labels: y_mixed = λ · y_t + (1-λ) · y_reconstructed
5. Train on (x_reconstructed, y_mixed)
```

**Intuition**: Tail samples that look like head samples should inherit some of the head class label, reducing overfitting to spurious tail-specific features.

## Key Results

| Dataset | LMR | Previous Best |
|---------|----:|-------------:|
| EPIC-KITCHENS | 55.4% | 52.3% |
| SSv2-LT | 52.1% | 48.7% |
| VideoLT-LT | 64.3% | 61.2% |

## POPW Relevance

> [!IMPORTANT]
> This paper is the most directly relevant for POPW's video activity recognition:
>
> 1. **Video-level aggregation**: POPW needs to aggregate frame-level features into video-level activity predictions
> 2. **Long-tail in video**: POPW's activity classes are heavily imbalanced — some activities (assemble) occur far more than others (inspect)
> 3. **LMR reconstruction**: Could help POPW's tail activities by leveraging similarity to head activities
>
> For POPW's **33-class activity head** with 2545:1 imbalance, LMR-style reconstruction could help rare activities learn robust features by borrowing from common activities.

## Key Insights for POPW

1. **Video benchmarks often miss few-shot classes**: When creating POPW's evaluation splits, ensure few-shot activity classes are present
2. **Mixed reconstruction helps tail**: Tail activities that visually resemble head activities should use mixed labels
3. **Head/tail distinction matters**: Not just sample count, but visual similarity to head classes

## Combinability

- ✅ **LMR + MiSLAS (053)**: Use LMR for representation, MiSLAS for calibrated classifier
- ✅ **LMR + Decoupling (051)**: LMR as representation learning in decoupled framework
- ✅ **LMR + Logit Adjustment (055)**: Apply logit adjustment after LMR features
- ✅ **LMR + Remix (054)**: Combine reconstruction with remix augmentation

## Code Availability

- Official: https://github.com/tobyperrett/lmr-release
- Project page: http://tobyperrett.github.io/lmr

## See Also

- [[053-mislas-zhong-2021]] — MiSLAS calibration (complementary)
- [[051-decoupling-kang-2020]] — Decoupled framework (LMR fits here)
- [[055-logit-adjustment-menon-2021]] — Logit adjustment for tail classes
