---
paper_id: "082"
title: "MS-TCN: Multi-Stage Temporal Convolutional Network for Action Segmentation"
authors: "Abu Farha, Yazan; Gall, Juergen"
year: 2021
venue: "ECCV 2020 / arXiv 1903.01945"
arxiv: "1903.01945"
doi: "10.48550/arXiv.1903.01945"
citations: 1000+
domain: "Temporal Action Segmentation"
popw_relevance: "Foundational action segmentation architecture; POPW's temporal modeling can build on MS-TCN"
key_contribution: "Multi-stage temporal convolutional network with dilated convolutions for action segmentation"
tags:
  - temporal convolutional network
  - action segmentation
  - multi-stage
  - dilated convolutions
pdf_path: "project/popw/working/external/papers/MS-TCN_ActionSegmentation.pdf"
---

# Summary

MS-TCN proposes a multi-stage temporal convolutional network for action segmentation in unconstrained videos. The architecture uses multiple stages of dilated 1D convolutions to progressively refine action boundaries and classifications, achieving state-of-the-art results on multiple benchmarks.

## Key Contributions

1. **Multi-Stage Architecture**: Cascaded stages refine predictions progressively
2. **Dilated Convolutions**: Capture long-range temporal dependencies without attention overhead
3. **Boundary Refinement**: Explicit modeling of action transition boundaries

## Relevance to POPW

POPW's activity recognition head can leverage MS-TCN's temporal modeling approach. The multi-stage design with dilated convolutions offers an efficient alternative to transformer-based approaches for frame-level action prediction.