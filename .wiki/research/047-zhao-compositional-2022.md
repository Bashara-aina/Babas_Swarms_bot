---
title: Zhao Compositional 2022
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
summary: This paper addresses compositional action recognition - understanding actions
  as combinations of verbs and nouns. The authors propose a multi-view feature fusion
  framework that leverages cross-atte...
wikilinks: []
confidence: medium
source: research
---

# Summary

This paper addresses compositional action recognition - understanding actions as combinations of verbs and nouns. The authors propose a multi-view feature fusion framework that leverages cross-attention to combine complementary information from different camera views, enabling generalization to unseen action-object combinations.

## Key Contributions

1. **Multi-View Fusion Framework**: Uses cross-attention to share information between views
2. **Compositional Action Recognition**: Enables recognition of unseen verb+noun combinations
3. **Cooperative Learning**: Joint training with compositional loss

## Method

1. Extract spatio-temporal features using I3D from each view
2. Apply cross-attention module where each view's CLS token queries other views' patch tokens
3. Fuse features and predict action categories
4. Train with compositional loss measuring verb+noun understanding

## Results

On IKEA ASM:
- **Top-1**: 56.2% (18.1% improvement over single-view)
- **Top-3**: 87.3%
- Significant improvement on compositional split where test actions use unseen object combinations

## Relevance to POPW

Multi-view fusion is relevant for POPW's assembly understanding. The compositional action framework addresses generalization to novel assembly configurations, important for real-world deployment.

## Citation

```bibtex
@article{zhao2022compositional,
  title={Compositional action recognition with multi-view feature fusion},
  author={Zhao, Zhicheng and Liu, Yingan and Ma, Lei},
  journal={PLoS ONE},
  volume={17},
  number={4},
  pages={e0266259},
  year={2022}
}
```
