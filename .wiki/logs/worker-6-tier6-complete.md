---
title: Worker 6 Tier6 Complete
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- logs
created: '2026-04-14'
updated: '2026-04-14'
summary: '**Task:** Write wiki pages for Tier 6 papers (059-067)'
wikilinks: []
confidence: medium
source: research
---
# Worker-6: Tier 6 Complete — Semi-Supervised Detection & Pseudo-GT

**Date:** 2026-04-11
**Task:** Write wiki pages for Tier 6 papers (059-067)
**Status:** ✅ COMPLETE (9/9 papers written)

## Papers Completed

| # | File | Paper | Venue |
|---|------|-------|-------|
| 059 | `059-soft-teacher-xu-2021.md` | Soft Teacher (SS-OD) | ICCV 2021 |
| 060 | `060-pais-hu-2023.md` | PAIS (SSIS) | ICCV 2023 |
| 061 | `061-pointly-supervised-cheng-2022.md` | Pointly-Supervised IS | CVPR 2022 |
| 062 | `062-s4m-yoon-2025.md` | S⁴M (SAM-augmented SSIS) | ICCV 2025 |
| 063 | `063-unbiased-teacher-liu-2021.md` | Unbiased Teacher (SS-OD) | ICLR 2021 |
| 064 | `064-better-pseudo-labels-porcher-2024.md` | Better Pseudo-Labels (SSIS) | arXiv 2024 |
| 065 | `065-pl-dc-lin-2025.md` | PL-DC (Decoupling & Correction) | arXiv 2025 |
| 066 | `066-pointrend-kirillov-2020.md` | PointRend | CVPR 2020 |
| 067 | `067-sam-kirillov-2023.md` | SAM (Segment Anything Model) | ICCV 2023 |

## Key Findings

### Critical for POPW Pseudo-GT

1. **SAM (067) — MOST IMPORTANT**: Foundation model for zero-shot furniture segmentation. POPW uses SAM as the pseudo-GT bootstrapping segmenter per deepresearch.md.

2. **S⁴M (062) — Direct Template**: Shows exactly how to integrate SAM into semi-supervised instance segmentation. POPW should follow this pattern.

3. **PL-DC (065) — Quality Decoupling**: Separate handling of class vs mask quality produces +11.6 mAP gains. POPW should implement separate quality gates for furniture category and mask boundary.

### Pattern Across Papers

```
Semi-supervised IS evolution:
Baseline → PAIS (alignment) → Better Pseudo-Labels (calibration) → PL-DC (decoupling) → S⁴M (SAM augmentation)
```

### POPW Implementation Recommendations

From tier 6 research:
- Use teacher-student framework with EMA updates
- Apply quality-aware thresholding (not just confidence thresholding)
- Decouple class prediction quality from mask quality
- Leverage SAM for zero-shot mask generation and refinement
- Use PointRend-style boundary refinement for pseudo-GT polish

## Verification

All papers verified via web search. arXiv IDs confirmed:
- 059: arXiv:2106.09018 ✅
- 060: arXiv:2308.05359 ✅
- 061: arXiv:2104.06404 ✅
- 062: arXiv:2504.05301 ✅
- 063: arXiv:2102.09480 ✅
- 064: arXiv:2403.11675 ✅
- 065: arXiv:2505.11075 ✅
- 066: arXiv:1912.08193 ✅
- 067: arXiv:2304.02643 ✅

## Output Location

All files written to: `/home/newadmin/swarm-bot/.wiki/research/`

## Next Steps

Report to @planner for review. Tier 7 (068+) next if additional tiers exist.
