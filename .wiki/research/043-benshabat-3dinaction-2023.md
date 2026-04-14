---
title: Benshabat 3Dinaction 2023
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
summary: 'This paper proposes a novel method for 3D point cloud action recognition,
  addressing the unique challenges of point cloud data: lack of structure, permutation
  invariance, and varying number of poin...'
wikilinks: []
confidence: medium
source: research
---

# Summary

This paper proposes a novel method for 3D point cloud action recognition, addressing the unique challenges of point cloud data: lack of structure, permutation invariance, and varying number of points. The 3DINAction pipeline introduces temporal patches (t-patches) as a key building block alongside a hierarchical architecture for learning informative spatio-temporal representations.

## Key Contributions

1. **Temporal Patches (t-patches)**: Key temporal decomposition unit for point cloud sequences
2. **Hierarchical Architecture**: Learns multi-level spatio-temporal representations
3. **Point Cloud Handling**: Addresses permutation invariance through dedicated architecture

## Method

The approach:
1. Extracts t-patches as moving point groups in time
2. Processes through hierarchical network capturing spatial relationships within patches
3. Models temporal evolution through patch-level aggregations
4. Achieves improved performance on standard benchmarks

## Results

Demonstrates improved performance on DFAUST and IKEA ASM datasets compared to baseline methods.

## Relevance to POPW

Point clouds provide an alternative modality relevant for industrial depth sensors. POPW could explore point cloud representations or multi-modal fusion including depth data.

## Citation

```bibtex
@article{benshabat2023action,
  title={3DInAction: Understanding Human Actions in 3D Point Clouds},
  author={Ben-Shabat, Yizhak and Shrout, Oren and Gould, Stephen},
  journal={arXiv preprint arXiv:2303.06346},
  year={2023}
}
```
