---
title: Aganian Objects 2023
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
summary: 'This paper addresses a critical limitation in skeleton-based action recognition
  for assembly tasks: the loss of object interaction information when processing skeletons
  alone. The authors propose i...'
wikilinks: []
confidence: medium
source: research
---

# Summary

This paper addresses a critical limitation in skeleton-based action recognition for assembly tasks: the loss of object interaction information when processing skeletons alone. The authors propose integrating object information by treating object centers as additional skeleton joints, thereby preserving spatial relationships between human and objects during assembly tasks.

## Key Contributions

1. **Novel Integration Approach**: Treats object centers from instance segmentation as additional skeleton joints
2. **Enhanced GCN Methods**: Extends state-of-the-art GCN-based action recognition methods with object-augmented skeletons
3. **Comprehensive Analysis**: Analyzes the effect of object detector quality on combined performance

## Method

The approach enhances skeleton-based action recognition by:
1. Using instance segmentation (Mask R-CNN) to detect and localize objects
2. Extracting object center coordinates as additional "joints"
3. Augmenting the skeleton graph with object nodes connected to relevant body joints
4. Processing the enhanced skeleton through GCN-based action classifiers

## Results

On the IKEA ASM dataset:
- Significant improvement over skeleton-only baselines when combining skeleton + object information
- Object detector quality directly impacts fusion performance
- Benefits particularly evident in assembly-specific actions involving tool/object manipulation

## Relevance to POPW

This paper establishes one of the SOTA baselines on IKEA ASM for skeleton-based methods. POPW must surpass these performance levels to demonstrate improvement in the assembly action recognition domain.

## Citation

```bibtex
@article{aganian2023object,
  title={How Object Information Improves Skeleton-based Human Action Recognition in Assembly Tasks},
  author={Aganian, Dustin and Köhler, Mona and Baake, Sebastian and Eisenbach, Markus and Gross, Horst-Michael},
  journal={arXiv preprint arXiv:2306.05844},
  year={2023}
}
```
