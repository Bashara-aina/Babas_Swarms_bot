---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/research/039-thiyakesan-order-matters-2025.md",
  "reason": "daily_fast_scan: score=0.150 < 0.3",
  "score": 0.15000000000000002,
  "quarantined_at": "2026-04-11T18:14:42.425720"
}
---

---
paper_id: "039"
title: "Order Matters: On Parameter-Efficient Image-to-Video Probing for Recognizing Nearly Symmetric Actions"
authors: "Ponbagavathi, Thinesh Thiyakesan; Roitberg, Alina"
year: 2025 (ICRA 2026)
venue: "ICRA 2026"
arxiv: "2503.24298"
doi: "10.48550/arXiv.2503.24298"
domain: "Assembly & Industrial Action Recognition"
popw_relevance: "SOTA for nearly symmetric actions (pick up vs. place down); relevant for assembly manipulation recognition"
key_contribution: "STEP (Self-attentive Temporal Embedding Probing) models temporal order via frame-wise positional encodings and simplified attention"
tags:
  - parameter-efficient fine-tuning
  - image-to-video probing
  - symmetric actions
  - human-robot interaction
  - ICRA 2026
sota_metrics:
  - dataset: "HRI, Industrial Assembly, Driver Assistance benchmarks"
    notes: "4-10% improvement on nearly symmetric actions; 6-15% overall improvement over conventional probing"
architecture:
  - type: "Temporal Probing Extension"
  - key_components: ["Frame-wise positional encodings", "Global CLS token", "Simplified attention block"]
key_insight: "Probing is permutation-invariant and blind to frame order; STEP addresses this with lightweight temporal modeling"
code_url: "https://github.com/th-nesh/STEP"
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
