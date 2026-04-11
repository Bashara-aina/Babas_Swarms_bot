---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/research/040-ponbagavathi-probing-foundation-2024.md",
  "reason": "daily_fast_scan: score=0.150 < 0.3",
  "score": 0.15000000000000002,
  "quarantined_at": "2026-04-11T18:14:42.336884"
}
---

---
paper_id: "040"
title: "Probing Fine-Grained Action Understanding and Cross-View Generalization of Foundation Models"
authors: "Ponbagavathi, Thinesh Thiyakesan; Peng, Kunyu; Roitberg, Alina"
year: 2024
venue: "arXiv preprint"
arxiv: "2407.15605"
doi: "10.48550/arXiv.2407.15605"
domain: "Assembly & Industrial Action Recognition"
popw_relevance: "Systematic study of foundation models for fine-grained action recognition; provides guidance for backbone selection"
key_contribution: "First systematic study of different foundation models and design choices for human activity recognition from unknown views"
tags:
  - foundation models
  - cross-view generalization
  - fine-grained action
  - video understanding
  - temporal aggregation
datasets:
  - "Multiple including industrial assembly datasets"
key_insight: "Popular benchmarks offer diverse views but only coarse actions; domain-specific datasets (industrial assembly) use limited static perspectives"
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
