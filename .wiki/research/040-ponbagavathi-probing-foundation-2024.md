---
title: Ponbagavathi Probing Foundation 2024
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
summary: This paper provides the first systematic evaluation of how perspective changes
  affect different Vision Foundation Models (VFMs) in fine-grained human activity
  recognition. The authors compare multi...
wikilinks: []
confidence: medium
source: research
---

# Summary

This paper provides the first systematic evaluation of how perspective changes affect different Vision Foundation Models (VFMs) in fine-grained human activity recognition. The authors compare multiple backbone architectures and temporal fusion strategies, providing guidance for backbone selection in domain-specific applications.

## Key Contributions

1. **Systematic Benchmarking**: Comprehensive study of VFMs under view changes
2. **Architecture Comparison**: Image-based vs. video-based models with various temporal fusion strategies
3. **Cross-View Analysis**: Evaluation of generalization to unknown camera perspectives

## Method

The study evaluates:
1. Different VFM backbones (image-based and video-based)
2. Temporal aggregation strategies (score averaging vs. attention-based)
3. Performance under varying camera viewpoints

## Key Findings

- Standard benchmarks draw "artificially rosy picture" due to diverse views but coarse actions
- Domain-specific datasets (industrial assembly) typically have limited static perspectives
- Temporal aggregation mechanism significantly impacts cross-view generalization

## Relevance to POPW

POPW's approach must handle varying camera perspectives in industrial environments. This paper provides baseline understanding of how current VFMs perform on such challenges.

## Citation

```bibtex
@article{ponbagavathi2024probing,
  title={Probing Fine-Grained Action Understanding and Cross-View Generalization of Foundation Models},
  author={Ponbagavathi, Thinesh Thiyakesan and Peng, Kunyu and Roitberg, Alina},
  journal={arXiv preprint arXiv:2407.15605},
  year={2024}
}
```
