---
title: Thiyakesan Order Matters 2025
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
summary: This paper tackles the challenge of recognizing nearly symmetric actions
  critical for human-robot collaboration - actions like picking up vs. placing down
  a tool, or opening vs. closing a drawer. T...
wikilinks: []
confidence: medium
source: research
---

# Summary

This paper tackles the challenge of recognizing nearly symmetric actions critical for human-robot collaboration - actions like picking up vs. placing down a tool, or opening vs. closing a drawer. The authors identify that conventional probing is permutation-invariant and blind to frame order, limiting its effectiveness for these temporally-sensitive actions.

## Key Contributions

1. **STEP Framework**: Self-attentive Temporal Embedding Probing that enforces temporal order
2. **Lightweight Solution**: Addresses compute constraints in real-world robotics applications
3. **Broad Benchmark Coverage**: Evaluated on HRI, industrial assembly, and driver assistance datasets

## Method

STEP enhances conventional probing with:
1. Frame-wise positional encodings to capture temporal order
2. A global CLS token for sequence-level representation
3. Simplified attention block for efficient temporal modeling

## Results

- **Nearly Symmetric Actions**: 4-10% improvement over conventional probing
- **Overall Benchmarks**: 6-15% improvement across action recognition benchmarks
- **Comparison**: Surpasses heavier PEFT methods and even fully fine-tuned models

## Relevance to POPW

Nearly symmetric actions are common in assembly tasks (attach/detach, insert/remove, tighten/loosen). STEP provides a lightweight approach relevant for POPW's industrial assembly focus.

## Citation

```bibtex
@article{thiyakesan2025order,
  title={Order Matters: On Parameter-Efficient Image-to-Video Probing for Recognizing Nearly Symmetric Actions},
  author={Ponbagavathi, Thinesh Thiyakesan and Roitberg, Alina},
  journal={arXiv preprint arXiv:2503.24298},
  year={2025},
  note={Accepted to ICRA 2026}
}
```
