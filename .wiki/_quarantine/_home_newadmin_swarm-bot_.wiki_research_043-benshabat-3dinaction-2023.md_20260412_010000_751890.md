---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/research/043-benshabat-3dinaction-2023.md",
  "reason": "daily_fast_scan: score=0.200 < 0.3",
  "score": 0.2,
  "quarantined_at": "2026-04-12T01:00:00.751921"
}
---

---
paper_id: "043"
title: "3DInAction: Understanding Human Actions in 3D Point Clouds"
authors: "Ben-Shabat, Yizhak; Shrout, Oren; Gould, Stephen"
year: 2023
venue: "arXiv preprint"
arxiv: "2303.06346"
doi: "10.48550/arXiv.2303.06346"
domain: "Assembly & Industrial Action Recognition"
popw_relevance: "Point cloud-based action recognition for assembly; addresses depth data modality for industrial settings"
key_contribution: "Novel pipeline for 3D point cloud action recognition with t-patches (temporal patches) and hierarchical architecture"
tags:
  - point cloud
  - 3D action recognition
  - deep learning
  - temporal patches
  - assembly tasks
datasets:
  - "DFAUST"
  - "IKEA ASM"
code_url: "https://github.com/sitzikbs/3dincaction"
architecture:
  type: "Hierarchical Point Cloud Network"
  key_components:
    - "Temporal patches (t-patches) as key building blocks"
    - "Hierarchical spatio-temporal representation learning"
    - "Point cloud permutation invariance handling"
key_insight: "Point cloud modality lacks structure and has permutation invariance; t-patches provide meaningful temporal decomposition"
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
