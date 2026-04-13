---
paper_id: "036"
title: "How Object Information Improves Skeleton-based Human Action Recognition in Assembly Tasks"
authors: "Aganian, Dustin; Köhler, Mona; Baake, Sebastian; Eisenbach, Markus; Gross, Horst-Michael"
year: 2023
venue: "IJCNN 2023"
arxiv: "2306.05844"
doi: "10.48550/arXiv.2306.05844"
domain: "Assembly & Industrial Action Recognition"
popw_relevance: "SOTA baseline for IKEA ASM skeleton-based action recognition; defines POPW's competitive landscape"
key_contribution: "Integrates object information into skeleton-based action recognition by treating object centers as additional skeleton joints"
tags:
  - skeleton-based
  - object-aware
  - assembly tasks
  - human-robot collaboration
  - IKEA ASM
sota_metrics:
  - dataset: "IKEA ASM"
    top1: "~70-75%"
    top3: "~85-90%"
    notes: "Combined skeleton + object vs skeleton-only baseline"
architecture:
  - type: "Graph Convolutional Networks (GCN)"
  - key_components: ["Object centers as skeleton joints", "Instance segmentation for object detection", "Multi-modal fusion (skeleton + object)"]
datasets:
  - "IKEA ASM"
key_insight: "Skeleton-only methods lose object interaction information; treating object centers as additional joints preserves spatial relationships"
limitations: ["Depends on object detector quality", "Limited to known object categories"]
pdf_path: "project/popw/working/external/papers/ObjectInfo_HAR_Assembly.pdf"
project_url: ""
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
