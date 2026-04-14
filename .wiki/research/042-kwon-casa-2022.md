---
title: Kwon Casa 2022
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
summary: CASA addresses temporal alignment of fine-grained human actions, which is
  crucial for applications in robotics and mixed reality. The authors identify that
  state-of-the-art image-based methods prod...
wikilinks: []
confidence: medium
source: research
---

# Summary

CASA addresses temporal alignment of fine-grained human actions, which is crucial for applications in robotics and mixed reality. The authors identify that state-of-the-art image-based methods produce temporally discontinuous alignments without post-processing, and propose a skeleton-based self-supervised approach with novel 4D augmentation.

## Key Contributions

1. **Context-Aware Framework**: Uses self-attention and cross-attention to incorporate spatial-temporal context
2. **4D Skeletal Augmentation**: Novel augmentation technique operating in 4D (3D space + time) for skeleton representations
3. **Temporal Continuity**: Solves the temporal discontinuity problem plaguing image-based methods

## Method

CASA works by:
1. Extracting 3D skeleton sequences from videos using off-the-shelf pose estimators
2. Applying 4D augmentation (joint-wise and temporal transformations)
3. Learning alignment through self-supervised context-aware attention mechanisms
4. Predicting phase progress and aligning action sequences

## Results

Significantly improves phase progress and Kendall's Tau scores over previous state-of-the-art on three public datasets.

## Relevance to POPW

Temporal alignment and phase progress estimation are relevant for POPW's assembly step recognition task. CASA's self-supervised approach could benefit POPW's representation learning.

## Citation

```bibtex
@article{kwon2022casa,
  title={Context-Aware Sequence Alignment Using 4D Skeletal Augmentation},
  author={Kwon, Taein and Tekin, Bugra and Tang, Siyu and Pollefeys, Marc},
  journal={arXiv preprint arXiv:2204.12223},
  year={2022},
  note={CVPR 2022 Oral}
}
```
