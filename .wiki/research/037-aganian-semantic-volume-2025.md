---
paper_id: "037"
title: "Including Semantic Information via Word Embeddings for Skeleton-based Action Recognition"
aka_titles:
  - "Semantic-Volume Encoding for Skeleton+Object Action Recognition (2025)"
authors: "Aganian, Dustin; Franze, Erik; Eisenbach, Markus; Gross, Horst-Michael"
year: 2025
venue: "IJCNN 2025"
arxiv: "2506.18721"
doi: "10.48550/arXiv.2506.18721"
domain: "Assembly & Industrial Action Recognition"
popw_relevance: "Extends 036 with semantic word embeddings; advances skeleton-based methods for assembly"
key_contribution: "Replaces one-hot keypoint encodings with semantic volumes using word embeddings to capture joint relationships"
tags:
  - skeleton-based
  - semantic embeddings
  - word embeddings
  - assembly recognition
  - generalization
architecture:
  - type: "GCN with Semantic Volume Encoding"
  - key_components: ["Word embeddings for joint semantics", "Semantic volume keypoint encoding", "Cross-skeleton generalization support"]
datasets:
  - "IKEA ASM"
  - "Other assembly datasets"
key_insight: "One-hot encodings lose semantic relationships between joints; word embeddings capture meaningful anatomical and functional relationships"
improvements_over_036: "Enhanced generalization across different skeleton types and object classes through semantic representations"
---

# Summary

This follow-up to paper 036 introduces semantic information into skeleton-based action recognition by leveraging word embeddings. Instead of using traditional one-hot encodings for skeleton keypoints, the method constructs "semantic volumes" that encode meaningful relationships between joints and objects using pre-trained word vectors.

## Key Contributions

1. **Semantic Volume Encoding**: Novel keypoint encoding using word embeddings instead of one-hot vectors
2. **Generalization Enhancement**: Supports different skeleton types and object classes simultaneously
3. **End-to-end Learning**: Joint optimization of semantic representations and action classification

## Method

The approach works by:
1. Mapping skeleton keypoints and object labels to word embedding space
2. Constructing semantic volume representations that capture joint relationships
3. Processing through GCN with enhanced input representations
4. Enabling cross-domain generalization through shared semantic space

## Results

Demonstrates improved classification performance on assembly datasets with enhanced generalization capabilities compared to baseline skeleton-only methods.

## Relevance to POPW

Building on paper 036, this represents an advancement in skeleton-based methods for assembly recognition. POPW's approach should be compared against these semantic-enhanced methods.

## Citation

```bibtex
@article{aganian2025semantic,
  title={Including Semantic Information via Word Embeddings for Skeleton-based Action Recognition},
  author={Aganian, Dustin and Franze, Erik and Eisenbach, Markus and Gross, Horst-Michael},
  journal={arXiv preprint arXiv:2506.18721},
  year={2025}
}
```
