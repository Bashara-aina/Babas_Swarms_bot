---
title: Ponbagavathi Frame2Freq 2026
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
summary: 'Frame2Freq addresses a fundamental limitation in adapting image-pretrained
  backbones to video: existing time-domain adapters focus on static image cues and
  very fast temporal changes, missing cruci...'
wikilinks: []
confidence: medium
source: research
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
