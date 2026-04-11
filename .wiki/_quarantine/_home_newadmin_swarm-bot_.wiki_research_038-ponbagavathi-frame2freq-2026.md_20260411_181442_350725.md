---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/research/038-ponbagavathi-frame2freq-2026.md",
  "reason": "daily_fast_scan: score=0.200 < 0.3",
  "score": 0.2,
  "quarantined_at": "2026-04-11T18:14:42.350753"
}
---

---
paper_id: "038"
title: "Frame2Freq: Spectral Adapters for Fine-Grained Video Understanding"
authors: "Ponbagavathi, Thinesh Thiyakesan; Seibold, Constantin; Roitberg, Alina"
year: 2026
venue: "CVPR 2026 (Main Track)"
arxiv: "2602.18977"
doi: "10.48550/arXiv.2602.18977"
domain: "Assembly & Industrial Action Recognition"
popw_relevance: "CRITICAL - Current SOTA at 78.1% Top-1 on IKEA ASM; POPW must beat this benchmark"
key_contribution: "Frequency-aware adapters using FFT for spectral encoding during image-to-video adaptation of Vision Foundation Models"
tags:
  - spectral methods
  - frequency analysis
  - fine-grained action recognition
  - vision foundation models
  - parameter-efficient fine-tuning
  - CVPR 2026
sota_metrics:
  - dataset: "IKEA ASM"
    top1: "78.1%"
    top3: "N/A"
    notes: "CVPR 2026 Main Track; surpasses fully fine-tuned models on 4 of 5 datasets"
architecture:
  - type: "Vision Foundation Model Adapter"
  - key_components: ["FFT along time dimension", "Frequency-band specific embeddings", "Adaptive spectral highlighting"]
key_insight: "Time-domain adapters pick up static cues and fast flicker but miss medium-speed motion; spectral encoding captures multi-scale temporal dynamics"
code_url: "https://github.com/th-nesh/Frame2Freq"
---

# Summary

Frame2Freq addresses a fundamental limitation in adapting image-pretrained backbones to video: existing time-domain adapters focus on static image cues and very fast temporal changes, missing crucial medium-speed motion patterns that distinguish fine-grained actions (e.g., opening vs. closing a bottle).

## Key Contributions

1. **Spectral Encoding**: Uses Fast Fourier Transform (FFT) along time to learn frequency-band specific embeddings
2. **Multi-scale Temporal Modeling**: Adaptively highlights discriminative frequency ranges across different time scales
3. **PEFT Framework**: Parameter-efficient fine-tuning suitable for limited data scenarios

## Method

Frame2Freq operates by:
1. Applying FFT to video frames along temporal dimension
2. Learning frequency-band specific embeddings that highlight discriminative temporal patterns
3. Adapting Vision Foundation Models (VFMs) with spectral awareness
4. Outperforming both prior PEFT methods and fully fine-tuned models

## Results

- **IKEA ASM**: 78.1% Top-1 (Current SOTA for fine-grained action recognition)
- Surpasses fully fine-tuned models on 4 of 5 fine-grained activity recognition benchmarks
- Particularly effective for actions differing in medium-speed temporal patterns

## Relevance to POPW

**THIS IS THE PRIMARY SOTA BASELINE FOR POPW TO BEAT.**
- POPW Target: >75% Top-1 (stretch goal)
- Current SOTA Frame2Freq-ST: 78.1% on IKEA ASM
- POPW must demonstrate superior performance on fine-grained assembly actions

## Citation

```bibtex
@article{ponbagavathi2026frame2freq,
  title={Frame2Freq: Spectral Adapters for Fine-Grained Video Understanding},
  author={Ponbagavathi, Thinesh Thiyakesan and Seibold, Constantin and Roitberg, Alina},
  journal={arXiv preprint arXiv:2602.18977},
  year={2026},
  note={CVPR 2026 Main Track}
}
```
