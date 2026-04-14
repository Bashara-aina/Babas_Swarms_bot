---
title: Aganian Semantic Volume 2025
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
summary: This follow-up to paper 036 introduces semantic information into skeleton-based
  action recognition by leveraging word embeddings. Instead of using traditional one-hot
  encodings for skeleton keypoin...
wikilinks: []
confidence: medium
source: research
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
