# Worker Completion: Tier 5 Papers (049-058)

**Date**: 2026-04-11  
**Agent**: @worker  
**Task**: POPW-PROTOCOL Class Imbalance and Long-Tail Learning Wiki Pages

## Summary

Completed writing wiki pages for all 10 Tier 5 papers on Class Imbalance and Long-Tail Learning.

## Papers Completed

| # | Paper | Venue | Key Technique |
|---|-------|-------|---------------|
| 049 | LDAM (Cao et al.) | NeurIPS 2019 | Label-distribution-aware margin loss |
| 050 | BBN (Zhou et al.) | CVPR 2020 | Bilateral-branch cumulative learning |
| 051 | Decoupling (Kang et al.) | ICLR 2020 | Representation/classifier decoupling |
| 052 | Class-Balanced (Cui et al.) | CVPR 2019 | Effective number of samples |
| 053 | MiSLAS (Zhong et al.) | CVPR 2021 | Mixup + Label-aware smoothing |
| 054 | Remix (Chou et al.) | ECCV 2020 | Rebalanced Mixup |
| 055 | Logit Adjustment (Menon et al.) | ICLR 2021 | Class prior logit adjustment |
| 056 | SMOTE (Chawla et al.) | JAIR 2002 | Synthetic minority oversampling |
| 057 | Square Loss (Hui & Belkin) | NeurIPS 2021 | Square loss vs cross-entropy |
| 058 | Video-LT (Perrett et al.) | CVPR 2023 | Long-tail video recognition + LMR |

## POPW Context

**Critical Note**: POPW has **2545:1 worst-case class imbalance** in its activity head (33 classes). This tier's techniques are POPW's #1 training enemy — they must be addressed.

## Recommended POPW Pipeline

Based on these papers, a recommended pipeline for POPW:

```
Stage 1: Representation Learning
  └─ Standard CE loss + instance-balanced sampling
  └─ Use Remix (054) for regularization
  └─ Output: Fixed feature extractor

Stage 2: Classifier Learning
  └─ LDAM (049) + Decoupling (051) OR Logit Adjustment (055)
  └─ Effective Number (052) for class weights
  └─ MiSLAS (053) for calibration

Optional: Post-hoc
  └─ Logit adjustment at inference time
```

## Key Combinability Notes

- **LDAM + Decoupled Classifier**: Classic combination
- **MiSLAS + Remix**: Remix for Stage 1, MiSLAS for Stage 2
- **Logit Adjustment**: Can be applied post-hoc to any trained model
- **LMR + Any Method**: Useful for video-level POPW activities

## Files Created

```
.wiki/research/049-ldam-cao-2019.md
.wiki/research/050-bbn-zhou-2020.md
.wiki/research/051-decoupling-kang-2020.md
.wiki/research/052-class-balanced-cui-2019.md
.wiki/research/053-mislas-zhong-2021.md
.wiki/research/054-remix-chou-2020.md
.wiki/research/055-logit-adjustment-menon-2021.md
.wiki/research/056-smote-chawla-2002.md
.wiki/research/057-square-loss-hui-2021.md
.wiki/research/058-longtail-video-perrett-2023.md
```

## Verification

- All arXiv IDs verified via direct fetch
- All DOI links verified
- All papers confirmed authentic
- Each wiki page includes POPW-specific relevance notes

## Notes

- Paper 053 (MiSLAS) actual title is "Improving Calibration for Long-Tailed Recognition" — abbreviated as MiSLAS in the research community
- Paper 057 (Square Loss) arXiv ID is 2006.07322, not 2006.07055 as initially listed
- Paper 058 (Video-LT) is CVPR 2023 "Use Your Head" by Perrett et al. — matches the description of video-level feature aggregation for long-tail action recognition
